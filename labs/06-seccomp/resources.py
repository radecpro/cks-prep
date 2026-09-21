"""Initial namespace-scoped seccomp exercise fixtures."""
import json

SECURITY = {"runAsUser": 10000, "runAsGroup": 10000, "runAsNonRoot": True,
            "allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"]}}

def resources():
    return [
        {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "status-page"}, "data": {"index.html": "cks-lab-06-ready\n"}},
        {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "status"}, "spec": {
            "replicas": 1, "selector": {"matchLabels": {"app": "status"}},
            "template": {"metadata": {"labels": {"app": "status"}}, "spec": {
                "terminationGracePeriodSeconds": 1, "automountServiceAccountToken": False,
                "securityContext": {"seccompProfile": {"type": "Unconfined"}},
                "containers": [
                    {"name": "web", "image": "busybox:1.37.0", "command": ["httpd"], "args": ["-f", "-p", "8080", "-h", "/www"],
                     "securityContext": SECURITY,
                     "readinessProbe": {"httpGet": {"path": "/", "port": 8080}, "periodSeconds": 2},
                     "volumeMounts": [{"name": "page", "mountPath": "/www", "readOnly": True}]},
                    {"name": "observer", "image": "busybox:1.37.0", "command": ["sleep", "infinity"],
                     "securityContext": dict(SECURITY, seccompProfile={"type": "Unconfined"})}],
                "volumes": [{"name": "page", "configMap": {"name": "status-page"}}]}}}},
        {"apiVersion": "v1", "kind": "Service", "metadata": {"name": "status"}, "spec": {
            "selector": {"app": "status"}, "ports": [{"port": 8080, "targetPort": 8080}]}}
    ]

if __name__ == "__main__":
    print(json.dumps({"apiVersion": "v1", "kind": "List", "items": resources()}))
