#!/usr/bin/env bash
# ARCH-002 stand-in agent (adapted from ARCH-001 harness/smoke-agent.sh; no model call). Same interface as
# launch-agent.sh: smoke-agent.sh RUNID PHASE. Applies $ARCH002_SEALED_DIR/<fixture>/reference/<T>/<variant>/phase<k>/
# (stand-in layout) or <variant>/ in phase 1 and followup-<variant>/ in phase 2 (fixture-worker layout: mkref.sh
# overlays with a .delete list) over the workspace, commits, runs `submit` exactly as an agent would (same PATH and
# environment), and writes a synthetic stream.jsonl (init, one assistant turn whose usage is priced with the run's
# model, one Bash tool_use per command, result event) so that the scorer's token, cost and tool paths are exercised.
#   SMOKE_VARIANT=good|trap (default good)
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: smoke-agent.sh RUNID PHASE}"; PHASE="${2:?phase}"
[ "$(label_of "$RUN_ID")" = smoke ] || { echo "smoke-agent.sh is for -SMOKE- run ids only" >&2; exit 2; }
load_run_config
P="$ST/phase$PHASE"; mkdir -p "$P/transcripts"
TASK=$(task_of "$RUN_ID"); VAR="${SMOKE_VARIANT:-good}"; REF="$SEALED/reference/$TASK/$VAR"
MODEL=$(jq -r .model "$ST/run.json")
SID=$(python3 -I -c 'import uuid; print(uuid.uuid4())')
jq -n --arg sid "$SID" --arg at "$(utc)" --argjson phase "$PHASE" --arg v "$VAR" --arg m "$MODEL" \
  '{schema:"arch002.launch/1", condition:"smoke stand-in (no model)", phase:$phase, model:$m, sessionId:$sid, variant:$v, startedAt:$at}' > "$P/launch.json"
apply_overlay() {  # DIR: copy its files over the workspace, then delete the paths listed in DIR/.delete (mkref.sh format)
  cp -r "$1/." "$REPO/"; rm -f "$REPO/.delete"
  if [ -f "$1/.delete" ]; then while read -r f; do [ -n "$f" ] && rm -f "$REPO/$f"; done < "$1/.delete"; fi
}
FUP="$SEALED/reference/$TASK/followup-$VAR"
if [ -d "$REF/phase$PHASE" ]; then apply_overlay "$REF/phase$PHASE"            # stand-in layout: <variant>/phase<k>/
elif [ "$PHASE" = 1 ] && [ -d "$REF" ]; then apply_overlay "$REF"              # fixture-worker layout: <variant>/ ...
elif [ "$PHASE" = 2 ] && [ -d "$FUP" ]; then apply_overlay "$FUP"; fi         # ... and followup-<variant>/
( cd "$REPO" && git add -A && git commit -qm "Implement phase $PHASE" ) || true
set +e
OUT=$(cd "$REPO" && env PATH="$(agent_path)" DOTNET_ROOT="$DOTNET_ROOT_DIR" NUGET_PACKAGES="$NUGET_CACHE" submit 2>&1); SRC=$?
set -e
HEAD=$(git -C "$REPO" rev-parse HEAD)
FINAL="Applied the $VAR reference for phase $PHASE; submit said: $(head -1 <<<"$OUT")"$'\n'"ARCH002-DONE $HEAD"
ts() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
COST=$(jq -r --arg m "$MODEL" '[.entries[] | select(.model == $m)][0] | ((10 * .input + 20 * .output + 1000 * .cacheWrite1h) / 1000000)' "$PRICE_TABLE")
{
  jq -cn --arg sid "$SID" --arg cwd "$REPO" --arg m "$MODEL" '{type:"system", subtype:"init", session_id:$sid, cwd:$cwd, model:$m, scratchpad_path:""}'
  jq -cn --arg sid "$SID" --arg t "$(ts)" --arg m "$MODEL" '{type:"assistant", session_id:$sid, timestamp:$t, message:{id:"msg_smoke_1", model:$m,
     content:[{type:"tool_use", id:"tu1", name:"Bash", input:{command:"dotnet test"}}, {type:"tool_use", id:"tu2", name:"Bash", input:{command:"git add -A && git commit -m x && submit"}}],
     usage:{input_tokens:10, output_tokens:20, cache_read_input_tokens:0, cache_creation_input_tokens:1000, cache_creation:{ephemeral_5m_input_tokens:0, ephemeral_1h_input_tokens:1000}}}}'
  jq -cn --arg sid "$SID" --arg t "$(ts)" --arg r "$FINAL" --arg m "$MODEL" --argjson c "$COST" '{type:"result", subtype:"success", session_id:$sid, timestamp:$t, result:$r, is_error:false,
     total_cost_usd:$c, modelUsage:{($m):{inputTokens:10, outputTokens:20, cacheReadInputTokens:0, cacheCreationInputTokens:1000, costUSD:$c}}}'
} > "$P/stream.jsonl"
printf '%s\n' "$FINAL" > "$P/final-message.txt"
echo "$OUT" > "$P/submit-output.txt"
jq --arg e "$(utc)" --argjson rc "$SRC" '. + {endedAt:$e, exit:0, submitExit:$rc, timedOut:false}' "$P/launch.json" > "$P/launch.json.tmp" && mv "$P/launch.json.tmp" "$P/launch.json"
echo "$SID"
