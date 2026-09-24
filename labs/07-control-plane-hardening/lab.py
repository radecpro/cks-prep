"""Scoped kubelet lab lifecycle and read-only grading, with durable rollback."""
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

NS = os.environ['LAB_NAMESPACE']
NODE = 'cks-worker2'
CONFIG = '/var/lib/kubelet/config.yaml'
STATE = Path(os.environ['REPO_ROOT']) / '.local/lab07-state'
K = ['kubectl', '--kubeconfig', os.environ['LAB_KUBECONFIG'], '--context', 'kind-cks', '--request-timeout=10s']


def run(args, data=None, required=True):
    r = subprocess.run(args, input=data, text=True, capture_output=True, timeout=150)
    if required and r.returncode:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r


def k(*args, **kwargs):
    return run(K + list(args), **kwargs)


def dx(*args, **kwargs):
    return run(['docker', 'exec', '-i', NODE] + list(args), **kwargs)


def identity():
    obj = json.loads(run(['docker', 'inspect', NODE]).stdout)[0]
    if obj['Config']['Labels'].get('io.x-k8s.kind.cluster') != 'cks':
        raise RuntimeError('Target is not a node of kind cluster cks')
    return obj['Id']


def effective():
    return json.loads(k('get', '--raw', f'/api/v1/nodes/{NODE}/proxy/configz').stdout)['kubeletconfig']


def wait_config(expected):
    deadline = time.monotonic() + 100
    while time.monotonic() < deadline:
        try:
            if effective() == expected:
                return
        except RuntimeError:
            pass
        time.sleep(2)
    raise RuntimeError('Effective kubelet configuration did not converge; recovery state retained')


def write_config(text):
    dx('sh', '-ec', 'cat > /var/lib/kubelet/config.yaml.lab07.tmp; chmod --reference=/var/lib/kubelet/config.yaml /var/lib/kubelet/config.yaml.lab07.tmp; chown --reference=/var/lib/kubelet/config.yaml /var/lib/kubelet/config.yaml.lab07.tmp; mv /var/lib/kubelet/config.yaml.lab07.tmp /var/lib/kubelet/config.yaml', data=text)


def owner():
    obj = json.loads((STATE / 'owner.json').read_text())
    if obj['namespace'] != NS or obj['containerId'] != identity():
        raise RuntimeError('Saved ownership or container identity mismatch; refusing node mutation')
    return obj


def fixtures():
    return [
        {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'health-page'}, 'data': {'index.html': 'cks-lab-07-ready\n'}},
        {'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'health', 'labels': {'app': 'health'}}, 'spec': {
            'nodeSelector': {'kubernetes.io/hostname': NODE}, 'terminationGracePeriodSeconds': 1, 'automountServiceAccountToken': False,
            'containers': [{'name': 'web', 'image': 'busybox:1.37.0', 'command': ['httpd'], 'args': ['-f', '-p', '8080', '-h', '/www'],
                'volumeMounts': [{'name': 'page', 'mountPath': '/www', 'readOnly': True}],
                'readinessProbe': {'httpGet': {'path': '/', 'port': 8080}}}],
            'volumes': [{'name': 'page', 'configMap': {'name': 'health-page'}}]}},
        {'apiVersion': 'v1', 'kind': 'Service', 'metadata': {'name': 'health'}, 'spec': {'selector': {'app': 'health'}, 'ports': [{'port': 8080, 'targetPort': 8080}]}}
    ]


