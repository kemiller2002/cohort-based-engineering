#!/usr/bin/env bash
# REL-001 run-02 session driver (run-01 amendments A3 and A4 carried over).
#   trial.sh start ARM TASK RUNID
#       setup.sh, then records startedAt in the harness state; prints each workspace's brief path
#       (two lines for U6: agent-1 first). A setup failure is X1: nothing is scored, the trial is rerun.
#   trial.sh finish RUNID TRANSCRIPT_DIR AGENT [AGENT2] [--final-message agent-N=FILE]...
#       AGENT is AGENT_ID or AGENT_ID:SUBAGENT_TOKENS:TOOL_USES:DURATION_MS (the orchestrator's Agent tool
#       result, the A4 secondary measurement). For U6 the first agent ran in agent-1, the second in agent-2.
#       Records endedAt, writes the praxis.agent-binding/1 file from the agent ids, copies the agents'
#       transcripts (and, when given, the final messages the orchestrator received), stops the D verifier
#       and scores. The observation goes to $REL002_OBSERVATIONS/ARM/RUNID.json (pilot runs too, labelled);
#       smoke runs (RUNID contains -SMOKE-) are harness checks and stay in the harness state only.
source "$(dirname "$0")/lib.sh"

case "${1:?usage: trial.sh start|finish ...}" in
  start)
    [ $# -eq 4 ] || { echo "usage: trial.sh start ARM TASK RUNID" >&2; exit 2; }
    run_paths "$4"; mkdir -p "$STATES"
    if ! bash "$H2/setup.sh" "$2" "$3" "$RUN_ID" > "$STATES/setup-$RUN_ID.log" 2>&1; then
      echo "X1 setup failure for $RUN_ID (see $STATES/setup-$RUN_ID.log); rerun with a fresh RUNID" >&2; exit 3
    fi
    jq -n --arg s "$(utc)" '{startedAt: $s}' > "$HS/agent.json"
    jq -r '.workspaces[].brief' "$HS/run.json"
    ;;
  finish)
    [ $# -ge 4 ] || { echo "usage: trial.sh finish RUNID TRANSCRIPT_DIR AGENT [AGENT2] [--final-message agent-N=FILE]..." >&2; exit 2; }
    run_paths "$2"; SRC="$3"; shift 3
    [ -f "$HS/run.json" ] || { echo "no run.json for $RUN_ID" >&2; exit 2; }
    SPECS=(); FINALS=()
    while [ $# -gt 0 ]; do
      case "$1" in --final-message) FINALS+=("$2"); shift 2;; *) SPECS+=("$1"); shift;; esac
    done
    WANT=$(jq -r .agents "$HS/run.json")
    [ "${#SPECS[@]}" -eq "$WANT" ] || { echo "$RUN_ID ran $WANT agent(s); got ${#SPECS[@]} agent id(s)" >&2; exit 2; }
    ITEM=$(jq -r .workItem "$HS/run.json")
    # agents: [{name, agentId, harness}] in workspace order
    AGENTS_JSON=$(for i in "${!SPECS[@]}"; do
      IFS=: read -r id tok uses ms <<<"${SPECS[$i]}"
      jq -cn --arg n "agent-$((i + 1))" --arg id "$id" --arg t "${tok:-}" --arg u "${uses:-}" --arg d "${ms:-}" '
        {name:$n, agentId:$id, harness:(if $t == "" then null else {source:"Agent tool result (orchestrator)",
          subagentTokens:($t|tonumber), toolUses:($u|tonumber), durationMs:($d|tonumber)} end)}'
    done | jq -sc .)
    jq --arg e "$(utc)" --argjson a "$AGENTS_JSON" '. + {endedAt:$e, agents:$a}' "$HS/agent.json" > "$HS/agent.json.tmp"
    mv "$HS/agent.json.tmp" "$HS/agent.json"
    # F2 attribution: one binding per agent, scoped to the run (and workspace), bound to the run's work item.
    jq -n --argjson a "$AGENTS_JSON" --arg run "$RUN_ID" --arg item "$ITEM" --arg s "${REL002_SESSION_ID:-}" '
      {schema:"praxis.agent-binding/1", bindings:[$a[] | {agentId, scope:($run + "/" + .name), workItems:[$item]}
        + (if $s == "" then {} else {sessionId:$s} end)]}' > "$HS/agent-binding.json"
    # transcripts: only the bound agents' files
    rm -rf "${HS:?}/transcripts"; mkdir -p "$HS/transcripts"
    for id in $(jq -r '.[].agentId' <<<"$AGENTS_JSON"); do
      found=$(find "$SRC" -maxdepth 3 -type f -name "agent-$id*.jsonl" | LC_ALL=C sort)
      if [ -z "$found" ] && [ "$WANT" -eq 1 ]; then found=$(find "$SRC" -maxdepth 1 -type f -name '*.jsonl' | LC_ALL=C sort); fi
      [ -n "$found" ] || { echo "no transcript for agent $id under $SRC" >&2; exit 2; }
      while read -r f; do cp "$f" "$HS/transcripts/"; done <<<"$found"
    done
    for fm in "${FINALS[@]}"; do cp "${fm#*=}" "$HS/final-message-${fm%%=*}.txt"; done
    verifier_stop
    ARM=$(jq -r .arm "$HS/run.json"); LABEL=$(jq -r .label "$HS/run.json")
    bash "$H2/score.sh" "$RUN_ID" --out "$HS/observation.json" > /dev/null
    if [ "$LABEL" != smoke ]; then
      mkdir -p "$OBSERVATIONS/$ARM"; cp "$HS/observation.json" "$OBSERVATIONS/$ARM/$RUN_ID.json"
      echo "$OBSERVATIONS/$ARM/$RUN_ID.json"
    else
      echo "$HS/observation.json"
    fi
    ;;
  *) echo "usage: trial.sh start|finish ..." >&2; exit 2 ;;
esac
