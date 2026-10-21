#!/usr/bin/env bash
# ARCH-001 trial driver (adapted from REL-001 run-03 harness/trial.sh; two phases per trial; see PROVENANCE.md).
#   trial.sh run RUNID           the whole trial: setup -> phase 1 -> transition -> phase 2 -> score (resumable: a
#                                trial with state/done is skipped; one process per trial holds RUN/.lock)
#   trial.sh setup RUNID         setup.sh; failure = X1 (state stays for diagnosis; rerun with a fresh run id)
#   trial.sh phase RUNID K       render the phase-K brief, integrity snapshot, run $ARCH001_AGENT_CMD RUNID K,
#                                integrity re-hash, contamination scan
#   trial.sh transition RUNID    workspace -> last phase-1 submitted commit (or HEAD), follow-up material committed
#   trial.sh score RUNID         score.sh (oracle, archcheck, diffs, tokens) -> observation
# The agent runner gets RUNID and K; launch-agent.sh is K1; smoke-agent.sh is the no-model stand-in.
source "$(dirname "$0")/lib.sh"

ordinal() { case "$1" in 1) echo first;; 2) echo second;; 3) echo third;; *) echo "${1}th";; esac; }
set_run() { jq "$1" "$ST/run.json" > "$ST/run.json.tmp" && mv "$ST/run.json.tmp" "$ST/run.json"; }
last_submitted() {  # PHASE -> gitHead of the last PASS/FAIL submit in that phase, or empty
  [ -f "$LEDGER" ] || return 0
  jq -rs --argjson p "$1" '[.[] | select(.phase == $p and (.verdict == "PASS" or .verdict == "FAIL")) | .gitHead][-1] // empty' "$LEDGER"
}

render_brief() {  # PHASE -> brief path
  local k="$1" arm task cf line
  arm=$(jq -r .arm "$ST/run.json"); task=$(jq -r .task "$ST/run.json")
  if [ "$k" = 1 ]; then cf="$task.contract.json"; line="Implement the requirement in \`requirements/$task.md\`."
  else cf="$task-followup.contract.json"
       line="This repository already contains earlier work, submitted for \`requirements/$task.md\`; keep it working. Implement the follow-up requirement in \`requirements/$task-followup.md\`."; fi
  local tpl=("$H/briefs/core.md")
  has_pack "$arm" && tpl+=("$H/briefs/arm-b-architecture.md")
  has_contract "$arm" && tpl+=("$H/briefs/arm-c-contract.md")
  has_verifier "$arm" && tpl+=("$H/briefs/arm-d-verifier.md")
  jq -n --arg REPO "$REPO" --arg TOOLS "$TOOLS" --arg TASK_LINE "$line" --arg MAX_SUBMITS "$MAX_SUBMITS" \
    --arg MAX_SUBMITS_ORDINAL "$(ordinal "$MAX_SUBMITS")" --arg BUDGET_MINUTES "$BUDGET_MINUTES" --arg CONTRACT_FILE "$cf" \
    --arg POLICY "$TOOLS/policy/lending.policy.json" '$ARGS.named' > "$ST/brief-values-phase$k.json"
  local out="$BRIEFS/AGENT_BRIEF-phase$k.md"
  python3 -I "$H/render-brief.py" "$ST/brief-values-phase$k.json" "${tpl[@]}" > "$out"
  local tj; tj=$(for t in "${tpl[@]}"; do jq -n --arg n "${t#"$H"/}" --arg s "$(sha "$t")" '{template:$n, sha256:$s}'; done | jq -sc .)
  set_run ".phases[\"$k\"].brief = {path:\"$out\", sha256:\"$(sha "$out")\", templates:$tj, valuesSha256:\"$(sha "$ST/brief-values-phase$k.json")\"}"
  echo "$out"
}

