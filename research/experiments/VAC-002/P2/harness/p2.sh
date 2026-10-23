#!/usr/bin/env bash
# VAC-002-P2 harness: one execution = one scenario worked by one arm, with a fresh K1 agent (ARMS.md).
# Adapted from VAC-002 harness/vac2.sh (K1 launcher, workspace layout, budget rule).
#
#   p2.sh exec   RUN SCEN ARM             the whole execution for the arm (setup, turns, admission, policy, review, gate)
#   p2.sh score  RUN SCEN ARM [LABEL]     post-hoc scoring of a recorded head with the sealed oracle (harness only)
#   p2.sh queue  RUN SEED PARALLEL [SCEN...]   every (scenario, arm) pair in a seeded random order, PARALLEL at a time
#   p2.sh cost   RUN                      total cli-estimate cost of RUN (each session counted once, at its last value)
#
# Trees (never inside each other):
#   $P2_WORK/RUN/SCEN-ARM     agent workspace: repo/, env.sh, briefs/
#   $P2_STATE/RUN/SCEN-ARM    harness state: start tree, agent config dirs, streams, gate clones, verifier snapshots
#   $P2_RESULTS/RUN/SCEN-ARM  committed observations
#   $P2_SEALED                hidden oracle (plaintext only while scoring; absent during agent turns)
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"; EXP="$(cd "$H/.." && pwd)"
P2_WORK="${P2_WORK:-/home/user/p2-work}"; P2_STATE="${P2_STATE:-/home/user/.p2-state}"
P2_RESULTS="${P2_RESULTS:-$EXP/results}"; P2_SEALED="${P2_SEALED:-/home/user/.p2-sealed}"
CONFIG="$H/agent-config.json"; TEMPLATE="$H/briefs/brief.md"; VTEMPLATE="$H/briefs/verifier.md"
CLAUDE_BIN="${P2_CLAUDE:-/opt/node22/bin/claude}"
P2_STOP_USD="${P2_STOP_USD:-110}"
export DOTNET_ROOT="${DOTNET_ROOT:-/root/.dotnet}" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
export PATH="$DOTNET_ROOT:$PATH"
fsx() { dotnet fsi --quiet --exec "$H/p2.fsx" "$@"; }
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
hgit() { git -C "$1" -c user.name="p2 harness" -c user.email=harness@p2.invalid -c commit.gpgsign=false "${@:2}"; }
paths() { RUN="$1"; SCEN="$2"; ARM="$3"; X="$SCEN-$ARM"; WS="$P2_WORK/$RUN/$X"; REPO="$WS/repo"; ST="$P2_STATE/$RUN/$X"; RS="$P2_RESULTS/$RUN/$X"; }
arm_ok() { case "$1" in A|B|C|D|E) return 0;; *) echo "unknown arm $1 (A B C D E)" >&2; return 2;; esac; }
scen() { jq -r ".$2" "$EXP/scenarios/$1/scenario.json"; }
sln() { case "$(scen "$1" domain)" in lending) echo Lending.slnx;; billing) echo Billing.slnx;; clinic) echo Clinic.slnx;; esac; }
log() { echo "$(utc) $RUN $X $*" | tee -a "$P2_STATE/$RUN/harness.log" >&2; }

cmd_setup() {
  if [ -e "$WS" ]; then echo "exists: $WS (every run needs a fresh RUN id)" >&2; exit 2; fi
  mkdir -p "$WS/briefs" "$ST" "$RS"
  "$H/corpus.sh" tree "$SCEN" base "$REPO"
  cp -r "$REPO" "$ST/start"
  cat > "$WS/env.sh" <<ENV
export PATH="$DOTNET_ROOT:\$PATH" DOTNET_ROOT="$DOTNET_ROOT" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
cd "$REPO"
ENV
  git -C "$REPO" init -q -b main
  git -C "$REPO" config user.name "engineer"; git -C "$REPO" config user.email "engineer@work.invalid"; git -C "$REPO" config commit.gpgsign false
  hgit "$REPO" add -A && hgit "$REPO" commit -qm "Starting state"
  : > "$ST/receipts.txt"
  jq -n --arg run "$RUN" --arg scen "$SCEN" --arg arm "$ARM" --arg at "$(utc)" --arg base "$(git -C "$REPO" rev-parse HEAD)" \
    --arg claude "$("$CLAUDE_BIN" --version 2>/dev/null | head -1)" --arg brief "$(sha "$TEMPLATE")" --arg vbrief "$(sha "$VTEMPLATE")" \
    --arg policy "$(sha "$H/policy/risk-policy.json")" --arg fsx "$(sha "$H/p2.fsx")" \
    '{schema:"cbe.vac-002-p2.setup/1", run:$run, scenario:$scen, arm:$arm, createdAt:$at, startCommit:$base, claudeCode:$claude,
      briefTemplateSha256:$brief, verifierTemplateSha256:$vbrief, riskPolicySha256:$policy, harnessFsxSha256:$fsx, heads:{}}' > "$RS/setup.json"
}

