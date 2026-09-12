"""Generate the deliberately insecure initial resources; no solution included."""
import json
import sys

ns = sys.argv[1]
resources = [
    {'apiVersion': 'v1', 'kind': 'ServiceAccount', 'metadata': {'name': 'inspector'}, 'automountServiceAccountToken': True},
    {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'app-config'}, 'data': {'mode': 'observe'}},
    {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'internal-config'}, 'data': {'mode': 'internal'}},
    {'apiVersion': 'v1', 'kind': 'Secret', 'metadata': {'name': 'demo-secret'}, 'stringData': {'password': 'synthetic-lab-value'}},
    {'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'Role', 'metadata': {'name': 'observer-access'},
     'rules': [{'apiGroups': ['*'], 'resources': ['*'], 'verbs': ['*']}]},
    {'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'RoleBinding', 'metadata': {'name': 'observer-access'},
     'roleRef': {'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'Role', 'name': 'observer-access'},
     'subjects': [{'kind': 'ServiceAccount', 'name': 'default', 'namespace': ns}]},
    {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': 'observer'},
     'spec': {'replicas': 1, 'selector': {'matchLabels': {'app': 'observer'}}, 'template': {
         'metadata': {'labels': {'app': 'observer'}}, 'spec': {
             'serviceAccountName': 'default', 'automountServiceAccountToken': True,
             'terminationGracePeriodSeconds': 1,
             'containers': [{'name': 'worker', 'image': 'busybox:1.37.0',
                             'command': ['sleep'], 'args': ['infinity']}]}}}},
]
print(json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': resources}))