def setup():
    cid = identity()
    if STATE.exists():
        raise RuntimeError('Existing lab07-state; complete cleanup first')
    found = k('get', 'namespace', NS, '-o', 'name', '--ignore-not-found').stdout
    if found.strip():
        raise RuntimeError('Namespace already exists; refusing reset')
    before = effective()
    if before.get('readOnlyPort', 0) != 0 or before['authentication']['anonymous']['enabled'] or before['authorization']['mode'] != 'Webhook' or not before['authentication']['webhook']['enabled']:
        raise RuntimeError('Unexpected insecure baseline; refusing to overwrite existing node work')
    original = dx('cat', CONFIG).stdout
    if original.count('  anonymous:\n    enabled: false') != 1 or re.search(r'^readOnlyPort:', original, re.M):
        raise RuntimeError('Unsupported source layout; refusing ambiguous configuration edit')
    insecure = original.replace('  anonymous:\n    enabled: false', '  anonymous:\n    enabled: true') + '\nreadOnlyPort: 10255\n'
    STATE.mkdir(mode=0o700)
    (STATE / 'config.yaml').write_text(original)
    (STATE / 'effective.json').write_text(json.dumps(before))
    (STATE / 'owner.json').write_text(json.dumps({'namespace': NS, 'containerId': cid}))
    try:
        k('create', 'namespace', NS)
        k('label', 'namespace', NS, 'cks-prep/lab=07')
        write_config(insecure)
        dx('systemctl', 'restart', 'kubelet')
        expected = copy.deepcopy(before)
        expected['readOnlyPort'] = 10255
        expected['authentication']['anonymous']['enabled'] = True
        wait_config(expected)
        k('-n', NS, 'apply', '-f', '-', data=json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': fixtures()}))
        k('-n', NS, 'wait', '--for=condition=Ready', 'pod/health', '--timeout=120s')
    except Exception:
        print('Setup failed; attempting original node configuration restore.', flush=True)
        write_config(original)
        dx('systemctl', 'restart', 'kubelet')
        print('Recovery state retained; run cleanup.sh before retrying.', flush=True)
        raise
    print(f'Exercise ready in {NS}; worker backup saved. Read TASK.md.')


def cleanup():
    owner()
    original = (STATE / 'config.yaml').read_text()
    write_config(original)
    dx('systemctl', 'restart', 'kubelet')
    wait_config(json.loads((STATE / 'effective.json').read_text()))
    if dx('cat', CONFIG).stdout != original:
        raise RuntimeError('Restored file differs from backup')
    k('wait', '--for=condition=Ready', 'node/' + NODE, '--timeout=120s')
    ns = k('get', 'namespace', NS, '-o', 'json', '--ignore-not-found').stdout
    if ns.strip():
        if json.loads(ns)['metadata'].get('labels', {}).get('cks-prep/lab') != '07':
            raise RuntimeError('Node restored; refusing to delete namespace without ownership label')
        k('delete', 'namespace', NS, '--timeout=120s')
    shutil.rmtree(STATE)
    print('Original worker file and effective configuration restored; lab namespace and recovery state removed.')


def subset(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and all(key in b and subset(value, b[key]) for key, value in a.items())
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(subset(x, y) for x, y in zip(a, b))
    return a == b


def verify():
    owner()
    checks = []
    def check(label, ok):
        checks.append(bool(ok))
        print(('PASS' if ok else 'FAIL') + ': ' + label, flush=True)
    actual = effective()
    original = json.loads((STATE / 'effective.json').read_text())
    disk = dx('cat', CONFIG).stdout
    # Support both YAML scalar edits and a valid JSON form without installing a YAML parser.
    try:
        disk_obj = json.loads(disk)
        disk_closed = disk_obj.get('readOnlyPort') == 0
        disk_anon = disk_obj['authentication']['anonymous']['enabled'] is False
    except (ValueError, KeyError):
        disk_closed = bool(re.search(r'^readOnlyPort:\s*0\s*(?:#.*)?$', disk, re.M))
        disk_anon = bool(re.search(r'^authentication:\s*\n\s+anonymous:\s*\n\s+enabled:\s*false\s*(?:#.*)?$', disk, re.M))
    check('disk read-only port explicitly disabled', disk_closed)
    check('disk anonymous authentication disabled', disk_anon)
    check('effective read-only port disabled', actual.get('readOnlyPort', 0) == 0)
    check('effective anonymous authentication disabled', actual['authentication']['anonymous']['enabled'] is False)
    expected = copy.deepcopy(actual)
    if 'readOnlyPort' in original:
        expected['readOnlyPort'] = original['readOnlyPort']
    else:
        expected.pop('readOnlyPort', None)
    expected['authentication']['anonymous']['enabled'] = original['authentication']['anonymous']['enabled']
    check('other effective kubelet settings preserved', expected == original)
    check('kubelet service active', dx('systemctl', 'is-active', '--quiet', 'kubelet', required=False).returncode == 0)
    check('local read-only port refuses connections', dx('curl', '--noproxy', '*', '-sS', '--max-time', '3', '-o', '/dev/null', 'http://127.0.0.1:10255/pods', required=False).returncode == 7)
    node = json.loads(k('get', 'node', NODE, '-o', 'json').stdout)
    ip = next(a['address'] for a in node['status']['addresses'] if a['type'] == 'InternalIP')
    remote = run(['docker', 'exec', 'cks-control-plane', 'curl', '--noproxy', '*', '-sS', '--max-time', '3', '-o', '/dev/null', f'http://{ip}:10255/pods'], required=False)
    check('cross-node read-only port refuses connections', remote.returncode == 7)
    r = dx('curl', '--noproxy', '*', '-ksS', '--max-time', '3', '-o', '/dev/null', '-w', '%{http_code}', 'https://127.0.0.1:10250/pods', required=False)
    check('anonymous secure request receives HTTP 401', r.returncode == 0 and r.stdout == '401')
    nodes = json.loads(k('get', 'nodes', '-o', 'json').stdout)['items']
    check('all three nodes Ready', len(nodes) == 3 and all(any(c['type'] == 'Ready' and c['status'] == 'True' for c in n['status']['conditions']) for n in nodes))
    check('API ready', k('get', '--raw=/readyz', required=False).stdout.strip() == 'ok')
    for fixture in fixtures():
        live = json.loads(k('-n', NS, 'get', fixture['kind'], fixture['metadata']['name'], '-o', 'json').stdout)
        check(f'{fixture["kind"]} fixture preserved', subset(fixture, live))
    pod = json.loads(k('-n', NS, 'get', 'pod', 'health', '-o', 'json').stdout)
    check('health Pod Ready on target worker', pod['spec'].get('nodeName') == NODE and any(c['type'] == 'Ready' and c['status'] == 'True' for c in pod['status'].get('conditions', [])))
    r = k('-n', NS, 'exec', 'health', '--', 'wget', '-q', '-T', '3', '-O', '-', f'http://health.{NS}.svc.cluster.local:8080/', required=False)
    check('exec and Service HTTP work', r.returncode == 0 and r.stdout.strip() == 'cks-lab-07-ready')
    check('container logs accessible', k('-n', NS, 'logs', 'health', required=False).returncode == 0)
    print(f'\n{sum(checks)} passed; {len(checks) - sum(checks)} failed.')
    return not all(checks)


if __name__ == '__main__':
    try:
        if sys.argv[1] not in ('setup', 'verify', 'cleanup'):
            raise RuntimeError('Unknown action')
        sys.exit(globals()[sys.argv[1]]())
    except (RuntimeError, KeyError, ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
