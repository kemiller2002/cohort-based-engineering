#!/usr/bin/env bash
# REL-001 Experiment D workspace setup. usage: harness/d/setup.sh baseline|treatment T1|T2|T3 RUNID
# Creates $RUNS/RUNID (default /tmp/claude-0/rel001/runs/RUNID):
#   repo/            fixture repository (git init + one commit), work queue with LEDGER-Tn
#   tools/bin/       praxis and dotnet shims that log every invocation to logs/
#   env.sh           environment the agent session must source (PATH, actor, Dokimos)
#   AGENT_BRIEF.md   arm-specific workflow instructions; identical task text and limits
#   run.json         pins: arm, task, binaries' sha256, fixture/acceptance digests, initial commit
# Hidden oracle tests (fixtures/d/oracle) and the reference solution are never copied.
# Optional model identity for the observation: REL001_MODEL_PROVIDER, REL001_MODEL, REL001_MODEL_CONFIG (file).
source "$(dirname "$0")/../lib.sh"
[ $# -eq 3 ] || { echo "usage: $0 baseline|treatment T1|T2|T3 RUNID" >&2; exit 2; }
ARM_ARG="$1"; TASK="$2"; RUN_ID="$3"
case "$TASK" in T1|T2|T3) ;; *) echo "unknown task $TASK" >&2; exit 2 ;; esac
[[ "$RUN_ID" =~ ^REL-001-[A-Za-z0-9-]+$ ]] || { echo "RUNID must match ^REL-001-[A-Za-z0-9-]+$" >&2; exit 2; }
for v in REL001_MODEL_PROVIDER REL001_MODEL REL001_MODEL_CONFIG; do
  [ -n "${!v:-}" ] || { echo "set $v (model identity is pinned per run; REL001_MODEL_CONFIG is a file whose sha256 is the configuration digest)" >&2; exit 2; }
done
[ -f "$REL001_MODEL_CONFIG" ] || { echo "REL001_MODEL_CONFIG is not a file" >&2; exit 2; }
arm_init "$ARM_ARG"
FIX="$REL/fixtures/d"; RUN_DIR="$RUNS/$RUN_ID"; REPO="$RUN_DIR/repo"
[ -e "$RUN_DIR" ] && { echo "run directory exists: $RUN_DIR (every run needs a fresh runId)" >&2; exit 2; }
ITEM="LEDGER-$TASK"
mkdir -p "$RUN_DIR"/{tools/bin,logs,inputs}

# --- tools: a private copy of the arm's Praxis (+ Dokimos for treatment) and logging shims
cp -r "$(dirname "$PRAXIS")" "$RUN_DIR/tools/praxis"
if [ "$ARM" = treatment ]; then mkdir -p "$RUN_DIR/tools/dokimos"; cp "$DOKIMOS" "$RUN_DIR/tools/dokimos/dokimos"; fi
REAL_DOTNET="$(command -v dotnet)"
cat > "$RUN_DIR/tools/bin/praxis" <<EOF
#!/usr/bin/env bash
# REL-001 shim: records each invocation (argv, exit, timing) to logs/praxis.jsonl, then runs the pinned Praxis.
start=\$(date +%s%3N); set +e; "$RUN_DIR/tools/praxis/praxis" "\$@"; rc=\$?
jq -cn --arg at "\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" --argjson ms \$(( \$(date +%s%3N) - start )) --argjson rc \$rc '\$ARGS.positional as \$a | {at:\$at, ms:\$ms, exit:\$rc, argv:\$a}' --args -- "\$@" >> "$RUN_DIR/logs/praxis.jsonl"
exit \$rc
EOF
cat > "$RUN_DIR/tools/bin/dotnet" <<EOF
#!/usr/bin/env bash
# REL-001 shim: records each dotnet invocation to logs/dotnet.jsonl (test runs are counted from it).
start=\$(date +%s%3N); set +e; "$REAL_DOTNET" "\$@"; rc=\$?
jq -cn --arg at "\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" --argjson ms \$(( \$(date +%s%3N) - start )) --argjson rc \$rc '\$ARGS.positional as \$a | {at:\$at, ms:\$ms, exit:\$rc, argv:\$a}' --args -- "\$@" >> "$RUN_DIR/logs/dotnet.jsonl"
exit \$rc
EOF
chmod +x "$RUN_DIR/tools/bin/praxis" "$RUN_DIR/tools/bin/dotnet"
{
  echo "# source this file before starting the agent session (REL-001 $RUN_ID)"
  echo "export PATH=\"$RUN_DIR/tools/bin:/root/.dotnet:\$PATH\" DOTNET_ROOT=/root/.dotnet DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1"
  echo "export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=rel001/$RUN_ID PRAXIS_TELEMETRY_PROVIDER=\${REL001_MODEL_PROVIDER:-unknown} PRAXIS_TELEMETRY_RUNTIME=\${REL001_RUNTIME:-unknown}"
  [ "$ARM" = treatment ] && echo "export PRAXIS_DOKIMOS_EXECUTABLE=\"$RUN_DIR/tools/dokimos/dokimos\""
  echo "cd \"$REPO\""
} > "$RUN_DIR/env.sh"

