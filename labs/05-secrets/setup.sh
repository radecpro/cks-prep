#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
require python3
k get --raw=/readyz >/dev/null
k create namespace "$LAB_NAMESPACE"
k label namespace "$LAB_NAMESPACE" cks-prep/lab=05
python3 "$(dirname "${BASH_SOURCE[0]}")/resources.py" | k -n "$LAB_NAMESPACE" apply -f -
k -n "$LAB_NAMESPACE" rollout status deployment/payments --timeout=120s
echo "Exercise ready in $LAB_NAMESPACE. Read TASK.md."
