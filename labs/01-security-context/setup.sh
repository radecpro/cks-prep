#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
k get --raw=/readyz >/dev/null
# create, not apply: never reset a learner's existing work.
k create namespace "$LAB_NAMESPACE"
k label namespace "$LAB_NAMESPACE" cks-prep/lab=01
k -n "$LAB_NAMESPACE" apply -f "$(dirname "${BASH_SOURCE[0]}")/initial.yaml"
k -n "$LAB_NAMESPACE" rollout status deployment/status --timeout=120s
echo "Exercise ready in $LAB_NAMESPACE. Read TASK.md and start your timer."
