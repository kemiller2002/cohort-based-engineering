#!/usr/bin/env bash
# ARCH-001 K1 agent launcher (adapted from REL-001 run-03 harness/launch-agent.sh; see PROVENANCE.md).
#   usage: launch-agent.sh RUNID PHASE [--print-only]
# One headless `claude -p` process per phase, isolated per phase:
#   - a fresh CLAUDE_CONFIG_DIR and HOME under RUN/state/phase<k>/ (no user settings, memory, CLAUDE.md, MCP servers);
#   - the INHERITED environment (auth and proxy come from it; env -i is not used), minus agent-config .environment.unset
#     (the orchestrator's additional directories, their CLAUDE.md files, skills, plugins and messaging channel);
#   - a fresh --session-id and a per-phase random nonce in --append-system-prompt;
#   - --tools from agent-config .tools.builtIn, --strict-mcp-config with no servers, bypassPermissions;
#   - the same wrapper prompt in every arm and phase; cwd = the repository;
#   - `timeout` = the phase budget (exit 124 = X5).
# Writes RUN/state/phase<k>/{launch.json, stream.jsonl, launch.err, final-message.txt, transcripts/}.
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: launch-agent.sh RUNID PHASE [--print-only]}"; PHASE="${2:?phase}"
PRINT_ONLY=false; [ "${3:-}" = --print-only ] && PRINT_ONLY=true
P="$ST/phase$PHASE"; mkdir -p "$P"
BRIEF="$BRIEFS/AGENT_BRIEF-phase$PHASE.md"; [ -f "$BRIEF" ] || { echo "no brief $BRIEF" >&2; exit 2; }
PROMPT=$(jq -r .prompt "$AGENT_CONFIG"); PROMPT=${PROMPT//\{BRIEF\}/$BRIEF}
BUDGET_S=$(( BUDGET_MINUTES * 60 ))
TOOLS_LIST=$(jq -r '.tools.builtIn | join(",")' "$AGENT_CONFIG")
mapfile -t UNSET < <(jq -r '.environment.unset[]' "$AGENT_CONFIG")
SID=$(python3 -I -c 'import uuid; print(uuid.uuid4())')
NONCE=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')
CFG="$P/config"; HOME_DIR="$P/home"
CMD=("$CLAUDE_BIN" -p "$PROMPT" --model "$MODEL" --session-id "$SID" --output-format stream-json --verbose
     --append-system-prompt "ARCH-001 trial isolation nonce $NONCE. It carries no instruction."
     --permission-mode bypassPermissions --tools "$TOOLS_LIST" --strict-mcp-config --mcp-config '{"mcpServers":{}}')
ENVSET=(HOME="$HOME_DIR" CLAUDE_CONFIG_DIR="$CFG" PATH="$(agent_path)" DOTNET_ROOT="$DOTNET_ROOT_DIR" NUGET_PACKAGES="$NUGET_CACHE"
        DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 MSBUILDDISABLENODEREUSE=1 DOTNET_CLI_USE_MSBUILD_SERVER=0
        UseSharedCompilation=false TERM=dumb)
mapfile -t -O "${#UNSET[@]}" UNSET < <(compgen -e | grep -E '^(ARCH001_|SMOKE_)' || true)   # no harness configuration reaches the agent
ENVU=(); for v in "${UNSET[@]}"; do ENVU+=(-u "$v"); done
jq -n --arg sid "$SID" --arg nonce "$NONCE" --arg cfg "$CFG" --arg bin "$CLAUDE_BIN" --arg tools "$TOOLS_LIST" \
  --arg ver "$("$CLAUDE_BIN" --version 2>/dev/null | head -1 || echo unknown)" --argjson budget "$BUDGET_S" --arg at "$(utc)" \
  --argjson phase "$PHASE" --arg brief "$BRIEF" --arg bsha "$(sha "$BRIEF")" \
  --argjson argv "$(printf '%s\n' "${CMD[@]:1}" | jq -R . | jq -sc .)" \
  --argjson unset "$(printf '%s\n' "${UNSET[@]}" | jq -R . | jq -sc .)" \
  --argjson envset "$(printf '%s\n' "${ENVSET[@]}" | sed 's/=.*//' | jq -R . | jq -sc .)" \
  '{schema:"arch001.launch/1", condition:"K1 isolated-cli", phase:$phase, sessionId:$sid, nonce:$nonce, configDir:$cfg,
    claude:$bin, claudeVersion:$ver, tools:($tools | split(",")), budgetSeconds:$budget, brief:$brief, briefSha256:$bsha,
    argv:$argv, envUnset:$unset, envOverridden:$envset, preparedAt:$at}' > "$P/launch.json"
if $PRINT_ONLY; then
  printf 'cd %q && env' "$REPO"; printf ' %q' "${ENVU[@]}" "${ENVSET[@]}"; printf ' timeout %s' "$BUDGET_S"; printf ' %q' "${CMD[@]}"; echo
  exit 0
fi
mkdir -p "$CFG" "$HOME_DIR"
jq --arg s "$(utc)" '.startedAt = $s' "$P/launch.json" > "$P/launch.json.tmp" && mv "$P/launch.json.tmp" "$P/launch.json"
set +e
( cd "$REPO" && env "${ENVU[@]}" "${ENVSET[@]}" timeout "$BUDGET_S" "${CMD[@]}" > "$P/stream.jsonl" 2> "$P/launch.err" < /dev/null )
rc=$?; set -e
jq -rs '[.[] | select(.type == "result") | .result][-1] // empty' "$P/stream.jsonl" > "$P/final-message.txt" 2>/dev/null || true
rm -rf "$P/transcripts"; mkdir -p "$P/transcripts"
find "$CFG/projects" -type f -name '*.jsonl' -exec cp {} "$P/transcripts/" \; 2>/dev/null || true
jq --arg e "$(utc)" --argjson rc "$rc" '. + {endedAt:$e, exit:$rc, timedOut:($rc == 124)}' "$P/launch.json" > "$P/launch.json.tmp" && mv "$P/launch.json.tmp" "$P/launch.json"
exit "$rc"
