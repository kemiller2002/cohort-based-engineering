#!/usr/bin/env bash
# ARCH-002 trial setup (adapted from ARCH-001 harness/setup.sh; see ../PROVENANCE.md).
#   usage: harness/setup.sh RUNID          (fixture, task, model, replicate and arm are read from the run id)
# Builds $ARCH002_RUNS/RUNID/ (outside every repository):
#   repo/     the agent workspace: fixtures/<fixture>/repo + requirements/T<n>.md + visible acceptance tests (base
#             commit, fixed date, identical in every arm and model), then the arm material as a second commit (B-D:
#             docs/architecture/ from the pack; C-D: docs/contracts/T<n>.contract.json). The follow-up is NOT copied.
#   tools/    workspace-external tools: bin/submit (all arms), bin/ordo (C, D), bin/archcheck + policy/ + contracts/ +
#             baseline/start.report.json (D). Every contract, policy, baseline and probe file the verifier reads is
#             outside the evaluated tree (ARCH-001 A1).
#   brief/    rendered briefs (one per phase, written when the phase starts)
#   state/    harness state: run.json, pristine copies used for gating and scoring, integrity snapshots, ledger
# Brownfield baseline (INTERFACES §3): archcheck evaluates the BASE commit (identical in every arm; the arm-material
# commit adds documents only) twice with the pristine policy:
#   state/pristine/baseline-gate.json     policy only (what submit and arm D's dev-time runs compare with);
#   state/pristine/baseline-scoring.json  policy + the sealed task probes (what scoring compares S1/S2 with).
# Both are cached per (fixture, task, base commit, policy, probes, verifier) under $ARCH002_RUNS/.baseline-cache/.
# Exit 0 = ready; anything else = X1 (harness failure before agent start; rerun with a fresh run id).
source "$(dirname "$0")/lib.sh"
[ $# -eq 1 ] || { echo "usage: $0 RUNID" >&2; exit 2; }
[[ "$1" =~ $RUNID_RE ]] || { echo "RUNID must match $RUNID_RE" >&2; exit 2; }
run_paths "$1"
ARM=$(arm_of "$RUN_ID"); TASK=$(task_of "$RUN_ID"); REP=$(rep_of "$RUN_ID"); LABEL=$(label_of "$RUN_ID")
MODEL_KEY=$(model_of "$RUN_ID"); MODEL=$(model_id "$MODEL_KEY"); fixture_paths "$(fixture_of "$RUN_ID")"
TD="$FIX/tasks/$TASK"; ORACLE_DIR="$SEALED/oracle/$TASK"; PROBES="$ORACLE_DIR/probes.json"
[ -e "$ROOT" ] && { echo "exists: $ROOT (every run needs a fresh run id)" >&2; exit 2; }
need() { [ -e "$1" ] || { echo "missing $2: $1" >&2; exit 2; }; }
[ -n "$MODEL" ] || { echo "no model id for '$MODEL_KEY' in $AGENT_CONFIG .models" >&2; exit 2; }
need "$FIX/repo" "fixture repository"; need "$TD/requirement.md" "requirement"; need "$TD/acceptance" "acceptance tests"
need "$TD/followup.md" "follow-up requirement"; need "$TD/task.json" "task.json"; need "$PRICE_TABLE" "price table"
need "$POLICY_SRC" "policy"; need "$ARCHCHECK_SRC" "archcheck"; need "$SEALED" "sealed store"
has_pack "$ARM" && need "$FIX/pack" "architecture pack"
if has_contract "$ARM"; then need "$TD/contract.json" "contract"; need "$TD/followup-contract.json" "follow-up contract"; need "$ORDO_SRC" "ordo"; fi
if [ "$LABEL" != smoke ] && jq -e '.standIn == true' "$TD/task.json" >/dev/null 2>&1; then echo "stand-in fixtures are for SMOKE runs only" >&2; exit 2; fi

# Fixture metadata (fixture.json; defaults are the Lending layout).
APP_NAME=$(fixture_field .appName Lending)
ACCEPTANCE_DIR=$(fixture_field .acceptanceDir tests/Lending.Tests/Acceptance)
DOCTRINE_FILE=$(fixture_field .pack.doctrine FOUR-TIER-ARCHITECTURE.md)
INSTANCE_FILE=$(fixture_field .pack.instance "$(echo "$APP_NAME" | tr '[:lower:]' '[:upper:]')-ARCHITECTURE.md")
POLICY_NAME="$FIXTURE.policy.json"

mkdir -p "$REPO" "$TOOLS/bin" "$TOOLS/lib" "$BRIEFS" "$PRISTINE"
# --- pristine harness-side copies (gating and scoring read only these)
cp "$TD/task.json" "$PRISTINE/task.json"; cp "$PRICE_TABLE" "$PRISTINE/price-table.json"; cp "$AGENT_CONFIG" "$PRISTINE/agent-config.json"
cp "$POLICY_SRC" "$PRISTINE/policy.json"
[ -f "$FIXTURE_JSON" ] && cp "$FIXTURE_JSON" "$PRISTINE/fixture.json"
[ -f "$TD/contract.json" ] && cp "$TD/contract.json" "$PRISTINE/$TASK.contract.json"
[ -f "$TD/followup-contract.json" ] && cp "$TD/followup-contract.json" "$PRISTINE/$TASK-followup.contract.json"

# --- visible tests: task.json .files.visibleTests[] {source, target} (relative to the fixture), else every
#     tasks/T<n>/acceptance/*.fs into the fixture's acceptanceDir
copy_visible() {  # KEY DIR
  if jq -e ".files.$1 | length > 0" "$TD/task.json" >/dev/null 2>&1; then
    jq -r ".files.$1[] | [.source, .target] | @tsv" "$TD/task.json" | while IFS=$'\t' read -r s t; do
      mkdir -p "$REPO/$(dirname "$t")"; cp "$FIX/$s" "$REPO/$t"; done
  elif [ -d "$TD/$2" ]; then mkdir -p "$REPO/$ACCEPTANCE_DIR"; cp "$TD/$2"/*.fs "$REPO/$ACCEPTANCE_DIR/"; fi
}

# --- repository: base commit (identical in every arm and model), then the arm material
cp -r "$FIX/repo/." "$REPO/"
mkdir -p "$REPO/requirements"
cp "$TD/requirement.md" "$REPO/requirements/$TASK.md"
copy_visible visibleTests acceptance
( cd "$REPO" && git init -q -b main . && git config user.email "agent@arch002.invalid" && git config user.name "agent" \
  && git config commit.gpgsign false && git add -A \
  && GIT_AUTHOR_DATE="$FIXED_DATE" GIT_COMMITTER_DATE="$FIXED_DATE" hgit commit -qm "Initial repository" )
BASE=$(git -C "$REPO" rev-parse HEAD)
if has_pack "$ARM"; then
  mkdir -p "$REPO/docs/architecture"; cp -r "$FIX/pack/." "$REPO/docs/architecture/"
  if has_contract "$ARM"; then mkdir -p "$REPO/docs/contracts"; cp "$TD/contract.json" "$REPO/docs/contracts/$TASK.contract.json"; fi
  ( cd "$REPO" && git add -A && GIT_AUTHOR_DATE="$FIXED_DATE" GIT_COMMITTER_DATE="$FIXED_DATE" hgit commit -qm "Project documents" )
fi
START=$(git -C "$REPO" rev-parse HEAD)

# --- brownfield baseline of the base commit (cached; identical for every arm and model of this fixture task)
export DOTNET_ROOT="$DOTNET_ROOT_DIR" NUGET_PACKAGES="$NUGET_CACHE" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 \
       MSBUILDDISABLENODEREUSE=1 DOTNET_CLI_USE_MSBUILD_SERVER=0 UseSharedCompilation=false
AC_DIGEST=$(any_sha "$(dirname "$ARCHCHECK_SRC")"); POL_SHA=$(sha "$POLICY_SRC"); PRB_SHA=$([ -f "$PROBES" ] && sha "$PROBES" || echo none)
BL_KEY=$(printf '%s\n' "$BASE" "$POL_SHA" "$PRB_SHA" "$AC_DIGEST" | sha256sum | cut -c1-16)
CACHE="$RUNS/.baseline-cache/$FIXTURE-$TASK-$BL_KEY"
mkdir -p "$RUNS/.baseline-cache"
(
  flock 8
  if [ ! -f "$CACHE/done" ]; then
    rm -rf "$CACHE"; mkdir -p "$CACHE"
    git clone -q --no-hardlinks "$REPO" "$CACHE/tree" && git -C "$CACHE/tree" checkout -q --detach "$BASE"
    AC=$(archcheck_cmd); extra=(); [ -f "$PROBES" ] && extra=(--probes "$PROBES")
    set +e
    ( cd "$CACHE/tree" && $AC verify --repo "$CACHE/tree" --policy "$PRISTINE/policy.json" --require-clean --json --out "$CACHE/gate.json" > "$CACHE/gate.txt" 2>&1 ); g=$?
    ( cd "$CACHE/tree" && $AC verify --repo "$CACHE/tree" --policy "$PRISTINE/policy.json" "${extra[@]}" --require-clean --json --out "$CACHE/scoring.json" > "$CACHE/scoring.txt" 2>&1 ); s=$?
    set -e
    rm -rf "$CACHE/tree"
    if [ "$g" -gt 1 ] || [ "$s" -gt 1 ]; then
      echo "baseline: archcheck could not evaluate the base commit (gate exit $g, scoring exit $s):" >&2
      jq -r '.errors[]?' "$CACHE/gate.json" "$CACHE/scoring.json" >&2 2>/dev/null || tail -20 "$CACHE/gate.txt" >&2; exit 2
    fi
    jq -n --arg base "$BASE" --arg pol "$POL_SHA" --arg prb "$PRB_SHA" --arg ac "$AC_DIGEST" --argjson g "$g" --argjson s "$s" --arg at "$(utc)" \
      '{schema:"arch002.baseline-cache/1", baseCommit:$base, policySha256:$pol, probesSha256:$prb, archcheckDist:$ac, gateExit:$g, scoringExit:$s, createdAt:$at}' > "$CACHE/meta.json"
    touch "$CACHE/done"
  fi
) 8>"$CACHE.lock"
cp "$CACHE/gate.json" "$PRISTINE/baseline-gate.json"; cp "$CACHE/scoring.json" "$PRISTINE/baseline-scoring.json"; cp "$CACHE/meta.json" "$PRISTINE/baseline-meta.json"

# --- tools (outside the workspace)
cp "$H/submit.sh" "$TOOLS/lib/submit.sh"
printf '#!/usr/bin/env bash\nexec bash "%s" "%s" "$@"\n' "$TOOLS/lib/submit.sh" "$ROOT" > "$TOOLS/bin/submit"; chmod +x "$TOOLS/bin/submit"
if has_contract "$ARM"; then cp "$ORDO_SRC" "$TOOLS/bin/ordo"; chmod +x "$TOOLS/bin/ordo"; fi
if has_verifier "$ARM"; then
  mkdir -p "$TOOLS/archcheck" "$TOOLS/policy" "$TOOLS/contracts" "$TOOLS/baseline"
  cp -r "$(dirname "$ARCHCHECK_SRC")/." "$TOOLS/archcheck/"
  ENTRY="$TOOLS/archcheck/$(basename "$ARCHCHECK_SRC")"
  case "$ENTRY" in
    *.dll) printf '#!/usr/bin/env bash\nexec "%s" "%s" "$@"\n' "$REAL_DOTNET" "$ENTRY" > "$TOOLS/bin/archcheck" ;;
    *.py)  printf '#!/usr/bin/env bash\nexec python3 -I "%s" "$@"\n' "$ENTRY" > "$TOOLS/bin/archcheck" ;;
    *)     printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$ENTRY" > "$TOOLS/bin/archcheck" ;;
  esac
  chmod +x "$TOOLS/bin/archcheck"
  cp "$POLICY_SRC" "$TOOLS/policy/$POLICY_NAME"
  cp "$TD/contract.json" "$TOOLS/contracts/$TASK.contract.json"
  cp "$PRISTINE/baseline-gate.json" "$TOOLS/baseline/start.report.json"   # policy-only: no probe content
fi
jq -n --arg root "$ROOT" --arg repo "$REPO" --arg arm "$ARM" --arg task "$TASK" --arg ledger "$LEDGER" --arg st "$ST" \
  --arg dotnet "$DOTNET_ROOT_DIR" --arg nuget "$NUGET_CACHE" --argjson max "$MAX_SUBMITS" \
  --arg archcheck "$( has_verifier "$ARM" && echo "$TOOLS/bin/archcheck" || true)" --arg ordo "$( has_contract "$ARM" && echo "$TOOLS/bin/ordo" || true)" \
  '{schema:"arch002.submit-config/1", root:$root, repo:$repo, arm:$arm, task:$task, ledger:$ledger, state:$st,
    dotnetRoot:$dotnet, nugetPackages:$nuget, maxSubmits:$max, ordo:$ordo, archcheck:$archcheck}' > "$ST/submit-config.json"

# --- pristine ordo verdicts (C, D): submit compares the agent's contract file and ordo's verdict with these
ordo_verdict() {  # NAME -> state/pristine/ordo-NAME.json {exit, stdoutSha256}
  local f="$PRISTINE/$1.contract.json" out rc
  set +e; out=$(cd "$REPO" && "$TOOLS/bin/ordo" ecir check --blueprint "$f" --json 2>&1); rc=$?; set -e
  jq -n --argjson rc "$rc" --arg o "$out" --arg s "$(sha "$f")" '{exit:$rc, admitted:($rc==0), contractSha256:$s, output:$o}' > "$PRISTINE/ordo-$1.json"
}
if has_contract "$ARM"; then ordo_verdict "$TASK"; ordo_verdict "$TASK-followup"; fi

# --- brief values that come from the fixture (trial.sh adds the per-phase ones)
jq -n --arg app "$APP_NAME" --arg desc "$(fixture_field .appDescription 'a small library-lending application in F# on .NET 10')" \
  --arg sln "$(fixture_field .solution Lending.slnx)" --arg tests "$(fixture_field .testsDir tests/Lending.Tests)" \
  --arg acc "$(jq -r '.files.visibleTests[0].target // empty' "$TD/task.json" 2>/dev/null | xargs -r dirname)" --arg accdef "$ACCEPTANCE_DIR" \
  --arg doc "$DOCTRINE_FILE" --arg inst "$INSTANCE_FILE" --arg pol "$TOOLS/policy/$POLICY_NAME" \
  '{APP_NAME:$app, APP_DESCRIPTION:$desc, SOLUTION:$sln, TESTS_DIR:$tests, ACCEPTANCE_DIR:(if $acc == "" then $accdef else $acc end),
    DOCTRINE_FILE:$doc, INSTANCE_FILE:$inst, POLICY:$pol}' > "$ST/brief-fixture-values.json"

# --- run.json
PACK_SHA=$( [ -d "$FIX/pack" ] && tree_sha "$FIX/pack" || echo null)
jq -n --arg run "$RUN_ID" --arg arm "$ARM" --arg task "$TASK" --arg fixture "$FIXTURE" --argjson rep "$REP" --arg label "$LABEL" --arg at "$(utc)" \
  --arg mkey "$MODEL_KEY" --arg model "$MODEL" \
  --arg base "$BASE" --arg start "$START" --arg root "$ROOT" --arg repo "$REPO" --arg tools "$TOOLS" --arg st "$ST" --arg briefs "$BRIEFS" \
  --arg fix "$FIXTURES" --arg fixsha "$(tree_sha "$FIX/repo")" --arg tasksha "$(tree_sha "$TD")" --arg pack "$PACK_SHA" \
  --arg cfgsha "$(sha "$AGENT_CONFIG")" --arg pt "$(sha "$PRICE_TABLE")" --argjson budget "$BUDGET_MINUTES" \
  --argjson max "$MAX_SUBMITS" --argjson tj "$(jq -c . "$TD/task.json")" \
  --arg ordo "$( has_contract "$ARM" && sha "$ORDO_SRC" || true)" --arg ordov "$( has_contract "$ARM" && "$ORDO_SRC" --version 2>/dev/null | head -1 || true)" \
  --arg ac "$AC_DIGEST" --arg pol "$POL_SHA" --arg prb "$PRB_SHA" --arg blkey "$BL_KEY" \
  --arg blg "$(sha "$PRISTINE/baseline-gate.json")" --arg bls "$(sha "$PRISTINE/baseline-scoring.json")" \
  --argjson blgn "$(jq '.findings | length' "$PRISTINE/baseline-gate.json")" --argjson blsn "$(jq '[.findings[] | select(.class == "DET" and .ruleId != "ARC-TRC-01")] | length' "$PRISTINE/baseline-scoring.json")" \
  --arg dn "$("$REAL_DOTNET" --version 2>/dev/null || echo unknown)" --arg cl "$("$CLAUDE_BIN" --version 2>/dev/null | head -1 || echo unknown)" \
  --arg cbe "$(git -C "$X" rev-parse HEAD 2>/dev/null || echo unknown)" --arg h "$H" \
  --arg vd "$(dirname "$ARCHCHECK_SRC")" --arg pol_path "$POLICY_SRC" \
  --arg ordo_path "$( has_contract "$ARM" && echo "$ORDO_SRC" || true)" --arg sealed "${SEALED_ARCHIVE:-$SEALED}" --arg sealed_root "$SEALED_ROOT" \
  --arg acsrc "$ARCHCHECK_SRC" --arg conc "${ARCH002_QUEUE_CONCURRENCY:-}" '
  def nn: if . == "" or . == "null" then null else . end;
  {schema:"arch002.run/1", runId:$run, fixture:$fixture, arm:$arm, task:$task, taskKey:($fixture + "/" + $task), replicate:$rep,
   modelKey:$mkey, model:$model, block:($fixture + "/" + $task + "/" + $mkey + "/r" + ($rep|tostring)), label:$label,
   createdAt:$at, baseCommit:$base, startCommit:$start,
   paths:{root:$root, repo:$repo, tools:$tools, state:$st, briefs:$briefs, fixtures:$fix},
   digests:{fixtureRepoTree:$fixsha, taskTree:$tasksha, packTree:($pack|nn), policy:$pol, probes:$prb, ordo:($ordo|nn), archcheckDist:$ac,
            agentConfig:$cfgsha, priceTable:$pt, baselineGate:$blg, baselineScoring:$bls},
   baseline:{commit:$base, cacheKey:$blkey, gateFindings:$blgn, scoringDetFindings:$blsn,
             note:"archcheck on the base commit with the pristine policy (gate) and policy + sealed probes (scoring)"},
   task_json:$tj, crossTierCount:($tj.crossTierCount // ($tj.expectedTiers // [] | length)),
   tools:{dotnet:$dn, claudeCode:$cl, ordo:($ordov|nn)}, budgetMinutes:$budget, maxSubmits:$max,
   queueConcurrency:($conc|tonumber? // null), cohortCommit:$cbe,
   config:{fixtures:$fix, sealedRoot:$sealed_root, archcheck:$acsrc, policy:$pol_path},
   integrityTargets:{harness:$h, tools:$tools, verifierDist:$vd, policySource:$pol_path, ordo:($ordo_path|nn),
                     sealed:$sealed, pristine:($st + "/pristine")}}' > "$ST/run.json"
python3 -I "$H/integrity.py" snapshot "$ST/run.json" > "$ST/integrity-setup.json"
echo "$ROOT"
