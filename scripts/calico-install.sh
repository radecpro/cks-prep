#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
for tool in kubectl curl; do require "$tool"; done
[[ -f "$LAB_KUBECONFIG" ]] || { echo "Create the lab cluster first." >&2; exit 1; }
k get nodes
if [[ -n "$(k -n kube-system get daemonset kindnet --ignore-not-found -o name)" ]]; then
  echo "kindnet is installed. Use a fresh cluster with disableDefaultCNI: true." >&2
  exit 1
fi
manifest="$REPO_ROOT/.local/calico-v3.32.2.yaml"
curl --fail --location --retry 3 \
  https://raw.githubusercontent.com/projectcalico/calico/v3.32.2/manifests/calico.yaml \
  -o "$manifest"
k apply --server-side -f "$manifest"
k -n kube-system rollout status daemonset/calico-node --timeout=300s
k -n kube-system rollout status deployment/calico-kube-controllers --timeout=300s
k wait --for=condition=Ready nodes --all --timeout=300s
k -n kube-system rollout status deployment/coredns --timeout=180s
echo "Calico and CoreDNS are ready. Validate traffic enforcement in the NetworkPolicy lab."
