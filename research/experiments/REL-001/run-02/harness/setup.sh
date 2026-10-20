#!/usr/bin/env bash
# REL-001 run-02 workspace setup.
#   usage: run-02/harness/setup.sh ARM TASK RUNID
#   ARM  bare | directives | echelon-original | echelon-optimized   (arms A, B, C, D)
#   TASK U1..U9
# Three trees per run (all overridable, see lib.sh):
#   $REL002_RUNS/RUNID   the agent workspace(s): repo/ (or remote.git + agent-1/ agent-2/ for U6),
#                        AGENT_BRIEF.md, env.sh, DIRECTIVES.md (B, C, D), tools/bin shims, logs/
#   $REL002_HOST/RUNID   host-owned files outside every repository (C, D): contract, authority,
#                        policy (D), the D verifier binary and its socket
#   $REL002_STATE/RUNID  harness state the agent is never pointed at: run.json, host-file digests,
#                        verifier log, later transcripts and scoring
# The oracle, the reference solutions and task.json are never copied into, or named from, a
# workspace (R12). Ordo refusing a contract does not abort setup (R7).
source "$(dirname "$0")/lib.sh"
[ $# -eq 3 ] || { echo "usage: $0 bare|directives|echelon-original|echelon-optimized U1..U9 RUNID" >&2; exit 2; }
ARM="$1"; TASK="$2"; run_paths "$3"
LETTER=$(arm_letter "$ARM") || { echo "unknown arm $ARM (expected one of: $ARMS)" >&2; exit 2; }
[ -f "$FIX2/tasks/$TASK/task.json" ] || { echo "unknown task $TASK" >&2; exit 2; }
[[ "$RUN_ID" =~ ^REL-001-R2-[A-Za-z0-9-]+$ ]] || { echo "RUNID must match ^REL-001-R2-[A-Za-z0-9-]+$" >&2; exit 2; }
for d in "$RUN_DIR" "$HD" "$HS"; do [ -e "$d" ] && { echo "exists: $d (every run needs a fresh runId)" >&2; exit 2; }; done
[ -f "$AGENT_CONFIG" ] || { echo "agent configuration not found: $AGENT_CONFIG" >&2; exit 2; }
[ -f "$PRICE_TABLE" ] || { echo "price table not found: $PRICE_TABLE" >&2; exit 2; }

ITEM=$(task_field "$TASK" .workItem); AGENTS=$(task_field "$TASK" .agents)
CATEGORY=$(task_field "$TASK" .category); TITLE=$(task_field "$TASK" .title)
VISIBLE="tests/Ledger.Tests/Acceptance/${TASK}AcceptanceTests.fs"
mkdir -p "$RUN_DIR/tools/bin" "$RUN_DIR/logs" "$HS"
is_echelon "$ARM" && mkdir -p "$HI"
[ "$ARM" = echelon-optimized ] && mkdir -p "$HD/bin"
write_dotnet_shim "$RUN_DIR/tools/bin/dotnet" "$RUN_DIR/logs/dotnet.jsonl" agent

# --- Echelon tools (C, D): private copies, a logging praxis shim, a Dokimos entry point
PX_FILE=""; DK_FILE=""; VX_FILE=""; PRAXIS_VER=""; DOKIMOS_VER=""
if is_echelon "$ARM"; then
  if [ "$ARM" = echelon-original ]; then PX_SRC="$PRAXIS_C"; DK_SRC="$DOKIMOS_C"; else PX_SRC="$PRAXIS_D"; DK_SRC="$DOKIMOS_D"; fi
  for f in "$PX_SRC" "$DK_SRC" "$ORDO"; do [ -f "$f" ] || { echo "binary not found: $f" >&2; exit 2; }; done
  PX_FILE=$(copy_tool "$PX_SRC" "$RUN_DIR/tools/praxis" praxis)
  DK_FILE=$(copy_tool "$DK_SRC" "$RUN_DIR/tools/dokimos" dokimos)
  write_praxis_shim "$RUN_DIR/tools/bin/praxis" "$RUN_DIR/tools/praxis/praxis" "$RUN_DIR/logs"
  PRAXIS_VER=$(tool_version "$RUN_DIR/tools/praxis/praxis"); DOKIMOS_VER=$(tool_version "$RUN_DIR/tools/dokimos/dokimos")
  if [ "$ARM" = echelon-optimized ]; then
    VX_FILE=$(copy_tool "$PRAXIS_D" "$HD/bin/praxis" praxis)                # the verifier: a host-owned copy
    write_dotnet_shim "$HD/bin/dotnet" "$HS/verifier-dotnet.jsonl" verifier  # its test runs are counted too
  fi
fi

# --- repositories
# build_repo DIR NAME: the starting repository (+ U9 start overlay), requirement, visible tests,
# the work queue (C, D) and ros.json (D), as one initial commit on main.
build_repo() {
  local dir="$1" who="$2"
  cp -r "$FIX2/repo" "$dir"
  [ -d "$FIX2/tasks/$TASK/start-overlay" ] && cp -r "$FIX2/tasks/$TASK/start-overlay/." "$dir/"
  mkdir -p "$dir/requirements"
  cp "$FIX2/tasks/$TASK/requirement.md" "$dir/requirements/$TASK.md"
  cp "$FIX2/tasks/$TASK/${TASK}AcceptanceTests.fs" "$dir/$VISIBLE"
  if is_echelon "$ARM"; then
    mkdir -p "$dir/.ros/work"
    jq -cn --arg id "$ITEM" --arg t "$TITLE" '{schemaVersion:"1.0.0",items:[{id:$id,title:$t,status:"captured"}]}' > "$dir/.ros/work/queue.json"
  fi
  [ "$ARM" = echelon-optimized ] && jq -n '{workProtocol:{requireAttestedEvidence:true}}' > "$dir/ros.json"
  ( cd "$dir" && git init -q -b main . && git config user.email "$who@rel002.invalid" && git config user.name "rel002 $who"
    git add -A && git commit -qm "fixture: REL-001 run-02 $TASK" )
}
# clone_workspace W NAME: a clone of the run's bare remote, with the agent's own git identity.
clone_workspace() {
  git clone -q "$RUN_DIR/remote.git" "$1/repo"
  git -C "$1/repo" config user.email "$2@rel002.invalid"; git -C "$1/repo" config user.name "rel002 $2"
}
if [ "$AGENTS" -eq 2 ]; then
  # U6 (R8): one bare remote, two clones, one brief each. The remote keeps a reflog of every ref
  # update so that pushed-then-overwritten work stays observable (lost work).
  build_repo "$HS/seed" seed
  git init -q --bare -b main "$RUN_DIR/remote.git"
  git -C "$RUN_DIR/remote.git" config core.logAllRefUpdates always
  git -C "$RUN_DIR/remote.git" config gc.auto 0
  git -C "$HS/seed" push -q "$RUN_DIR/remote.git" main 2>/dev/null
  { echo '#!/usr/bin/env bash'
    echo '# REL-001 run-02: records every ref update pushed to this remote (lost-work observable, R8).'
    echo 'while read -r old new ref; do'
    echo "  jq -cn --arg at \"\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\" --arg o \"\$old\" --arg n \"\$new\" --arg r \"\$ref\" '{at:\$at, old:\$o, new:\$n, ref:\$r}' >> \"$RUN_DIR/logs/remote-pushes.jsonl\""
    echo 'done'; } > "$RUN_DIR/remote.git/hooks/post-receive"
  chmod +x "$RUN_DIR/remote.git/hooks/post-receive"
  WS_JSON=$(jq -cn --arg r "$RUN_DIR" '[{name:"agent-1", dir:($r+"/agent-1")}, {name:"agent-2", dir:($r+"/agent-2")}]')
  for n in agent-1 agent-2; do mkdir -p "$RUN_DIR/$n"; clone_workspace "$RUN_DIR/$n" "$n"; done
else
  WS_JSON=$(jq -cn --arg r "$RUN_DIR" '[{name:"agent-1", dir:$r}]')
  build_repo "$RUN_DIR/repo" agent
fi
INITIAL=$(git -C "$(jq -r '.[0].dir' <<<"$WS_JSON")/repo" rev-parse HEAD)

# --- host-owned contract and authority (C, D). Ordo's verdict is recorded, never enforced here (R7).
ORDO_RC=null; ORDO_DIGEST=""; PRAXIS_CHECK_RC=null; CONTRACT_DIGEST=""; VERIFIER='null'
if is_echelon "$ARM"; then
  cp "$FIX2/tasks/$TASK/contract.json" "$HI/contract.json"
  set +e
  "$ORDO" ecir check --blueprint "$HI/contract.json" --json > "$HS/setup-ordo-check.json" 2> "$HS/setup-ordo-check.err"; ORDO_RC=$?
  "$RUN_DIR/tools/praxis/praxis" ordo contract check --contract "$HI/contract.json" > "$HS/setup-praxis-check.txt" 2>&1; PRAXIS_CHECK_RC=$?
  set -e
  ORDO_DIGEST=$(jq -r '.contractDigest // empty' "$HS/setup-ordo-check.json" 2>/dev/null || true)
  # The receipt binds a contract digest. A refused contract has no Ordo digest, so the verifier binds
  # the file's sha256 instead; completion then fails closed at admission with the Ordo codes.
  CONTRACT_DIGEST="${ORDO_DIGEST:-sha256:$(sha "$HI/contract.json")}"
  write_authority "$HI/authority.json" "$(contract_decisions "$HI/contract.json")"   # run-01 amendment A2
  if [ "$ARM" = echelon-optimized ]; then
    jq -n --arg task "$TASK" --arg dn "$HD/bin/dotnet" --arg p "$VISIBLE" --arg s "$(sha "$FIX2/tasks/$TASK/${TASK}AcceptanceTests.fs")" '
      {schemaVersion:"echelon.validation-policy/1", policyId:("rel002-" + $task),
       validations:[{name:"unit-tests", evidenceId:"EV-TESTS", command:[$dn,"test","Ledger.slnx"], timeoutSeconds:900}],
       protectedPaths:[{path:$p, sha256:$s}]}' > "$HI/policy.json"
    # The verifier daemon: key generated at start-up and held only in memory; socket outside every workspace.
    ( unset PRAXIS_ACTOR PRAXIS_ACTOR_KIND PRAXIS_VERIFIER_SOCKET PRAXIS_COMPLETION_AUTHORITY PRAXIS_ORDO_CONTRACT
      export REL002_DOTNET_SOURCE=verifier
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

# --- directives (B, C, D): identical bytes for every arm that gets them (R10, R11)
DIRECTIVES_SHA=$(sha "$DIRECTIVES")

# --- per-workspace env.sh, DIRECTIVES.md and AGENT_BRIEF.md
REQ_ARGS=""
if is_echelon "$ARM"; then
  REQ_ARGS=$( { jq -r '.requirements[].source.key | "--requirement " + .' "$HI/contract.json"; jq -r '.nodes[] | select(.kind=="decision") | "--decision " + .id' "$HI/contract.json"; } | paste -sd' ')
fi
STORE=""; [ "$AGENTS" -eq 2 ] && STORE=" --store git --remote origin"
BRIEFS='[]'
for n in $(jq -r '.[].name' <<<"$WS_JSON"); do
  W=$(jq -r --arg n "$n" '.[] | select(.name==$n) | .dir' <<<"$WS_JSON"); REPO="$W/repo"
  TOKEN="tok-$RUN_ID"; [ "$AGENTS" -eq 2 ] && TOKEN="tok-$RUN_ID-$n"
  {
    echo "# source this file before starting the agent session (REL-001 run-02 $RUN_ID, $n)"
    echo "export PATH=\"$RUN_DIR/tools/bin:/root/.dotnet:\$PATH\" DOTNET_ROOT=/root/.dotnet DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1"
    echo "export REL002_AGENT=$n"
    if is_echelon "$ARM"; then
      echo "export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=rel002/$RUN_ID/$n PRAXIS_TELEMETRY_PROVIDER=$MODEL_PROVIDER PRAXIS_TELEMETRY_RUNTIME=claude-code"
      echo "export PRAXIS_DOKIMOS_EXECUTABLE=\"$RUN_DIR/tools/dokimos/dokimos\""
    fi
    if [ "$ARM" = echelon-optimized ]; then
      echo "export PRAXIS_VERIFIER_SOCKET=\"$HD/verifier.sock\" PRAXIS_COMPLETION_AUTHORITY=\"$HI/authority.json\" PRAXIS_ORDO_CONTRACT=\"$HI/contract.json\""
    fi
    echo "cd \"$REPO\""
  } > "$W/env.sh"
  has_directives "$ARM" && cp "$DIRECTIVES" "$W/DIRECTIVES.md"
  TEMPLATES=("$H2/briefs/core.md")
  [ "$AGENTS" -eq 2 ] && TEMPLATES+=("$H2/briefs/shared-remote.md")
  has_directives "$ARM" && TEMPLATES+=("$H2/briefs/directives.md")
  [ "$ARM" = echelon-original ] && TEMPLATES+=("$H2/briefs/workflow-c.md")
  [ "$ARM" = echelon-optimized ] && TEMPLATES+=("$H2/briefs/workflow-d.md")
  TEMPLATES+=("$H2/briefs/outcome.md")
  ATTEMPTS=""; is_echelon "$ARM" && ATTEMPTS="- At most 3 completion attempts (each \`praxis work complete-verified\` invocation counts)."
  LOCAL_CLAIM=""
  [ "$ARM" = echelon-optimized ] && [ "$AGENTS" -eq 2 ] && LOCAL_CLAIM="   Once that claim is yours, claim the item in your local store too, with the same token
   (\`praxis work verify\` and the host verifier read the local claim store):
   \`praxis work claim --id $ITEM --token $TOKEN --lease-seconds 3600\`
"
  jq -n --arg REPO "$REPO" --arg ENV "$W/env.sh" --arg ITEM "$ITEM" --arg TASK "$TASK" --arg WORKSPACE "$W" \
    --arg ATTEMPTS_LINE "$ATTEMPTS" --arg DIRECTIVES "$W/DIRECTIVES.md" --arg CONTRACT "$HI/contract.json" \
    --arg AUTHORITY "$HI/authority.json" --arg TOKEN "$TOKEN" --arg STORE "$STORE" --arg REQ_ARGS "$REQ_ARGS" \
    --arg D_LOCAL_CLAIM "$LOCAL_CLAIM" '$ARGS.named' > "$HS/brief-values-$n.json"
  python3 -I "$H2/render-brief.py" "$HS/brief-values-$n.json" "${TEMPLATES[@]}" > "$W/AGENT_BRIEF.md"
  BRIEFS=$(jq -c --arg n "$n" --arg w "$W" --arg r "$REPO" --arg b "$W/AGENT_BRIEF.md" --arg bs "$(sha "$W/AGENT_BRIEF.md")" --arg t "$TOKEN" \
    --argjson tpl "$(printf '%s\n' "${TEMPLATES[@]}" | xargs -n1 basename | jq -R . | jq -sc .)" \
    '. + [{name:$n, dir:$w, repo:$r, brief:$b, briefSha256:$bs, token:$t, templates:$tpl}]' <<<"$BRIEFS")
done

# --- host-file digests (X6): host inputs, the verifier, the agents' tool copies, price table, directives
DIGESTS=$(
  { [ -d "$HI" ] && find "$HI" -type f
    [ -d "$HD/bin" ] && echo "$HD/bin"
    [ -d "$RUN_DIR/tools/praxis" ] && echo "$RUN_DIR/tools/praxis"
    [ -d "$RUN_DIR/tools/dokimos" ] && echo "$RUN_DIR/tools/dokimos"
    echo "$PRICE_TABLE"
    has_directives "$ARM" && jq -r '.[].dir + "/DIRECTIVES.md"' <<<"$WS_JSON"
    true; } | LC_ALL=C sort | while read -r p; do
      if [ -d "$p" ]; then printf '%s\t%s\n' "$p" "$(tree_sha "$p")"; else printf '%s\t%s\n' "$p" "$(sha "$p")"; fi
    done | jq -Rn '[inputs | split("\t") | {key:.[0], value:.[1]}] | from_entries')
echo "$DIGESTS" > "$HS/host-digests.json"

# --- run.json (harness state only)
REPLICATE=$(sed -nE 's/.*-r([0-9]+)-.*/\1/p' <<<"$RUN_ID"); REPLICATE=${REPLICATE:-1}
LABEL=trial; [[ "$RUN_ID" == *-PILOT-* ]] && LABEL=pilot; [[ "$RUN_ID" == *-SMOKE-* ]] && LABEL=smoke
fixture_digest=$(cd "$FIX2" && find repo tasks oracle reference -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)
oracle_digest=$(cd "$FIX2" && find oracle -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)
jq -n --arg run "$RUN_ID" --arg arm "$ARM" --arg letter "$LETTER" --arg task "$TASK" --arg item "$ITEM" --arg cat "$CATEGORY" \
  --arg at "$(utc)" --arg init "$INITIAL" --argjson agents "$AGENTS" --argjson rep "$REPLICATE" --arg label "$LABEL" \
  --arg acc "$(sha "$FIX2/tasks/$TASK/requirement.md")" --arg vis "$(sha "$FIX2/tasks/$TASK/${TASK}AcceptanceTests.fs")" --arg visp "$VISIBLE" \
  --arg fx "$fixture_digest" --arg ox "$oracle_digest" --arg cbe "$(git -C "$CBE" rev-parse HEAD)" --arg dn "$(dotnet --version)" \
  --argjson ws "$BRIEFS" --arg runDir "$RUN_DIR" --arg hd "$HD" --arg hs "$HS" \
  --argjson reqs "$(jq -c .requirementIds "$FIX2/tasks/$TASK/task.json")" --argjson keys "$(jq -c .requirementKeys "$FIX2/tasks/$TASK/task.json")" \
  --argjson decs "$(jq -c .decisionIds "$FIX2/tasks/$TASK/task.json")" --argjson exp "$(jq -c .expectedOutcome "$FIX2/tasks/$TASK/task.json")" \
  --arg pv "$PRAXIS_VER" --arg dv "$DOKIMOS_VER" --arg ov "$(is_echelon "$ARM" && tool_version "$ORDO" || true)" \
  --arg ps "$( [ -n "$PX_FILE" ] && sha "$PX_FILE" || true)" --arg ds "$( [ -n "$DK_FILE" ] && sha "$DK_FILE" || true)" \
  --arg vs "$( [ -n "$VX_FILE" ] && sha "$VX_FILE" || true)" --arg os "$(is_echelon "$ARM" && sha "$ORDO" || true)" \
  --arg pxsrc "$( is_echelon "$ARM" && echo "$PX_SRC" || true)" --arg dksrc "$( is_echelon "$ARM" && echo "$DK_SRC" || true)" \
  --arg dirs "$DIRECTIVES_SHA" --argjson ordoRc "$ORDO_RC" --arg ordoDigest "$ORDO_DIGEST" --argjson pxRc "$PRAXIS_CHECK_RC" \
  --arg cdig "$CONTRACT_DIGEST" --arg csha "$(sha "$FIX2/tasks/$TASK/contract.json")" --argjson verifier "$VERIFIER" \
  --arg mp "$MODEL_PROVIDER" --arg mm "$MODEL" --arg mc "$(sha "$AGENT_CONFIG")" --arg mpath "$AGENT_CONFIG" \
  --arg pt "$PRICE_TABLE" --arg pts "$(sha "$PRICE_TABLE")" --arg mx "$MEASURE_PRAXIS" --arg mxs "$(sha "$MEASURE_PRAXIS")" '
  def nn: if . == "" then null else . end;
  {schema:"cbe.rel-001.run-02-run/1", runId:$run, arm:$arm, armLetter:$letter, task:$task, workItem:$item, category:$cat,
   categoryBasis:"builder-assigned (unvalidated)", label:$label, replicate:$rep, block:($task + "-r" + ($rep|tostring)),
   createdAt:$at, initialCommit:$init, agents:$agents, requirementIds:$reqs, requirementKeys:$keys, decisionIds:$decs,
   expectedOutcome:$exp, acceptanceCriteriaDigest:$acc, visibleTests:{path:$visp, sha256:$vis},
   fixtureDigest:$fx, oracleDigest:$ox, cohortBasedEngineeringCommit:$cbe,
   paths:{runDir:$runDir, host:$hd, state:$hs, remote:(if $agents == 2 then ($runDir + "/remote.git") else null end)},
   workspaces:$ws,
   directives:(if $letter == "A" then null else {sha256:$dirs} end),
   tools:({dotnet:$dn} + (if $pv == "" then {} else {praxis:$pv, dokimos:$dv, ordo:($ov|nn)} end)),
   binaries:(if $ps == "" then {} else {praxis:{source:$pxsrc, sha256:$ps}, dokimos:{source:$dksrc, sha256:$ds}, ordo:{sha256:$os}}
             + (if $vs == "" then {} else {verifier:{sha256:$vs}} end) end),
   contract:(if $pv == "" then null else {sha256:$csha, ordoExit:$ordoRc, ordoAdmits:($ordoRc == 0), ordoContractDigest:($ordoDigest|nn),
             praxisCheckExit:$pxRc, boundDigest:$cdig} end),
   verifier:$verifier,
   enforcement:{ordoContracts:($pv != ""), praxisOwnership:($pv != ""), dokimosVerification:($pv != ""), attestedEvidence:($letter == "D")},
   measurement:{praxis:$mx, sha256:$mxs, priceTable:$pt, priceTableSha256:$pts},
   model:{provider:$mp, configuredModel:$mm, configuration:$mpath, configurationDigest:$mc}}' > "$HS/run.json"
echo "$RUN_DIR"
