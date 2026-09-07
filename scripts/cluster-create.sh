#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
for tool in docker kind kubectl; do require "$tool"; done
docker info >/dev/null
clusters="$(kind get clusters)"
if grep -qx cks <<< "$clusters"; then
  echo "Cluster cks already exists; refusing to replace it." >&2
  echo "To recover this repo's kubeconfig: kind export kubeconfig --name cks --kubeconfig $LAB_KUBECONFIG" >&2
  exit 1
fi
umask 077
mkdir -p "$REPO_ROOT/.local"
args=(create cluster --config "$REPO_ROOT/cluster/kind.yaml" --kubeconfig "$LAB_KUBECONFIG")
if [[ -n "${KIND_NODE_IMAGE:-}" ]]; then args+=(--image "$KIND_NODE_IMAGE"); fi
kind "${args[@]}"
docker inspect --format '{{.Name}} {{.Config.Image}} {{.Image}}' \
  cks-control-plane cks-worker cks-worker2 > "$REPO_ROOT/.local/node-images.txt"
echo "Cluster created. Run ./scripts/calico-install.sh to install networking."
