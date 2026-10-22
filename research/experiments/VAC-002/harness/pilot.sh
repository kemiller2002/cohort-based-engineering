#!/usr/bin/env bash
# VAC-002 pilot P1: one 12-unit chain per arm, all six arms concurrently, launched in the seeded random order.
# Run from a frozen checkout (a git worktree of the freeze commit) so that no edit can reach a running chain;
# observations go to VAC2_RESULTS (the experiment's results directory in the working checkout).
#   VAC2_RESULTS=.../results harness/pilot.sh [RUN]
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"; RUN="${1:-P1}"
: "${VAC2_RESULTS:?set VAC2_RESULTS to the results directory}"
STATE="${VAC2_STATE:-/home/user/.vac2-state}"; mkdir -p "$STATE"
TASKS=(L01 L02 L03 L04 L05 L06 L07 L08 L09 L10 L11 L12)
ORDER=$(python3 -I -c 'import random; print(*random.Random(20261022).sample(list("ABCDEF"), 6))')
echo "$RUN launch order: $ORDER (freeze commit $(git -C "$H" rev-parse HEAD))" | tee "$STATE/$RUN-launch.txt"
for arm in $ORDER; do
  "$H/vac2.sh" setup "$RUN" "$arm" > /dev/null 2>&1
  nohup "$H/vac2.sh" chain "$RUN" "$arm" "${TASKS[@]}" > "$STATE/$RUN-$arm.log" 2>&1 &
  echo "$arm pid $!" >> "$STATE/$RUN-launch.txt"
  sleep 5
done
