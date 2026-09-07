#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
for tool in docker kind kubectl curl; do require "$tool"; done
kind version
kubectl version --client
docker info --format 'Docker server: {{.ServerVersion}}'
kind get clusters
if [[ -f "$LAB_KUBECONFIG" ]]; then
  k get nodes -o wide
else
  echo "No repository kubeconfig yet. Run ./scripts/cluster-create.sh."
fi
