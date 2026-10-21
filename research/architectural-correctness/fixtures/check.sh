#!/usr/bin/env bash
# ARCH-001 fixture self-check (Workstream B). Adapted from REL-001 run-03 fixtures/check.sh.
#   usage: fixtures/check.sh [> check-output.txt]
#   env:   ARCH001_SEALED  sealed oracle/reference directory (default /home/user/arch001-sealed)
#          ARCH001_ORDO    ordo binary (default /home/user/.tools/ordo/ordo-linux-x64/ordo)
#          ARCH001_DOTNET_ROOT (default /home/user/.tools/dotnet)
#          CHECK_TASKS="T1 T5" limits the tasks; CHECK_JOBS=N runs N tasks in parallel (default 4)
#          CHECK_WORK=DIR keeps the work directory
#
# Static checks first (pack hash, no sealed content in the public tree, task.json digests,
# make-contracts.py reproduces the contracts). Then, for every task, in fresh copies outside the fixture tree:
#   1. the starting repository builds and its own tests pass (once);
#   2. the starting repository FAILS the task's visible acceptance tests and its hidden initial oracle;
#   3. good:  visible + oracle pass; archcheck (policy + task probes) passes;
#   4. trap:  visible + oracle pass (functionally correct); archcheck FAILS (exit 1);
#      T5 conflict: visible pass, oracle FAILS on the DEC-006 tests;
#   5. follow-up: good FAILS the follow-up visible tests and follow-up oracle; followup-good (over good)
#      passes visible (initial + follow-up) and the follow-up oracle, and archcheck passes;
#   6. ordo admits every contract except T5's initial one, which it refuses with ORDO.CONTRACT.UNRESOLVED_CONFLICT.
# archcheck steps print SKIP when the verifier (../verifier) is not available. Exit 0 only when every expectation holds.
set -uo pipefail
FIX="$(cd "$(dirname "$0")" && pwd)"
EXP="$(dirname "$FIX")"
SEALED="${ARCH001_SEALED:-/home/user/arch001-sealed}"
ORDO="${ARCH001_ORDO:-/home/user/.tools/ordo/ordo-linux-x64/ordo}"
export DOTNET_ROOT="${ARCH001_DOTNET_ROOT:-/home/user/.tools/dotnet}"
export PATH="$DOTNET_ROOT:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 MSBUILDDISABLENODEREUSE=1
WORK="${CHECK_WORK:-$(mktemp -d)}"; mkdir -p "$WORK"
TASKS="${CHECK_TASKS:-T1 T2 T3 T4 T5 T6 T7 T8}"
JOBS="${CHECK_JOBS:-4}"
command -v dotnet >/dev/null || { echo "BLOCKED: dotnet not found (set ARCH001_DOTNET_ROOT)"; exit 3; }
[ -d "$SEALED/oracle" ] || { echo "BLOCKED: sealed directory $SEALED not found (set ARCH001_SEALED)"; exit 3; }

# ---- verifier ------------------------------------------------------------------------------------------
VERIFIER=""
POLICY="$FIX/policy/lending.policy.json"; [ -f "$POLICY" ] || POLICY="$EXP/verifier/policy/lending.policy.json"
if [ -f "$EXP/verifier/dist/archcheck.dll" ]; then
  VERIFIER="$EXP/verifier/dist/archcheck.dll"
elif [ -f "$EXP/verifier/src/Archcheck/Archcheck.fsproj" ] &&
     (cd "$EXP/verifier" && dotnet publish src/Archcheck/Archcheck.fsproj -c Release -o "$WORK/archcheck" >"$WORK/archcheck-build.log" 2>&1); then
  VERIFIER="$WORK/archcheck/archcheck.dll"
