#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
require python3
export LAB_NAMESPACE LAB_KUBECONFIG
python3 "$(dirname "${BASH_SOURCE[0]}")/verify.py"