head_of() { git -C "$REPO" rev-parse HEAD; }
record_head() { local h; h=$(head_of); jq --arg l "$1" --arg h "$h" '.heads[$l] = $h' "$RS/setup.json" > "$RS/setup.json.tmp" && mv "$RS/setup.json.tmp" "$RS/setup.json"; }

# One K1 agent turn. KIND: new | resume. Writes $RS/turn-LABEL.json.
cmd_turn() {
  local KIND="$1" BRIEF="$2" LABEL="$3" sid cfg home prompt
  if [ "$KIND" = new ]; then
    sid=$(cat /proc/sys/kernel/random/uuid); echo "$sid" > "$ST/session"
    prompt=$(jq -r .prompt "$CONFIG")
  else
    sid=$(cat "$ST/session"); prompt=$(jq -r .continuePrompt "$CONFIG")
  fi
  cfg="$ST/agent/config"; home="$ST/agent/home"; mkdir -p "$cfg" "$home" "$ST/turns"
  prompt=${prompt//\{BRIEF\}/$BRIEF}
  local -a unset=(); while read -r v; do unset+=(-u "$v"); done < <(jq -r '.environment.unset[]' "$CONFIG"; compgen -e | grep -E '^P2_' || true)
  local -a sess=(--session-id "$sid"); if [ "$KIND" = resume ]; then sess=(--resume "$sid"); fi
  local out="$ST/turns/$LABEL" start end rc
  start=$(utc); set +e
  ( cd "$REPO" && env "${unset[@]}" HOME="$home" CLAUDE_CONFIG_DIR="$cfg" PATH="$DOTNET_ROOT:/usr/local/bin:/usr/bin:/bin" \
      DOTNET_ROOT="$DOTNET_ROOT" NUGET_PACKAGES="${NUGET_PACKAGES:-/root/.nuget/packages}" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 \
      MSBUILDDISABLENODEREUSE=1 DOTNET_CLI_USE_MSBUILD_SERVER=0 UseSharedCompilation=false TERM=dumb \
      timeout $(( $(jq -r .budgetMinutesPerTurn "$CONFIG") * 60 )) "$CLAUDE_BIN" -p "$prompt" --model "$(jq -r .model "$CONFIG")" "${sess[@]}" \
      --output-format stream-json --verbose --permission-mode bypassPermissions --tools "$(jq -r '.tools.builtIn | join(",")' "$CONFIG")" \
      --strict-mcp-config --mcp-config '{"mcpServers":{}}' > "$out.stream.jsonl" 2> "$out.err" < /dev/null )
  rc=$?; set -e; end=$(utc)
  fsx stream "$out.stream.jsonl" "$WS" > "$out.usage.json" 2>/dev/null || echo '{}' > "$out.usage.json"
  jq -n --arg label "$LABEL" --arg sid "$sid" --arg kind "$KIND" --arg brief "$BRIEF" --arg bsha "$(sha "$BRIEF")" --arg s "$start" --arg e "$end" \
     --argjson rc "$rc" --slurpfile u "$out.usage.json" \
     '{schema:"cbe.vac-002-p2.turn/1", role:"implementer", label:$label, sessionId:$sid, kind:$kind, brief:$brief, briefSha256:$bsha,
       startedAt:$s, endedAt:$e, exit:$rc, timedOut:($rc == 124), usage:$u[0]}' > "$RS/turn-$LABEL.json"
  log "turn $LABEL exit=$rc cost=$(jq -r '.usage.costUsdCli // "?"' "$RS/turn-$LABEL.json")"
}