# --- repository
cp -r "$FIX/repo" "$REPO"
mkdir -p "$REPO/requirements"
cp "$FIX/tasks/$TASK/requirement.md" "$REPO/requirements/$TASK.md"
cp "$FIX/tasks/$TASK/starter-tests.fs" "$REPO/tests/Ledger.Tests/${TASK}StarterTests.fs"
if [ "$ARM" = treatment ]; then
  cp "$FIX/tasks/$TASK/contract.json" "$REPO/contract.json"
  write_authority "$REPO/authority.json"
  # The contract must be admitted by Ordo AND Praxis before the run is usable.
  "$SDE" ecir check --blueprint "$REPO/contract.json" --json > "$RUN_DIR/logs/setup-ordo-check.json" || { echo "Ordo refused the contract" >&2; exit 3; }
  "$PRAXIS" ordo contract check --contract "$REPO/contract.json" > "$RUN_DIR/logs/setup-praxis-check.txt" 2>&1 || { echo "Praxis refused the contract" >&2; exit 3; }
fi
mkdir -p "$REPO/.ros/work"
jq -cn --arg id "$ITEM" --arg t "$(head -1 "$FIX/tasks/$TASK/requirement.md" | sed 's/^# //')" '{schemaVersion:"1.0.0",items:[{id:$id,title:$t,status:"captured"}]}' > "$REPO/.ros/work/queue.json"
( cd "$REPO"
  git init -q -b main . && git config user.email agent@rel001.invalid && git config user.name "rel001 agent"
  git add -A && git commit -qm "fixture: REL-001 D $TASK ($ARM)" )
if [ "$ARM" = baseline ]; then
  ( cd "$REPO" && "$PRAXIS" work backlog-transition --id "$ITEM" --action ready --occurred-at "$(utc)" > /dev/null
    git add -A && git commit -qm "work: $ITEM ready" )
fi
INITIAL=$(git -C "$REPO" rev-parse HEAD)

