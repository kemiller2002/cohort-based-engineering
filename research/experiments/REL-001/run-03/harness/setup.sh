#!/usr/bin/env bash
# REL-001 run-03 workspace setup (adapted from run-02/harness/setup.sh: one agent per trial, no shared remote).
#   usage: run-03/harness/setup.sh ARM TASK RUNID
#   ARM  bare | directives | echelon-original | echelon-optimized   (arms A, B, C, D)
#   TASK V1..V8
# Three trees per run (see lib.sh): $REL003_RUNS/RUNID (the agent workspace: repo/, AGENT_BRIEF.md, env.sh,
# DIRECTIVES.md in B-D, tools/bin shims, logs/), $REL003_HOST/RUNID (host-owned contract, authority, policy
# and the D verifier; C and D only) and $REL003_STATE/RUNID (harness state the agent is never pointed at).
# The oracle, the reference solutions and task.json are never copied into, or named from, a workspace.
# Ordo refusing a contract does not abort setup (run-02 R7): V7's refusal reaches the agent during the run.
# A pilot or confirmatory run (no -SMOKE- in RUNID) refuses to start while a pin it needs is TBD (gate G4)
# or a binary's sha256 differs from its pin.
source "$(dirname "$0")/lib.sh"
[ $# -eq 3 ] || { echo "usage: $0 bare|directives|echelon-original|echelon-optimized V1..V8 RUNID" >&2; exit 2; }
ARM="$1"; TASK="$2"; run_paths "$3"
LETTER=$(arm_letter "$ARM") || { echo "unknown arm $ARM (expected one of: $ARMS)" >&2; exit 2; }
[ -f "$FIX3/tasks/$TASK/task.json" ] || { echo "unknown task $TASK" >&2; exit 2; }
[[ "$RUN_ID" =~ ^REL-001-R3-[A-Za-z0-9-]+$ ]] || { echo "RUNID must match ^REL-001-R3-[A-Za-z0-9-]+$" >&2; exit 2; }
LABEL=$(label_of "$RUN_ID")
for d in "$RUN_DIR" "$HD" "$HS"; do [ -e "$d" ] && { echo "exists: $d (every run needs a fresh runId)" >&2; exit 2; }; done
[ -f "$AGENT_CONFIG" ] || { echo "agent configuration not found: $AGENT_CONFIG" >&2; exit 2; }
[ -f "$PRICE_TABLE" ] || { echo "price table not found: $PRICE_TABLE" >&2; exit 2; }
if [ "$LABEL" != smoke ]; then
  require_pins "$ARM" || exit 2
  [ "$DRY_RUN" = 1 ] && { echo "dry-run is for smoke runs only" >&2; exit 2; }
  [ "$(sha "$PRICE_TABLE")" = "$(pin .priceTable.sha256)" ] || { echo "price table sha256 differs from its pin" >&2; exit 2; }
  [ "$(sha "$DIRECTIVES")" = "$(pin .directives.sha256)" ] || { echo "directives sha256 differs from its pin" >&2; exit 2; }
fi
ARM_PRAXIS=$( [ "$ARM" = echelon-original ] && echo "$PRAXIS_C" || echo "$PRAXIS_D")
if is_echelon "$ARM" && { is_tbd "$ARM_PRAXIS" || [ ! -e "$ARM_PRAXIS" ]; }; then
  echo "arm $LETTER needs its Echelon binaries (REL003_PRAXIS_*, REL003_DOKIMOS_*, REL003_ORDO_*); arms A and B need none" >&2; exit 2
fi

ITEM=$(task_field "$TASK" .workItem); CATEGORY=$(task_field "$TASK" .category); TITLE=$(task_field "$TASK" .title)
VISIBLE="tests/Ledger.Tests/Acceptance/${TASK}AcceptanceTests.fs"
mkdir -p "$RUN_DIR/tools/bin" "$RUN_DIR/logs" "$HS"
is_echelon "$ARM" && mkdir -p "$HI"
[ "$ARM" = echelon-optimized ] && mkdir -p "$HD/bin"
write_dotnet_shim "$RUN_DIR/tools/bin/dotnet" "$RUN_DIR/logs/dotnet.jsonl" agent

# --- Echelon tools (C, D): private copies, a logging praxis shim, a Dokimos entry point
PX_FILE=""; DK_FILE=""; VX_FILE=""; PRAXIS_VER=""; DOKIMOS_VER=""; ORDO=""
if is_echelon "$ARM"; then
  if [ "$ARM" = echelon-original ]; then PX_SRC="$PRAXIS_C"; DK_SRC="$DOKIMOS_C"; ORDO="$ORDO_C"; else PX_SRC="$PRAXIS_D"; DK_SRC="$DOKIMOS_D"; ORDO="$ORDO_D"; fi
  for f in "$PX_SRC" "$DK_SRC" "$ORDO"; do [ -f "$f" ] || { echo "binary not found: $f" >&2; exit 2; }; done
  PX_FILE=$(copy_tool "$PX_SRC" "$RUN_DIR/tools/praxis" praxis)
  DK_FILE=$(copy_tool "$DK_SRC" "$RUN_DIR/tools/dokimos" dokimos)
  write_praxis_shim "$RUN_DIR/tools/bin/praxis" "$RUN_DIR/tools/praxis/praxis" "$RUN_DIR/logs"
  PRAXIS_VER=$(tool_version "$RUN_DIR/tools/praxis/praxis"); DOKIMOS_VER=$(tool_version "$RUN_DIR/tools/dokimos/dokimos")
  if [ "$LABEL" != smoke ]; then
    L=$LETTER; want=$(pin ".arms.$L.sha256Entry")
    [ "$(sha "$PX_FILE")" = "$want" ] || { echo "arm $L Praxis entry sha256 $(sha "$PX_FILE") differs from pin $want" >&2; exit 2; }
    [ "$PRAXIS_VER" = "$(pin ".arms.$L.praxis.version")" ] || { echo "arm $L Praxis version $PRAXIS_VER differs from its pin" >&2; exit 2; }
  fi
  if [ "$ARM" = echelon-optimized ]; then
    VX_FILE=$(copy_tool "$PRAXIS_D" "$HD/bin/praxis" praxis)
    write_dotnet_shim "$HD/bin/dotnet" "$HS/verifier-dotnet.jsonl" verifier
  fi
fi

# --- repository: the starting repository, the requirement, the visible tests, the work queue (C, D) and
# ros.json (D), as one initial commit on main.
REPO="$RUN_DIR/repo"
cp -r "$FIX3/repo" "$REPO"
mkdir -p "$REPO/requirements"
cp "$FIX3/tasks/$TASK/requirement.md" "$REPO/requirements/$TASK.md"
cp "$FIX3/tasks/$TASK/${TASK}AcceptanceTests.fs" "$REPO/$VISIBLE"
if is_echelon "$ARM"; then
  mkdir -p "$REPO/.ros/work"
  jq -cn --arg id "$ITEM" --arg t "$TITLE" '{schemaVersion:"1.0.0",items:[{id:$id,title:$t,status:"captured"}]}' > "$REPO/.ros/work/queue.json"
fi
[ "$ARM" = echelon-optimized ] && jq -n '{workProtocol:{requireAttestedEvidence:true}}' > "$REPO/ros.json"
( cd "$REPO" && git init -q -b main . && git config user.email "agent@rel003.invalid" && git config user.name "rel003 agent"
  git add -A && git commit -qm "fixture: REL-001 run-03 $TASK" )
INITIAL=$(git -C "$REPO" rev-parse HEAD)

# --- host-owned contract and authority (C, D). Ordo's verdict is recorded, never enforced here (R7).
ORDO_RC=null; ORDO_DIGEST=""; PRAXIS_CHECK_RC=null; CONTRACT_DIGEST=""; VERIFIER='null'
if is_echelon "$ARM"; then
  cp "$FIX3/tasks/$TASK/contract.json" "$HI/contract.json"
  set +e
  "$ORDO" ecir check --blueprint "$HI/contract.json" --json > "$HS/setup-ordo-check.json" 2> "$HS/setup-ordo-check.err"; ORDO_RC=$?
  "$RUN_DIR/tools/praxis/praxis" ordo contract check --contract "$HI/contract.json" > "$HS/setup-praxis-check.txt" 2>&1; PRAXIS_CHECK_RC=$?
  set -e
  ORDO_DIGEST=$(jq -r '.contractDigest // empty' "$HS/setup-ordo-check.json" 2>/dev/null || true)
  CONTRACT_DIGEST="${ORDO_DIGEST:-sha256:$(sha "$HI/contract.json")}"
  write_authority "$HI/authority.json" "$(contract_decisions "$HI/contract.json")"
  if [ "$ARM" = echelon-optimized ]; then
    jq -n --arg task "$TASK" --arg dn "$HD/bin/dotnet" --arg p "$VISIBLE" --arg s "$(sha "$FIX3/tasks/$TASK/${TASK}AcceptanceTests.fs")" '
      {schemaVersion:"echelon.validation-policy/1", policyId:("rel003-" + $task),
       validations:[{name:"unit-tests", evidenceId:"EV-TESTS", command:[$dn,"test","Ledger.slnx"], timeoutSeconds:900}],
       protectedPaths:[{path:$p, sha256:$s}]}' > "$HI/policy.json"
    ( unset PRAXIS_ACTOR PRAXIS_ACTOR_KIND PRAXIS_VERIFIER_SOCKET PRAXIS_COMPLETION_AUTHORITY PRAXIS_ORDO_CONTRACT
      export REL003_DOTNET_SOURCE=verifier
      setsid "$HD/bin/praxis/praxis" verifier serve --socket "$HD/verifier.sock" --policy "$HI/policy.json" \
        --contract-digest "$CONTRACT_DIGEST" > "$HS/verifier.out" 2> "$HS/verifier.err" < /dev/null &
      echo $! > "$HS/verifier.pid" )
    for _ in $(seq 1 120); do [ -s "$HS/verifier.out" ] && [ -S "$HD/verifier.sock" ] && break; sleep 0.5; done
    [ -s "$HS/verifier.out" ] && [ -S "$HD/verifier.sock" ] || { echo "verifier did not start (see $HS/verifier.err)" >&2; verifier_stop; exit 3; }
    VLINE=$(head -1 "$HS/verifier.out")
    jq --argjson v "$VLINE" '. + {TrustedVerifierKeys:[{KeyId:$v.keyId, Algorithm:"ecdsa-p256-sha256", PublicKey:$v.publicKey}], ValidationPolicyDigest:$v.policyDigest}' \
      "$HI/authority.json" > "$HI/authority.json.tmp" && mv "$HI/authority.json.tmp" "$HI/authority.json"
    VERIFIER=$(jq -cn --argjson v "$VLINE" --arg pid "$(cat "$HS/verifier.pid")" --arg sock "$HD/verifier.sock" --arg cd "$CONTRACT_DIGEST" \
      --arg ps "$(sha "$HI/policy.json")" '{keyId:$v.keyId, policyDigest:$v.policyDigest, policySha256:$ps, contractDigest:$cd, pid:($pid|tonumber), socket:$sock}')
  fi
fi

# --- env.sh, DIRECTIVES.md (B, C, D: identical bytes) and AGENT_BRIEF.md
W="$RUN_DIR"; TOKEN="tok-$RUN_ID"
REQ_ARGS=""
if is_echelon "$ARM"; then
  REQ_ARGS=$( { jq -r '.requirements[].source.key | "--requirement " + .' "$HI/contract.json"; jq -r '.nodes[] | select(.kind=="decision") | "--decision " + .id' "$HI/contract.json"; } | paste -sd' ')
fi
{
  echo "# source this file before starting the agent session (REL-001 run-03 $RUN_ID)"
  echo "export PATH=\"$RUN_DIR/tools/bin:$DOTNET_ROOT_DIR:\$PATH\" DOTNET_ROOT=\"$DOTNET_ROOT_DIR\" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1"
  echo "export REL003_AGENT=agent-1"
  if is_echelon "$ARM"; then
    echo "export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=rel003/$RUN_ID/agent-1 PRAXIS_TELEMETRY_PROVIDER=$MODEL_PROVIDER PRAXIS_TELEMETRY_RUNTIME=claude-code"
    echo "export PRAXIS_DOKIMOS_EXECUTABLE=\"$RUN_DIR/tools/dokimos/dokimos\""
  fi
  if [ "$ARM" = echelon-optimized ]; then
    echo "export PRAXIS_VERIFIER_SOCKET=\"$HD/verifier.sock\" PRAXIS_COMPLETION_AUTHORITY=\"$HI/authority.json\" PRAXIS_ORDO_CONTRACT=\"$HI/contract.json\""
  fi
  echo "cd \"$REPO\""
} > "$W/env.sh"
has_directives "$ARM" && cp "$DIRECTIVES" "$W/DIRECTIVES.md"
TEMPLATES=("$H3/briefs/core.md")
has_directives "$ARM" && TEMPLATES+=("$H3/briefs/directives.md")
[ "$ARM" = echelon-original ] && TEMPLATES+=("$H3/briefs/workflow-c.md")
[ "$ARM" = echelon-optimized ] && TEMPLATES+=("$H3/briefs/workflow-d.md")
TEMPLATES+=("$H3/briefs/outcome.md")
ATTEMPTS=""; is_echelon "$ARM" && ATTEMPTS="- At most 3 completion attempts (each \`praxis work complete-verified\` invocation counts)."
jq -n --arg REPO "$REPO" --arg ENV "$W/env.sh" --arg ITEM "$ITEM" --arg TASK "$TASK" --arg WORKSPACE "$W" \
  --arg ATTEMPTS_LINE "$ATTEMPTS" --arg DIRECTIVES "$W/DIRECTIVES.md" --arg CONTRACT "$HI/contract.json" \
  --arg AUTHORITY "$HI/authority.json" --arg TOKEN "$TOKEN" --arg STORE "" --arg REQ_ARGS "$REQ_ARGS" '$ARGS.named' > "$HS/brief-values-agent-1.json"
python3 -I "$H3/render-brief.py" "$HS/brief-values-agent-1.json" "${TEMPLATES[@]}" > "$W/AGENT_BRIEF.md"
WS_JSON=$(jq -cn --arg w "$W" --arg r "$REPO" --arg b "$W/AGENT_BRIEF.md" --arg bs "$(sha "$W/AGENT_BRIEF.md")" --arg t "$TOKEN" \
  --argjson tpl "$(printf '%s\n' "${TEMPLATES[@]}" | xargs -n1 basename | jq -R . | jq -sc .)" \
  '[{name:"agent-1", dir:$w, repo:$r, brief:$b, briefSha256:$bs, token:$t, templates:$tpl}]')

# --- host-file digests (X6)
DIGESTS=$(
  { [ -d "$HI" ] && find "$HI" -type f
    [ -d "$HD/bin" ] && echo "$HD/bin"
    [ -d "$RUN_DIR/tools/praxis" ] && echo "$RUN_DIR/tools/praxis"
    [ -d "$RUN_DIR/tools/dokimos" ] && echo "$RUN_DIR/tools/dokimos"
    echo "$PRICE_TABLE"
    has_directives "$ARM" && echo "$W/DIRECTIVES.md"
    true; } | LC_ALL=C sort | while read -r p; do
      if [ -d "$p" ]; then printf '%s\t%s\n' "$p" "$(tree_sha "$p")"; else printf '%s\t%s\n' "$p" "$(sha "$p")"; fi
    done | jq -Rn '[inputs | split("\t") | {key:.[0], value:.[1]}] | from_entries')
echo "$DIGESTS" > "$HS/host-digests.json"

# --- run.json (harness state only)
REPLICATE=$(sed -nE 's/.*-r([0-9]+)-.*/\1/p' <<<"$RUN_ID"); REPLICATE=${REPLICATE:-1}
fixture_digest=$(cd "$FIX3" && find repo tasks oracle reference -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)
oracle_digest=$(cd "$FIX3" && find oracle -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)
DOTNET_VER=$([ "$DRY_RUN" = 1 ] && echo dry-run || "$REAL_DOTNET" --version)
CBE_COMMIT=$(git -C "$CBE" rev-parse HEAD 2>/dev/null || echo unknown)
jq -n --arg run "$RUN_ID" --arg arm "$ARM" --arg letter "$LETTER" --arg task "$TASK" --arg item "$ITEM" --arg cat "$CATEGORY" \
  --arg at "$(utc)" --arg init "$INITIAL" --argjson rep "$REPLICATE" --arg label "$LABEL" --arg dry "$DRY_RUN" \
  --arg acc "$(sha "$FIX3/tasks/$TASK/requirement.md")" --arg vis "$(sha "$FIX3/tasks/$TASK/${TASK}AcceptanceTests.fs")" --arg visp "$VISIBLE" \
  --arg fx "$fixture_digest" --arg ox "$oracle_digest" --arg cbe "$CBE_COMMIT" --arg dn "$DOTNET_VER" \
  --argjson ws "$WS_JSON" --arg runDir "$RUN_DIR" --arg hd "$HD" --arg hs "$HS" \
  --argjson tj "$(jq -c . "$FIX3/tasks/$TASK/task.json")" \
  --arg pv "$PRAXIS_VER" --arg dv "$DOKIMOS_VER" --arg ov "$( [ -n "$ORDO" ] && tool_version "$ORDO" || true)" \
  --arg ps "$( [ -n "$PX_FILE" ] && sha "$PX_FILE" || true)" --arg ds "$( [ -n "$DK_FILE" ] && sha "$DK_FILE" || true)" \
  --arg vs "$( [ -n "$VX_FILE" ] && sha "$VX_FILE" || true)" --arg os "$( [ -n "$ORDO" ] && sha "$ORDO" || true)" \
  --arg dirs "$(sha "$DIRECTIVES")" --argjson ordoRc "$ORDO_RC" --arg ordoDigest "$ORDO_DIGEST" --argjson pxRc "$PRAXIS_CHECK_RC" \
  --arg cdig "$CONTRACT_DIGEST" --arg csha "$(sha "$FIX3/tasks/$TASK/contract.json")" --argjson verifier "$VERIFIER" \
  --arg mp "$MODEL_PROVIDER" --arg mm "$MODEL" --arg mc "$(sha "$AGENT_CONFIG")" --arg mpath "$AGENT_CONFIG" \
  --arg pt "$PRICE_TABLE" --arg pts "$(sha "$PRICE_TABLE")" --arg mx "$MEASURE_PRAXIS" \
  --arg mxs "$( [ -f "$MEASURE_PRAXIS" ] && sha "$MEASURE_PRAXIS" || true)" --arg cache "$CACHE_CONDITION" --arg pins "$(sha "$PINS")" '
  def nn: if . == "" then null else . end;
  {schema:"cbe.rel-001.run-03-run/1", runId:$run, arm:$arm, armLetter:$letter, task:$task, workItem:$item, category:$cat,
   categoryBasis:"builder-assigned (unvalidated)", label:$label, dryRun:($dry == "1"), replicate:$rep, block:($task + "-r" + ($rep|tostring)),
   createdAt:$at, initialCommit:$init, agents:1, requirementIds:$tj.requirementIds, requirementKeys:$tj.requirementKeys,
   decisionIds:$tj.decisionIds, conflict:$tj.conflict, expectedOutcome:$tj.expectedOutcome,
   acceptanceCriteriaDigest:$acc, visibleTests:{path:$visp, sha256:$vis},
   fixtureDigest:$fx, oracleDigest:$ox, cohortBasedEngineeringCommit:$cbe, pinsSha256:$pins,
   paths:{runDir:$runDir, host:$hd, state:$hs, remote:null}, workspaces:$ws,
   directives:(if $letter == "A" then null else {sha256:$dirs} end),
   tools:({dotnet:$dn} + (if $pv == "" then {} else {praxis:$pv, dokimos:$dv, ordo:($ov|nn)} end)),
   binaries:(if $ps == "" then {} else {praxis:{sha256:$ps}, dokimos:{sha256:$ds}, ordo:{sha256:$os}}
             + (if $vs == "" then {} else {verifier:{sha256:$vs}} end) end),
   contract:(if $pv == "" then null else {sha256:$csha, ordoExit:$ordoRc, ordoAdmits:($ordoRc == 0), ordoContractDigest:($ordoDigest|nn),
             praxisCheckExit:$pxRc, boundDigest:$cdig} end),
   verifier:$verifier,
   enforcement:{ordoContracts:($pv != ""), praxisOwnership:($pv != ""), dokimosVerification:($pv != ""), attestedEvidence:($letter == "D")},
   cache:{condition:$cache},
   measurement:{praxis:($mx|nn), sha256:($mxs|nn), priceTable:$pt, priceTableSha256:$pts},
   model:{provider:$mp, configuredModel:$mm, configuration:$mpath, configurationDigest:$mc}}' > "$HS/run.json"
echo "$RUN_DIR"