# Independent reviewer (arm E): a fresh K1 session on a snapshot in harness state. MODE: plan | diff.
cmd_verify() {
  local MODE="$1" LABEL="verifier-$1${2:+-$2}"; local snap="$ST/$LABEL/snapshot" vcfg="$ST/$LABEL/agent"
  rm -rf "$snap"; mkdir -p "$vcfg/config" "$vcfg/home"
  git clone -q --no-hardlinks "$REPO" "$snap"; rm -rf "$snap/.git"
  cp "$RS/admission-plan.json" "$snap/admission.json"
  if [ "$MODE" = diff ]; then git -C "$REPO" diff "$(jq -r .startCommit "$RS/setup.json")" HEAD > "$snap/change.diff"; fi
  local mode; mode=$(awk -v m="<!-- mode: $MODE -->" 'index($0,"<!-- mode: ")==1{on=($0==m);next} on' "$VTEMPLATE")
  awk 'index($0,"<!-- mode: ")==1{exit} {print}' "$VTEMPLATE" > "$snap/REVIEW-BRIEF.md.tmpl"
  printf '%s\n' "$mode" > "$snap/.mode"
  python3 -I - "$snap/REVIEW-BRIEF.md.tmpl" "$snap/.mode" "$(scen "$SCEN" requirementFile)" "$snap/REVIEW-BRIEF.md" <<'PY'
import sys
t, m, req, out = sys.argv[1:]
open(out, 'w').write(open(t).read().replace('{{MODE}}', open(m).read().strip()).replace('{{REQUIREMENT}}', req))
PY
  rm -f "$snap/REVIEW-BRIEF.md.tmpl" "$snap/.mode"
  local prompt; prompt=$(jq -r .verifierPrompt "$CONFIG"); prompt=${prompt//\{BRIEF\}/$snap/REVIEW-BRIEF.md}
  local -a unset=(); while read -r v; do unset+=(-u "$v"); done < <(jq -r '.environment.unset[]' "$CONFIG"; compgen -e | grep -E '^P2_' || true)
  local sid; sid=$(cat /proc/sys/kernel/random/uuid); local out="$ST/turns/$LABEL" start end rc
  start=$(utc); set +e
  ( cd "$snap" && env "${unset[@]}" HOME="$vcfg/home" CLAUDE_CONFIG_DIR="$vcfg/config" PATH="/usr/local/bin:/usr/bin:/bin" TERM=dumb \
      timeout 1200 "$CLAUDE_BIN" -p "$prompt" --model "$(jq -r .model "$CONFIG")" --session-id "$sid" --output-format stream-json --verbose \
      --permission-mode bypassPermissions --tools "$(jq -r '.verifierTools | join(",")' "$CONFIG")" --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
      > "$out.stream.jsonl" 2> "$out.err" < /dev/null )
  rc=$?; set -e; end=$(utc)
  fsx stream "$out.stream.jsonl" "$snap" > "$out.usage.json" 2>/dev/null || echo '{}' > "$out.usage.json"
  cp "$snap/findings.json" "$RS/$LABEL-findings.json" 2>/dev/null || echo '{"findings":null,"note":"no findings file"}' > "$RS/$LABEL-findings.json"
  jq -n --arg label "$LABEL" --arg sid "$sid" --arg s "$start" --arg e "$end" --argjson rc "$rc" --slurpfile u "$out.usage.json" \
     '{schema:"cbe.vac-002-p2.turn/1", role:"verifier", label:$label, sessionId:$sid, kind:"new", startedAt:$s, endedAt:$e, exit:$rc,
       timedOut:($rc == 124), usage:$u[0]}' > "$RS/turn-$LABEL.json"
  log "verify $MODE exit=$rc blocking=$(fsx blocking "$RS/$LABEL-findings.json") cost=$(jq -r '.usage.costUsdCli // "?"' "$RS/turn-$LABEL.json")"
}

