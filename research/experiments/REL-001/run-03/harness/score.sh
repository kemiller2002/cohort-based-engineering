#!/usr/bin/env bash
# REL-001 run-03 scoring (adapted from run-02/harness/score.sh). usage: run-03/harness/score.sh RUNID [--out FILE]
# Everything runs in the harness state directory ($REL003_STATE/RUNID/score), never in the workspace:
#   1. the HIDDEN oracle (fixtures/oracle/V<n>) at the workspace HEAD and, in C and D, at the commit of the first
#      completion attempt when its tree differs (first-pass correctness). Skipped in a dry run;
#   2. the reliability report (pinned measurement Praxis, --agent-binding, --price-table) over the transcript,
#      when the measurement Praxis exists;
#   3. D: `praxis work completion-identity`;
#   4. score.py builds the observation.
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: score.sh RUNID [--out FILE]}"; shift
OUT=""
while [ $# -gt 0 ]; do case "$1" in --out) OUT="$2"; shift 2;; *) echo "unknown $1" >&2; exit 2;; esac; done
RJ="$HS/run.json"; [ -f "$RJ" ] || { echo "no run.json for $RUN_ID" >&2; exit 2; }
TASK=$(jq -r .task "$RJ"); ARM=$(jq -r .arm "$RJ"); ITEM=$(jq -r .workItem "$RJ"); REPO=$(jq -r '.workspaces[0].repo' "$RJ")
SC="$HS/score"; rm -rf "${SC:?}"; mkdir -p "$SC"

oracle() {
  local label="$1" commit="$2" d="$SC/$1"
  mkdir -p "$d/src" "$d/oracle"
  git -C "$REPO" archive "$commit" | tar -x -C "$d/src"
  sed "s#LEDGER_PROJECT_PATH#$d/src/src/Ledger/Ledger.fsproj#" "$FIX3/oracle/Oracle.fsproj" > "$d/oracle/Oracle.fsproj"
  cp "$FIX3/oracle/$TASK/OracleTests.fs" "$d/oracle/OracleTests.fs"
  set +e; (cd "$d/oracle" && DOTNET_ROOT="$DOTNET_ROOT_DIR" "$REAL_DOTNET" test --logger "trx;LogFileName=oracle.trx" --results-directory "$d/results" > "$d/oracle-output.txt" 2>&1); echo $? > "$d/exit"; set -e
  echo "$commit" > "$d/commit"
}

FINAL=$(git -C "$REPO" rev-parse HEAD)
if [ "$DRY_RUN" = 1 ]; then
  mkdir -p "$SC/final"; echo "$FINAL" > "$SC/final/commit"   # no exit file: score.py records the oracle as not run
else
  oracle final "$FINAL"
  if is_echelon "$ARM" && [ -f "$RUN_DIR/logs/praxis.jsonl" ]; then
    FIRST=$(jq -rs '[.[] | select(.argv[0]=="work" and .argv[1]=="complete-verified") | .head][0] // empty' "$RUN_DIR/logs/praxis.jsonl")
    if [ -n "$FIRST" ] && git -C "$REPO" cat-file -e "$FIRST^{commit}" 2>/dev/null; then
      if git -C "$REPO" diff --quiet "$FIRST" "$FINAL" -- . ':!.ros'; then echo same > "$SC/first-same-tree"; else oracle first "$FIRST"; fi
    fi
  fi
fi

REPORT_RC=null
if [ -f "$MEASURE_PRAXIS" ] && [ -f "$HS/agent-binding.json" ] && [ -n "$(ls -A "$HS/transcripts" 2>/dev/null)" ]; then
  mkdir -p "$SC/no-executions"; : > "$SC/no-events.jsonl"; launcher "$MEASURE_PRAXIS" "$SC/measure-praxis"
  set +e
  ( cd "$SC" && "$SC/measure-praxis" telemetry reliability-report \
      --events "$SC/no-events.jsonl" --executions "$SC/no-executions" --transcripts "$HS/transcripts" \
      --agent-binding "$HS/agent-binding.json" --price-table "$PRICE_TABLE" --out "$SC/reliability-report.json" > "$SC/report.log" 2>&1 )
  REPORT_RC=$?; set -e
fi

if [ "$ARM" = echelon-optimized ] && [ -f "$MEASURE_PRAXIS" ]; then
  set +e; (cd "$REPO" && "$SC/measure-praxis" work completion-identity --id "$ITEM") > "$SC/completion-identity-agent-1.json" 2> "$SC/completion-identity-agent-1.err"; set -e
fi

python3 -I "$H3/score.py" "$RJ" "$SC" "$REPORT_RC" > "$SC/observation.json"
[ -n "$OUT" ] && cp "$SC/observation.json" "$OUT"
cat "$SC/observation.json"
