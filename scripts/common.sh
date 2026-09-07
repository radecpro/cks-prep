#!/usr/bin/env bash
# Source from other scripts; never use the ambient Kubernetes context.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_KUBECONFIG="$REPO_ROOT/.local/kubeconfig"
export KIND_EXPERIMENTAL_PROVIDER=docker

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }
}

k() {
  kubectl --kubeconfig "$LAB_KUBECONFIG" --context kind-cks --request-timeout=30s "$@"
}