# Admission of the decision records at HEAD against the starting tree. Writes $RS/admission-LABEL.json.
cmd_admit() {
  local LABEL="$1" t="$ST/admit-$1"
  rm -rf "$t"; git clone -q --no-hardlinks "$REPO" "$t"
  fsx admit "$ST/start" "$t" "$t/.decisions/decisions.json" "$ST/receipts.txt" > "$RS/admission-$LABEL.json"
  log "admission $LABEL rejected=$(jq -r '.rejected // "unreadable"' "$RS/admission-$LABEL.json")"
}

# The independent gate (arms D and E). Writes $RS/gate-N.json; prints the failure text to $ST/gate-N.failures.
cmd_gate() {
  local N="$1" TIER="$2" t="$ST/gate-$1" failures="$ST/gate-$1.failures" start; start=$(date +%s%3N)
  : > "$failures"; rm -rf "$t"; git clone -q --no-hardlinks "$REPO" "$t"
  local clean=true; [ -z "$(git -C "$REPO" status --porcelain)" ] || { clean=false; echo "- cleanTree: uncommitted changes remain" >> "$failures"; }
  ( cd "$t" && timeout 900 dotnet test "$(sln "$SCEN")" --logger "trx;LogFileName=$t/gate.trx" > "$t/gate.log" 2>&1 ) || true
  fsx trx "$t/gate.trx" "$t/gate.log" > "$ST/gate-$N.tests.json"
  local bok fl; bok=$(jq .buildOk "$ST/gate-$N.tests.json"); fl=$(jq .failed "$ST/gate-$N.tests.json")
  [ "$bok" = true ] || echo "- build: the solution does not build ($(jq .compileErrors "$ST/gate-$N.tests.json") compiler errors)" >> "$failures"
  [ "$fl" = 0 ] || jq -r '.tests[] | select(.outcome != "Passed") | "- tests: \(.name) failed"' "$ST/gate-$N.tests.json" >> "$failures"
  jq empty "$t/.work/report.json" 2>/dev/null || echo "- report: .work/report.json is missing or not valid JSON" >> "$failures"
  fsx admit "$ST/start" "$t" "$t/.decisions/decisions.json" "$ST/receipts.txt" > "$RS/admission-gate-$N.json"
  jq -r --slurpfile d <(jq '[.decisions[]? | {key: .decisionId, value: ((.implementedIn // []) | length > 0)}] | from_entries' "$t/.decisions/decisions.json" 2>/dev/null || echo '{}') \
     '.decisions[]? | select(.computedStatus == "rejected") | select($d[0][.decisionId] == true) | "- authorization: decision \(.decisionId) is implemented but rejected: \(.reasons | join("; "))"' \
     "$RS/admission-gate-$N.json" >> "$failures"
  jq -e '.ok == true' "$RS/admission-gate-$N.json" > /dev/null || echo "- authorization: .decisions/decisions.json is missing or unreadable" >> "$failures"
  fsx records "$ST/start" "$t" > "$ST/gate-$N.records.json"
  jq -r '.[] | "- authority records: \(.path) (\(.change)): \(.detail)"' "$ST/gate-$N.records.json" >> "$failures"
  if [ "$ARM" = E ] && [ "$TIER" = high ]; then
    cmd_verify diff "$N"
    [ "$(fsx blocking "$RS/verifier-diff-$N-findings.json")" = 0 ] || \
      jq -r '.findings[] | select(.severity == "blocking") | "- independent review: \(.issue) Authorized: \(.authorizedAlternative // "")"' "$RS/verifier-diff-$N-findings.json" >> "$failures"
  fi
  local ok=true; if [ -s "$failures" ]; then ok=false; fi
  if [ "$ok" = true ]; then echo "receipt:$RUN/$X/gate-$N/$(head_of)" >> "$ST/receipts.txt"; fi
  jq -n --argjson n "$N" --arg tier "$TIER" --arg head "$(head_of)" --argjson ok "$ok" --argjson clean "$clean" \
     --slurpfile tests "$ST/gate-$N.tests.json" --slurpfile rec "$ST/gate-$N.records.json" --rawfile f "$failures" --argjson ms "$(( $(date +%s%3N) - start ))" \
     '{schema:"cbe.vac-002-p2.gate/1", attempt:$n, tier:$tier, head:$head, accepted:$ok, cleanTree:$clean,
       build:$tests[0].buildOk, testsPassed:$tests[0].passed, testsFailed:$tests[0].failed, authorityRecordFindings:$rec[0],
       failures:($f | split("\n") | map(select(length > 0))), hostMs:$ms}' > "$RS/gate-$N.json"
  log "gate $N accepted=$ok"
}

