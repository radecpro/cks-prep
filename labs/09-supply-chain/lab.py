"""Scoped image pinning/admission exercise with ownership-checked cleanup."""
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

NS = os.environ['LAB_NAMESPACE']
ROOT = Path(os.environ['REPO_ROOT'])
STATE = ROOT / '.local/lab09-state'
K = ['kubectl', '--kubeconfig', os.environ['LAB_KUBECONFIG'], '--context', 'kind-cks', '--request-timeout=20s']
NODE = 'cks-worker2'
TAG = 'docker.io/library/busybox:1.37.0'
PREFIX = NS + '-image-'


def run(args, data=None, required=True):
    r = subprocess.run(args, input=data, text=True, capture_output=True, timeout=150)
    if required and r.returncode:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r


def k(*args, **kwargs):
    return run(K + list(args), **kwargs)


def names():
    return {kind: PREFIX + kind for kind in ('pods', 'deployments')}


def cid_and_digest():
    obj = json.loads(run(['docker', 'inspect', NODE]).stdout)[0]
    if obj['Config']['Labels'].get('io.x-k8s.kind.cluster') != 'cks':
        raise RuntimeError('Target is not a node in kind cluster cks')
    images = json.loads(run(['docker', 'exec', NODE, 'crictl', 'images', '-o', 'json']).stdout)['images']
    matching = [i for i in images if TAG in i.get('repoTags', [])]
    if len(matching) != 1:
        raise RuntimeError('Expected cached BusyBox tag unavailable or ambiguous')
    digests = [d for d in matching[0].get('repoDigests', []) if re.fullmatch(r'docker.io/library/busybox@sha256:[a-f0-9]{64}', d)]
    if len(digests) != 1:
        raise RuntimeError('Expected immutable digest unavailable or ambiguous')
    return obj['Id'], digests[0]


def saved():
    obj = json.loads((STATE / 'owner.json').read_text())
    node = json.loads(run(['docker', 'inspect', NODE]).stdout)[0]
    if node['Config']['Labels'].get('io.x-k8s.kind.cluster') != 'cks' or obj['namespace'] != NS or obj['containerId'] != node['Id']:
        raise RuntimeError('Saved namespace or node identity mismatch')
    if not re.fullmatch(r'docker.io/library/busybox@sha256:[a-f0-9]{64}', obj['approvedImage']):
        raise RuntimeError('Invalid saved approved image digest')
    return obj


def expression(kind, digest):
    spec = 'object.spec' if kind == 'pods' else 'object.spec.template.spec'
    value = json.dumps(digest)
    return f'{spec}.containers.all(c, c.image == {value}) && (!has({spec}.initContainers) || {spec}.initContainers.all(c, c.image == {value}))'


def policy(kind, digest):
    group = '' if kind == 'pods' else 'apps'
    name = names()[kind]
    return {'apiVersion': 'admissionregistration.k8s.io/v1', 'kind': 'ValidatingAdmissionPolicy',
            'metadata': {'name': name, 'labels': {'cks-prep/lab': '09'}},
            'spec': {'failurePolicy': 'Fail', 'matchConstraints': {'resourceRules': [{
                'apiGroups': [group], 'apiVersions': ['v1'], 'operations': ['CREATE', 'UPDATE'], 'resources': [kind]}]},
                'validations': [{'expression': expression(kind, digest), 'message': 'Only the approved image digest is allowed'}]}}


def binding(kind):
    name = names()[kind]
    return {'apiVersion': 'admissionregistration.k8s.io/v1', 'kind': 'ValidatingAdmissionPolicyBinding',
            'metadata': {'name': name + '-binding', 'labels': {'cks-prep/lab': '09'}},
            'spec': {'policyName': name, 'validationActions': ['Audit'],
                     'matchResources': {'namespaceSelector': {'matchLabels': {'kubernetes.io/metadata.name': NS}}}}}


def deployment(image):
    return {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': 'status', 'namespace': NS},
            'spec': {'replicas': 1, 'selector': {'matchLabels': {'app': 'status'}}, 'template': {
                'metadata': {'labels': {'app': 'status'}}, 'spec': {
                    'nodeSelector': {'kubernetes.io/hostname': NODE}, 'automountServiceAccountToken': False,
                    'terminationGracePeriodSeconds': 1,
                    'containers': [{'name': 'web', 'image': image, 'imagePullPolicy': 'IfNotPresent',
                        'command': ['httpd'], 'args': ['-f', '-p', '8080', '-h', '/www'],
                        'readinessProbe': {'httpGet': {'path': '/', 'port': 8080}, 'periodSeconds': 2},
                        'volumeMounts': [{'name': 'page', 'mountPath': '/www', 'readOnly': True}]}],
                    'volumes': [{'name': 'page', 'configMap': {'name': 'status-page'}}]}}}}


