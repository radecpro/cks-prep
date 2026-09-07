#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
require kubectl
k cluster-info
k get nodes -o wide
k get pods -A
