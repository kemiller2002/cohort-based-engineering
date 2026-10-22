#!/usr/bin/env bash
# VAC-002 corpus self-check (harness only; reads the sealed store).
#   check.sh SEALED_DIR OUT_DIR
# For every pilot unit k: the reference after unit k (sealed ref repo, tag ref-Lk) builds, passes every repository test,
# passes the hidden oracle of every task 1..k and passes archcheck. Every trap passes the repository tests but fails the
# check it targets. The base fixture fails L01's oracle; the dependency update alone (before-L10) breaks L03/L09.
set -uo pipefail
SEALED="$1"; OUT="$2"; mkdir -p "$OUT"
FIXDIR="$(cd "$(dirname "$0")" && pwd)"
POLICY="${VAC2_ARCH_POLICY:-$FIXDIR/../../../architectural-correctness/verifier/policy/lending.policy.json}"
ARCHCHECK="${VAC2_ARCHCHECK:-/home/user/.vac2-tools/archcheck/archcheck.dll}"
export DOTNET_ROOT="${DOTNET_ROOT:-/root/.dotnet}" PATH="${DOTNET_ROOT:-/root/.dotnet}:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
TASKS=(L01 L02 L03 L04 L05 L06 L07 L08 L09 L10 L11 L12)
pass=0; fail=0
expect() {  # LABEL EXPECTED ACTUAL
  if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "ok   $1"; else fail=$((fail+1)); echo "FAIL $1 (expected $2, got $3)"; fi
}
tree_at() {  # REV -> $OUT/tree
  rm -rf "$OUT/tree"; git clone -q "$SEALED/ref" "$OUT/tree" && git -C "$OUT/tree" checkout -q "$1"
}
repo_tests() { ( cd "$OUT/tree" && dotnet test Lending.slnx > "$OUT/tests.log" 2>&1 ) && echo pass || echo fail; }
oracle() { [ "$("$SEALED/oracle/run.sh" "$OUT/tree" "$1" "$OUT/oracle")" = 0 ] && echo pass || echo fail; }
arch() { dotnet "$ARCHCHECK" verify --repo "$OUT/tree" --policy "$POLICY" > "$OUT/arch.log" 2>&1 && echo pass || echo fail; }

tree_at "$(git -C "$SEALED/ref" rev-list --max-parents=0 main)"
expect "base fixture: repository tests" pass "$(repo_tests)"
expect "base fixture: L01 oracle fails" fail "$(oracle L01)"
for k in $(seq 1 ${#TASKS[@]}); do
  t=${TASKS[$((k-1))]}; tree_at "ref-$t"
  expect "ref-$t: repository tests" pass "$(repo_tests)"
  expect "ref-$t: archcheck" pass "$(arch)"
  for j in $(seq 1 "$k"); do s=${TASKS[$((j-1))]}; expect "ref-$t: oracle $s" pass "$(oracle "$s")"; done
done
tree_at before-L10
expect "before-L10 (OpenDays 2.0.0, no adaptation): repository tests fail" fail "$(repo_tests)"
expect "before-L10: L09 oracle fails" fail "$(oracle L09)"
# trap | targeted check | expected verdict of that check
while read -r trap check target; do
  [ -z "$trap" ] && continue
  tree_at "$trap"
  expect "$trap: repository tests" pass "$(repo_tests)"
  case "$check" in
    oracle) expect "$trap: oracle $target fails" fail "$(oracle "$target")";;
    arch) expect "$trap: archcheck fails" fail "$(arch)"; expect "$trap: oracle $target" pass "$(oracle "$target")";;
  esac
done <<'TRAPS'
trap-L01-no-persist oracle L01
trap-L02-cli arch L02
trap-L05-F1-newest-first oracle L05
trap-L06-F2-outstanding-unchanged oracle L06
trap-L10-stale-nextOpen oracle L10
trap-L12-stale-renewal oracle L12
TRAPS
echo "RESULT: $([ $fail -eq 0 ] && echo PASS || echo FAIL) ($pass passed, $fail failed)"
