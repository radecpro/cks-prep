"""Initial application fixtures; no NetworkPolicies are installed."""
import json

NAMES = ("frontend", "api", "rogue", "sink")
COMMAND = ["sh", "-ec", "mkdir -p /www; echo cks-lab-03-ready > /www/index.html; httpd -p 8080 -h /www; exec httpd -f -p 9090 -h /www"]

def resources():
    items = []
    for i, name in enumerate(NAMES):
        items.append({"apiVersion": "v1", "kind": "Pod", "metadata": {"name": name, "labels": {"app": name}}, "spec": {
            "nodeSelector": {"kubernetes.io/hostname": "cks-worker" if i % 2 == 0 else "cks-worker2"},
            "automountServiceAccountToken": False,
            "containers": [{"name": "web", "image": "busybox:1.37.0", "command": COMMAND,
                "readinessProbe": {"httpGet": {"path": "/", "port": 8080}, "periodSeconds": 2}}]}})
    items.append({"apiVersion": "v1", "kind": "Service", "metadata": {"name": "api"}, "spec": {
        "selector": {"app": "api"}, "ports": [{"port": 8080, "targetPort": 8080}]}})
    return items

if __name__ == "__main__":
    print(json.dumps({"apiVersion": "v1", "kind": "List", "items": resources()}))