# --- brief
KEYS=$(jq -r '.requirements[].source.key' "$FIX/tasks/$TASK/contract.json")
REQ_ARGS=$(printf '%s\n' $KEYS | sed 's/^/--requirement /' | paste -sd' ')
{
cat <<EOF
# Agent brief: $RUN_ID

You are working in \`$REPO\` (a git repository). Before anything else run
\`source $RUN_DIR/env.sh\` in your shell; it puts \`praxis\` and \`dotnet\` on PATH.

## Task

Work item **$ITEM**. The requirement and its acceptance criteria are in
\`requirements/$TASK.md\`. Implement it in \`src/Ledger\` and add or extend tests in
\`tests/Ledger.Tests\`. A starter test, \`tests/Ledger.Tests/${TASK}StarterTests.fs\`, is
provided; it fails until the work is done.

## Limits (identical for every run)

- Time budget: 45 minutes of wall-clock time from your first command.
- At most 3 completion attempts (each \`praxis work complete...\` invocation counts).
- Use only this run directory. No network access, no package installs beyond the
  restore of the packages already referenced. Do not read anything outside \`$RUN_DIR\`.
- Commit your work with git; the final commit is what is evaluated.
- When you stop (done, budget exhausted, or giving up), say so in one line.

## Workflow
EOF
if [ "$ARM" = baseline ]; then cat <<EOF

1. Start the work item:
   \`praxis work start --id $ITEM --occurred-at \$(date -u +%Y-%m-%dT%H:%M:%SZ)\`
2. Implement the requirement and its tests.
3. Run the tests and keep the output: \`dotnet test Ledger.slnx 2>&1 | tee test-output.txt\`
4. Commit: \`git add -A && git commit -m "$ITEM: ..."\`
5. Complete the work item:
   \`praxis work complete --id $ITEM --occurred-at \$(date -u +%Y-%m-%dT%H:%M:%SZ) --evidence implementation=src/Ledger/Ledger.fs --evidence tests=test-output.txt\`
   If it is refused, read the message, fix the cause and retry (within the attempt limit).
EOF
else cat <<EOF

The treatment contract for this task is \`contract.json\` (Ordo \`ecir/1\`); the
completion authority is \`authority.json\`. Both are committed; do not edit them.

1. Claim the work item (keep the token; the lease covers the time budget):
   \`praxis work claim --id $ITEM --token tok-$RUN_ID --lease-seconds 3600\`
   Note the \`generation\` in the output (1 for a fresh claim).
2. Implement the requirement and its tests.
3. Commit: \`git add -A && git commit -m "$ITEM: ..."\` (validate-run refuses a dirty worktree).
4. Run the tests through Praxis so the result is recorded as evidence:
   \`praxis work validate-run --id $ITEM --token tok-$RUN_ID --generation 1 --validation unit-tests --evidence-id EV-TESTS -- dotnet test Ledger.slnx\`
   Note \`resultPath\` in the output.
5. Complete with independent verification:
   \`praxis work complete-verified --id $ITEM --token tok-$RUN_ID --generation 1 --commit \$(git rev-parse HEAD) --verification-revision \$(git rev-parse HEAD) --authority authority.json --ordo-contract contract.json $REQ_ARGS --validation unit-tests=passed:EV-TESTS --evidence EV-TESTS=RESULT_PATH\`
   If it is refused, read the codes, fix the cause, commit, re-run step 4 and retry
   (within the attempt limit).
EOF
fi
} > "$RUN_DIR/AGENT_BRIEF.md"

# --- pins
fixture_digest=$(cd "$FIX" && find repo tasks -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)
oracle_digest=$(cd "$FIX" && find oracle -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)
model_cfg_digest="\"$(sha256sum "$REL001_MODEL_CONFIG" | cut -d' ' -f1)\""
jq -n --arg run "$RUN_ID" --arg arm "$ARM" --arg task "$TASK" --arg item "$ITEM" --arg at "$(utc)" --arg init "$INITIAL" \
  --arg acc "$(sha256sum "$FIX/tasks/$TASK/requirement.md" | cut -d' ' -f1)" --arg fx "$fixture_digest" --arg ox "$oracle_digest" \
  --arg pv "$PRAXIS_VERSION" --arg ps "$PRAXIS_SHA" --arg ds "$DOKIMOS_SHA" --arg ss "$SDE_SHA" --arg oc "$ORDO_COMMIT" \
  --arg cbe "$(git -C "$REL" rev-parse HEAD)" --arg dn "$(dotnet --version)" \
  --arg mp "${REL001_MODEL_PROVIDER:-}" --arg mm "${REL001_MODEL:-}" --argjson mc "$model_cfg_digest" \
  --argjson reqs "$(jq -c '[.requirements[].source.originalId]' "$FIX/tasks/$TASK/contract.json")" \
  --arg cx "$(case $TASK in T1) echo low;; *) echo medium;; esac)" '
  {schema:"cbe.rel-001.d-run/1", runId:$run, arm:$arm, task:$task, workItem:$item, createdAt:$at, initialCommit:$init,
   requirementIds:$reqs, complexity:$cx, acceptanceCriteriaDigest:$acc, fixtureDigest:$fx, oracleDigest:$ox,
   cohortBasedEngineeringCommit:$cbe,
   tools:({praxis:$pv, dotnet:$dn} + (if $arm=="treatment" then {dokimos:"0.6.0", ordo:$oc} else {} end)),
   binaries:({praxis:$ps} + (if $arm=="treatment" then {dokimos:$ds, ordoSdeDll:$ss} else {} end)),
   enforcement:{ordoContracts:($arm=="treatment"), praxisOwnership:($arm=="treatment"), dokimosVerification:($arm=="treatment")},
   model:{provider:(if $mp=="" then null else $mp end), configuredModel:(if $mm=="" then null else $mm end), configurationDigest:$mc}}' > "$RUN_DIR/run.json"
echo "$RUN_DIR"