phase() {
  local k="$1" P="$ST/phase$1" rc
  mkdir -p "$P"; echo "$k" > "$ST/current-phase"
  render_brief "$k" > /dev/null
  if [ -n "${ARCH001_BRIEF_OVERRIDE:-}" ]; then   # smoke-live.sh only: a trivial brief instead of the task brief
    [ "$(label_of "$RUN_ID")" = smoke ] || { echo "ARCH001_BRIEF_OVERRIDE is for -SMOKE- runs only" >&2; return 2; }
    cp "$ARCH001_BRIEF_OVERRIDE" "$BRIEFS/AGENT_BRIEF-phase$k.md"
    set_run ".phases[\"$k\"].brief.sha256 = \"$(sha "$BRIEFS/AGENT_BRIEF-phase$k.md")\" | .phases[\"$k\"].brief.override = true"
  fi
  set_run ".phases[\"$k\"].startCommit = \"$(git -C "$REPO" rev-parse HEAD)\" | .phases[\"$k\"].startedAt = \"$(utc)\""
  python3 -I "$H/integrity.py" snapshot "$ST/run.json" > "$P/integrity-before.json"
  set +e; bash "$AGENT_CMD" "$RUN_ID" "$k" > "$P/agent-runner.out" 2> "$P/agent-runner.err"; rc=$?; set -e
  echo 0 > "$ST/current-phase"
  python3 -I "$H/integrity.py" snapshot "$ST/run.json" > "$P/integrity-after.json"
  python3 -I "$H/integrity.py" compare "$P/integrity-before.json" "$P/integrity-after.json" > "$P/integrity.json"
  ARCH001_SEALED_DIR="$SEALED" ARCH001_VERIFIER_SRC="$VERIFIER_SRC_DIR" python3 -I "$H/scan.py" "$ST/run.json" "$k" > "$P/contamination.json"
  set_run ".phases[\"$k\"] += {endedAt:\"$(utc)\", runnerExit:$rc, timedOut:($rc == 124), endHead:\"$(git -C "$REPO" rev-parse HEAD)\",
           lastSubmitted:(\"$(last_submitted "$k")\" | if . == \"\" then null else . end)}"
  return 0
}

transition() {
  local task arm commit
  task=$(jq -r .task "$ST/run.json"); arm=$(jq -r .arm "$ST/run.json")
  commit=$(last_submitted 1); [ -n "$commit" ] || commit=$(git -C "$REPO" rev-parse HEAD)
  local TD="$FIX/tasks/$task"
  ( cd "$REPO" && git checkout -q -f -B main "$commit" && git clean -q -fdx )
  cp "$TD/followup.md" "$REPO/requirements/$task-followup.md"
  mkdir -p "$REPO/tests/Lending.Tests/Acceptance"
  if [ -d "$TD/followup-acceptance" ]; then cp "$TD"/followup-acceptance/*.fs "$REPO/tests/Lending.Tests/Acceptance/"; fi
  if has_contract "$arm"; then mkdir -p "$REPO/docs/contracts"; cp "$TD/followup-contract.json" "$REPO/docs/contracts/$task-followup.contract.json"; fi
  ( cd "$REPO" && git add -A && hgit commit -qm "Follow-up requirement" )
  set_run ".phase1Commit = \"$commit\" | .followupCommit = \"$(git -C "$REPO" rev-parse HEAD)\""
}

case "${1:?usage: trial.sh run|setup|phase|transition|score RUNID ...}" in
  setup)
    run_paths "${2:?RUNID}"
    mkdir -p "$RUNS"
    if ! bash "$H/setup.sh" "$RUN_ID" > "$RUNS/.setup-$RUN_ID.log" 2>&1; then
      mkdir -p "$ST"; cp "$RUNS/.setup-$RUN_ID.log" "$ST/setup.log" 2>/dev/null || true
      jq -n --arg at "$(utc)" --arg log "$ST/setup.log" '{exclusion:"X1", reason:"setup failed before agent start", at:$at, log:$log}' > "$ST/x1.json"
      echo "X1 setup failure for $RUN_ID (see $ST/setup.log); rerun with a fresh run id" >&2; exit 3
    fi
    mv "$RUNS/.setup-$RUN_ID.log" "$ST/setup.log"
    ;;
  phase) run_paths "${2:?RUNID}"; phase "${3:?K}" ;;
  transition) run_paths "${2:?RUNID}"; transition ;;
  score) run_paths "${2:?RUNID}"; bash "$H/score.sh" "$RUN_ID" ;;
  run)
    run_paths "${2:?RUNID}"; mkdir -p "$RUNS"
    [ -f "$ST/done" ] && { echo "skip $RUN_ID (done)"; exit 0; }
    [ -f "$ST/x1.json" ] && { echo "skip $RUN_ID (X1; rerun with a fresh run id)"; exit 0; }
    exec 9>"$RUNS/.lock-$RUN_ID"; flock -n 9 || { echo "skip $RUN_ID (another process holds it)"; exit 0; }
    [ -d "$ST" ] && [ ! -f "$ST/run.json" ] && { echo "skip $RUN_ID (incomplete setup; rerun with a fresh run id)"; exit 0; }
    if [ ! -f "$ST/run.json" ]; then bash "$0" setup "$RUN_ID" || exit 3; fi
    for k in 1 2; do   # a phase that started but never finished is never re-run on the used workspace
      if [ -f "$ST/phase$k/integrity-before.json" ] && [ ! -f "$ST/phase$k/integrity.json" ]; then
        jq -n --arg at "$(utc)" --argjson k "$k" '{reason:"phase interrupted (harness or host failure after agent start)", phase:$k, at:$at}' > "$ST/interrupted.json"
        echo "skip $RUN_ID (phase $k was interrupted; see $ST/interrupted.json)"; exit 0
      fi
    done
    [ -f "$ST/phase1/integrity.json" ] || phase 1
    [ -n "$(jq -r '.followupCommit // empty' "$ST/run.json")" ] || transition
    [ -f "$ST/phase2/integrity.json" ] || phase 2
    bash "$H/score.sh" "$RUN_ID"
    date -u +%Y-%m-%dT%H:%M:%SZ > "$ST/done"
    ;;
  *) echo "usage: trial.sh run|setup|phase|transition|score RUNID ..." >&2; exit 2 ;;
esac
