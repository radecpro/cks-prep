#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../scripts/common.sh"
LAB_NAMESPACE="${CKS_LAB_NAMESPACE:-cks-lab-05}"
case "$LAB_NAMESPACE" in
  cks-lab-05|cks-lab-05-qa) ;;
  *) echo 'Unsupported lab namespace' >&2; exit 1 ;;
esac
require kubectl
