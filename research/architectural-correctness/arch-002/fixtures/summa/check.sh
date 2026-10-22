#!/usr/bin/env bash
# ARCH-002 F2 (summa) fixture self-check (Worker S). Adapted from ARCH-001 fixtures/check.sh.
#   usage: fixtures/summa/check.sh [> check-output.txt]
#   env:   ARCH002_SEALED  sealed directory (default /home/user/arch002-sealed/summa)
#          ARCH002_ORDO    ordo binary (default /home/user/.tools/ordo/ordo-linux-x64/ordo)
#          ARCH002_DOTNET_ROOT (default /home/user/.tools/dotnet)
#          ARCH002_VERIFIER archcheck.dll with --baseline (default arch-002/verifier/dist/archcheck.dll)
#          SUMMA_CLONE     source clone for the snapshot reproduction check (default /home/user/kemiller2002/summa)
#          CHECK_TASKS="T1 T3" limits the tasks; CHECK_JOBS=N runs N tasks in parallel (default 3)
#          CHECK_WORK=DIR keeps the work directory
#
# Static checks first: the doctrine's hash; no sealed content in the public tree; every policy rule is stated in
# the instance document; task.json digests; make-contracts.py reproduces the contracts; make-snapshot.sh
# reproduces repo/. Then the starting repository builds, its own tests pass, and archcheck on it reproduces the
# sealed baseline (same finding keys). Then, for every task, in fresh copies outside the fixture tree:
#   1. start FAILS the task's visible tests and its hidden initial oracle;
#   2. good:  visible + initial oracle pass; archcheck --baseline passes (0 new DET sev>=2);
#             good FAILS the follow-up visible tests and the follow-up oracle;
#   3. trap (tasks whose sealed task-private says it has one): visible + initial oracle pass (functionally
#      correct); archcheck --baseline FAILS with at least one new DET finding of severity >= 2;
#   (the baseline is archcheck on the start commit with the policy only: no probes, no contract; ARC-TRC-01 is
#    severity 1 and never gates)
#   4. followup-good (over good): visible (initial + follow-up) and the follow-up oracle pass; the initial
#      oracle fails only on the tests oracle.json lists as superseded (the regression list passes); archcheck
#      --baseline passes;
#   5. ordo admits contract.json and followup-contract.json.
# Each line ends with the step's wall time. Exit 0 only when every expectation holds.
set -uo pipefail
FIX="$(cd "$(dirname "$0")" && pwd)"
A2="$(cd "$FIX/../.." && pwd)"
SEALED="${ARCH002_SEALED:-/home/user/arch002-sealed/summa}"
ORDO="${ARCH002_ORDO:-/home/user/.tools/ordo/ordo-linux-x64/ordo}"
VERIFIER="${ARCH002_VERIFIER:-$A2/verifier/dist/archcheck.dll}"
CLONE="${SUMMA_CLONE:-/home/user/kemiller2002/summa}"
export DOTNET_ROOT="${ARCH002_DOTNET_ROOT:-/home/user/.tools/dotnet}"
export PATH="$DOTNET_ROOT:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 MSBUILDDISABLENODEREUSE=1
WORK="${CHECK_WORK:-$(mktemp -d)}"; mkdir -p "$WORK"
TASKS="${CHECK_TASKS:-T1 T2 T3}"
JOBS="${CHECK_JOBS:-3}"
POLICY="$FIX/policy.json"
BASELINE="$SEALED/baseline/start.report.json"
command -v dotnet >/dev/null || { echo "BLOCKED: dotnet not found (set ARCH002_DOTNET_ROOT)"; exit 3; }
[ -d "$SEALED/oracle" ] || { echo "BLOCKED: sealed directory $SEALED not found (set ARCH002_SEALED)"; exit 3; }
[ -f "$VERIFIER" ] || { echo "BLOCKED: verifier $VERIFIER not found (set ARCH002_VERIFIER)"; exit 3; }

