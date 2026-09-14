"""Read-only resource inspection and traffic probes; never repairs the exercise."""
import concurrent.futures
import json
import os
import subprocess
import sys
from resources import NAMES, resources

NS = os.environ['LAB_NAMESPACE']
BASE = ['kubectl', '--kubeconfig', os.environ['LAB_KUBECONFIG'], '--context', 'kind-cks', '--request-timeout=30s']
results = []


def run(args):
    return subprocess.run(BASE + args, text=True, capture_output=True, timeout=40)


def get(kind, name=None, namespace=NS):
    result = run(['-n', namespace, 'get', kind] + ([name] if name else []) + ['-o', 'json'])
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def check(name, ok):
    results.append(bool(ok))
    print(('PASS' if ok else 'FAIL') + ': ' + name, flush=True)


def execute(pod, command):
    return run(['-n', NS, 'exec', pod, '--'] + command)


def http(pod, host, port, allowed):
    for _ in range(1 if allowed else 2):
        r = execute(pod, ['wget', '-q' if allowed else '-S', '-T', '2', '-O', '-', f'http://{host}:{port}/'])
        if allowed:
            if r.returncode or r.stdout.strip() != 'cks-lab-03-ready':
                return False
        elif r.returncode == 0 or 'timed out' not in r.stderr.lower():
            return False
    return True


def main():
    pods = {p['metadata']['name']: p for p in get('pods')['items']}
    check('exactly the four fixture Pods exist', set(pods) == set(NAMES))
    for expected in resources()[:4]:
        name = expected['metadata']['name']
        actual = pods.get(name, {})
        spec = actual.get('spec', {})
        expected_spec = expected['spec']
        containers = spec.get('containers', [])
        intact = actual.get('metadata', {}).get('labels') == expected['metadata']['labels']
        intact &= all(spec.get(key) == expected_spec[key] for key in ('nodeSelector', 'automountServiceAccountToken'))
        intact &= len(containers) == 1 and all(containers[0].get(key) == expected_spec['containers'][0][key] for key in ('name', 'image', 'command'))
        intact &= bool(containers) and containers[0].get('readinessProbe', {}).get('httpGet', {}).get('port') == 8080 and containers[0].get('readinessProbe', {}).get('httpGet', {}).get('path') == '/'
        intact &= not any(spec.get(key) for key in ('initContainers', 'ephemeralContainers', 'volumes', 'hostNetwork'))
        check(f'{name}: fixture unchanged and Ready', intact and any(c['type'] == 'Ready' and c['status'] == 'True' for c in actual.get('status', {}).get('conditions', [])))
        for port in (8080, 9090):
            check(f'{name}: local listener {port}', http(name, '127.0.0.1', port, True))
    service = get('service', 'api')['spec']
    check('API Service unchanged', service.get('selector') == {'app': 'api'} and len(service['ports']) == 1 and service['ports'][0]['port'] == 8080 and service['ports'][0]['targetPort'] == 8080)
    policies = [p['spec'] for p in get('networkpolicies')['items']]
    for direction in ('Ingress', 'Egress'):
        check(f'namespace-wide default deny {direction}', any(not p.get('podSelector') and direction in p.get('policyTypes', ['Ingress']) and not p.get(direction.lower()) for p in policies))
    dns = get('service', 'kube-dns', 'kube-system')['spec']['clusterIP']
    for name in NAMES:
        r = execute(name, ['nslookup', f'api.{NS}.svc.cluster.local', dns])
        check(f'{name}: DNS resolution over UDP', r.returncode == 0 and service['clusterIP'] in r.stdout)
        r = execute(name, ['nc', '-z', '-w', '2', dns, '53'])
        check(f'{name}: DNS TCP port reachable', r.returncode == 0)
    check('frontend → API Service TCP 8080', http('frontend', f'api.{NS}.svc.cluster.local', 8080, True))
    jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for source in NAMES:
            for target in NAMES:
                if source == target:
                    continue
                ip = pods[target]['status']['podIP']
                for port in (8080, 9090):
                    allowed = (source, target, port) == ('frontend', 'api', 8080)
                    label = f'{source} → {target}:{port} ' + ('allowed' if allowed else 'blocked')
                    jobs.append((label, pool.submit(http, source, ip, port, allowed)))
        for label, future in jobs:
            check(label, future.result())
    failures = len(results) - sum(results)
    print(f'\n{sum(results)} passed; {failures} failed.')
    return bool(failures)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, KeyError, subprocess.TimeoutExpired) as error:
        print(f'ERROR: verification could not complete: {error}', file=sys.stderr)
        sys.exit(1)
