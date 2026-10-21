#!/usr/bin/env bash
# REL-001 run-03 fixture self-check (needs the .NET 10 SDK; adapted from run-02/fixtures/check.sh).
#   usage: fixtures/check.sh [> check-output.txt]      CHECK_TASKS="V3 V5" limits the tasks
# For every task V1..V8 it proves, in fresh copies outside the fixture tree:
#   1. the starting repository builds and its own tests pass;
#   2. the starting repository FAILS the task's visible acceptance tests (they do not compile);
#   3. the reference solution passes the visible tests AND the hidden oracle
#      (V7 has no reference: both forced "pick one rule" variants pass the visible test and FAIL the oracle);
#   4. every plausible wrong solution reference/V<n>-<variant> (overlaid on the reference) passes the
#      visible tests and FAILS the oracle, and the failing oracle tests are listed;
#   5. with REL003_ORDO set: the pinned Ordo admits every contract except V7's, which it refuses with
#      ORDO.CONTRACT.UNRESOLVED_CONFLICT (skipped, and reported as skipped, without it).
# The static checks (python3 -I check-static.py) run first. Exit status 0 only when every expectation holds.
set -uo pipefail
FIX="$(cd "$(dirname "$0")" && pwd)"
export PATH="${REL003_DOTNET_ROOT:-/root/.dotnet}:$PATH" DOTNET_ROOT="${REL003_DOTNET_ROOT:-/root/.dotnet}" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
ORDO="${REL003_ORDO:-}"
WORK="${CHECK_WORK:-$(mktemp -d)}"; mkdir -p "$WORK"
TASKS="${CHECK_TASKS:-V1 V2 V3 V4 V5 V6 V7 V8}"
FAILURES=0
command -v dotnet >/dev/null || { echo "BLOCKED: dotnet not found (set REL003_DOTNET_ROOT)"; exit 3; }

repo() {
  local task="$1" name="$2"; shift 2
  local dir="$WORK/$task-$name"
  rm -rf "$dir"; cp -r "$FIX/repo" "$dir"
  for o in "$@"; do cp -r "$FIX/$o/." "$dir/"; done
  echo "$dir"
}
with_visible() { cp "$FIX/tasks/$1/$1AcceptanceTests.fs" "$2/tests/Ledger.Tests/Acceptance/"; }
summary() {
  local line; line=$(grep -E '^(Passed|Failed)! ' "$1" | tail -1)
  if [ -n "$line" ]; then echo "$line" | sed -E 's/.*Failed: +([0-9]+), Passed: +([0-9]+).*/passed \2, failed \1/'
  else echo "build failed ($(grep -cE ' error FS[0-9]+' "$1") compiler errors)"; fi
}
run_tests() { (cd "$1" && dotnet test Ledger.slnx > "$1.tests.log" 2>&1); }
run_oracle() {
  local task="$1" dir="$2" od="$2.oracle"
  rm -rf "$od"; mkdir -p "$od"
  sed "s#LEDGER_PROJECT_PATH#$dir/src/Ledger/Ledger.fsproj#" "$FIX/oracle/Oracle.fsproj" > "$od/Oracle.fsproj"
  cp "$FIX/oracle/$task/OracleTests.fs" "$od/OracleTests.fs"
  (cd "$od" && dotnet test > "$od.log" 2>&1)
}
# expect LABEL EXPECTED(PASS|FAIL) RC LOG [BUILD_REQUIRED]: a FAIL that is a build failure counts only when allowed.
expect() {
  local got; [ "$3" -eq 0 ] && got=PASS || got=FAIL
  local mark=ok; [ "$got" = "$2" ] || { mark=MISMATCH; FAILURES=$((FAILURES + 1)); }
  if [ "$got" = FAIL ] && [ "${5:-}" = built ] && ! grep -qE '^(Passed|Failed)! ' "$4"; then mark=MISMATCH-NOT-BUILT; FAILURES=$((FAILURES + 1)); fi
  printf '%-4s %-44s expected %-4s got %-4s %-9s (%s)\n' "$TASK" "$1" "$2" "$got" "$mark" "$(summary "$4")"
}