def fixtures(digest):
    return [
        {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'release-metadata', 'namespace': NS, 'labels': {'cks-prep/lab': '09'}},
         'data': {'approvedImage': digest, 'sourceTag': TAG}},
        {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'status-page', 'namespace': NS, 'labels': {'cks-prep/lab': '09'}},
         'data': {'index.html': 'cks-lab-09-ready\n'}},
        {'apiVersion': 'v1', 'kind': 'Service', 'metadata': {'name': 'status', 'namespace': NS, 'labels': {'cks-prep/lab': '09'}},
         'spec': {'selector': {'app': 'status'}, 'ports': [{'port': 8080, 'targetPort': 8080}]}}]


def apply(obj):
    k('apply', '-f', '-', data=json.dumps(obj))


def setup():
    cid, digest = cid_and_digest()
    if STATE.exists() or k('get', 'namespace', NS, '--ignore-not-found', '-o', 'name').stdout.strip():
        raise RuntimeError('Existing Lab 09 state or namespace; refusing reset')
    for kind, name in names().items():
        for resource in ('validatingadmissionpolicy', 'validatingadmissionpolicybinding'):
            target = name if resource == 'validatingadmissionpolicy' else name + '-binding'
            if k('get', resource, target, '--ignore-not-found', '-o', 'name').stdout.strip():
                raise RuntimeError(f'Existing cluster-scoped resource {target}; refusing overwrite')
    STATE.mkdir(mode=0o700)
    (STATE / 'owner.json').write_text(json.dumps({'namespace': NS, 'containerId': cid, 'approvedImage': digest, 'names': names()}))
    try:
        k('create', 'namespace', NS)
        k('label', 'namespace', NS, 'cks-prep/lab=09')
        for kind in names():
            apply(policy(kind, digest))
            apply(binding(kind))
        for obj in fixtures(digest):
            apply(obj)
        apply(deployment(TAG))
        k('-n', NS, 'rollout', 'status', 'deployment/status', '--timeout=120s')
    except Exception:
        print('Setup incomplete; recovery state retained. Run cleanup before retrying.', flush=True)
        raise
    print(f'Exercise ready in {NS}; cluster-scoped objects recorded. Read TASK.md.')


def get(resource, name, namespace=False, required=True):
    args = (['-n', NS] if namespace else []) + ['get', resource, name, '-o', 'json', '--ignore-not-found']
    r = k(*args, required=required)
    return json.loads(r.stdout) if r.stdout.strip() else None


def cleanup():
    saved()
    for kind, name in names().items():
        for resource, target in (('validatingadmissionpolicybinding', name + '-binding'), ('validatingadmissionpolicy', name)):
            obj = get(resource, target)
            if obj and obj['metadata'].get('labels', {}).get('cks-prep/lab') != '09':
                raise RuntimeError(f'Refusing to delete unowned {target}')
    ns = get('namespace', NS)
    if ns and ns['metadata'].get('labels', {}).get('cks-prep/lab') != '09':
        raise RuntimeError('Refusing to delete unowned namespace')
    for kind, name in names().items():
        k('delete', 'validatingadmissionpolicybinding', name + '-binding', '--ignore-not-found')
    for kind, name in names().items():
        k('delete', 'validatingadmissionpolicy', name, '--ignore-not-found')
    k('delete', 'namespace', NS, '--ignore-not-found', '--timeout=120s')
    shutil.rmtree(STATE)
    print('Owned bindings, policies and namespace removed; recovery state cleared.')


