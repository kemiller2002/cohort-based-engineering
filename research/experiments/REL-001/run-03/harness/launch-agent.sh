#!/usr/bin/env bash
# REL-001 run-03 cache condition K1 ("isolated-cli"): runs one trial's agent as its own headless Claude Code
# process, so that no prompt-cache prefix is shared with an orchestrating session (run-01/run-02 A3).
#   usage: launch-agent.sh RUNID [--print-only]
# Isolation, per trial:
#   - a fresh CLAUDE_CONFIG_DIR and HOME under the harness state (no user settings, memory, CLAUDE.md, hooks,
#     plugins or MCP servers; --strict-mcp-config with an empty server list);
#   - a fresh --session-id (the agent id the binding and the transcript use);
#   - a per-trial random nonce in --append-system-prompt, so the system prompt differs between trials and a
#     cache entry written by an earlier trial cannot match past the system-prompt breakpoint;
#   - trials run one at a time (never block-concurrent, unlike run-02 A3).
# The cache state is MEASURED, not assumed: score.py records the first request's cache-read tokens
# (firstRequestCold) and the run's cache-read share. Any cache read on the first request means some prefix
# (e.g. tool definitions) was still shared; the analysis reports it (protocol M2).
# Credentials: ANTHROPIC_API_KEY from the environment, or REL003_CLAUDE_CREDENTIALS (a credentials file copied
# into the fresh config dir). The same wrapper prompt as every arm (agent-config.json .prompt) is used.
# Exit status: claude's, or 124 when the 45-minute budget (X5) stopped it.
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: launch-agent.sh RUNID [--print-only]}"
PRINT_ONLY=false; [ "${2:-}" = --print-only ] && PRINT_ONLY=true
RJ="$HS/run.json"; [ -f "$RJ" ] || { echo "no run.json for $RUN_ID (run trial.sh start first)" >&2; exit 2; }
COND=$(jq -r .cache.condition "$RJ")
[[ "$COND" == K1* ]] || $PRINT_ONLY || { echo "run $RUN_ID is cache condition '$COND'; launch-agent.sh is for K1 only" >&2; exit 2; }
CLAUDE_BIN="${REL003_CLAUDE:-$(command -v claude || echo claude)}"
BRIEF=$(jq -r '.workspaces[0].brief' "$RJ")
PROMPT=$(jq -r .prompt "$AGENT_CONFIG"); PROMPT=${PROMPT//\{BRIEF\}/$BRIEF}
BUDGET_S=$(( $(jq -r .budgetMinutes "$AGENT_CONFIG") * 60 ))
SID=$(python3 -I -c 'import uuid; print(uuid.uuid4())')
NONCE=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')
CFG="$HS/claude-config"; HOME_DIR="$HS/home"
CMD=("$CLAUDE_BIN" -p "$PROMPT" --model "$MODEL" --session-id "$SID" --output-format stream-json --verbose
     --append-system-prompt "REL-001 run-03 trial isolation nonce $NONCE. It carries no instruction."
     --permission-mode bypassPermissions --strict-mcp-config --mcp-config '{"mcpServers":{}}')
jq -n --arg sid "$SID" --arg nonce "$NONCE" --arg cfg "$CFG" --arg root "$CFG/projects" --arg bin "$CLAUDE_BIN" \
  --arg ver "$("$CLAUDE_BIN" --version 2>/dev/null | head -1 || echo unknown)" --argjson budget "$BUDGET_S" --arg at "$(utc)" \
  --argjson argv "$(printf '%s\n' "${CMD[@]:1}" | jq -R . | jq -sc .)" \
  '{schema:"cbe.rel-001.run-03-launch/1", condition:"K1 isolated-cli", sessionId:$sid, nonce:$nonce, configDir:$cfg,
    transcriptRoot:$root, claude:$bin, claudeVersion:$ver, budgetSeconds:$budget, argv:$argv, preparedAt:$at}' > "$HS/launch.json"
if $PRINT_ONLY; then
  printf 'cd %q && env -i HOME=%q CLAUDE_CONFIG_DIR=%q PATH=%q timeout %s' "$RUN_DIR" "$HOME_DIR" "$CFG" "$PATH" "$BUDGET_S"
  printf ' %q' "${CMD[@]}"; echo
  exit 0
fi
mkdir -p "$CFG" "$HOME_DIR"
[ -n "${REL003_CLAUDE_CREDENTIALS:-}" ] && cp "$REL003_CLAUDE_CREDENTIALS" "$CFG/.credentials.json"
jq --arg s "$(utc)" '.startedAt = $s' "$HS/agent.json" > "$HS/agent.json.tmp" && mv "$HS/agent.json.tmp" "$HS/agent.json"
set +e
( cd "$RUN_DIR" && env -i HOME="$HOME_DIR" CLAUDE_CONFIG_DIR="$CFG" PATH="$PATH" TERM=dumb \
    ${ANTHROPIC_API_KEY:+ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"} \
    timeout "$BUDGET_S" "${CMD[@]}" > "$HS/stream.jsonl" 2> "$HS/launch.err" < /dev/null )
rc=$?; set -e
jq -rs '[.[] | select(.type == "result") | .result][-1] // empty' "$HS/stream.jsonl" > "$HS/final-message.txt" 2>/dev/null || true
jq --arg e "$(utc)" --argjson rc "$rc" '. + {endedAt:$e, exit:$rc}' "$HS/launch.json" > "$HS/launch.json.tmp" && mv "$HS/launch.json.tmp" "$HS/launch.json"
exit "$rc"
