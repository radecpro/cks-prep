#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
owner="$(k get namespace "$LAB_NAMESPACE" -o jsonpath='{.metadata.labels.cks-prep/lab}')"
[[ "$owner" == 01 ]] || { echo 'Refusing to delete namespace without lab ownership label' >&2; exit 1; }
k delete namespace "$LAB_NAMESPACE" --timeout=120s
