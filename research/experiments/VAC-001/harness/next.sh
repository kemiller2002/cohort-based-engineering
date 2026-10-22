#!/usr/bin/env bash
# Orchestration helper: after every arm of RUN finished unit UNIT-1, write D/DR verified state and stage UNIT.
#   next.sh RUN UNIT TASK [FAULT] [ARMS...]
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"; RUN="$1"; UNIT="$2"; TASK="$3"; FAULT="${4:-none}"; shift 4 || shift $#
ARMS=("${@:-A B C D}"); [ $# -eq 0 ] && ARMS=(A B C D)
for a in ${ARMS[@]}; do case "$a" in D|DR) "$H/vac.sh" state "$RUN" "$a" $(( UNIT - 1 )) > /dev/null;; esac; done
for a in ${ARMS[@]}; do "$H/vac.sh" stage "$RUN" "$a" "$UNIT" "$TASK" "$FAULT"; done
