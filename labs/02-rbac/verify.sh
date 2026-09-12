#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
require python3
exec python3 "$(dirname "${BASH_SOURCE[0]}")/verify.py" "$LAB_KUBECONFIG" "$LAB_NAMESPACE"