def subset(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and all(key in b and subset(value, b[key]) for key, value in a.items())
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(subset(x, y) for x, y in zip(a, b))
    return a == b


def admission(kind, image, sidecar=None, init=False):
    obj = {'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'probe-' + uuid.uuid4().hex[:12], 'namespace': NS},
           'spec': {'containers': [{'name': 'main', 'image': image, 'command': ['sleep', '1']}], 'restartPolicy': 'Never'}}
    if sidecar:
        bucket = 'initContainers' if init else 'containers'
        obj['spec'].setdefault(bucket, []).append({'name': 'extra', 'image': sidecar, 'command': ['sleep', '1']})
    if kind == 'deployments':
        obj = {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': obj['metadata']['name'], 'namespace': NS},
               'spec': {'replicas': 1, 'selector': {'matchLabels': {'probe': 'yes'}},
                        'template': {'metadata': {'labels': {'probe': 'yes'}}, 'spec': obj['spec']}}}
        obj['spec']['template']['spec'].pop('restartPolicy', None)
    return k('-n', NS, 'create', '--dry-run=server', '-f', '-', data=json.dumps(obj), required=False)


def wait_admission(kind, expect_deny):
    # Admission bindings propagate asynchronously to API servers.
    for _ in range(12):
        r = admission(kind, TAG)
        denied = r.returncode != 0 and names()[kind] in r.stderr and 'denied request' in r.stderr
        if denied == expect_deny and (denied or r.returncode == 0):
            return
        time.sleep(1)


def verify():
    info = saved()
    approved = info['approvedImage']
    checks = []
    def check(label, ok):
        checks.append(bool(ok))
        print(('PASS' if ok else 'FAIL') + ': ' + label, flush=True)
    ns = get('namespace', NS)
    check('namespace ownership and scope label retained', ns and ns['metadata'].get('labels', {}).get('cks-prep/lab') == '09')
    for kind, name in names().items():
        p = get('validatingadmissionpolicy', name)
        b = get('validatingadmissionpolicybinding', name + '-binding')
        check(f'{kind}: policy preserved and owned', p and p['metadata'].get('labels', {}).get('cks-prep/lab') == '09' and subset(policy(kind, approved)['spec'], p['spec']))
        expected = binding(kind)['spec']
        match = b['spec'].get('matchResources', {}) if b else {}
        check(f'{kind}: exact namespace binding with Deny', b and b['metadata'].get('labels', {}).get('cks-prep/lab') == '09'
              and b['spec'].get('policyName') == expected['policyName']
              and match.get('namespaceSelector') == expected['matchResources']['namespaceSelector']
              and not match.get('objectSelector') and match.get('matchPolicy', 'Equivalent') == 'Equivalent'
              and set(match) <= {'namespaceSelector', 'objectSelector', 'matchPolicy'}
              and 'Deny' in b['spec'].get('validationActions', []) and 'Warn' not in b['spec'].get('validationActions', []))
        wait_admission(kind, b is not None and 'Deny' in b['spec'].get('validationActions', []))
        positive = admission(kind, approved)
        check(f'{kind}: approved digest admitted', positive.returncode == 0)
        for case, args in [('mutable tag', (kind, TAG)), ('unapproved sidecar', (kind, approved, TAG)),
                           ('unapproved init container', (kind, approved, TAG, True))]:
            r = admission(*args)
            check(f'{kind}: {case} denied', r.returncode != 0 and name in r.stderr and 'denied request' in r.stderr)
    cms = {o['metadata']['name']: o for o in fixtures(approved) if o['kind'] == 'ConfigMap'}
    for name, expected in cms.items():
        obj = get('configmap', name, True)
        check(f'{name} unchanged', obj and obj.get('data') == expected['data'] and obj['metadata'].get('labels', {}).get('cks-prep/lab') == '09')
    dep = get('deployment', 'status', True)
    expected = deployment(approved)
    check('Deployment uses exact approved digest and original fixture', dep and subset(expected['spec'], dep['spec']))
    st = dep.get('status', {}) if dep else {}
    check('one completed available replica', dep and st.get('observedGeneration', 0) >= dep['metadata']['generation']
          and all(st.get(k) == 1 for k in ('replicas', 'updatedReplicas', 'readyReplicas', 'availableReplicas')))
    pods = k('-n', NS, 'get', 'pods', '-o', 'json')
    items = json.loads(pods.stdout)['items']
    check('one Ready Pod on target worker', len(items) == 1 and items[0]['spec'].get('nodeName') == NODE
          and any(c['type'] == 'Ready' and c['status'] == 'True' for c in items[0]['status'].get('conditions', [])))
    if len(items) == 1:
        pod = items[0]
        check('running Pod image reference and imageID match approved digest', pod['spec']['containers'][0]['image'] == approved
              and pod['status']['containerStatuses'][0]['imageID'] == approved)
        r = k('-n', NS, 'exec', pod['metadata']['name'], '--', 'wget', '-q', '-T', '3', '-O', '-', f'http://status.{NS}.svc.cluster.local:8080/', required=False)
        check('Service returns original content', r.returncode == 0 and r.stdout.strip() == 'cks-lab-09-ready')
    service = get('service', 'status', True)
    check('Service unchanged', service and subset(fixtures(approved)[2]['spec'], service['spec']))
    failures = len(checks) - sum(checks)
    print(f'\n{sum(checks)} passed; {failures} failed.')
    return bool(failures)


if __name__ == '__main__':
    try:
        if sys.argv[1] not in ('setup', 'verify', 'cleanup'):
            raise RuntimeError('Unknown action')
        sys.exit(globals()[sys.argv[1]]())
    except (RuntimeError, OSError, ValueError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