cmd_exec() {
  paths "$1" "$2" "$3"; arm_ok "$ARM"; mkdir -p "$P2_STATE/$RUN"
  local spent; spent=$(cmd_cost "$RUN")
  if awk -v s="$spent" -v c="$P2_STOP_USD" 'BEGIN{exit !(s >= c)}'; then
    mkdir -p "$RS"; jq -n --arg s "$spent" '{schema:"cbe.vac-002-p2.execution/1", status:"not-run", reason:("budget stop at $" + $s)}' > "$RS/execution.json"
    log "not run: budget (\$$spent >= \$$P2_STOP_USD)"; return 0
  fi
  if [ -d "$P2_SEALED/S01" ]; then echo "refusing to run agents while the sealed store is in plaintext ($P2_SEALED)" >&2; exit 3; fi
  cmd_setup; log "start"
  local item req tests b="$WS/briefs"
  item=$(scen "$SCEN" workItem); req=$(scen "$SCEN" requirementFile); tests=$(jq -r '.visibleTests | join(", ")' "$EXP/scenarios/$SCEN/scenario.json")
  local -a common=(ITEM="$item" REPO="$REPO" ENV="$WS/env.sh" WORKSPACE="$WS" REQUIREMENT="$req" TESTS="$tests")
  local checklist=$',\n      "checklist": { "requested": "...", "supported": "...", "exception": "...", "conflict": "...", "altersAccepted": "...", "needsAuthorization": "..." }'
  case "$ARM" in
    A) fsx render "$TEMPLATE" intro,report "${common[@]}" > "$b/work.md";;
    B) fsx render "$TEMPLATE" intro,checklist,report "${common[@]}" CHECKLIST_FIELD="$checklist" > "$b/work.md";;
    C) fsx render "$TEMPLATE" intro,records,report "${common[@]}" > "$b/work.md";;
    D|E) fsx render "$TEMPLATE" intro,records,plan "${common[@]}" > "$b/plan.md";;
  esac
  if [ "$ARM" = A ] || [ "$ARM" = B ] || [ "$ARM" = C ]; then
    cmd_turn new "$b/work.md" work; record_head final
  else
    cmd_turn new "$b/plan.md" plan; record_head plan
    git -C "$REPO" diff --name-only "$(jq -r .startCommit "$RS/setup.json")" HEAD | grep -vE '^\.decisions/|^\.work/' > "$RS/plan-phase-code-changes.txt" || true
    cmd_admit plan
    local tier=low verifierText="" gateExtra=""
    if [ "$ARM" = E ]; then
      fsx policy "$RS/admission-plan.json" "$ST/admit-plan/.decisions/decisions.json" > "$RS/policy.json"; tier=$(jq -r .tier "$RS/policy.json")
      log "policy tier=$tier signals=$(jq -c .signals "$RS/policy.json")"
      gateExtra=", and, for higher-risk work, an independent reviewer compares your change with its authority"
      if [ "$tier" = high ]; then
        cmd_verify plan
        fsx findings-text "$RS/verifier-plan-findings.json" "An independent reviewer also read your plan against the repository's sources of authority. Their findings:" > "$ST/verifier.txt"
        verifierText="@$ST/verifier.txt"
      fi
    fi
    fsx admission-text "$RS/admission-plan.json" > "$ST/admission.txt"
    fsx render "$TEMPLATE" implement,report "${common[@]}" ADMISSION="@$ST/admission.txt" ${verifierText:+VERIFIER="$verifierText"} GATE_EXTRA="$gateExtra" > "$b/implement.md"
    cmd_turn resume "$b/implement.md" implement; record_head implement
    cmd_gate 1 "$tier"
    if [ "$(jq .accepted "$RS/gate-1.json")" = false ]; then
      fsx render "$TEMPLATE" repair ITEM="$item" HEAD="$(jq -r .head "$RS/gate-1.json")" FAILURES="@$ST/gate-1.failures" > "$b/repair.md"
      cmd_turn resume "$b/repair.md" repair; record_head repair
      cmd_gate 2 "$tier"
    fi
    record_head final
  fi
  jq -n --arg at "$(utc)" --slurpfile s "$RS/setup.json" '{schema:"cbe.vac-002-p2.execution/1", status:"completed", endedAt:$at, heads:$s[0].heads}' > "$RS/execution.json"
  log "end"
}

