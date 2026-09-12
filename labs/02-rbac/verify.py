"""Check RBAC and token exposure without repairing learner resources."""
import base64
import itertools
import json
import subprocess
import sys

ns = sys.argv[2]
base = ['kubectl', '--kubeconfig', sys.argv[1], '--context', 'kind-cks', '--request-timeout=15s']
failures = []


def command(args):
    return subprocess.run(base + args, capture_output=True, text=True, timeout=25)


def run(*args):
    r = command(['-n', ns, *args])
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or 'kubectl failed')
    return r.stdout


def get(kind, name=None):
    return json.loads(run('get', kind, *([name] if name else []), '-o', 'json'))


def check(ok, label):
    print(('PASS' if ok else 'FAIL') + ': ' + label)
    if not ok:
        failures.append(label)


def authorization(sa, verb, resource, expected, namespace=None, subresource=None):
    args = ['-n', namespace or ns, 'auth', 'can-i', verb, resource,
            '--as', f'system:serviceaccount:{ns}:{sa}',
            '--as-group', 'system:authenticated', '--as-group', 'system:serviceaccounts',
            '--as-group', f'system:serviceaccounts:{ns}']
    if subresource:
        args += ['--subresource', subresource]
    r = command(args)
    answer = r.stdout.strip()
    valid = (answer == 'yes' and r.returncode == 0) or (answer == 'no' and r.returncode == 1)
    check(valid and (answer == 'yes') == expected,
          f'{sa}: {verb} {resource}{"/" + subresource if subresource else ""} in {namespace or ns} => '
          + ('allow' if expected else 'deny'))
    if not valid:
        print('Authorization check error: ' + r.stderr.strip())


def workload(spec, sa, label):
    check(spec.get('serviceAccountName') == 'inspector', label + ': inspector identity')
    effective = spec.get('automountServiceAccountToken', sa.get('automountServiceAccountToken', True))
    check(effective is False, label + ': token automount disabled')
    check(not spec.get('volumes') and not spec.get('initContainers') and not spec.get('ephemeralContainers'),
          label + ': no token volumes or extra container types')
    containers = spec.get('containers', [])
    check(len(containers) == 1 and containers[0]['name'] == 'worker'
          and containers[0].get('image') == 'busybox:1.37.0'
          and containers[0].get('command') == ['sleep'] and containers[0].get('args') == ['infinity']
          and not containers[0].get('volumeMounts'), label + ': original workload preserved')


def main():
    sa = get('serviceaccount', 'inspector')
    check(sa.get('automountServiceAccountToken') is False, 'ServiceAccount token automount explicitly disabled')
    roles = get('roles')['items']
    bindings = get('rolebindings')['items']
    check([r['metadata']['name'] for r in roles] == ['observer-access'], 'only original Role exists')
    check([r['metadata']['name'] for r in bindings] == ['observer-access'], 'only original RoleBinding exists')
    role = get('role', 'observer-access')
    actual = set()
    clean_rules = True
    for rule in role.get('rules', []):
        clean_rules &= not rule.get('nonResourceURLs')
        for group, resource, verb, name in itertools.product(rule.get('apiGroups', []), rule.get('resources', []),
                                                            rule.get('verbs', []), rule.get('resourceNames') or [None]):
            actual.add((group, resource, verb, name))
    expected = {('', 'pods', verb, None) for verb in ('get', 'list', 'watch')}
    expected |= {('', 'pods/log', 'get', None), ('', 'configmaps', 'get', 'app-config')}
    check(clean_rules and actual == expected, 'Role grants exactly the required resource permissions')
    binding = get('rolebinding', 'observer-access')
    subjects = binding.get('subjects', [])
    check(len(subjects) == 1 and subjects[0].get('kind') == 'ServiceAccount'
          and subjects[0].get('name') == 'inspector' and subjects[0].get('namespace') == ns
          and binding.get('roleRef') == {'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'Role', 'name': 'observer-access'},
          'binding targets only inspector and the original Role')
    for verb in ('get', 'list', 'watch'):
        authorization('inspector', verb, 'pods', True)
    authorization('inspector', 'get', 'pods', True, subresource='log')
    authorization('inspector', 'get', 'configmaps/app-config', True)
    for verb, resource, subresource in [
        ('get', 'configmaps/internal-config', None), ('list', 'configmaps', None), ('watch', 'configmaps', None),
        ('get', 'secrets/demo-secret', None), ('list', 'secrets', None), ('create', 'pods', None),
        ('delete', 'pods', None), ('patch', 'deployments.apps', None), ('create', 'pods', 'exec'),
        ('create', 'pods', 'attach'), ('create', 'serviceaccounts/inspector', 'token'),
        ('create', 'rolebindings.rbac.authorization.k8s.io', None), ('get', 'nodes', None)]:
        authorization('inspector', verb, resource, False, subresource=subresource)
    authorization('inspector', 'list', 'pods', False, namespace='default')
    for verb, resource in [('list', 'pods'), ('get', 'configmaps/app-config'), ('get', 'secrets/demo-secret')]:
        authorization('default', verb, resource, False)
    deployment = get('deployment', 'observer')
    workload(deployment['spec']['template']['spec'], sa, 'Deployment')
    status = deployment.get('status', {})
    check(deployment['spec'].get('replicas') == 1
          and status.get('observedGeneration', 0) >= deployment['metadata']['generation']
          and all(status.get(key) == 1 for key in ('replicas', 'updatedReplicas', 'readyReplicas', 'availableReplicas')),
          'one available replica and completed rollout')
    owners = {r['metadata']['uid'] for r in get('replicasets')['items']
              if any(o['uid'] == deployment['metadata']['uid'] for o in r['metadata'].get('ownerReferences', []))}
    pods = [p for p in get('pods')['items'] if not p['metadata'].get('deletionTimestamp')
            and any(o['uid'] in owners for o in p['metadata'].get('ownerReferences', []))]
    check(len(pods) == 1, 'one active Deployment-owned Pod')
    for pod in pods:
        workload(pod['spec'], sa, 'Pod')
        check(any(c['type'] == 'Ready' and c['status'] == 'True' for c in pod.get('status', {}).get('conditions', [])), 'Pod Ready')
        r = command(['-n', ns, 'exec', pod['metadata']['name'], '-c', 'worker', '--', 'sh', '-c',
                     'if test -e /var/run/secrets/kubernetes.io/serviceaccount/token; then echo present; else echo absent; fi'])
        check(r.returncode == 0 and r.stdout.strip() == 'absent', 'runtime standard token path absent')
    for name, value in [('app-config', 'observe'), ('internal-config', 'internal')]:
        check(get('configmap', name).get('data') == {'mode': value}, name + ' unchanged')
    secret = get('secret', 'demo-secret').get('data', {})
    check(secret == {'password': base64.b64encode(b'synthetic-lab-value').decode()}, 'synthetic Secret unchanged')


try:
    main()
except (RuntimeError, ValueError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
    check(False, 'unable to grade: ' + str(error))
print(f'\nResult: {len(failures)} failed checks. ' + ('PASS' if not failures else 'NOT YET PASSING'))
sys.exit(1 if failures else 0)
