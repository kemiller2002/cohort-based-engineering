#!/usr/bin/env bash
# REL-001 run-02 fixture self-check. usage: fixtures/check.sh [> check-output.txt]
# For every task U1..U9 it proves, in fresh copies outside the fixture tree:
#   1. the starting repository (plus the task's start overlay) builds and its own tests pass;
#   2. the starting repository FAILS the task's visible acceptance tests;
#   3. the reference solution passes the visible tests AND the hidden oracle
#      (U2 has no reference: both forced "pick one rule" variants pass the visible
#      test and FAIL the oracle);
#   4. the U3 naive solution passes the visible tests and FAILS the oracle;
#   5. contract admission: Ordo 1.17.0 (and Praxis 3.16.0, when present) admit every
#      contract except U2's, which is refused with ORDO.CONTRACT.UNRESOLVED_CONFLICT;
#      the contract sha256 and Ordo digest match task.json.
# Exit status 0 only when every expectation holds.
set -uo pipefail
FIX="$(cd "$(dirname "$0")" && pwd)"
export PATH="/root/.dotnet:$PATH" DOTNET_ROOT=/root/.dotnet DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
ORDO="${REL001_ORDO:-/tmp/claude-0/rel001/bin/ordo-1.17.0/x/ordo-linux-x64/ordo}"
PRAXIS="${REL001_PRAXIS_C:-/tmp/claude-0/rel001/bin/praxis-3.16.0/x/praxis-linux-x64/praxis}"
WORK="${CHECK_WORK:-$(mktemp -d)}"; mkdir -p "$WORK"
TASKS="${CHECK_TASKS:-U1 U2 U3 U4 U5 U6 U7 U8 U9}"
FAILURES=0

# repo TASK NAME [OVERLAY...]: fresh copy of the starting repo, task start overlay, overlays, visible test.
repo() {
  local task="$1" name="$2"; shift 2
  local dir="$WORK/$task-$name"
  rm -rf "$dir"; cp -r "$FIX/repo" "$dir"
  [ -d "$FIX/tasks/$task/start-overlay" ] && cp -r "$FIX/tasks/$task/start-overlay/." "$dir/"
  for o in "$@"; do cp -r "$FIX/$o/." "$dir/"; done
  echo "$dir"
}
with_visible() { cp "$FIX/tasks/$1/$1AcceptanceTests.fs" "$2/tests/Ledger.Tests/Acceptance/"; }

# summary LOG: "passed P, failed F" or "build failed"
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
# expect LABEL EXPECTED(PASS|FAIL) RC LOG
expect() {
  local got; [ "$3" -eq 0 ] && got=PASS || got=FAIL
  local mark=ok; [ "$got" = "$2" ] || { mark=MISMATCH; FAILURES=$((FAILURES + 1)); }
  printf '%-4s %-40s expected %-4s got %-4s %-9s (%s)\n' "$TASK" "$1" "$2" "$got" "$mark" "$(summary "$4")"
}

echo "REL-001 run-02 fixture check"
echo "fixture tree digest: $(cd "$FIX" && find repo tasks oracle reference -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)"
echo "oracle digest:       $(cd "$FIX" && find oracle -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)"
echo "dotnet $(dotnet --version); ordo $(sha256sum "$ORDO" | cut -c1-16)…"
echo

