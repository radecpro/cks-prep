#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../scripts/common.sh"
LAB_NAMESPACE="${CKS_LAB_NAMESPACE:-cks-lab-08}"
case "$LAB_NAMESPACE" in
  cks-lab-08|cks-lab-08-qa) ;;
  *) echo 'Unsupported lab namespace' >&2; exit 1 ;;
esac
require kubectl
require docker
require python3
export LAB_NAMESPACE LAB_KUBECONFIG REPO_ROOT
