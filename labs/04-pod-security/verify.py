"""Inspect learner resources and submit admission dry runs; never repair."""
import copy
import json
import os
import subprocess
import sys
import uuid

NS = os.environ['LAB_NAMESPACE']
BASE = ['kubectl', '--kubeconfig', os.environ['LAB_KUBECONFIG'], '--context', 'kind-cks', '--request-timeout=30s']
results = []


def run(args, data=None):
    return subprocess.run(BASE + args, input=data, text=True, capture_output=True, timeout=40)


def get(kind, name=None):
    r = run(['-n', NS, 'get', kind] + ([name] if name else []) + ['-o', 'json'])
    if r.returncode:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)


def check(label, ok):
    results.append(bool(ok))
    print(('PASS' if ok else 'FAIL') + ': ' + label, flush=True)


def admission(spec):
    spec = copy.deepcopy(spec)
    for key in ('nodeName',):
        spec.pop(key, None)
    obj = {'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'admission-check-' + uuid.uuid4().hex[:12], 'namespace': NS}, 'spec': spec}
    return run(['-n', NS, 'create', '--dry-run=server', '-f', '-'], json.dumps(obj))


def fixture(spec):
    cs = spec.get('containers', [])
    if len(cs) != 1:
        return False
    c = cs[0]
    return (c.get('name') == 'web' and c.get('image') == 'busybox:1.37.0'
            and c.get('command') == ['httpd'] and c.get('args') == ['-f', '-p', '8080', '-h', '/www']
            and c.get('readinessProbe', {}).get('httpGet', {}).get('port') == 8080
            and c.get('readinessProbe', {}).get('httpGet', {}).get('path') == '/'
            and c.get('volumeMounts') == [{'name': 'page', 'mountPath': '/www', 'readOnly': True}, *([m for m in c.get('volumeMounts', []) if m['name'].startswith('kube-api-access-')])]
            and any(v['name'] == 'page' and v.get('configMap', {}).get('name') == 'status-page' for v in spec.get('volumes', []))
            and all(v['name'] == 'page' or v['name'].startswith('kube-api-access-') for v in spec.get('volumes', []))
            and not any(spec.get(k) for k in ('initContainers', 'ephemeralContainers', 'hostNetwork', 'hostPID', 'hostIPC')))


def main():
    labels = get('namespace', NS)['metadata'].get('labels', {})
    check('ownership label preserved', labels.get('cks-prep/lab') == '04')
    for mode in ('enforce', 'warn', 'audit'):
        check(f'{mode}: Restricted pinned to v1.37', labels.get('pod-security.kubernetes.io/' + mode) == 'restricted' and labels.get('pod-security.kubernetes.io/' + mode + '-version') == 'v1.37')
    dep = get('deployment', 'status')
    template = dep['spec']['template']
    spec = template['spec']
    check('Deployment fixture preserved', fixture(spec) and template['metadata']['labels'] == {'app': 'status'})
    status = dep.get('status', {})
    check('one available replica and completed rollout', dep['spec']['replicas'] == 1 and status.get('observedGeneration', 0) >= dep['metadata']['generation'] and all(status.get(k) == 1 for k in ('replicas', 'updatedReplicas', 'readyReplicas', 'availableReplicas')))
    rs_ids = {r['metadata']['uid'] for r in get('replicasets')['items'] if any(o['uid'] == dep['metadata']['uid'] for o in r['metadata'].get('ownerReferences', []))}
    pods = get('pods')['items']
    owned = [p for p in pods if any(o['uid'] in rs_ids for o in p['metadata'].get('ownerReferences', [])) and not p['metadata'].get('deletionTimestamp')]
    check('exactly one live owned Pod and no extra Pods', len(owned) == 1 and len(pods) == 1)
    check('template accepted for fresh Pod admission', admission(spec).returncode == 0)
    for field, token in [('privileged', 'privileged'), ('allowPrivilegeEscalation', 'allowPrivilegeEscalation')]:
        bad = copy.deepcopy(spec)
        bad['containers'][0].setdefault('securityContext', {})[field] = True
        if field == 'privileged':
            # Avoid contradictory settings rejected by API validation before PSA.
            bad['containers'][0]['securityContext']['allowPrivilegeEscalation'] = True
            bad['containers'][0]['securityContext'].pop('seccompProfile', None)
            bad.get('securityContext', {}).pop('seccompProfile', None)
        r = admission(bad)
        check(f'admission rejects {field}=true', r.returncode != 0 and 'violates PodSecurity' in r.stderr and token in r.stderr)
    if len(owned) == 1:
        pod = owned[0]
        check('running Pod fixture preserved and Ready', fixture(pod['spec']) and pod['metadata']['labels'].get('app') == 'status' and any(c['type'] == 'Ready' and c['status'] == 'True' for c in pod.get('status', {}).get('conditions', [])))
        check('running Pod spec satisfies admission', admission(pod['spec']).returncode == 0)
        name = pod['metadata']['name']
        r = run(['-n', NS, 'exec', name, '--', 'cat', '/proc/1/status'])
        lines = {line.split(':', 1)[0]: line.split(':', 1)[1].split() for line in r.stdout.splitlines() if ':' in line}
        check('web process UID/GID 10000', r.returncode == 0 and lines.get('Uid') == ['10000'] * 4 and lines.get('Gid') == ['10000'] * 4)
        r = run(['-n', NS, 'exec', name, '--', 'wget', '-q', '-T', '3', '-O', '-', f'http://status.{NS}.svc.cluster.local:8080/'])
        check('Service HTTP returns original page', r.returncode == 0 and r.stdout.strip() == 'cks-lab-04-ready')
    cm = get('configmap', 'status-page')
    check('ConfigMap unchanged', cm.get('data') == {'index.html': 'cks-lab-04-ready\n'})
    svc = get('service', 'status')['spec']
    check('Service unchanged', svc.get('selector') == {'app': 'status'} and len(svc.get('ports', [])) == 1 and svc['ports'][0]['port'] == 8080 and svc['ports'][0]['targetPort'] == 8080)
    failures = len(results) - sum(results)
    print(f'\n{sum(results)} passed; {failures} failed.')
    return bool(failures)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        print(f'ERROR: verification could not complete: {error}', file=sys.stderr)
        sys.exit(1)
