#!/usr/bin/env bash
# REL-001 run-02 scoring. usage: run-02/harness/score.sh RUNID [--out FILE]
# Everything runs in the harness state directory ($REL002_STATE/RUNID/score), never in a workspace:
#   1. the HIDDEN oracle (fixtures/oracle/U<n>) at the final commit: the workspace HEAD, or for U6 the bare
#      remote's main; and, in C and D, at the commit of the first completion attempt when its tree differs
#      (first-pass correctness). Oracle tests are tagged by requirement ID; the unit is the requirement (R9);
#   2. the reliability report (measurement Praxis, --agent-binding, --price-table) over the run's transcripts;
#   3. D: `praxis work completion-identity` in every workspace;
#   4. score.py: outcome lines, completion evidence per arm, U2 rubric (R6), U6 observables (R8),
#      reliability counts, tokens and cost, test runs, X2/X4/X6, and the observation document.
# Prints the observation (cbe.rel-001.observation/1 with the additive run02 block) to stdout and --out.
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: score.sh RUNID [--out FILE]}"; shift
OUT=""
while [ $# -gt 0 ]; do case "$1" in --out) OUT="$2"; shift 2;; *) echo "unknown $1" >&2; exit 2;; esac; done
RJ="$HS/run.json"; [ -f "$RJ" ] || { echo "no run.json for $RUN_ID" >&2; exit 2; }
TASK=$(jq -r .task "$RJ"); ARM=$(jq -r .arm "$RJ"); ITEM=$(jq -r .workItem "$RJ"); AGENTS=$(jq -r .agents "$RJ")
SC="$HS/score"; rm -rf "${SC:?}"; mkdir -p "$SC"

# oracle LABEL GITDIR COMMIT: runs the hidden oracle against COMMIT's tree; leaves SC/LABEL/{oracle.trx,oracle-output.txt,exit}.
oracle() {
  local label="$1" gitdir="$2" commit="$3" d="$SC/$1"
  mkdir -p "$d/src" "$d/oracle"
  git -C "$gitdir" archive "$commit" | tar -x -C "$d/src"
  sed "s#LEDGER_PROJECT_PATH#$d/src/src/Ledger/Ledger.fsproj#" "$FIX2/oracle/Oracle.fsproj" > "$d/oracle/Oracle.fsproj"
  cp "$FIX2/oracle/$TASK/OracleTests.fs" "$d/oracle/OracleTests.fs"
  set +e; (cd "$d/oracle" && "$REAL_DOTNET" test --logger "trx;LogFileName=oracle.trx" --results-directory "$d/results" > "$d/oracle-output.txt" 2>&1); echo $? > "$d/exit"; set -e
  echo "$commit" > "$d/commit"
}

if [ "$AGENTS" -eq 2 ]; then
  FINAL_GIT="$RUN_DIR/remote.git"; FINAL=$(git -C "$FINAL_GIT" rev-parse --verify -q refs/heads/main || jq -r .initialCommit "$RJ")
else
  FINAL_GIT="$RUN_DIR/repo"; FINAL=$(git -C "$FINAL_GIT" rev-parse HEAD)
fi
oracle final "$FINAL_GIT" "$FINAL"

# first completion attempt (C, D single-agent runs): HEAD recorded by the praxis shim
FIRST=""
if is_echelon "$ARM" && [ "$AGENTS" -eq 1 ] && [ -f "$RUN_DIR/logs/praxis.jsonl" ]; then
  FIRST=$(jq -rs '[.[] | select(.argv[0]=="work" and .argv[1]=="complete-verified") | .head][0] // empty' "$RUN_DIR/logs/praxis.jsonl")
  if [ -n "$FIRST" ] && git -C "$FINAL_GIT" cat-file -e "$FIRST^{commit}" 2>/dev/null; then
    if git -C "$FINAL_GIT" diff --quiet "$FIRST" "$FINAL" -- . ':!.ros'; then echo same > "$SC/first-same-tree"
    else oracle first "$FINAL_GIT" "$FIRST"; fi
  fi
fi

# reliability report: the same measurement tool and inputs for every arm
mkdir -p "$SC/no-executions"; : > "$SC/no-events.jsonl"; launcher "$MEASURE_PRAXIS" "$SC/measure-praxis"
REPORT_RC=null
if [ -f "$HS/agent-binding.json" ] && [ -n "$(ls -A "$HS/transcripts" 2>/dev/null)" ]; then
  set +e
  ( cd "$SC" && "$SC/measure-praxis" telemetry reliability-report \
      --events "$SC/no-events.jsonl" --executions "$SC/no-executions" --transcripts "$HS/transcripts" \
      --agent-binding "$HS/agent-binding.json" --price-table "$PRICE_TABLE" --out "$SC/reliability-report.json" > "$SC/report.log" 2>&1 )
  REPORT_RC=$?; set -e
fi

# D: completion identity per workspace (F3), with the measurement Praxis
if [ "$ARM" = echelon-optimized ]; then
  STORE=(); [ "$AGENTS" -eq 2 ] && STORE=(--store git --remote origin)
  for n in $(workspace_names); do
    repo=$(jq -r --arg n "$n" '.workspaces[] | select(.name==$n) | .repo' "$RJ")
    set +e; (cd "$repo" && "$SC/measure-praxis" work completion-identity --id "$ITEM" "${STORE[@]}") > "$SC/completion-identity-$n.json" 2> "$SC/completion-identity-$n.err"; set -e
  done
fi

python3 -I "$H2/score.py" "$RJ" "$SC" "$REPORT_RC" > "$SC/observation.json"
[ -n "$OUT" ] && cp "$SC/observation.json" "$OUT"
cat "$SC/observation.json"