# ---- helpers (each task runs in its own process; results go to $WORK/<task>.out) ----------------------
overlay() {   # overlay DIR SRC: copy SRC over DIR and remove the paths SRC/.delete lists
  cp -r "$2/." "$1/"
  if [ -f "$2/.delete" ]; then while read -r f; do rm -f "${1:?}/$f"; done < "$2/.delete"; rm -f "${1:?}/.delete"; fi
}
repo() {      # repo TASK NAME [OVERLAY...]: a fresh copy of the starting repository with overlays applied
  local dir="$WORK/$1-$2"; shift 2
  rm -rf "${dir:?}"; cp -r "$FIX/repo" "$dir"
  for o in "$@"; do overlay "$dir" "$SEALED/reference/$o"; done
  echo "$dir"
}
with_tests() { local d="$1"; shift; for s in "$@"; do cp "$FIX/tasks/$s/"*.fs "$d/tests/Summa.Acceptance.Tests/Acceptance/"; done; }
summary() {
  if grep -qE '^(Passed|Failed)! ' "$1"; then
    echo "$(grep -E '^(Passed|Failed)! ' "$1" | sed -E 's/.*Failed: +([0-9]+), Passed: +([0-9]+).*/\2 \1/' | awk '{p+=$1; f+=$2} END {printf "passed %d, failed %d", p, f}')"
  else echo "build failed ($(grep -oE ' error FS[0-9]+' "$1" | sort -u | wc -l) distinct compiler errors)"; fi
}
run_tests() { (cd "$1" && dotnet test Summa.sln > "$1.tests.log" 2>&1); }
run_oracle() {  # run_oracle TASK KIND DIR
  local od="$3.oracle-$2"
  rm -rf "${od:?}"; mkdir -p "$od"
  sed "s#SUMMA_REPO#$3#" "$SEALED/oracle/Oracle.fsproj" > "$od/Oracle.fsproj"
  sed "s#SUMMA_REPO#$3#" "$SEALED/oracle/NuGet.config" > "$od/NuGet.config"
  cp "$SEALED/oracle/OracleKit.fs" "$od/"; cp "$SEALED/oracle/$1/${2}OracleTests.fs" "$od/OracleTests.fs"
  (cd "$od" && dotnet test > "$od.log" 2>&1)
}
run_verifier() {  # run_verifier TASK DIR CONTRACT: archcheck on a committed copy of DIR (sources only)
  local vd="$2.git"
  rm -rf "${vd:?}"; mkdir -p "$vd"
  (cd "$2" && tar --exclude=bin --exclude=obj --exclude=TestResults -cf - .) | (cd "$vd" && tar -xf -)
  (cd "$vd" && git init -q && git add -A && git -c user.email=fixture@arch002 -c user.name=fixture commit -qm fixture)
  local extra=(); [ -f "$SEALED/oracle/$1/probes.json" ] && extra+=(--probes "$SEALED/oracle/$1/probes.json")
  [ -n "$3" ] && extra+=(--contract "$3")
  [ "$1" = "--" ] || extra+=(--baseline "$BASELINE")
  dotnet "$VERIFIER" verify --repo "$vd" --policy "$POLICY" "${extra[@]}" --out "$vd.report.json" > "$vd.log" 2>&1
}
newsummary() { jq -r '"new DET sev3=\(.summary.new.det.bySeverity["3"]) sev2=\(.summary.new.det.bySeverity["2"]); preexisting \(.summary.preexisting.det.total)"' "$1" 2>/dev/null || echo "no report"; }
T0=0; tick() { T0=$SECONDS; }; took() { echo "$((SECONDS - T0))s"; }
# expect TASK LABEL EXPECTED(PASS|FAIL) RC LOG
expect() {
  local got; [ "$4" -eq 0 ] && got=PASS || got=FAIL
  local mark=ok; [ "$got" = "$3" ] || mark=MISMATCH
  printf '%-3s %-56s expected %-4s got %-4s %-9s (%s) %s\n' "$1" "$2" "$3" "$got" "$mark" "$(summary "$5")" "$(took)"
}
vexpect() {     # vexpect TASK LABEL EXPECTED(PASS|FAIL) DIR CONTRACT
  tick; run_verifier "$1" "$4" "$5"; local rc=$?
  local got mark=ok; case $rc in 0) got=PASS;; 1) got=FAIL;; *) got="ERR$rc";; esac
  [ "$got" = "$3" ] || mark=MISMATCH
  printf '%-3s %-56s expected %-4s got %-4s %-9s (%s) %s\n' "$1" "$2" "$3" "$got" "$mark" "$(newsummary "$4.git.report.json")" "$(took)"
  if [ "$got" = FAIL ]; then
    echo "       new DET findings: $(jq -r '[.findings[] | select(.class == "DET" and .preexisting == false and .severity >= 2) | .ruleId + " " + .file] | group_by(.) | map("\(.[0]) x\(length)") | join("; ")' "$4.git.report.json")"
  fi
}
ordo_expect() {  # ordo_expect TASK FILE LABEL
  local out rc got mark=ok
  out=$("$ORDO" ecir check --blueprint "$2" --json 2>/dev/null); rc=$?
  got=$([ $rc -eq 0 ] && echo true || echo false)
  [ "$got" = true ] || mark=MISMATCH
  printf '%-3s %-56s expected true  got %-5s %-8s (%s)\n' "$1" "$3" "$got" "$mark" "$(echo "$out" | jq -r '.contractDigest // empty' | cut -c1-23)"
}

