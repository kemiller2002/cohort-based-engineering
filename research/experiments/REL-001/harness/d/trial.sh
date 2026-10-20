#!/usr/bin/env bash
# REL-001 Experiment D session driver (amendment A3).
#   trial.sh start ARM TASK RUNID   -> setup.sh, then records logs/agent.json startedAt
#   trial.sh finish RUNID TRANSCRIPT_DIR [AGENT_ID SUBAGENT_TOKENS TOOL_USES DURATION_MS]
#                                   -> records endedAt, copies the agent's transcripts,
#                                      scores into observations/ARM/RUNID.json
# Pins come from the environment set by the orchestrator (REL001_TREATMENT_PRAXIS,
# REL001_SDE, REL001_ORDO_COMMIT, REL001_MODEL*).
set -euo pipefail
REL="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNS="${REL001_RUNS:-/tmp/claude-0/rel001/runs}"
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }

case "${1:?usage: trial.sh start|finish ...}" in
  start)
    ARM="$2"; TASK="$3"; RUN_ID="$4"
    bash "$REL/harness/d/setup.sh" "$ARM" "$TASK" "$RUN_ID" > "$RUNS/../setup-$RUN_ID.log" 2>&1
    jq -n --arg s "$(utc)" '{startedAt: $s}' > "$RUNS/$RUN_ID/logs/agent.json"
    echo "$RUNS/$RUN_ID/AGENT_BRIEF.md"
    ;;
  finish)
    RUN_ID="$2"; SRC="$3"; RUN_DIR="$RUNS/$RUN_ID"
    jq --arg e "$(utc)" --arg id "${4:-}" --arg t "${5:-}" --arg u "${6:-}" --arg d "${7:-}" \
      '. + {endedAt: $e} + (if $id == "" then {} else {harness: {source: "Agent tool result (orchestrator)",
        agentId: $id, subagentTokens: ($t|tonumber), toolUses: ($u|tonumber), durationMs: ($d|tonumber)}} end)' \
      "$RUN_DIR/logs/agent.json" > "$RUN_DIR/logs/agent.json.tmp"
    mv "$RUN_DIR/logs/agent.json.tmp" "$RUN_DIR/logs/agent.json"
    mkdir -p "$RUN_DIR/transcripts"; cp "$SRC"/*.jsonl "$RUN_DIR/transcripts/"
    ARM="$(jq -r .arm "$RUN_DIR/run.json")"
    mkdir -p "$REL/observations/$ARM"
    bash "$REL/harness/d/score.sh" "$RUN_ID" --transcripts "$RUN_DIR/transcripts" \
      --out "$REL/observations/$ARM/$RUN_ID.json"
    ;;
esac
