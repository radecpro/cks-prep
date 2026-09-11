"""Read-only lab grader; checks requirements without modifying cluster resources."""
import json
import subprocess
import sys

base = ['kubectl', '--kubeconfig', sys.argv[1], '--context', 'kind-cks',
        '--request-timeout=15s', '-n', sys.argv[2]]
failures = []


def run(*args):
    result = subprocess.run(base + list(args), capture_output=True, text=True, timeout=25)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'kubectl failed')
    return result.stdout


def get(kind, name=None):
    return json.loads(run('get', kind, *([name] if name else []), '-o', 'json'))


def check(ok, label):
    print(('PASS' if ok else 'FAIL') + ': ' + label)
    if not ok:
        failures.append(label)


def inspect_spec(spec, label):
    containers = spec.get('containers', [])
    check(len(containers) == 1 and containers[0]['name'] == 'web', label + ': original container only')
    check(not spec.get('initContainers') and not spec.get('ephemeralContainers')
          and not any(spec.get(k) for k in ('hostPID', 'hostIPC', 'hostNetwork'))
          and not any('hostPath' in v for v in spec.get('volumes', [])), label + ': no added containers or host access')
    for container in containers:
        security = container.get('securityContext', {})
        effective = dict(spec.get('securityContext', {}))
        effective.update(security)
        check(effective.get('runAsUser') == 10000 and effective.get('runAsGroup') == 10000,
              label + ': UID/GID 10000')
        check(effective.get('runAsNonRoot') is True, label + ': non-root required')
        check(security.get('privileged', False) is False, label + ': not privileged')
        check(security.get('allowPrivilegeEscalation') is False, label + ': no privilege escalation')
        caps = security.get('capabilities', {})
        check('ALL' in caps.get('drop', []) and not caps.get('add'), label + ': all capabilities dropped, none added')
        check(security.get('readOnlyRootFilesystem') is True, label + ': read-only root filesystem')
        probe = container.get('readinessProbe', {}).get('httpGet', {})
        check(container.get('image') == 'busybox:1.37.0' and container.get('command') == ['httpd']
              and container.get('args') == ['-f', '-p', '8080', '-h', '/www']
              and probe.get('path') == '/' and probe.get('port') == 8080,
              label + ': application image, command and readiness endpoint preserved')


def main():
    deployment = get('deployment', 'status')
    inspect_spec(deployment['spec']['template']['spec'], 'Deployment')
    status = deployment.get('status', {})
    check(deployment['spec'].get('replicas') == 1
          and status.get('observedGeneration', 0) >= deployment['metadata']['generation']
          and all(status.get(k, 0) == 1 for k in ('replicas', 'updatedReplicas', 'readyReplicas', 'availableReplicas')),
          'one available replica; rollout complete')
    rs_uids = {r['metadata']['uid'] for r in get('replicasets')['items']
               if any(o['uid'] == deployment['metadata']['uid'] for o in r['metadata'].get('ownerReferences', []))}
    pods = [p for p in get('pods')['items'] if not p['metadata'].get('deletionTimestamp')
            and any(o['uid'] in rs_uids for o in p['metadata'].get('ownerReferences', []))]
    check(len(pods) == 1, 'exactly one active Deployment-owned Pod')
    for pod in pods:
        name = pod['metadata']['name']
        inspect_spec(pod['spec'], 'Pod')
        check(any(c['type'] == 'Ready' and c['status'] == 'True'
                  for c in pod.get('status', {}).get('conditions', [])), 'Pod Ready')
        def execute(*args):
            return run('exec', name, '-c', 'web', '--', *args)
        try:
            fields = dict(line.split(':', 1) for line in execute('cat', '/proc/1/status').splitlines() if ':' in line)
            check(all(int(v) == 10000 for v in fields['Uid'].split())
                  and all(int(v) == 10000 for v in fields['Gid'].split()), 'runtime process UID/GID')
            check(fields['NoNewPrivs'].strip() == '1', 'runtime privilege escalation blocked')
            check(all(int(fields[k].strip(), 16) == 0 for k in ('CapEff', 'CapPrm', 'CapBnd', 'CapAmb')),
                  'runtime capability sets empty')
            roots = [line.split()[5] for line in execute('cat', '/proc/1/mountinfo').splitlines()
                     if line.split()[4] == '/']
            check(len(roots) == 1 and 'ro' in roots[0].split(','), 'runtime root mount read-only')
            check(execute('wget', '-T', '5', '-qO-', 'http://status:8080').strip() == 'cks-lab-01-ready',
                  'HTTP through Service returns expected content')
        except (RuntimeError, KeyError, ValueError, subprocess.TimeoutExpired) as error:
            check(False, 'runtime verification: ' + str(error))
    service = get('service', 'status')['spec']
    check(service.get('selector') == {'app': 'status'} and len(service['ports']) == 1
          and service['ports'][0]['port'] == 8080 and service['ports'][0]['targetPort'] == 8080,
          'Service selector and port preserved')
    check(get('configmap', 'status-page').get('data') == {'index.html': 'cks-lab-01-ready\n'},
          'ConfigMap content preserved')


try:
    main()
except (RuntimeError, KeyError, ValueError, subprocess.TimeoutExpired) as error:
    check(False, 'unable to grade: ' + str(error))
print(f'\nResult: {len(failures)} failed checks. ' + ('PASS' if not failures else 'NOT YET PASSING'))
sys.exit(1 if failures else 0)