check_task() {
  local T="$1" d
  local C="$FIX/tasks/$T/contract.json" FC="$FIX/tasks/$T/followup-contract.json"
  local trap; trap=$(jq -r '.trap.exists' "$SEALED/task-private/$T.json")
  tick; d=$(repo "$T" start); with_tests "$d" "$T/acceptance"; run_tests "$d"; expect "$T" "start: visible tests" FAIL $? "$d.tests.log"
  tick; run_oracle "$T" Initial "$d"; expect "$T" "start: initial oracle" FAIL $? "$d.oracle-Initial.log"

  tick; d=$(repo "$T" good "$T/good"); with_tests "$d" "$T/acceptance"
  run_tests "$d"; expect "$T" "good: visible tests (whole solution)" PASS $? "$d.tests.log"
  tick; run_oracle "$T" Initial "$d"; expect "$T" "good: initial oracle" PASS $? "$d.oracle-Initial.log"
  vexpect "$T" "good: archcheck --baseline (policy + probes)" PASS "$d" "$C"
  tick; run_oracle "$T" Followup "$d"; expect "$T" "good: follow-up oracle (not yet solved)" FAIL $? "$d.oracle-Followup.log"
  tick; d=$(repo "$T" good-fvisible "$T/good"); with_tests "$d" "$T/acceptance" "$T/followup-acceptance"
  run_tests "$d"; expect "$T" "good: follow-up visible tests (not yet solved)" FAIL $? "$d.tests.log"

  if [ "$trap" = true ]; then
    tick; d=$(repo "$T" trap "$T/trap"); with_tests "$d" "$T/acceptance"
    run_tests "$d"; expect "$T" "trap: visible tests (whole solution)" PASS $? "$d.tests.log"
    tick; run_oracle "$T" Initial "$d"; expect "$T" "trap: initial oracle (functionally correct)" PASS $? "$d.oracle-Initial.log"
    vexpect "$T" "trap: archcheck --baseline (policy + probes)" FAIL "$d" "$C"
  else
    printf '%-3s %-56s none (control task)\n' "$T" "trap"
  fi

  tick; d=$(repo "$T" followup "$T/good" "$T/followup-good"); with_tests "$d" "$T/acceptance" "$T/followup-acceptance"
  run_tests "$d"; expect "$T" "followup-good: visible tests (whole solution)" PASS $? "$d.tests.log"
  tick; run_oracle "$T" Followup "$d"; expect "$T" "followup-good: follow-up oracle" PASS $? "$d.oracle-Followup.log"
  tick; run_oracle "$T" Initial "$d"
  local failed superseded mark=ok
  failed=$(grep -E '^\s+Failed OracleT[0-9]+Initial\.' "$d.oracle-Initial.log" | sed -E 's/^\s+Failed (.*) \[.*/\1/' | sort)
  superseded=$(jq -r '.superseded[]' "$SEALED/oracle/$T/oracle.json" | sort)
  grep -qE '^(Passed|Failed)! ' "$d.oracle-Initial.log" || mark=MISMATCH-NOT-BUILT
  [ "$failed" = "$superseded" ] || mark=MISMATCH
  printf '%-3s %-56s expected %-4s got %-4s %-9s (%s; %s superseded) %s\n' "$T" "followup-good: regression (initial oracle minus superseded)" PASS \
    "$([ "$mark" = ok ] && echo PASS || echo FAIL)" "$mark" "$(summary "$d.oracle-Initial.log")" "$(echo "$superseded" | grep -c .)" "$(took)"
  vexpect "$T" "followup-good: archcheck --baseline (policy + probes)" PASS "$d" "$FC"

  ordo_expect "$T" "$C" "ordo admits contract.json"
  ordo_expect "$T" "$FC" "ordo admits followup-contract.json"
}

