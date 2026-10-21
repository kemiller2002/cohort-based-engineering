#!/usr/bin/env bash
# ARCH-001 trial setup (adapted from REL-001 run-03 harness/setup.sh; see PROVENANCE.md).
#   usage: harness/setup.sh RUNID          (arm, task and replicate are read from the run id)
# Builds $ARCH001_RUNS/RUNID/ (outside every repository):
#   repo/     the agent workspace: fixture repo + requirements/T<n>.md + visible acceptance tests (base commit, fixed
#             date, identical in every arm), then the arm material as a second commit (B-D: docs/architecture/ from the
#             pack; C-D: docs/contracts/T<n>.contract.json). The follow-up is NOT copied (trial.sh transition does it).
#   tools/    workspace-external tools: bin/submit (all arms), bin/ordo (C, D), bin/archcheck + policy/ copy (D)
#   brief/    rendered briefs (one per phase, written when the phase starts)
#   state/    harness state: run.json, pristine copies used for gating and scoring, integrity snapshots, ledger
# Exit 0 = ready; anything else = X1 (harness failure before agent start; rerun with a fresh run id).
source "$(dirname "$0")/lib.sh"
[ $# -eq 1 ] || { echo "usage: $0 RUNID" >&2; exit 2; }
[[ "$1" =~ $RUNID_RE ]] || { echo "RUNID must match $RUNID_RE" >&2; exit 2; }
run_paths "$1"
ARM=$(arm_of "$RUN_ID"); TASK=$(task_of "$RUN_ID"); REP=$(rep_of "$RUN_ID"); LABEL=$(label_of "$RUN_ID")
TD="$FIX/tasks/$TASK"
[ -e "$ROOT" ] && { echo "exists: $ROOT (every run needs a fresh run id)" >&2; exit 2; }
need() { [ -e "$1" ] || { echo "missing $2: $1" >&2; exit 2; }; }
need "$FIX/repo" "fixture repository"; need "$TD/requirement.md" "requirement"; need "$TD/acceptance" "acceptance tests"
need "$TD/followup.md" "follow-up requirement"; need "$TD/task.json" "task.json"; need "$PRICE_TABLE" "price table"
has_pack "$ARM" && need "$FIX/pack" "architecture pack"
if has_contract "$ARM"; then need "$TD/contract.json" "contract"; need "$TD/followup-contract.json" "follow-up contract"; need "$ORDO_SRC" "ordo"; fi
if has_verifier "$ARM"; then need "$POLICY_SRC" "policy"; need "$ARCHCHECK_SRC" "archcheck"; fi
if [ "$LABEL" != smoke ] && grep -q '"standIn": *true' "$TD/task.json"; then echo "stand-in fixtures are for SMOKE runs only" >&2; exit 2; fi

mkdir -p "$REPO" "$TOOLS/bin" "$TOOLS/lib" "$BRIEFS" "$ST/pristine"
# --- pristine harness-side copies (gating and scoring read only these)
cp "$TD/task.json" "$PRISTINE/task.json"; cp "$PRICE_TABLE" "$PRISTINE/price-table.json"; cp "$AGENT_CONFIG" "$PRISTINE/agent-config.json"
[ -f "$POLICY_SRC" ] && cp "$POLICY_SRC" "$PRISTINE/policy.json"
[ -f "$TD/contract.json" ] && cp "$TD/contract.json" "$PRISTINE/$TASK.contract.json"
[ -f "$TD/followup-contract.json" ] && cp "$TD/followup-contract.json" "$PRISTINE/$TASK-followup.contract.json"

# --- repository: base commit (identical in every arm), then the arm material
cp -r "$FIX/repo/." "$REPO/"
mkdir -p "$REPO/requirements" "$REPO/tests/Lending.Tests/Acceptance"
cp "$TD/requirement.md" "$REPO/requirements/$TASK.md"
cp "$TD"/acceptance/*.fs "$REPO/tests/Lending.Tests/Acceptance/"
( cd "$REPO" && git init -q -b main . && git config user.email "agent@arch001.invalid" && git config user.name "agent" \
  && git config commit.gpgsign false && git add -A \
  && GIT_AUTHOR_DATE="$FIXED_DATE" GIT_COMMITTER_DATE="$FIXED_DATE" hgit commit -qm "Initial repository" )
BASE=$(git -C "$REPO" rev-parse HEAD)
if has_pack "$ARM"; then
  mkdir -p "$REPO/docs/architecture"; cp -r "$FIX/pack/." "$REPO/docs/architecture/"
  if has_contract "$ARM"; then mkdir -p "$REPO/docs/contracts"; cp "$TD/contract.json" "$REPO/docs/contracts/$TASK.contract.json"; fi
  ( cd "$REPO" && git add -A && GIT_AUTHOR_DATE="$FIXED_DATE" GIT_COMMITTER_DATE="$FIXED_DATE" hgit commit -qm "Project documents" )
fi
START=$(git -C "$REPO" rev-parse HEAD)

# --- tools (outside the workspace)
cp "$H/submit.sh" "$TOOLS/lib/submit.sh"
printf '#!/usr/bin/env bash\nexec bash "%s" "%s" "$@"\n' "$TOOLS/lib/submit.sh" "$ROOT" > "$TOOLS/bin/submit"; chmod +x "$TOOLS/bin/submit"
if has_contract "$ARM"; then cp "$ORDO_SRC" "$TOOLS/bin/ordo"; chmod +x "$TOOLS/bin/ordo"; fi
if has_verifier "$ARM"; then
  mkdir -p "$TOOLS/archcheck" "$TOOLS/policy"
  if [ -d "$(dirname "$ARCHCHECK_SRC")" ] && [ "$(dirname "$ARCHCHECK_SRC")" != / ]; then cp -r "$(dirname "$ARCHCHECK_SRC")/." "$TOOLS/archcheck/"; fi
  ENTRY="$TOOLS/archcheck/$(basename "$ARCHCHECK_SRC")"
  case "$ENTRY" in
    *.dll) printf '#!/usr/bin/env bash\nexec "%s" "%s" "$@"\n' "$REAL_DOTNET" "$ENTRY" > "$TOOLS/bin/archcheck" ;;
    *.py)  printf '#!/usr/bin/env bash\nexec python3 -I "%s" "$@"\n' "$ENTRY" > "$TOOLS/bin/archcheck" ;;
    *)     printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$ENTRY" > "$TOOLS/bin/archcheck" ;;
  esac
  chmod +x "$TOOLS/bin/archcheck"
  cp "$POLICY_SRC" "$TOOLS/policy/lending.policy.json"
fi
jq -n --arg root "$ROOT" --arg repo "$REPO" --arg arm "$ARM" --arg task "$TASK" --arg ledger "$LEDGER" --arg st "$ST" \
  --arg dotnet "$DOTNET_ROOT_DIR" --arg nuget "$NUGET_CACHE" --argjson max "$MAX_SUBMITS" \
  --arg archcheck "$( has_verifier "$ARM" && echo "$TOOLS/bin/archcheck" || true)" --arg ordo "$( has_contract "$ARM" && echo "$TOOLS/bin/ordo" || true)" \
  '{schema:"arch001.submit-config/1", root:$root, repo:$repo, arm:$arm, task:$task, ledger:$ledger, state:$st,
    dotnetRoot:$dotnet, nugetPackages:$nuget, maxSubmits:$max, ordo:$ordo, archcheck:$archcheck}' > "$ST/submit-config.json"

# --- pristine ordo verdicts (C, D): submit compares the agent's contract file and ordo's verdict with these
ordo_verdict() {  # NAME -> state/pristine/ordo-NAME.json {exit, stdoutSha256}
  local f="$PRISTINE/$1.contract.json" out rc
  set +e; out=$(cd "$REPO" && "$TOOLS/bin/ordo" ecir check --blueprint "$f" --json 2>&1); rc=$?; set -e
  jq -n --argjson rc "$rc" --arg o "$out" --arg s "$(sha "$f")" '{exit:$rc, admitted:($rc==0), contractSha256:$s, output:$o}' > "$PRISTINE/ordo-$1.json"
}
if has_contract "$ARM"; then ordo_verdict "$TASK"; ordo_verdict "$TASK-followup"; fi

# --- run.json
PACK_SHA=$( [ -d "$FIX/pack" ] && tree_sha "$FIX/pack" || echo null)
jq -n --arg run "$RUN_ID" --arg arm "$ARM" --arg task "$TASK" --argjson rep "$REP" --arg label "$LABEL" --arg at "$(utc)" \
  --arg base "$BASE" --arg start "$START" --arg root "$ROOT" --arg repo "$REPO" --arg tools "$TOOLS" --arg st "$ST" --arg briefs "$BRIEFS" \
  --arg fix "$FIX" --arg fixsha "$(tree_sha "$FIX/repo")" --arg tasksha "$(tree_sha "$TD")" --arg pack "$PACK_SHA" \
  --arg model "$MODEL" --arg cfgsha "$(sha "$AGENT_CONFIG")" --arg pt "$(sha "$PRICE_TABLE")" --argjson budget "$BUDGET_MINUTES" \
  --argjson max "$MAX_SUBMITS" --argjson tj "$(jq -c . "$TD/task.json")" \
  --arg ordo "$( has_contract "$ARM" && sha "$ORDO_SRC" || true)" --arg ordov "$( has_contract "$ARM" && "$ORDO_SRC" --version 2>/dev/null | head -1 || true)" \
  --arg ac "$( has_verifier "$ARM" && any_sha "$(dirname "$ARCHCHECK_SRC")" || true)" --arg pol "$( [ -f "$POLICY_SRC" ] && sha "$POLICY_SRC" || true)" \
  --arg dn "$("$REAL_DOTNET" --version 2>/dev/null || echo unknown)" --arg cl "$("$CLAUDE_BIN" --version 2>/dev/null | head -1 || echo unknown)" \
  --arg cbe "$(git -C "$X" rev-parse HEAD 2>/dev/null || echo unknown)" --arg h "$H" \
  --arg vd "$( has_verifier "$ARM" && dirname "$ARCHCHECK_SRC" || true)" --arg pol_path "$( [ -f "$POLICY_SRC" ] && echo "$POLICY_SRC" || true)" \
  --arg ordo_path "$( has_contract "$ARM" && echo "$ORDO_SRC" || true)" --arg sealed "${SEALED_ARCHIVE:-$SEALED}" --arg sealed_dir "$SEALED" --arg acsrc "$ARCHCHECK_SRC" --arg doctrine "$DOCTRINE" --arg conc "${ARCH001_QUEUE_CONCURRENCY:-}" '
  def nn: if . == "" or . == "null" then null else . end;
  {schema:"arch001.run/1", runId:$run, arm:$arm, task:$task, replicate:$rep, block:($task + "-r" + ($rep|tostring)), label:$label,
   createdAt:$at, baseCommit:$base, startCommit:$start,
   paths:{root:$root, repo:$repo, tools:$tools, state:$st, briefs:$briefs, fixtures:$fix},
   digests:{fixtureRepoTree:$fixsha, taskTree:$tasksha, packTree:($pack|nn), policy:($pol|nn), ordo:($ordo|nn), archcheckDist:($ac|nn),
            agentConfig:$cfgsha, priceTable:$pt},
   task_json:$tj, crossTierCount:($tj.crossTierCount // ($tj.expectedTiers // [] | length)),
   tools:{dotnet:$dn, claudeCode:$cl, ordo:($ordov|nn)}, model:$model, budgetMinutes:$budget, maxSubmits:$max,
   queueConcurrency:($conc|tonumber? // null), cohortCommit:$cbe, config:{fixtures:$fix, sealed:$sealed_dir, archcheck:$acsrc, policy:($pol_path|nn), doctrine:$doctrine},
   integrityTargets:{harness:$h, tools:$tools, verifierDist:($vd|nn), policySource:($pol_path|nn), ordo:($ordo_path|nn),
                     sealed:$sealed, pristine:($st + "/pristine")}}' > "$ST/run.json"
python3 -I "$H/integrity.py" snapshot "$ST/run.json" > "$ST/integrity-setup.json"
echo "$ROOT"