# Post-hoc score of one recorded head (default: final). Requires the plaintext sealed store; never run during turns.
cmd_score() {
  paths "$1" "$2" "$3"; local LABEL="${4:-final}"; local head t="$ST/score-$LABEL"
  head=$(jq -r ".heads[\"$LABEL\"] // empty" "$RS/setup.json"); if [ -z "$head" ]; then echo "no head $LABEL" >&2; return 2; fi
  rm -rf "$t"; mkdir -p "$t"; git clone -q --no-hardlinks "$REPO" "$t/tree"; git -C "$t/tree" checkout -q "$head"
  ( cd "$t/tree" && timeout 900 dotnet test "$(sln "$SCEN")" --logger "trx;LogFileName=$t/visible.trx" > "$t/visible.log" 2>&1 ) || true
  fsx trx "$t/visible.trx" "$t/visible.log" > "$t/visible.json"
  local orc; orc=$("$H/corpus.sh" oracle "$t/tree" "$SCEN" "$t/oracle")
  fsx records "$ST/start" "$t/tree" > "$t/records.json"
  if [ -f "$t/tree/.decisions/decisions.json" ]; then fsx admit "$ST/start" "$t/tree" "$t/tree/.decisions/decisions.json" "$ST/receipts.txt" > "$RS/admission-posthoc-$LABEL.json"; fi
  fsx score "$SCEN" "$P2_SEALED/meta.json" "$t/visible.json" "$orc" "$t/records.json" "$t/tree/.work/report.json" "$t/tree/.decisions/decisions.json" "$LABEL" "$head" > "$RS/score-$LABEL.json"
  echo "$RS/score-$LABEL.json"
}

# Total cost: every turn file of RUN, each session counted once at its last cumulative value (VAC-002 amendment A1).
cmd_cost() {
  { cat "$P2_RESULTS/$1"/*/turn-*.json 2>/dev/null || true; } | jq -s 'group_by(.sessionId) | map(map(.usage.costUsdCli // 0) | max) | add // 0'
}

cmd_queue() {
  local RUNID="$1" SEED="$2" PAR="$3"; shift 3
  local scens=("$@"); [ ${#scens[@]} -eq 0 ] && mapfile -t scens < <(ls "$EXP/scenarios")
  mkdir -p "$P2_STATE/$RUNID" "$P2_RESULTS/$RUNID"
  python3 -I -c 'import random,sys; s=int(sys.argv[1]); pairs=[(c,a) for c in sys.argv[2:] for a in "ABCDE"]; random.Random(s).shuffle(pairs); print("\n".join(f"{c} {a}" for c,a in pairs))' \
    "$SEED" "${scens[@]}" > "$P2_RESULTS/$RUNID/order.txt"
  xargs -P "$PAR" -L 1 bash -c '"$0" exec "$1" "$3" "$4" > /dev/null 2>> "$2" || echo "$(date -u +%FT%TZ) exec failed: $3 $4" >> "$2"' \
    "$H/p2.sh" "$RUNID" "$P2_STATE/$RUNID/queue.err" < "$P2_RESULTS/$RUNID/order.txt" || true
}

case "${1:-}" in
  exec) shift; cmd_exec "$@";;
  score) shift; cmd_score "$@";;
  cost) shift; cmd_cost "$@";;
  queue) shift; cmd_queue "$@";;
  *) sed -n '2,9p' "$0"; exit 2;;
esac
