"""Read-only grading of Secret projection, exposure and application health."""
import base64
import json
import os
import subprocess
import sys
from resources import SECRET, SCRIPT, SECURITY

NS = os.environ['LAB_NAMESPACE']
BASE = ['kubectl', '--kubeconfig', os.environ['LAB_KUBECONFIG'], '--context', 'kind-cks', '--request-timeout=30s']
results = []


def run(args):
    return subprocess.run(BASE + args, text=True, capture_output=True, timeout=40)


def get(kind, name=None):
    r = run(['-n', NS, 'get', kind] + ([name] if name else []) + ['-o', 'json'])
    if r.returncode:
        raise RuntimeError(f'Cannot read {kind}: {r.stderr}')
    return json.loads(r.stdout)


def check(label, ok):
    results.append(bool(ok))
    print(('PASS' if ok else 'FAIL') + ': ' + label, flush=True)


def subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    return expected == actual


def inspect_spec(spec, label):
    containers = {c['name']: c for c in spec.get('containers', [])}
    check(f'{label}: original containers and identity', set(containers) == {'app', 'observer'} and all(
        c.get('image') == 'busybox:1.37.0' and c.get('securityContext') == SECURITY
        and c.get('command') == (['sh', '/opt/app/start.sh'] if name == 'app' else ['sleep', 'infinity'])
        and not c.get('args') for name, c in containers.items()))
    check(f'{label}: no environment injection', all(not c.get('env') and not c.get('envFrom') for c in containers.values()))
    check(f'{label}: Pod security and service account preserved', spec.get('securityContext') == {'fsGroup': 10000}
          and spec.get('automountServiceAccountToken') is False and spec.get('serviceAccountName', 'default') == 'default'
          and not any(spec.get(k) for k in ('hostNetwork', 'hostPID', 'hostIPC', 'shareProcessNamespace', 'initContainers', 'ephemeralContainers')))
    volumes = {v['name']: v for v in spec.get('volumes', [])}
    check(f'{label}: original volume sources only', set(volumes) == {'credentials', 'scripts'}
          and subset({'configMap': {'name': 'app-script'}}, volumes.get('scripts'))
          and set(volumes.get('credentials', {})) == {'name', 'secret'})
    secret = volumes.get('credentials', {}).get('secret', {})
    items = secret.get('items', [])
    check(f'{label}: only password projected with mode 0440', secret.get('secretName') == 'db-credentials'
          and len(items) == 1 and items[0].get('key') == 'password' and items[0].get('path') == 'password'
          and items[0].get('mode', secret.get('defaultMode', 420)) == 288 and not secret.get('optional', False))
    mounts = containers.get('app', {}).get('volumeMounts', [])
    expected = [{'name': 'credentials', 'mountPath': '/etc/db', 'readOnly': True}, {'name': 'scripts', 'mountPath': '/opt/app', 'readOnly': True}]
    check(f'{label}: app has exact read-only mounts without subPath', sorted(mounts, key=lambda m: m['name']) == expected)
    check(f'{label}: observer has no volume mounts', not containers.get('observer', {}).get('volumeMounts'))
    check(f'{label}: readiness probe preserved', subset({'httpGet': {'path': '/', 'port': 8080}, 'periodSeconds': 2}, containers.get('app', {}).get('readinessProbe')))


def execute(pod, container, command):
    return run(['-n', NS, 'exec', pod, '-c', container, '--'] + command)


def main():
    check('namespace ownership retained', get('namespace', NS)['metadata'].get('labels', {}).get('cks-prep/lab') == '05')
    secret = get('secret', 'db-credentials')
    expected = {k: base64.b64encode(v.encode()).decode() for k, v in SECRET.items()}
    check('original Secret keys and values preserved', secret.get('type') == 'Opaque' and secret.get('data') == expected)
    check('original application script preserved', get('configmap', 'app-script').get('data') == {'start.sh': SCRIPT})
    dep = get('deployment', 'payments')
    template = dep['spec']['template']
    inspect_spec(template['spec'], 'template')
    check('Deployment labels and selector preserved', template['metadata']['labels'] == {'app': 'payments'} and dep['spec']['selector'] == {'matchLabels': {'app': 'payments'}})
    st = dep.get('status', {})
    check('completed rollout with one available replica', dep['spec']['replicas'] == 1 and st.get('observedGeneration', 0) >= dep['metadata']['generation'] and all(st.get(k) == 1 for k in ('replicas', 'readyReplicas', 'updatedReplicas', 'availableReplicas')))
    rs = {r['metadata']['uid'] for r in get('replicasets')['items'] if any(o['uid'] == dep['metadata']['uid'] for o in r['metadata'].get('ownerReferences', []))}
    pods = get('pods')['items']
    owned = [p for p in pods if not p['metadata'].get('deletionTimestamp') and any(o['uid'] in rs for o in p['metadata'].get('ownerReferences', []))]
    check('exactly one owned Ready Pod', len(pods) == len(owned) == 1 and any(c['type'] == 'Ready' and c['status'] == 'True' for c in owned[0].get('status', {}).get('conditions', [])))
    if len(owned) == 1:
        pod = owned[0]
        name = pod['metadata']['name']
        inspect_spec(pod['spec'], 'running Pod')
        r = execute(name, 'app', ['cat', '/etc/db/password'])
        check('application reads original password file', r.returncode == 0 and r.stdout == SECRET['password'])
        r = execute(name, 'app', ['stat', '-L', '-c', '%a', '/etc/db/password'])
        check('runtime password mode is 0440', r.returncode == 0 and r.stdout.strip() == '440')
        r = execute(name, 'app', ['sh', '-c', 'test ! -e /etc/db/admin-token && test "$(ls /etc/db)" = password'])
        check('application directory exposes only password', r.returncode == 0)
        r = execute(name, 'observer', ['sh', '-c', 'test ! -e /etc/db/password && test ! -e /etc/db/admin-token'])
        check('observer cannot see credential files', r.returncode == 0)
        for container in ('app', 'observer'):
            r = execute(name, container, ['cat', '/proc/1/environ'])
            entries = r.stdout.split('\x00')
            check(f'{container}: process environment contains no credentials', r.returncode == 0
                  and not any(value in r.stdout for value in SECRET.values())
                  and not any(e.split('=', 1)[0] in ('DB_PASSWORD', 'password', 'admin-token') for e in entries))
            r = run(['-n', NS, 'logs', name, '-c', container])
            check(f'{container}: current logs contain no credential values', r.returncode == 0 and not any(v in r.stdout for v in SECRET.values()))
        r = execute(name, 'app', ['wget', '-q', '-T', '3', '-O', '-', f'http://payments.{NS}.svc.cluster.local:8080/'])
        check('Service returns original ready response', r.returncode == 0 and r.stdout.strip() == 'cks-lab-05-ready')
    svc = get('service', 'payments')['spec']
    check('original Service preserved', svc.get('selector') == {'app': 'payments'} and len(svc.get('ports', [])) == 1 and subset({'port': 8080, 'targetPort': 8080, 'protocol': 'TCP'}, svc['ports'][0]))
    failures = len(results) - sum(results)
    print(f'\n{sum(results)} passed; {failures} failed.')
    return bool(failures)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        print(f'ERROR: verification incomplete: {error}', file=sys.stderr)
        sys.exit(1)
