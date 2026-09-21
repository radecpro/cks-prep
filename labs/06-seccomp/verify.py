"""Read-only seccomp configuration, process and availability checks."""
import json
import os
import subprocess
import sys
from resources import SECURITY, resources

NS = os.environ['LAB_NAMESPACE']
BASE = ['kubectl', '--kubeconfig', os.environ['LAB_KUBECONFIG'], '--context', 'kind-cks', '--request-timeout=30s']
results = []


def run(args):
    return subprocess.run(BASE + args, text=True, capture_output=True, timeout=40)


def get(kind, name=None):
    r = run(['-n', NS, 'get', kind] + ([name] if name else []) + ['-o', 'json'])
    if r.returncode:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)


def check(label, ok):
    results.append(bool(ok))
    print(('PASS' if ok else 'FAIL') + ': ' + label, flush=True)


def subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    return expected == actual


def inspect(spec, label):
    psc = spec.get('securityContext', {})
    check(f'{label}: explicit Pod RuntimeDefault', psc.get('seccompProfile') == {'type': 'RuntimeDefault'})
    expected = resources()[1]['spec']['template']['spec']
    cs = {c['name']: c for c in spec.get('containers', [])}
    check(f'{label}: original two containers', set(cs) == {'web', 'observer'} and len(spec.get('containers', [])) == 2)
    for original in expected['containers']:
        name = original['name']
        c = cs.get(name, {})
        sc = c.get('securityContext', {})
        effective = sc.get('seccompProfile', psc.get('seccompProfile'))
        check(f'{label}: {name} effective RuntimeDefault', effective == {'type': 'RuntimeDefault'})
        non_seccomp = {k: v for k, v in sc.items() if k != 'seccompProfile'}
        intact = non_seccomp == SECURITY and all(c.get(k) == original.get(k) for k in ('image', 'command', 'args', 'volumeMounts'))
        intact &= not any(c.get(k) for k in ('env', 'envFrom', 'lifecycle', 'volumeDevices'))
        if name == 'web':
            intact &= subset(original['readinessProbe'], c.get('readinessProbe'))
        check(f'{label}: {name} fixture and other security settings preserved', intact)
    check(f'{label}: Pod isolation and volume preserved', spec.get('automountServiceAccountToken') is False
          and spec.get('serviceAccountName', 'default') == 'default'
          and not {k: v for k, v in psc.items() if k != 'seccompProfile'}
          and len(spec.get('volumes', [])) == 1
          and subset({'name': 'page', 'configMap': {'name': 'status-page'}}, spec['volumes'][0])
          and not any(spec.get(k) for k in ('hostNetwork', 'hostPID', 'hostIPC', 'shareProcessNamespace', 'initContainers', 'ephemeralContainers')))


def main():
    check('namespace ownership retained', get('namespace', NS)['metadata'].get('labels', {}).get('cks-prep/lab') == '06')
    dep = get('deployment', 'status')
    template = dep['spec']['template']
    inspect(template['spec'], 'template')
    check('Deployment labels and selector preserved', template['metadata']['labels'] == {'app': 'status'} and dep['spec']['selector'] == {'matchLabels': {'app': 'status'}})
    st = dep.get('status', {})
    check('completed rollout and one available replica', dep['spec']['replicas'] == 1 and st.get('observedGeneration', 0) >= dep['metadata']['generation'] and all(st.get(k) == 1 for k in ('replicas', 'readyReplicas', 'updatedReplicas', 'availableReplicas')))
    rs = {r['metadata']['uid'] for r in get('replicasets')['items'] if any(o['uid'] == dep['metadata']['uid'] for o in r['metadata'].get('ownerReferences', []))}
    pods = get('pods')['items']
    owned = [p for p in pods if not p['metadata'].get('deletionTimestamp') and any(o['uid'] in rs for o in p['metadata'].get('ownerReferences', []))]
    check('exactly one owned Ready Pod', len(pods) == len(owned) == 1 and any(c['type'] == 'Ready' and c['status'] == 'True' for c in owned[0].get('status', {}).get('conditions', [])))
    if len(owned) == 1:
        pod = owned[0]
        inspect(pod['spec'], 'running Pod')
        name = pod['metadata']['name']
        for container in ('web', 'observer'):
            r = run(['-n', NS, 'exec', name, '-c', container, '--', 'cat', '/proc/1/status'])
            fields = {line.split(':', 1)[0]: line.split(':', 1)[1].split() for line in r.stdout.splitlines() if ':' in line}
            check(f'{container}: PID 1 seccomp filter mode', r.returncode == 0 and fields.get('Seccomp') == ['2'])
            check(f'{container}: PID 1 identity and privilege constraints', r.returncode == 0 and fields.get('Uid') == ['10000'] * 4 and fields.get('Gid') == ['10000'] * 4 and fields.get('NoNewPrivs') == ['1'] and fields.get('CapEff') == ['0000000000000000'])
        r = run(['-n', NS, 'exec', name, '-c', 'web', '--', 'wget', '-q', '-T', '3', '-O', '-', f'http://status.{NS}.svc.cluster.local:8080/'])
        check('Service returns original response', r.returncode == 0 and r.stdout.strip() == 'cks-lab-06-ready')
    check('ConfigMap preserved', get('configmap', 'status-page').get('data') == {'index.html': 'cks-lab-06-ready\n'})
    svc = get('service', 'status')['spec']
    check('Service preserved', svc.get('selector') == {'app': 'status'} and len(svc.get('ports', [])) == 1 and subset({'port': 8080, 'targetPort': 8080, 'protocol': 'TCP'}, svc['ports'][0]))
    failures = len(results) - sum(results)
    print(f'\n{sum(results)} passed; {failures} failed.')
    return bool(failures)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        print(f'ERROR: verification incomplete: {error}', file=sys.stderr)
        sys.exit(1)
