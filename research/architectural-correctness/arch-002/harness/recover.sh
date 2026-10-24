#!/usr/bin/env bash
# ARCH-002 amendment A7: idempotent recovery after a container restart (applies the A4 rule unchanged).
#   usage: recover.sh        (run only when no run-queue.sh is alive)
# Rebuilds the next order-resumeN.json from order.json and harness state, marks attempts cut off in setup or an
# agent phase with interrupted.json, appends a line to analysis/restarts.md, and relaunches the queue at A5 limits.
set -euo pipefail
X=$(cd "$(dirname "$0")/.." && pwd); RUNS=/home/user/arch002-runs; Q=$RUNS/.queue
ps -eo args | grep -qE "^bash harness/[r]un-queue.sh" && { echo "a queue is alive; not recovering" >&2; exit 2; }
# The live order is the queue log written most recently; the next order number is one above the highest in use.
PLOG=$(ls -t "$Q"/order-resume*.log 2>/dev/null | head -1)
N=$(( $(ls "$X"/harness/order-resume*.json 2>/dev/null | sed -n 's/.*order-resume\([0-9]\+\)\.json$/\1/p' | sort -n | tail -1) + 1 ))
state() { python3 -I -c 'import importlib.util as u,sys; s=u.spec_from_file_location("r",sys.argv[1]); m=u.module_from_spec(s); s.loader.exec_module(m); print(m.state(sys.argv[2],sys.argv[3]))' "$X/harness/resume-order.py" "$RUNS" "$1"; }
LOST=(); KEPT=()
if [ -f "$PLOG" ]; then
  for id in $(comm -23 <(grep ' start ' "$PLOG" | awk '{print $3}' | sort) <(grep ' end ' "$PLOG" | awk '{print $3}' | sort)); do
    s=$(state "$id")
    if [ "$s" = lost ]; then LOST+=("$id"); [ -f "$RUNS/$id/state/interrupted.json" ] || \
      jq -n --arg at "$(date -u +%FT%TZ)" '{reason:"container restart during setup or an agent phase (A4 rule, recover.sh)", at:$at}' > "$RUNS/$id/state/interrupted.json"
    else KEPT+=("$id"); fi
  done
fi
python3 -I "$X/harness/resume-order.py" "$X/harness/order.json" "$RUNS" "$X/harness/order-resume$N.json" > /dev/null
echo "| $(date -u +%FT%TZ) | boot $(uptime -s) | order-resume$N | replaced: ${LOST[*]:-none} | resumed: ${KEPT[*]:-none} | done before: $(ls $RUNS/ARCH-002-CONF-*/state/done 2>/dev/null | wc -l) |" >> "$X/analysis/restarts.md"
export DOTNET_ROOT=/home/user/.tools/dotnet PATH=/home/user/.tools/dotnet:$PATH ARCH002_SEALED_DIR=/home/user/arch002-sealed
cd "$X" && setsid nohup bash harness/run-queue.sh "harness/order-resume$N.json" --concurrency 4 --fixture-concurrency summa=3,lending-brownfield=4 \
  > "/home/user/arch001-logs/arch002-conf-queue-r$N.log" 2>&1 < /dev/null &
echo "relaunched order-resume$N (replaced ${#LOST[@]}, resumed ${#KEPT[@]})"
