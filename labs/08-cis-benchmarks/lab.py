"""Two pinned CIS-style checks and a reversible node-metadata exercise."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

NS = os.environ['LAB_NAMESPACE']
NODE = 'cks-worker2'
CONFIG = '/var/lib/kubelet/config.yaml'
ROOT = Path(os.environ['REPO_ROOT'])
STATE = ROOT / '.local/lab08-state'
K = ['kubectl', '--kubeconfig', os.environ['LAB_KUBECONFIG'], '--context', 'kind-cks', '--request-timeout=10s']


def run(args, data=None, required=True):
    r = subprocess.run(args, input=data, text=True, capture_output=True, timeout=150)
    if required and r.returncode:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r


def k(*args, **kwargs):
    return run(K + list(args), **kwargs)


def dx(*args, **kwargs):
    return run(['docker', 'exec', NODE] + list(args), **kwargs)


def identity():
    obj = json.loads(run(['docker', 'inspect', NODE]).stdout)[0]
    if obj['Config']['Labels'].get('io.x-k8s.kind.cluster') != 'cks':
        raise RuntimeError('Target is not part of kind cluster cks')
    return obj['Id']


def metadata():
    mode, uid, gid, kind = dx('stat', '-c', '%a %u %g %F', CONFIG).stdout.strip().split(' ', 3)
    if kind not in ('regular file', 'regular empty file'):
        raise RuntimeError('Target is not a regular file; refusing operation')
    return {'mode': mode, 'uid': int(uid), 'gid': int(gid)}


def content():
    return dx('cat', CONFIG).stdout


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def command():
    pid = dx('systemctl', 'show', 'kubelet', '-p', 'MainPID', '--value').stdout.strip()
    if not pid.isdigit() or pid == '0':
        raise RuntimeError('Kubelet has no running main process')
    return dx('cat', f'/proc/{pid}/cmdline').stdout.rstrip('\x00').split('\x00')


def uses_config(cmd):
    return '--config=' + CONFIG in cmd or any(cmd[i:i+2] == ['--config', CONFIG] for i in range(len(cmd)))


def owner():
    obj = json.loads((STATE / 'owner.json').read_text())
    if obj['namespace'] != NS or obj['containerId'] != identity():
        raise RuntimeError('Saved namespace or container identity mismatch')
    return obj


def fixture():
    return {'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'health', 'labels': {'app': 'health'}}, 'spec': {
        'nodeSelector': {'kubernetes.io/hostname': NODE}, 'terminationGracePeriodSeconds': 1,
        'automountServiceAccountToken': False,
        'containers': [{'name': 'probe', 'image': 'busybox:1.37.0', 'command': ['sleep', 'infinity']}]}}


def restore(saved):
    metadata()  # Refuse symlinks before chown/chmod.
    if digest(content()) != saved['sha256']:
        raise RuntimeError('Configuration contents changed; recovery backup retained, inspect before restoring')
    dx('chown', f'{saved["uid"]}:{saved["gid"]}', CONFIG)
    dx('chmod', saved['mode'], CONFIG)
    if metadata() != {key: saved[key] for key in ('mode', 'uid', 'gid')}:
        raise RuntimeError('Metadata restore verification failed; recovery state retained')


def setup():
    cid = identity()
    if STATE.exists() or (ROOT / '.local/lab07-state').exists():
        raise RuntimeError('Existing node lab recovery state; complete cleanup first')
    if k('get', 'namespace', NS, '--ignore-not-found', '-o', 'name').stdout.strip():
        raise RuntimeError('Namespace exists; refusing reset')
    cmd = command()
    if not uses_config(cmd):
        raise RuntimeError('Kubelet does not use the expected config path')
    original = content()
    saved = dict(metadata(), namespace=NS, containerId=cid, sha256=digest(original), command=cmd)
    STATE.mkdir(mode=0o700)
    (STATE / 'config.yaml').write_text(original)
    (STATE / 'owner.json').write_text(json.dumps(saved, indent=2))
    try:
        k('create', 'namespace', NS)
        k('label', 'namespace', NS, 'cks-prep/lab=08')
        dx('chown', '10000:10000', CONFIG)
        dx('chmod', '0666', CONFIG)
        k('-n', NS, 'apply', '-f', '-', data=json.dumps(fixture()))
        k('-n', NS, 'wait', '--for=condition=Ready', 'pod/health', '--timeout=120s')
    except Exception:
        restore(saved)
        print('Setup failed; original metadata restored. Run cleanup before retrying.', flush=True)
        raise
    print(f'Exercise ready in {NS}; original metadata saved. Read TASK.md.')


def cleanup():
    saved = owner()
    restore(saved)
    ns = k('get', 'namespace', NS, '--ignore-not-found', '-o', 'json').stdout
    if ns.strip():
        if json.loads(ns)['metadata'].get('labels', {}).get('cks-prep/lab') != '08':
            raise RuntimeError('Metadata restored; refusing deletion without namespace ownership label')
        k('delete', 'namespace', NS, '--timeout=120s')
    shutil.rmtree(STATE)
    print('Original file metadata and content verified; namespace and recovery state removed.')


def findings():
    observed = metadata()
    mode = int(observed['mode'], 8)
    return [
        ('4.1.9', mode & ~0o600 == 0, f'mode={observed["mode"]}'),
        ('4.1.10', observed['uid'] == observed['gid'] == 0, f'uid={observed["uid"]}, gid={observed["gid"]}')]


def scan():
    owner()
    print(f'Targeted cis-1.12 checks on {NODE}:{CONFIG}; not a full benchmark scan.')
    items = findings()
    for control, ok, evidence in items:
        print(f'{"PASS" if ok else "FAIL"}: {control}: {evidence}')
    return not all(ok for _, ok, _ in items)


def verify():
    saved = owner()
    checks = []
    def check(label, ok):
        checks.append(bool(ok))
        print(('PASS' if ok else 'FAIL') + ': ' + label, flush=True)
    for control, ok, evidence in findings():
        check(f'{control}: {evidence}', ok)
    check('original file contents preserved', digest(content()) == saved['sha256'])
    cmd = command()
    check('active kubelet uses original config path and command', uses_config(cmd) and cmd == saved['command'])
    check('kubelet service active', dx('systemctl', 'is-active', '--quiet', 'kubelet', required=False).returncode == 0)
    ns = json.loads(k('get', 'namespace', NS, '-o', 'json').stdout)
    check('namespace ownership retained', ns['metadata'].get('labels', {}).get('cks-prep/lab') == '08')
    nodes = json.loads(k('get', 'nodes', '-o', 'json').stdout)['items']
    check('all three nodes Ready', len(nodes) == 3 and all(any(c['type'] == 'Ready' and c['status'] == 'True' for c in n['status']['conditions']) for n in nodes))
    check('API ready', k('get', '--raw=/readyz', required=False).stdout.strip() == 'ok')
    pods = json.loads(k('-n', NS, 'get', 'pods', '-o', 'json').stdout)['items']
    check('one preserved Ready health Pod on target worker', len(pods) == 1 and pods[0]['metadata']['name'] == 'health'
          and pods[0]['metadata'].get('labels') == {'app': 'health'}
          and pods[0]['spec'].get('nodeName') == NODE
          and pods[0]['spec'].get('automountServiceAccountToken') is False
          and len(pods[0]['spec'].get('containers', [])) == 1
          and pods[0]['spec']['containers'][0]['image'] == 'busybox:1.37.0'
          and pods[0]['spec']['containers'][0]['command'] == ['sleep', 'infinity']
          and any(c['type'] == 'Ready' and c['status'] == 'True' for c in pods[0]['status'].get('conditions', [])))
    r = k('-n', NS, 'exec', 'health', '--', 'echo', 'cks-lab-08-ready', required=False)
    check('container exec functional', r.returncode == 0 and r.stdout.strip() == 'cks-lab-08-ready')
    print(f'\n{sum(checks)} passed; {len(checks)-sum(checks)} failed. Scope: two controls plus lab integrity/health.')
    return not all(checks)


if __name__ == '__main__':
    try:
        if sys.argv[1] not in ('setup', 'cleanup', 'scan', 'verify'):
            raise RuntimeError('Unknown action')
        sys.exit(globals()[sys.argv[1]]())
    except (RuntimeError, OSError, ValueError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
