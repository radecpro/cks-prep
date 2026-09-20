"""Intentionally overexposed synthetic credentials for the exercise."""
import json

SECRET = {"password": "synthetic-db-password-05", "admin-token": "synthetic-admin-token-05"}
SCRIPT = """#!/bin/sh
set -eu
mkdir -p /tmp/www
(
  while true; do
    if [ -n "${DB_PASSWORD:-}" ] || [ -s /etc/db/password ]; then
      echo cks-lab-05-ready > /tmp/www/index.html
    else
      rm -f /tmp/www/index.html
    fi
    sleep 1
  done
) &
exec httpd -f -p 8080 -h /tmp/www
"""
SECURITY = {"runAsUser": 10000, "runAsGroup": 10000, "runAsNonRoot": True,
            "allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"]},
            "seccompProfile": {"type": "RuntimeDefault"}}

def resources():
    mount = {"name": "credentials", "mountPath": "/etc/db", "readOnly": True}
    app = {"name": "app", "image": "busybox:1.37.0", "command": ["sh", "/opt/app/start.sh"],
           "securityContext": SECURITY, "envFrom": [{"secretRef": {"name": "db-credentials"}}],
           "env": [{"name": "DB_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "db-credentials", "key": "password"}}}],
           "volumeMounts": [mount, {"name": "scripts", "mountPath": "/opt/app", "readOnly": True}],
           "readinessProbe": {"httpGet": {"path": "/", "port": 8080}, "periodSeconds": 2}}
    observer = {"name": "observer", "image": "busybox:1.37.0", "command": ["sleep", "infinity"],
                "securityContext": SECURITY, "envFrom": [{"secretRef": {"name": "db-credentials"}}], "volumeMounts": [mount]}
    return [
        {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "db-credentials"}, "type": "Opaque", "stringData": SECRET},
        {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "app-script"}, "data": {"start.sh": SCRIPT}},
        {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "payments"}, "spec": {
            "replicas": 1, "selector": {"matchLabels": {"app": "payments"}},
            "template": {"metadata": {"labels": {"app": "payments"}}, "spec": {
                "terminationGracePeriodSeconds": 1, "automountServiceAccountToken": False,
                "securityContext": {"fsGroup": 10000}, "containers": [app, observer],
                "volumes": [{"name": "credentials", "secret": {"secretName": "db-credentials"}},
                            {"name": "scripts", "configMap": {"name": "app-script"}}]}}}},
        {"apiVersion": "v1", "kind": "Service", "metadata": {"name": "payments"}, "spec": {
            "selector": {"app": "payments"}, "ports": [{"port": 8080, "targetPort": 8080}]}}
    ]

if __name__ == "__main__":
    print(json.dumps({"apiVersion": "v1", "kind": "List", "items": resources()}))
