#!/usr/bin/env bash
# Infrastructure smoke test, not a learner exercise. Removes only its own namespace.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
require kubectl
ns=cks-lab-smoke
k wait --for=condition=Ready nodes --all --timeout=180s
k get --raw='/readyz'
k create namespace "$ns"
trap 'k delete namespace "$ns" --wait=false' EXIT
k -n "$ns" apply -f - <<'YAML'
apiVersion: v1
kind: Pod
metadata:
  name: server
  labels:
    app: smoke-server
spec:
  nodeSelector:
    kubernetes.io/hostname: cks-worker
  containers:
    - name: server
      image: busybox:1.37.0
      command: [sh, -c, 'mkdir -p /tmp/www; echo cks-ready > /tmp/www/index.html; exec httpd -f -p 8080 -h /tmp/www']
---
apiVersion: v1
kind: Service
metadata:
  name: server
spec:
  selector:
    app: smoke-server
  ports:
    - port: 8080
---
apiVersion: v1
kind: Pod
metadata:
  name: client
  labels:
    app: smoke-client
spec:
  nodeSelector:
    kubernetes.io/hostname: cks-worker2
  containers:
    - name: client
      image: busybox:1.37.0
      command: [sleep, '3600']
YAML
k -n "$ns" wait --for=condition=Ready pod --all --timeout=180s
k -n "$ns" exec client -- nslookup kubernetes.default.svc.cluster.local
probe() { k -n "$ns" exec client -- wget -T 3 -qO- http://server:8080; }
[[ "$(probe)" == cks-ready ]]
echo 'PASS: DNS, Service routing and cross-worker HTTP'
k -n "$ns" apply -f - <<'YAML'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: server-ingress
spec:
  podSelector:
    matchLabels:
      app: smoke-server
  policyTypes: [Ingress]
  ingress: []
YAML
# Allow policy propagation; require several consecutive rejected connections.
blocked=0
for attempt in {1..15}; do
  if probe; then blocked=0; else blocked=$((blocked + 1)); fi
  if [[ "$blocked" -ge 3 ]]; then break; fi
  sleep 1
done
[[ "$blocked" -ge 3 ]] || { echo 'FAIL: ingress policy did not block HTTP' >&2; exit 1; }
echo 'PASS: deny ingress enforced'
k -n "$ns" patch networkpolicy server-ingress --type=merge -p \
  '{"spec":{"ingress":[{"from":[{"podSelector":{"matchLabels":{"app":"smoke-client"}}}],"ports":[{"protocol":"TCP","port":8080}]}]}}'
allowed=false
for attempt in {1..15}; do
  if [[ "$(probe)" == cks-ready ]]; then allowed=true; break; fi
  sleep 1
done
[[ "$allowed" == true ]] || { echo 'FAIL: explicit allow did not restore HTTP' >&2; exit 1; }
echo 'PASS: explicit allow restored HTTP'
k -n "$ns" get pods -o wide
echo 'PASS: cluster smoke test'
