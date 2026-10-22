#!/usr/bin/env bash
# BUDGET.md stopping rule: total the cli-estimate cost of every agent turn of RUN; at STOP_USD create the stop file
# (every chain stops before its next unit). Also applies the per-arm alarm (mean cost per unit > ALARM_USD after 3 units).
#   budget.sh RESULTS RUN [STOP_USD=95] [ALARM_USD=2.40]      prints one status line; exit 0
set -euo pipefail
R="$1"; RUN="$2"; STOP="${3:-95}"; ALARM="${4:-2.40}"; STATE="${VAC2_STATE:-/home/user/.vac2-state}"
# Amendment A1: the CLI's total_cost_usd is cumulative over a session, so a resumed session's turns must not be
# summed; the arm's cost is the sum over its sessions of each session's last (largest) cumulative value.
sessions_cost() { cat "$@" 2>/dev/null | jq -s 'group_by(.sessionId) | map(map(.usage.costUsdCli // 0) | max) | add // 0'; }
total=$(sessions_cost "$R/$RUN"/*/turn-*.json)
line="$(date -u +%FT%TZ) $RUN total=\$$total"
for d in "$R/$RUN"/*/; do
  a=$(basename "$d"); n=$(jq '[.units[]? | select((.attempts | length) > 0)] | length' "$d/setup.json" 2>/dev/null || echo 0)
  c=$(sessions_cost "$d"/turn-*.json)
  line="$line $a:${n}u/\$$c"
  if [ "$n" -ge 3 ] && [ "$(echo "$c / $n > $ALARM" | bc -l)" = 1 ]; then line="$line(ALARM)"; fi
done
if [ "$(echo "$total >= $STOP" | bc -l)" = 1 ] && [ ! -f "$STATE/$RUN/STOP" ]; then mkdir -p "$STATE/$RUN"; date -u +%FT%TZ > "$STATE/$RUN/STOP"; line="$line STOP-CREATED"; fi
echo "$line"