echo "REL-001 run-03 fixture check"
python3 -I "$FIX/check-static.py" "$FIX" || FAILURES=$((FAILURES + 1))
echo "dotnet $(dotnet --version); ordo ${ORDO:+$(sha256sum "$ORDO" | cut -c1-16)…}${ORDO:-not given (contract admission skipped)}"
echo

for TASK in $TASKS; do
  d=$(repo "$TASK" start-base); run_tests "$d"; expect "start: own tests" PASS $? "$d.tests.log"
  d=$(repo "$TASK" start); with_visible "$TASK" "$d"; run_tests "$d"; expect "start: visible tests" FAIL $? "$d.tests.log"
  if [ "$TASK" = V7 ]; then
    for v in forced-noop forced-refuse; do
      d=$(repo "$TASK" "$v" "reference/V7/$v"); with_visible "$TASK" "$d"
      run_tests "$d"; expect "$v: visible tests" PASS $? "$d.tests.log"
      run_oracle "$TASK" "$d"; expect "$v: oracle" FAIL $? "$d.oracle.log" built
      grep -E "^\s+Failed OracleV7" "$d.oracle.log" | sed -E "s/^\s+Failed /       $v fails: /; s/ \[.*//" | sort
    done
  else
    d=$(repo "$TASK" reference "reference/$TASK"); with_visible "$TASK" "$d"
    run_tests "$d"; expect "reference: visible tests" PASS $? "$d.tests.log"
    run_oracle "$TASK" "$d"; expect "reference: oracle" PASS $? "$d.oracle.log"
  fi
  for vdir in "$FIX"/reference/"$TASK"-*/; do
    [ -d "$vdir" ] || continue
    v=$(basename "$vdir"); v=${v#"$TASK"-}
    d=$(repo "$TASK" "$v" "reference/$TASK" "reference/$TASK-$v"); with_visible "$TASK" "$d"
    run_tests "$d"; expect "wrong ($v): visible tests" PASS $? "$d.tests.log"
    run_oracle "$TASK" "$d"; expect "wrong ($v): oracle" FAIL $? "$d.oracle.log" built
    grep -E "^\s+Failed Oracle$TASK" "$d.oracle.log" | sed -E "s/^\s+Failed /       $v fails: /; s/ \[.*//" | sort
  done
  if [ -n "$ORDO" ]; then
    c="$FIX/tasks/$TASK/contract.json"; [ "$TASK" = V7 ] && exp=false || exp=true
    out=$("$ORDO" ecir check --blueprint "$c" --json); rc=$?
    got=$([ $rc -eq 0 ] && echo true || echo false); diag=$(echo "$out" | jq -r '[.diagnostics[]?.code] | join(",")')
    mark=ok; [ "$got" = "$exp" ] || { mark=MISMATCH; FAILURES=$((FAILURES + 1)); }
    [ "$TASK" = V7 ] && { echo "$diag" | grep -q ORDO.CONTRACT.UNRESOLVED_CONFLICT || { mark=MISMATCH; FAILURES=$((FAILURES + 1)); }; }
    printf '%-4s %-44s expected %-5s got %-5s %-9s (%s)\n' "$TASK" "ordo admits contract" "$exp" "$got" "$mark" "${diag:-$(echo "$out" | jq -r '.contractDigest // empty' | cut -c1-23)}"
  else
    printf '%-4s %-44s SKIPPED (REL003_ORDO not set)\n' "$TASK" "ordo admits contract"
  fi
  echo
done

if [ "$FAILURES" -eq 0 ]; then echo "RESULT: PASS (every expectation held)"; else echo "RESULT: FAIL ($FAILURES mismatches)"; fi
[ -z "${CHECK_WORK:-}" ] && rm -rf "$WORK"
exit $([ "$FAILURES" -eq 0 ] && echo 0 || echo 1)