fi
[ -f "$POLICY" ] || VERIFIER=""

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
with_tests() { local d="$1"; shift; for s in "$@"; do cp "$FIX/tasks/$s/"*.fs "$d/tests/Lending.Tests/Acceptance/"; done; }
summary() {
  local line; line=$(grep -E '^(Passed|Failed)! ' "$1" | tail -1)
  if [ -n "$line" ]; then echo "$line" | sed -E 's/.*Failed: +([0-9]+), Passed: +([0-9]+).*/passed \2, failed \1/'
  else echo "build failed ($(grep -oE ' error FS[0-9]+' "$1" | sort -u | wc -l) distinct compiler errors)"; fi
}
run_tests() { (cd "$1" && dotnet test Lending.slnx > "$1.tests.log" 2>&1); }
run_oracle() {  # run_oracle TASK KIND DIR
  local od="$3.oracle-$2"
  rm -rf "${od:?}"; mkdir -p "$od"
  sed "s#LENDING_HOST_PROJECT_PATH#$3/src/Lending.Host/Lending.Host.fsproj#" "$SEALED/oracle/Oracle.fsproj" > "$od/Oracle.fsproj"
  cp "$SEALED/oracle/OracleKit.fs" "$od/"; cp "$SEALED/oracle/$1/${2}OracleTests.fs" "$od/OracleTests.fs"
  (cd "$od" && dotnet test > "$od.log" 2>&1)
}
run_verifier() {  # run_verifier TASK DIR CONTRACT: archcheck on a committed copy of DIR (sources only)
  local vd="$2.git"
  rm -rf "${vd:?}"; mkdir -p "$vd"
  (cd "$2" && tar --exclude=bin --exclude=obj --exclude=TestResults -cf - .) | (cd "$vd" && tar -xf -)
  (cd "$vd" && git init -q && git add -A && git -c user.email=fixture@arch001 -c user.name=fixture commit -qm fixture)
  local probes=(); [ -f "$SEALED/oracle/$1/probes.json" ] && probes=(--probes "$SEALED/oracle/$1/probes.json")
  dotnet "$VERIFIER" verify --repo "$vd" --policy "$POLICY" "${probes[@]}" --contract "$3" --out "$vd.report.json" > "$vd.log" 2>&1
}
vsummary() { tail -1 "$1" | sed -E 's/^summary: //'; }
# expect TASK LABEL EXPECTED(PASS|FAIL) RC LOG [built]: a FAIL that is a build failure counts only when allowed.
expect() {
  local got; [ "$4" -eq 0 ] && got=PASS || got=FAIL
  local mark=ok; [ "$got" = "$3" ] || mark=MISMATCH
  if [ "$got" = FAIL ] && [ "${6:-}" = built ] && ! grep -qE '^(Passed|Failed)! ' "$5"; then mark=MISMATCH-NOT-BUILT; fi
  printf '%-3s %-50s expected %-4s got %-4s %-9s (%s)\n' "$1" "$2" "$3" "$got" "$mark" "$(summary "$5")"
}
vexpect() {     # vexpect TASK LABEL EXPECTED(PASS|FAIL) DIR CONTRACT
  if [ -z "$VERIFIER" ]; then printf '%-3s %-50s SKIP (verifier not available)\n' "$1" "$2"; return; fi
  run_verifier "$1" "$4" "$5"; local rc=$?
  local got mark=ok; case $rc in 0) got=PASS;; 1) got=FAIL;; *) got="ERR$rc";; esac
  [ "$got" = "$3" ] || mark=MISMATCH
  printf '%-3s %-50s expected %-4s got %-4s %-9s (%s)\n' "$1" "$2" "$3" "$got" "$mark" "$(vsummary "$4.git.log")"
  if [ "$3" = FAIL ]; then
    echo "       DET findings: $(grep -E '^ARC-(DEP|SYM|BND)' "$4.git.log" | awk '{print $1}' | sort | uniq -c | awk '{printf "%s x%s  ", $2, $1}')"
  fi
}
ordo_expect() {  # ordo_expect TASK FILE EXPECTED(true|false) LABEL
  local out rc got diag mark=ok
  out=$("$ORDO" ecir check --blueprint "$2" --json 2>/dev/null); rc=$?
  got=$([ $rc -eq 0 ] && echo true || echo false)
  diag=$(echo "$out" | jq -r '[.diagnostics[]?.code] | join(",")')
  [ "$got" = "$3" ] || mark=MISMATCH
  [ "$3" = false ] && { echo "$diag" | grep -q ORDO.CONTRACT.UNRESOLVED_CONFLICT || mark=MISMATCH; }
  printf '%-3s %-50s expected %-5s got %-5s %-8s (%s)\n' "$1" "$4" "$3" "$got" "$mark" "${diag:-$(echo "$out" | jq -r '.contractDigest // empty' | cut -c1-23)}"
}