for TASK in $TASKS; do
  # 1. starting repository alone
  d=$(repo "$TASK" start-base); run_tests "$d"; expect "start: own tests" PASS $? "$d.tests.log"
  # 2. starting repository + visible tests
  d=$(repo "$TASK" start); with_visible "$TASK" "$d"; run_tests "$d"; expect "start: visible tests" FAIL $? "$d.tests.log"
  # 3. reference (or U2 forced variants)
  if [ "$TASK" = U2 ]; then
    for v in forced-allow forced-final; do
      d=$(repo "$TASK" "$v" "reference/U2/$v"); with_visible "$TASK" "$d"
      run_tests "$d"; expect "$v: visible tests" PASS $? "$d.tests.log"
      run_oracle "$TASK" "$d"; expect "$v: oracle" FAIL $? "$d.oracle.log"
    done
  else
    d=$(repo "$TASK" reference "reference/$TASK"); with_visible "$TASK" "$d"
    run_tests "$d"; expect "reference: visible tests" PASS $? "$d.tests.log"
    run_oracle "$TASK" "$d"; expect "reference: oracle" PASS $? "$d.oracle.log"
  fi
  # 4. U3 naive trap
  if [ "$TASK" = U3 ]; then
    d=$(repo "$TASK" naive reference/U3-naive); with_visible "$TASK" "$d"
    run_tests "$d"; expect "naive: visible tests" PASS $? "$d.tests.log"
    run_oracle "$TASK" "$d"; expect "naive: oracle" FAIL $? "$d.oracle.log"
    grep -E '^\s+Failed OracleU3' "$d.oracle.log" | sed -E 's/^\s+Failed /       naive fails: /; s/ \[.*//'
  fi
  # 5. contract admission
  c="$FIX/tasks/$TASK/contract.json"; tj="$FIX/tasks/$TASK/task.json"
  want=$(jq -r '.contract.ordoAdmits' "$tj"); [ "$TASK" = U2 ] && exp=false || exp=true
  out=$("$ORDO" ecir check --blueprint "$c" --json); rc=$?
  got=$([ $rc -eq 0 ] && echo true || echo false)
  dig=$(echo "$out" | jq -r '.contractDigest // empty'); diag=$(echo "$out" | jq -r '[.diagnostics[]?.code] | join(",")')
  shaok=$([ "$(sha256sum "$c" | cut -d' ' -f1)" = "$(jq -r .contract.sha256 "$tj")" ] && echo yes || echo no)
  digok=$([ "$dig" = "$(jq -r '.contract.ordoContractDigest // empty' "$tj")" ] && echo yes || echo no)
  mark=ok; { [ "$got" = "$exp" ] && [ "$want" = "$exp" ] && [ $shaok = yes ] && [ $digok = yes ]; } || { mark=MISMATCH; FAILURES=$((FAILURES + 1)); }
  [ "$TASK" = U2 ] && { echo "$diag" | grep -q ORDO.CONTRACT.UNRESOLVED_CONFLICT || { mark=MISMATCH; FAILURES=$((FAILURES + 1)); }; }
  printf '%-4s %-40s expected %-5s got %-5s %-9s (sha256 %s, task.json sha/digest match %s/%s%s)\n' "$TASK" "ordo 1.17.0 admits contract" "$exp" "$got" "$mark" \
    "$(sha256sum "$c" | cut -c1-16)…" "$shaok" "$digok" "$([ -n "$dig" ] && echo ", digest ${dig:0:23}…" || echo ", $diag")"
  if [ -x "$PRAXIS" ]; then
    pout=$("$PRAXIS" ordo contract check --contract "$c" 2>&1); prc=$?
    pgot=$(echo "$pout" | grep -q '^Ordo contract admitted' && [ $prc -eq 0 ] && echo true || echo false)
    mark=ok; [ "$pgot" = "$exp" ] || { mark=MISMATCH; FAILURES=$((FAILURES + 1)); }
    printf '%-4s %-40s expected %-5s got %-5s %-9s (exit %s)\n' "$TASK" "praxis 3.16.0 admits contract" "$exp" "$pgot" "$mark" "$prc"
  fi
  echo
done

if [ "$FAILURES" -eq 0 ]; then echo "RESULT: PASS (every expectation held)"; else echo "RESULT: FAIL ($FAILURES mismatches)"; fi
[ -z "${CHECK_WORK:-}" ] && rm -rf "$WORK"
exit $([ "$FAILURES" -eq 0 ] && echo 0 || echo 1)
