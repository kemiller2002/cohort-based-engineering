#!/usr/bin/env bash
# REL-001 run-03 session driver (adapted from run-02/harness/trial.sh; one agent per trial).
#   trial.sh start ARM TASK RUNID
#       setup.sh, then records startedAt; prints the brief path. A setup failure is X1: nothing is scored and the
#       trial is rerun with a fresh RUNID.
#   trial.sh launch RUNID [--print-only]
#       cache condition K1 only: runs the agent as an isolated headless Claude Code process (launch-agent.sh),
#       then finishes the trial. --print-only prints the command and starts nothing.
#   trial.sh finish RUNID TRANSCRIPT_DIR AGENT [--final-message FILE] [--timed-out]
#       AGENT is AGENT_ID or AGENT_ID:SUBAGENT_TOKENS:TOOL_USES:DURATION_MS (K0: the orchestrator's Agent tool
#       result; K1: the session id). Records endedAt, writes the praxis.agent-binding/1 file, copies the agent's
#       transcript (and the final message when given), stops the D verifier and scores. The observation goes to
#       $REL003_OBSERVATIONS/ARM/RUNID.json; smoke runs (-SMOKE-) stay in the harness state only.
source "$(dirname "$0")/lib.sh"

case "${1:?usage: trial.sh start|launch|finish ...}" in
  start)
    [ $# -eq 4 ] || { echo "usage: trial.sh start ARM TASK RUNID" >&2; exit 2; }
    run_paths "$4"; mkdir -p "$STATES"
    if ! bash "$H3/setup.sh" "$2" "$3" "$RUN_ID" > "$STATES/setup-$RUN_ID.log" 2>&1; then
      if grep -q "gate G4\|differs from its pin\|differs from pin" "$STATES/setup-$RUN_ID.log"; then
        echo "refused by the pin gate (G4) for $RUN_ID, not X1 (see $STATES/setup-$RUN_ID.log)" >&2; exit 4
      fi
      echo "X1 setup failure for $RUN_ID (see $STATES/setup-$RUN_ID.log); rerun with a fresh RUNID" >&2; exit 3
    fi
    jq -n --arg s "$(utc)" '{startedAt: $s}' > "$HS/agent.json"
    jq -r '.workspaces[0].brief' "$HS/run.json"
    ;;
  launch)
    run_paths "${2:?usage: trial.sh launch RUNID [--print-only]}"
    if [ "${3:-}" = --print-only ]; then bash "$H3/launch-agent.sh" "$RUN_ID" --print-only; exit 0; fi
    set +e; bash "$H3/launch-agent.sh" "$RUN_ID"; rc=$?; set -e
    SID=$(jq -r .sessionId "$HS/launch.json")
    EXTRA=(); [ "$rc" -eq 124 ] && EXTRA=(--timed-out)
    [ -s "$HS/final-message.txt" ] && EXTRA+=(--final-message "$HS/final-message.txt")
    exec bash "$0" finish "$RUN_ID" "$(jq -r .transcriptRoot "$HS/launch.json")" "$SID" "${EXTRA[@]}"
    ;;
  finish)
    [ $# -ge 4 ] || { echo "usage: trial.sh finish RUNID TRANSCRIPT_DIR AGENT [--final-message FILE] [--timed-out]" >&2; exit 2; }
    run_paths "$2"; SRC="$3"; SPEC="$4"; shift 4
    FINAL_MSG=""; TIMED_OUT=false
    while [ $# -gt 0 ]; do case "$1" in --final-message) FINAL_MSG="$2"; shift 2;; --timed-out) TIMED_OUT=true; shift;; *) echo "unknown $1" >&2; exit 2;; esac; done
    [ -f "$HS/run.json" ] || { echo "no run.json for $RUN_ID" >&2; exit 2; }
    ITEM=$(jq -r .workItem "$HS/run.json")
    IFS=: read -r id tok uses ms <<<"$SPEC"
    AGENTS_JSON=$(jq -cn --arg id "$id" --arg t "${tok:-}" --arg u "${uses:-}" --arg d "${ms:-}" --argjson to "$TIMED_OUT" '
      [{name:"agent-1", agentId:$id, timedOut:$to, harness:(if $t == "" then null else {source:"Agent tool result (orchestrator)",
        subagentTokens:($t|tonumber), toolUses:($u|tonumber), durationMs:($d|tonumber)} end)}]')
    jq --arg e "$(utc)" --argjson a "$AGENTS_JSON" '. + {endedAt:$e, agents:$a}' "$HS/agent.json" > "$HS/agent.json.tmp"
    mv "$HS/agent.json.tmp" "$HS/agent.json"
    jq -n --arg id "$id" --arg run "$RUN_ID" --arg item "$ITEM" --arg s "${REL003_SESSION_ID:-}" --arg cond "$(jq -r .cache.condition "$HS/run.json")" '
      {schema:"praxis.agent-binding/1", bindings:[{agentId:$id, scope:($run + "/agent-1"), workItems:[$item]}
        + (if $s != "" then {sessionId:$s} elif ($cond | startswith("K1")) then {sessionId:$id} else {} end)]}' > "$HS/agent-binding.json"
    rm -rf "${HS:?}/transcripts"; mkdir -p "$HS/transcripts"
    found=$(find "$SRC" -maxdepth 3 -type f \( -name "agent-$id*.jsonl" -o -name "$id.jsonl" \) | LC_ALL=C sort)
    [ -n "$found" ] || found=$(find "$SRC" -maxdepth 1 -type f -name '*.jsonl' | LC_ALL=C sort)
    [ -n "$found" ] || { echo "no transcript for agent $id under $SRC" >&2; exit 2; }
    while read -r f; do b=$(basename "$f"); case "$b" in *"$id"*) cp "$f" "$HS/transcripts/";; *) cp "$f" "$HS/transcripts/$id-$b";; esac; done <<<"$found"
    [ -n "$FINAL_MSG" ] && cp "$FINAL_MSG" "$HS/final-message-agent-1.txt"
    verifier_stop
    ARM=$(jq -r .arm "$HS/run.json"); LABEL=$(jq -r .label "$HS/run.json")
    bash "$H3/score.sh" "$RUN_ID" --out "$HS/observation.json" > /dev/null
    if [ "$LABEL" != smoke ]; then
      mkdir -p "$OBSERVATIONS/$ARM"; cp "$HS/observation.json" "$OBSERVATIONS/$ARM/$RUN_ID.json"; echo "$OBSERVATIONS/$ARM/$RUN_ID.json"
    else
      echo "$HS/observation.json"
    fi
    ;;
  *) echo "usage: trial.sh start|launch|finish ..." >&2; exit 2 ;;
esac