check_task() {
  local T="$1" d rc
  local C="$FIX/tasks/$T/contract.json" FC="$FIX/tasks/$T/followup-contract.json"
  local traps; traps=$(jq -r '.files.reference | keys[]' "$FIX/tasks/$T/task.json")
  d=$(repo "$T" start); with_tests "$d" "$T/acceptance"; run_tests "$d"; expect "$T" "start: visible tests" FAIL $? "$d.tests.log"
  run_oracle "$T" Initial "$d"; expect "$T" "start: initial oracle" FAIL $? "$d.oracle-Initial.log"

  d=$(repo "$T" good "$T/good"); with_tests "$d" "$T/acceptance"
  run_tests "$d"; expect "$T" "good: visible tests" PASS $? "$d.tests.log"
  run_oracle "$T" Initial "$d"; expect "$T" "good: initial oracle" PASS $? "$d.oracle-Initial.log"
  vexpect "$T" "good: archcheck (policy + probes)" PASS "$d" "$C"
  run_oracle "$T" Followup "$d"; expect "$T" "good: follow-up oracle (not yet solved)" FAIL $? "$d.oracle-Followup.log"
  d=$(repo "$T" good-fvisible "$T/good"); with_tests "$d" "$T/acceptance" "$T/followup-acceptance"
  run_tests "$d"; expect "$T" "good: follow-up visible tests (not yet solved)" FAIL $? "$d.tests.log"

  if echo "$traps" | grep -qx trap; then
    d=$(repo "$T" trap "$T/trap"); with_tests "$d" "$T/acceptance"
    run_tests "$d"; expect "$T" "trap: visible tests" PASS $? "$d.tests.log"
    run_oracle "$T" Initial "$d"; expect "$T" "trap: initial oracle (functionally correct)" PASS $? "$d.oracle-Initial.log"
    vexpect "$T" "trap: archcheck (policy + probes)" FAIL "$d" "$C"
  else
    printf '%-3s %-50s none (control task)\n' "$T" "trap"
  fi
  if echo "$traps" | grep -qx conflict; then
    d=$(repo "$T" conflict "$T/conflict"); with_tests "$d" "$T/acceptance"
    run_tests "$d"; expect "$T" "conflict: visible tests" PASS $? "$d.tests.log"
    run_oracle "$T" Initial "$d"; expect "$T" "conflict: initial oracle (DEC-006 preserved)" FAIL $? "$d.oracle-Initial.log" built
    grep -E "^\s+Failed Oracle" "$d.oracle-Initial.log" | sed -E "s/^\s+Failed /       fails: /; s/ \[.*//" | sort
  fi

  d=$(repo "$T" followup "$T/good" "$T/followup-good")
  if [ "$T" = T8 ]; then with_tests "$d" "$T/followup-acceptance"; else with_tests "$d" "$T/acceptance" "$T/followup-acceptance"; fi
  run_tests "$d"; expect "$T" "followup-good: visible tests" PASS $? "$d.tests.log"
  run_oracle "$T" Followup "$d"; expect "$T" "followup-good: follow-up oracle" PASS $? "$d.oracle-Followup.log"
  vexpect "$T" "followup-good: archcheck (policy + probes)" PASS "$d" "$FC"
  if [ "$T" = T2 ]; then
    local touched; touched=$(cd "$SEALED/reference/T2/followup-good" && find . -type f | grep -E '^\./src/Lending\.(Semantic|Transition|Application)/' || true)
    local mark=ok; [ -z "$touched" ] || mark=MISMATCH
    printf '%-3s %-50s expected none  got %-5s %-8s\n' "$T" "followup-good: touches no Tier 1-3 file" "$([ -z "$touched" ] && echo none || echo some)" "$mark"
  fi

  ordo_expect "$T" "$C" "$([ "$T" = T5 ] && echo false || echo true)" "ordo admits contract.json"
  ordo_expect "$T" "$FC" true "ordo admits followup-contract.json"
}

