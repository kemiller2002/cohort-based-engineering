#!/usr/bin/env bash
# Harness smoke: a full 12-unit chain with the reference-applying stand-in agent, then post-hoc scoring of every unit.
#   smoke/smoke-chain.sh RUN ARM
set -euo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"
export VAC2_CLAUDE="$H/smoke/fake-claude.sh" SMOKE_REF="${SMOKE_REF:-/home/user/.vac2-sealed/ref}"
TASKS=(L01 L02 L03 L04 L05 L06 L07 L08 L09 L10 L11 L12)
"$H/vac2.sh" setup "$1" "$2"
"$H/vac2.sh" chain "$1" "$2" "${TASKS[@]}"
for u in $(seq 1 ${#TASKS[@]}); do "$H/vac2.sh" score "$1" "$2" "$u"; done
