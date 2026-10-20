#!/usr/bin/env bash
# REL-001 run-02 HARNESS CHECK ONLY: a scripted stand-in "agent" (as run-01's harness/d/smoke-agent.sh).
# It applies fixtures/reference/U<n> (U2 has none: it reports the conflict and stops blocked), follows the
# workflow of AGENT_BRIEF.md for the run's arm, and writes a constructed Claude Code style transcript
# (sidechain entries with agentId, message ids, usage, one streamed duplicate, a SubagentHandback final
# report) so that binding attribution, outcome-line parsing, X2 and X4 are exercised end to end.
# Its runs are harness checks, never observations.
#   usage: smoke-agent.sh RUNID [agent-1|agent-2]    -> prints the agent id it used
#   U6: agent-1 implements and pushes; agent-2 finds the item taken (C/D: the shared claim) or done (A/B).
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: smoke-agent.sh RUNID [agent-N]}"; NAME="${2:-agent-1}"
RJ="$HS/run.json"; ARM=$(jq -r .arm "$RJ"); TASK=$(jq -r .task "$RJ"); ITEM=$(jq -r .workItem "$RJ"); AGENTS=$(jq -r .agents "$RJ")
W=$(jq -r --arg n "$NAME" '.workspaces[] | select(.name==$n) | .dir' "$RJ"); TOKEN=$(jq -r --arg n "$NAME" '.workspaces[] | select(.name==$n) | .token' "$RJ")
VALUES="$HS/brief-values-$NAME.json"
AGENT_ID="a$(printf '%s/%s' "$RUN_ID" "$NAME" | sha256sum | cut -c1-16)"
TX="$HS/smoke-src"; mkdir -p "$TX"
# shellcheck disable=SC1091
source "$W/env.sh"
STORE=(); [ "$AGENTS" -eq 2 ] && STORE=(--store git --remote origin)
LOG="$HS/smoke-$NAME.log"; : > "$LOG"
step() { echo "+ $*" >> "$LOG"; set +e; "$@" >> "$LOG" 2>&1; local rc=$?; set -e; echo "  exit $rc" >> "$LOG"; return $rc; }
apply_reference() { cp -r "$FIX2/reference/$TASK/." .; git add -A -- src tests && git commit -qm "$ITEM: reference solution (harness check)"; }

OUTCOME="OUTCOME: completed"; SUMMARY="Implemented $ITEM."
taken=false
if [ "$AGENTS" -eq 2 ] && [ "$NAME" = agent-2 ]; then
  if is_echelon "$ARM"; then step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS" "${STORE[@]}" || taken=true
  else git fetch -q origin; git grep -q freezeAccount origin/main -- src && taken=true; fi
fi
if $taken; then
  OUTCOME="OUTCOME: blocked - the other engineer already holds or finished $ITEM on origin"; SUMMARY="Found $ITEM taken; did not duplicate it."
elif [ "$TASK" = U2 ]; then
  if [ "$ARM" = echelon-original ]; then
    step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS" || true
    step praxis work validate-run --id "$ITEM" --token "$TOKEN" --generation 1 --validation unit-tests --evidence-id EV-TESTS -- dotnet test Ledger.slnx || true
    RES=$(jq -r '.resultPath // empty' "$(ls -t "$RUN_DIR"/logs/praxis-out/*.out | head -1)" 2>/dev/null || true)
    # shellcheck disable=SC2086
    step praxis work complete-verified --id "$ITEM" --token "$TOKEN" --generation 1 --commit "$(git rev-parse HEAD)" --verification-revision "$(git rev-parse HEAD)" \
      --authority "$(jq -r .AUTHORITY "$VALUES")" --ordo-contract "$(jq -r .CONTRACT "$VALUES")" $(jq -r .REQ_ARGS "$VALUES") \
      --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=${RES:-none}" || true
  elif [ "$ARM" = echelon-optimized ]; then
    step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS" || true
    step praxis work verify --id "$ITEM" --token "$TOKEN" || true
    step praxis work complete-verified --id "$ITEM" --token "$TOKEN" || true
  else
    step dotnet test Ledger.slnx || true
  fi
  OUTCOME="OUTCOME: blocked - DEC-U2-REOPEN-ALLOWED and DEC-U2-PERIOD-FINAL conflict for a closed period"
  SUMMARY="The two decisions contradict each other for reopening a closed period, so no implementation can satisfy both."
