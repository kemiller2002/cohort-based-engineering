#!/usr/bin/env bash
# Smoke stand-in for `claude -p` (no model): applies the sealed reference solution of the unit's task to the workspace,
# writes a completion report, commits, and prints K1-shaped stream-json. Used only to test the harness end to end.
#   SMOKE_REF=<sealed reference repo>   SMOKE_MODE=reference|nothing
set -euo pipefail
prompt="$2"; brief=$(grep -oE '/[^ ]+\.md' <<<"$prompt" | head -1)
task=$(grep -oE 'LEND-L[0-9]+' "$brief" | head -1 | sed 's/LEND-//')
unit=$(grep -oE '^# Work unit [0-9]+' "$brief" | grep -oE '[0-9]+' || grep -oE 'work unit [0-9]+' "$brief" | grep -oE '[0-9]+' | head -1)
[ -z "$unit" ] && unit=$(grep -oE 'unit-[0-9]+\.json' "$brief" | head -1 | grep -oE '[0-9]+')
if [ "${SMOKE_MODE:-reference}" = reference ] && [ -n "$task" ]; then
  git -C "$SMOKE_REF" archive "ref-$task" src tests README.md | tar -x -C .
fi
mkdir -p .vac/reports
cat > ".vac/reports/unit-$unit.json" <<JSON
{"schema":"vac.unit-report/1","unit":$unit,"task":"$task","workItem":"LEND-$task","outcome":"completed","blockedReason":null,
 "requirements":[],"decisions":[{"id":"U$unit-D1","statement":"smoke","basis":"evidence","evidence":["requirements/$task.md"],"requirementIds":[]}],
 "verification":[],"rejectedAssumptions":[],"openQuestions":[],"knownIssues":[],"handoff":"smoke"}
JSON
git add -A >/dev/null && git commit -qm "smoke: $task" >/dev/null || true
echo '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"ls"}}]}}'
echo "{\"type\":\"result\",\"subtype\":\"success\",\"is_error\":false,\"num_turns\":1,\"duration_ms\":10,\"duration_api_ms\":5,\"result\":\"smoke\\nOUTCOME: completed\",\"session_id\":\"smoke\",\"total_cost_usd\":0.0,\"usage\":{\"input_tokens\":0,\"output_tokens\":0,\"cache_read_input_tokens\":0,\"cache_creation_input_tokens\":0},\"modelUsage\":{},\"terminal_reason\":\"completed\"}"