# ---- static checks ---------------------------------------------------------------------------------------
STATIC="$WORK/static.out"
{
  echo "ARCH-001 fixture check"
  echo "fixture tree: $(cd "$FIX" && find repo pack tasks make-contracts.py -type f -not -path '*/bin/*' -not -path '*/obj/*' | sort | xargs sha256sum | sha256sum | cut -c1-64)"
  echo "sealed tree:  $(cd "$SEALED" && find oracle reference -type f | sort | xargs sha256sum | sha256sum | cut -c1-64)"
  echo "dotnet $(dotnet --version); ordo $(sha256sum "$ORDO" | cut -c1-16)…; archcheck ${VERIFIER:+$(sha256sum "$VERIFIER" | cut -c1-16)…}${VERIFIER:-not available}; policy ${POLICY#$EXP/}"
  doctrine=$(sha256sum "$FIX/pack/FOUR-TIER-ARCHITECTURE.md" | cut -c1-64)
  if [ "$doctrine" = 725cb3d97b56142a4de07ea6cbbdafbbb421735b79e375aa10fd40308d08775b ]; then mark="ok  "; else mark=MISMATCH; fi
  echo "$mark S1 pack/FOUR-TIER-ARCHITECTURE.md sha256 $doctrine (SDE-DOCTRINE-003 v0.2.1, ordo bb43c26)"
  leaks=$(grep -rlE 'OracleKit|module OracleT[0-9]|LENDING_HOST_PROJECT_PATH' "$FIX/repo" "$FIX/pack" "$FIX/tasks" 2>/dev/null)
  if [ -z "$leaks" ]; then echo "ok   S2 no oracle or reference content in repo/, pack/ or tasks/"; else echo "MISMATCH S2 sealed content found in: $leaks"; fi
  bad=0
  for t in $TASKS; do
    for f in $(jq -r '[.files.requirement, .files.followup] + .files.visibleTests + .files.followupVisibleTests | .[] | .source + "=" + .sha256' "$FIX/tasks/$t/task.json") \
             $(jq -r '[.contract, .followupContract] | .[] | .path + "=" + .sha256' "$FIX/tasks/$t/task.json") \
             $(jq -r '.files.oracle.initial, .files.oracle.followup, .files.probes | .path + "=" + .sha256' "$FIX/tasks/$t/task.json"); do
      p=${f%%=*}; h=${f##*=}; case $p in sealed:*) p="$SEALED/${p#sealed:}";; *) p="$FIX/$p";; esac
      [ "$(sha256sum "$p" | cut -c1-64)" = "$h" ] || { echo "MISMATCH S3 digest of $p"; bad=1; }
    done
  done
  [ $bad = 0 ] && echo "ok   S3 every file digest in task.json matches"
  before=$(cd "$FIX/tasks" && find . -name '*contract.json' -o -name task.json | sort | xargs sha256sum)
  python3 -I "$FIX/make-contracts.py" "$FIX" "$ORDO" "$SEALED" > /dev/null
  after=$(cd "$FIX/tasks" && find . -name '*contract.json' -o -name task.json | sort | xargs sha256sum)
  if [ "$before" = "$after" ]; then echo "ok   S4 make-contracts.py reproduces every contract.json, followup-contract.json and task.json"; else echo "MISMATCH S4 make-contracts.py output differs"; fi
  d=$(repo base start-base); run_tests "$d"; expect "--" "start: builds and its own tests pass" PASS $? "$d.tests.log"
  vexpect "--" "start: archcheck (policy only)" PASS "$d" "$FIX/tasks/T1/contract.json"
  echo
} > "$STATIC" 2>&1
cat "$STATIC"

export -f overlay repo with_tests summary run_tests run_oracle run_verifier vsummary expect vexpect ordo_expect check_task
export FIX EXP SEALED ORDO WORK VERIFIER POLICY
for t in $TASKS; do echo "$t"; done | xargs -P "$JOBS" -I{} bash -c 'check_task {} > "$WORK/{}.out" 2>&1'
for t in $TASKS; do cat "$WORK/$t.out"; echo; done

ALL=$(cat "$STATIC"; for t in $TASKS; do cat "$WORK/$t.out"; done)
FAILURES=$(echo "$ALL" | grep -cE 'MISMATCH')
CHECKS=$(echo "$ALL" | grep -cE '(^| )(ok|MISMATCH[A-Z-]*)( |$)')
SKIPS=$(echo "$ALL" | grep -c ' SKIP ')
if [ "$FAILURES" -eq 0 ]; then echo "RESULT: PASS (every expectation held: $CHECKS checks, $SKIPS skipped)"; else echo "RESULT: FAIL ($FAILURES mismatches of $CHECKS checks)"; fi
[ -z "${CHECK_WORK:-}" ] && rm -rf "${WORK:?}"
exit $([ "$FAILURES" -eq 0 ] && echo 0 || echo 1)