# ---- static checks ---------------------------------------------------------------------------------------
STATIC="$WORK/static.out"
{
  echo "ARCH-002 F2 (summa) fixture check"
  echo "fixture tree: $(cd "$FIX" && find repo pack tasks policy.json make-contracts.py make-snapshot.sh snapshot-additions tasks-public.json -type f -not -path '*/bin/*' -not -path '*/obj/*' | sort | xargs sha256sum | sha256sum | cut -c1-64)"
  echo "sealed tree:  $(cd "$SEALED" && find oracle reference baseline task-private tasks-meta.json -type f | sort | xargs sha256sum | sha256sum | cut -c1-64)"
  echo "dotnet $(dotnet --version); ordo $(sha256sum "$ORDO" | cut -c1-16)…; archcheck $(sha256sum "$VERIFIER" | cut -c1-16)… (${VERIFIER#$A2/}); policy $(jq -r .id "$POLICY")"
  doctrine=$(sha256sum "$FIX/pack/FOUR-TIER-ARCHITECTURE.md" | cut -c1-64)
  if [ "$doctrine" = 725cb3d97b56142a4de07ea6cbbdafbbb421735b79e375aa10fd40308d08775b ]; then mark="ok  "; else mark=MISMATCH; fi
  echo "$mark S1 pack/FOUR-TIER-ARCHITECTURE.md sha256 $doctrine (SDE-DOCTRINE-003 v0.2.1, byte for byte)"
  leaks=$(grep -rlE 'OracleKit|module OracleT[0-9]|SUMMA_REPO' "$FIX/repo" "$FIX/pack" "$FIX/tasks" 2>/dev/null)
  if [ -z "$leaks" ]; then echo "ok   S2 no oracle or reference content in repo/, pack/ or tasks/"; else echo "MISMATCH S2 sealed content found in: $leaks"; fi
  missing=$( { jq -r '.rules | keys[]' "$POLICY"; jq -r '.[].rule' "$SEALED"/oracle/*/probes.json; echo ARC-TRC-01; } | sort -u | while read -r r; do grep -q "\*\*$r\.\*\*" "$FIX/pack/SUMMA-ARCHITECTURE.md" || echo "$r"; done)
  if [ -z "$missing" ]; then echo "ok   S3 every policy and probe rule is stated in pack/SUMMA-ARCHITECTURE.md (no secret rules)"; else echo "MISMATCH S3 not stated: $missing"; fi
  bad=0
  for t in $TASKS; do
    for f in $(jq -r '[.files.requirement, .files.followup] + .files.visibleTests + .files.followupVisibleTests | .[] | .source + "=" + .sha256' "$FIX/tasks/$t/task.json") \
             $(jq -r '[.contract, .followupContract] | .[] | .path + "=" + .sha256' "$FIX/tasks/$t/task.json") \
             $(jq -r '.files.oracle.initial, .files.oracle.followup, .files.oracle.manifest, .files.probes, .files.baseline | .path + "=" + .sha256' "$FIX/tasks/$t/task.json"); do
      p=${f%%=*}; h=${f##*=}; case $p in sealed:*) p="$SEALED/${p#sealed:}";; *) p="$FIX/$p";; esac
      [ "$(sha256sum "$p" | cut -c1-64)" = "$h" ] || { echo "MISMATCH S4 digest of $p"; bad=1; }
    done
  done
  [ $bad = 0 ] && echo "ok   S4 every file digest in task.json matches"
  before=$(cd "$FIX/tasks" && find . -name '*contract.json' -o -name task.json | sort | xargs sha256sum; cd "$SEALED/task-private" && sha256sum ./*.json)
  python3 -I "$FIX/make-contracts.py" "$FIX" "$ORDO" "$SEALED" > /dev/null
  after=$(cd "$FIX/tasks" && find . -name '*contract.json' -o -name task.json | sort | xargs sha256sum; cd "$SEALED/task-private" && sha256sum ./*.json)
  if [ "$before" = "$after" ]; then echo "ok   S5 make-contracts.py reproduces every contract.json, followup-contract.json, task.json and task-private/*.json"; else echo "MISMATCH S5 make-contracts.py output differs"; fi
  if [ -d "$CLONE/.git" ]; then
    "$FIX/make-snapshot.sh" "$CLONE" "$WORK/snapshot" > /dev/null 2>&1
    if diff -r "$WORK/snapshot" "$FIX/repo" > "$WORK/snapshot.diff" 2>&1; then echo "ok   S6 make-snapshot.sh reproduces repo/ from $(git -C "$CLONE" rev-parse --short HEAD) ($(find "$FIX/repo" -type f | wc -l) files, $(du -sh "$FIX/repo" | cut -f1))"
    else echo "MISMATCH S6 make-snapshot.sh output differs from repo/ ($(wc -l < "$WORK/snapshot.diff") diff lines)"; fi
  else echo "     S6 SKIP (no source clone at $CLONE)"; fi
  tick; d=$(repo base start-base); run_tests "$d"; expect "--" "start: builds and its own tests pass (whole solution)" PASS $? "$d.tests.log"
  tick; run_verifier "--" "$d" ""
  keys() { jq -r '[.findings[] | [.ruleId, .file, .symbol, (.scope // "")] | join("|")] | sort | .[]' "$1"; }
  if [ "$(keys "$d.git.report.json")" = "$(keys "$BASELINE")" ]; then mark=ok; else mark=MISMATCH; fi
  printf '%-3s %-56s %-9s (%s DET findings: %s) %s\n' "--" "start: archcheck reproduces the sealed baseline keys" "$mark" \
    "$(jq '[.findings[] | select(.class == "DET")] | length' "$BASELINE")" "$(jq -r '[.findings[] | select(.class == "DET") | .ruleId] | group_by(.) | map("\(.[0]) x\(length)") | join(", ")' "$BASELINE")" "$(took)"
  echo
} > "$STATIC" 2>&1
cat "$STATIC"

export -f overlay repo with_tests summary run_tests run_oracle run_verifier newsummary tick took expect vexpect ordo_expect check_task
export FIX SEALED ORDO WORK VERIFIER POLICY BASELINE
for t in $TASKS; do echo "$t"; done | xargs -P "$JOBS" -I{} bash -c 'check_task {} > "$WORK/{}.out" 2>&1'
for t in $TASKS; do cat "$WORK/$t.out"; echo; done

ALL=$(cat "$STATIC"; for t in $TASKS; do cat "$WORK/$t.out"; done)
FAILURES=$(echo "$ALL" | grep -cE 'MISMATCH')
CHECKS=$(echo "$ALL" | grep -cE '(^| )(ok|MISMATCH[A-Z0-9-]*)( |$)')
if [ "$FAILURES" -eq 0 ]; then echo "RESULT: PASS (every expectation held: $CHECKS checks)"; else echo "RESULT: FAIL ($FAILURES mismatches of $CHECKS checks)"; fi
[ -z "${CHECK_WORK:-}" ] && rm -rf "${WORK:?}"
exit $([ "$FAILURES" -eq 0 ] && echo 0 || echo 1)