else
  case "$ARM" in
    bare|directives)
      apply_reference; step dotnet test Ledger.slnx ;;
    echelon-original)
      step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS" "${STORE[@]}"
      apply_reference
      step praxis work validate-run --id "$ITEM" --token "$TOKEN" --generation 1 --validation unit-tests --evidence-id EV-TESTS "${STORE[@]}" -- dotnet test Ledger.slnx
      RES=$(jq -r '.resultPath' "$(ls -t "$RUN_DIR"/logs/praxis-out/*.out | head -1)")
      # shellcheck disable=SC2086
      step praxis work complete-verified --id "$ITEM" --token "$TOKEN" --generation 1 --commit "$(git rev-parse HEAD)" --verification-revision "$(git rev-parse HEAD)" \
        --authority "$(jq -r .AUTHORITY "$VALUES")" --ordo-contract "$(jq -r .CONTRACT "$VALUES")" $(jq -r .REQ_ARGS "$VALUES") \
        --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=$RES" "${STORE[@]}" ;;
    echelon-optimized)
      step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS" "${STORE[@]}"
      [ "$AGENTS" -eq 2 ] && step praxis work claim --id "$ITEM" --token "$TOKEN" --lease-seconds "$LEASE_SECONDS"
      apply_reference
      step praxis work verify --id "$ITEM" --token "$TOKEN"
      step praxis work complete-verified --id "$ITEM" --token "$TOKEN" "${STORE[@]}" ;;
  esac
  if [ "$AGENTS" -eq 2 ]; then
    is_echelon "$ARM" && [ -n "$(git status --porcelain)" ] && { git add -A && git commit -qm "$ITEM: completion state"; }
    step git push -q origin HEAD:main
  fi
fi

# --- the constructed transcript (Claude Code sub-agent format; no harness, oracle or fixture path in it)
python3 -I - "$TX/agent-$AGENT_ID.jsonl" "$AGENT_ID" "$MODEL" "$SUMMARY"$'\n\n'"$OUTCOME" <<'PY'
import json, sys
out, agent, model, final = sys.argv[1:5]
session = "00000000-0000-4000-8000-00000000c0de"
def entry(i, content, output, ts):
    return {"parentUuid": None, "isSidechain": True, "agentId": agent, "type": "assistant", "sessionId": session,
            "uuid": f"{agent}-{i}", "timestamp": f"2026-10-20T12:00:{ts:02d}.000Z",
            "message": {"id": f"msg_smoke_{agent}_{i}", "model": model, "role": "assistant", "content": content,
                        "usage": {"input_tokens": 3, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 20000,
                                  "cache_creation": {"ephemeral_5m_input_tokens": 1000, "ephemeral_1h_input_tokens": 0},
                                  "output_tokens": output}}}
lines = [{"parentUuid": None, "isSidechain": True, "agentId": agent, "type": "user", "sessionId": session,
          "timestamp": "2026-10-20T12:00:00.000Z", "message": {"role": "user", "content": "Read the brief and follow it."}}]
lines.append(entry(1, [{"type": "text", "text": "Reading the brief."}], 5, 1))
lines.append(entry(2, [{"type": "tool_use", "id": f"toolu_{agent}_1", "name": "Bash", "input": {"command": "source env.sh"}}], 12, 2))
lines.append(entry(2, [{"type": "tool_use", "id": f"toolu_{agent}_1", "name": "Bash", "input": {"command": "source env.sh"}}], 40, 2))  # streamed repeat
lines.append(entry(3, [{"type": "tool_use", "id": f"toolu_{agent}_2", "name": "Bash", "input": {"command": "git commit"}}], 30, 3))
lines.append(entry(4, [{"type": "tool_use", "id": f"toolu_{agent}_3", "name": "SubagentHandback", "input": {"message": final}}], 25, 4))
with open(out, "w") as f:
    f.write("".join(json.dumps(l) + "\n" for l in lines))
PY
echo "$AGENT_ID"
