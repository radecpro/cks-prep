#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
python3 "$(dirname "${BASH_SOURCE[0]}")/lab.py" setup
