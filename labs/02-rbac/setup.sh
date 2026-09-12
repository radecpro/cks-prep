#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
k get --raw=/readyz >/dev/null
k create namespace "$LAB_NAMESPACE"
k label namespace "$LAB_NAMESPACE" cks-prep/lab=02
# Inject the namespace only into ServiceAccount subjects in this local manifest.
require python3
python3 "$(dirname "${BASH_SOURCE[0]}")/resources.py" "$LAB_NAMESPACE" | k -n "$LAB_NAMESPACE" apply -f -
k -n "$LAB_NAMESPACE" rollout status deployment/observer --timeout=120s
echo "Exercise ready in $LAB_NAMESPACE. Read TASK.md."
