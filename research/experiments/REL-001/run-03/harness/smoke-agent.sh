#!/usr/bin/env bash
# REL-001 run-03 HARNESS CHECK ONLY: a scripted stand-in "agent" (adapted from run-02/harness/smoke-agent.sh).
# It applies fixtures/reference/V<n> (V7 has none: it reports the conflict and stops blocked), or with
# SMOKE_VARIANT=<variant> the wrong solution reference/V<n>-<variant> (to exercise escaped-defect scoring),
# follows the workflow of AGENT_BRIEF.md for the run's arm, and writes a constructed Claude Code style
# transcript (message ids, usage with cache fields, one streamed duplicate, a final report) so that binding,
# outcome-line parsing, the cost cross-check, the cache measurement, X2 and X4 are exercised end to end.
# Its runs are harness checks, never observations.   usage: smoke-agent.sh RUNID   -> prints the agent id
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: smoke-agent.sh RUNID}"
RJ="$HS/run.json"; ARM=$(jq -r .arm "$RJ"); TASK=$(jq -r .task "$RJ"); ITEM=$(jq -r .workItem "$RJ")
TOKEN=$(jq -r '.workspaces[0].token' "$RJ"); VALUES="$HS/brief-values-agent-1.json"
AGENT_ID="a$(printf '%s' "$RUN_ID" | sha256sum | cut -c1-16)"
TX="$HS/smoke-src"; mkdir -p "$TX"
# shellcheck disable=SC1091
source "$RUN_DIR/env.sh"
LOG="$HS/smoke-agent-1.log"; : > "$LOG"
step() { echo "+ $*" >> "$LOG"; set +e; "$@" >> "$LOG" 2>&1; local rc=$?; set -e; echo "  exit $rc" >> "$LOG"; return $rc; }
apply_solution() {
  cp -r "$FIX3/reference/$TASK/." .
  [ -n "${SMOKE_VARIANT:-}" ] && cp -r "$FIX3/reference/$TASK-$SMOKE_VARIANT/." .
  git add -A -- src tests && git commit -qm "$ITEM: solution (harness check)"
}
test_step() { if [ "$DRY_RUN" = 1 ]; then echo "+ (dry run) dotnet test Ledger.slnx skipped" >> "$LOG"; else step dotnet test Ledger.slnx; fi; }

OUTCOME="OUTCOME: completed"; SUMMARY="Implemented $ITEM."
if [ "$(jq -r .conflict "$RJ")" = true ]; then
  case "$ARM" in
    echelon-original) step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS" || true ;;
    echelon-optimized) step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS" || true
                       step praxis work verify --id "$ITEM" --token "$TOKEN" || true ;;
    *) test_step || true ;;
  esac
  DECS=$(jq -r '.decisionIds | join(" and ")' "$RJ")
  OUTCOME="OUTCOME: blocked - $DECS conflict for a source with a zero balance"
  SUMMARY="The two decisions contradict each other for an empty sweep, so no implementation can satisfy both."
else
  case "$ARM" in
    bare|directives) apply_solution; test_step ;;
    echelon-original)
      step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS"
      apply_solution
      step praxis work validate-run --id "$ITEM" --token "$TOKEN" --generation 1 --validation unit-tests --evidence-id EV-TESTS -- dotnet test Ledger.slnx
      RES=$(jq -r '.resultPath' "$(ls -t "$RUN_DIR"/logs/praxis-out/*.out | head -1)")
      # shellcheck disable=SC2086
      step praxis work complete-verified --id "$ITEM" --token "$TOKEN" --generation 1 --commit "$(git rev-parse HEAD)" --verification-revision "$(git rev-parse HEAD)" \
        --authority "$(jq -r .AUTHORITY "$VALUES")" --ordo-contract "$(jq -r .CONTRACT "$VALUES")" $(jq -r .REQ_ARGS "$VALUES") \
        --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=$RES" ;;
    echelon-optimized)
      step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS"
      apply_solution
      step praxis work verify --id "$ITEM" --token "$TOKEN"
      step praxis work complete-verified --id "$ITEM" --token "$TOKEN" ;;
  esac
fi

# --- the constructed transcript (no harness, oracle or fixture path in it); timestamps follow the real clock
python3 -I - "$TX/agent-$AGENT_ID.jsonl" "$AGENT_ID" "$MODEL" "$SUMMARY"$'\n\n'"$OUTCOME" <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
out, agent, model, final = sys.argv[1:5]
t0 = datetime.now(timezone.utc)
ts = lambda s: (t0 + timedelta(seconds=s)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
session = "00000000-0000-4000-8000-00000000c0de"
def entry(i, content, output, s, cache_read):
    return {"parentUuid": None, "isSidechain": True, "agentId": agent, "type": "assistant", "sessionId": session,
            "uuid": f"{agent}-{i}-{output}", "timestamp": ts(s),
            "message": {"id": f"msg_smoke_{agent}_{i}", "model": model, "role": "assistant", "content": content,
                        "usage": {"input_tokens": 3, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": cache_read,
                                  "cache_creation": {"ephemeral_5m_input_tokens": 1000, "ephemeral_1h_input_tokens": 0},
                                  "output_tokens": output}}}
lines = [{"parentUuid": None, "isSidechain": True, "agentId": agent, "type": "user", "sessionId": session,
          "timestamp": ts(0), "message": {"role": "user", "content": "Read the brief and follow it."}}]
lines.append(entry(1, [{"type": "text", "text": "Reading the brief."}], 5, 1, 0))          # cold first request
lines.append(entry(2, [{"type": "tool_use", "id": f"toolu_{agent}_1", "name": "Bash", "input": {"command": "source env.sh"}}], 12, 2, 20000))
lines.append(entry(2, [{"type": "tool_use", "id": f"toolu_{agent}_1", "name": "Bash", "input": {"command": "source env.sh"}}], 40, 2, 20000))  # streamed repeat
lines.append(entry(3, [{"type": "tool_use", "id": f"toolu_{agent}_2", "name": "Bash", "input": {"command": "git commit"}}], 30, 3, 21000))
lines.append(entry(4, [{"type": "text", "text": final}], 25, 4, 22000))
with open(out, "w") as f:
    f.write("".join(json.dumps(l) + "\n" for l in lines))
PY
echo "$AGENT_ID"
