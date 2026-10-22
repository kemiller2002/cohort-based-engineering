#!/usr/bin/env bash
# ARCH-002 fixture F1 (lending-brownfield) self-check. Adapted from ARCH-001 fixtures/check.sh.
#   usage: arch-002/fixtures/lending-brownfield/check.sh [> check-output.txt]
#   env:   ARCH002_SEALED   sealed directory (default /home/user/arch002-sealed/lending-brownfield)
#          ARCH002_ORDO     ordo binary (default /home/user/.tools/ordo/ordo-linux-x64/ordo)
#          ARCH002_VERIFIER archcheck.dll (default: the ARCH-001 verifier, verifier/dist/archcheck.dll)
#          ARCH002_DOTNET_ROOT (default /home/user/.tools/dotnet)
#          CHECK_TASKS="T1 T5" limits the tasks; CHECK_JOBS=N runs N tasks in parallel (default 3)
#          CHECK_WORK=DIR keeps the work directory
#
# Brownfield scoring is relative to the start commit (INTERFACES.md §3): a NEW violation is a DET finding of
# severity >= 2 whose key (ruleId, file, symbol) is not in the start commit's report, compared as multisets
# (line numbers ignored). Until the verifier's --baseline lands, this script computes the difference itself.
#
# Static checks: pack doctrine hash; no sealed content in the public tree; task.json digests; make-contracts.py
# reproduces the contracts and task.json; the start repository builds and its own tests pass; the start
# commit's findings (policy only) equal sealed seeded.json (DET entries exactly; HEU entries too).
# Then, for every task, in fresh copies outside the fixture tree:
#   1. start FAILS the visible acceptance tests and the hidden initial oracle (it builds);
#   2. good: visible + initial oracle pass; 0 new DET sev>=2 findings vs start (policy + task probes);
#      good FAILS the follow-up visible tests and the follow-up oracle;
#   3. trap (when the task has one): visible + initial oracle pass; >= 1 new DET sev>=2 finding vs start;
#   4. conflict (T5): visible pass; the initial oracle fails, and exactly the oracle.json conflictTests fail;
#   5. followup-good (over good): visible (initial + follow-up) and follow-up oracle pass; every test in
#      oracle.json `regression` passes and the passing initial-oracle tests are exactly that list; 0 new DET
#      sev>=2 findings vs start;
#   6. ordo admits every contract except a contract with a conflict node, which it refuses with
#      ORDO.CONTRACT.UNRESOLVED_CONFLICT.
# Exit 0 only when every expectation holds.
set -uo pipefail
FIX="$(cd "$(dirname "$0")" && pwd)"
EXP="$(cd "$FIX/../../.." && pwd)"
SEALED="${ARCH002_SEALED:-/home/user/arch002-sealed/lending-brownfield}"
ORDO="${ARCH002_ORDO:-/home/user/.tools/ordo/ordo-linux-x64/ordo}"
VERIFIER="${ARCH002_VERIFIER:-$EXP/verifier/dist/archcheck.dll}"
POLICY="$FIX/policy.json"
export DOTNET_ROOT="${ARCH002_DOTNET_ROOT:-/home/user/.tools/dotnet}"
export PATH="$DOTNET_ROOT:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 MSBUILDDISABLENODEREUSE=1
WORK="${CHECK_WORK:-$(mktemp -d)}"; mkdir -p "$WORK"
TASKS="${CHECK_TASKS:-T1 T2 T3 T4 T5 T6}"
JOBS="${CHECK_JOBS:-3}"
command -v dotnet >/dev/null || { echo "BLOCKED: dotnet not found (set ARCH002_DOTNET_ROOT)"; exit 3; }
[ -d "$SEALED/oracle" ] || { echo "BLOCKED: sealed directory $SEALED not found (set ARCH002_SEALED)"; exit 3; }
[ -f "$VERIFIER" ] || { echo "BLOCKED: verifier $VERIFIER not found (set ARCH002_VERIFIER)"; exit 3; }

# ---- helpers (each task runs in its own process; results go to $WORK/<task>.out) ----------------------
overlay() {   # overlay DIR SRC: copy SRC over DIR and remove the paths SRC/.delete lists
  cp -r "$2/." "$1/"
  if [ -f "$2/.delete" ]; then while read -r f; do rm -f "${1:?}/$f"; done < "$2/.delete"; rm -f "${1:?}/.delete"; fi
}
repo() {      # repo TASK NAME [OVERLAY...]: a fresh copy of the start repository with overlays applied
  local dir="$WORK/$1-$2"; shift 2
  rm -rf "${dir:?}"; mkdir -p "$dir"
  (cd "$FIX/repo" && tar --exclude=bin --exclude=obj -cf - .) | (cd "$dir" && tar -xf -)
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
run_oracle() {  # run_oracle TASK KIND DIR: writes DIR.oracle-KIND.log and DIR.oracle-KIND.trx
  local od="$3.oracle-$2"
  rm -rf "${od:?}"; mkdir -p "$od"
  sed "s#LENDING_HOST_PROJECT_PATH#$3/src/Lending.Host/Lending.Host.fsproj#" "$SEALED/oracle/Oracle.fsproj" > "$od/Oracle.fsproj"
  cp "$SEALED/oracle/OracleKit.fs" "$od/"; cp "$SEALED/oracle/$1/${2}OracleTests.fs" "$od/OracleTests.fs"
  (cd "$od" && dotnet test --logger "trx;LogFileName=r.trx" --results-directory "$od/tr" > "$od.log" 2>&1); local rc=$?
  cp "$od/tr/r.trx" "$od.trx" 2>/dev/null
  return $rc
}
outcomes() {    # outcomes TRX: "<Passed|Failed>\t<test name>" per oracle test
  python3 -I - "$1" <<'PY'
import sys, xml.etree.ElementTree as ET
ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
try: rs = ET.parse(sys.argv[1]).getroot().findall(".//t:UnitTestResult", ns)
except Exception: rs = []
for r in rs: print(r.get("outcome"), r.get("testName").split(".", 1)[1], sep="\t")
PY
}
run_verifier() {  # run_verifier TASK DIR CONTRACT|- [noprobes]: archcheck on a committed copy of DIR -> DIR.report.json
  local vd="$2.git"
  rm -rf "${vd:?}"; mkdir -p "$vd"
  (cd "$2" && tar --exclude=bin --exclude=obj --exclude=TestResults -cf - .) | (cd "$vd" && tar -xf -)
  (cd "$vd" && git init -q && git add -A && git -c user.email=fixture@arch002 -c user.name=fixture commit -qm fixture)
  local probes=(); [ "${4:-}" != noprobes ] && [ -f "$SEALED/oracle/$1/probes.json" ] && probes=(--probes "$SEALED/oracle/$1/probes.json")
  local contract=(); [ "$3" != - ] && contract=(--contract "$3")
  dotnet "$VERIFIER" verify --repo "$vd" --policy "$POLICY" "${probes[@]}" "${contract[@]}" --out "$2.report.json" > "$vd.log" 2>&1
}
newdet() {      # newdet REPORT BASELINE: prints "<new> <fixed> <summary of new keys>"; exit 2 when a report is missing
  python3 -I - "$1" "$2" <<'PY'
import collections, json, sys
try: r, b = (json.load(open(p)) for p in sys.argv[1:3])
except Exception: print("ERR ERR report missing"); sys.exit(2)
if not r.get("buildOk", True) or r.get("errors"): print("ERR ERR not evaluated"); sys.exit(2)
det = lambda rep: collections.Counter((f["ruleId"], f["file"], f["symbol"]) for f in rep["findings"] if f["class"] == "DET" and f["severity"] >= 2)
new, fixed = det(r) - det(b), det(b) - det(r)
rules = collections.Counter(k[0] for k in new.elements())
print(sum(new.values()), sum(fixed.values()), " ".join(f"{k} x{v}" for k, v in sorted(rules.items())) or "-")
PY
}
# expect TASK LABEL EXPECTED(PASS|FAIL) RC LOG [built]: a FAIL that is a build failure counts only when allowed.
expect() {
  local got; [ "$4" -eq 0 ] && got=PASS || got=FAIL
  local mark=ok; [ "$got" = "$3" ] || mark=MISMATCH
  if [ "$got" = FAIL ] && [ "${6:-}" = built ] && ! grep -qE '^(Passed|Failed)! ' "$5"; then mark=MISMATCH-NOT-BUILT; fi
  printf '%-3s %-56s expected %-4s got %-4s %-9s (%s)\n' "$1" "$2" "$3" "$got" "$mark" "$(summary "$5")"
}
dexpect() {     # dexpect TASK LABEL WANT(zero|some) DIR BASEREPORT CONTRACT: new DET sev>=2 findings vs start
  run_verifier "$1" "$4" "$6"
  local out new fixed rest got mark=ok
  out=$(newdet "$4.report.json" "$5"); read -r new fixed rest <<< "$out"
  if [ "$new" = ERR ]; then got=ERR; mark=MISMATCH
  elif [ "$new" -eq 0 ]; then got=zero; else got=some; fi
  [ "$got" = "$3" ] || mark=MISMATCH
  printf '%-3s %-56s expected %-4s got %-4s %-9s (new %s, fixed %s; %s)\n' "$1" "$2" "$3" "$got" "$mark" "$new" "$fixed" "$rest"
}
ordo_expect() {  # ordo_expect TASK FILE EXPECTED(true|false) LABEL
  local out rc got diag mark=ok
  out=$("$ORDO" ecir check --blueprint "$2" --json 2>/dev/null); rc=$?
  got=$([ $rc -eq 0 ] && echo true || echo false)
  diag=$(echo "$out" | jq -r '[.diagnostics[]?.code] | join(",")')
  [ "$got" = "$3" ] || mark=MISMATCH
  [ "$3" = false ] && { echo "$diag" | grep -q ORDO.CONTRACT.UNRESOLVED_CONFLICT || mark=MISMATCH; }
  printf '%-3s %-56s expected %-5s got %-5s %-8s (%s)\n' "$1" "$4" "$3" "$got" "$mark" "${diag:-$(echo "$out" | jq -r '.contractDigest // empty' | cut -c1-23)}"
}

check_task() {
  local T="$1" d rc base
  local C="$FIX/tasks/$T/contract.json" FC="$FIX/tasks/$T/followup-contract.json" M="$SEALED/oracle/$T/oracle.json"
  local variants; variants=$(jq -r '.reference | keys[]' "$SEALED/task-private/$T.json")

  d=$(repo "$T" start); base="$d.report.json"
  run_verifier "$T" "$d" "$C"; rc=$?
  printf '%-3s %-56s %s\n' "$T" "start: baseline report (policy + task probes)" "$( [ $rc -le 1 ] && echo "ok        ($(tail -1 "$d.git.log" | sed 's/^summary: //'))" || echo "MISMATCH  (verifier exit $rc)")"
  with_tests "$d" "$T/acceptance"; run_tests "$d"; expect "$T" "start: visible tests" FAIL $? "$d.tests.log" built
  run_oracle "$T" Initial "$d"; expect "$T" "start: initial oracle" FAIL $? "$d.oracle-Initial.log" built

  d=$(repo "$T" good "$T/good"); with_tests "$d" "$T/acceptance"
  run_tests "$d"; expect "$T" "good: visible tests" PASS $? "$d.tests.log"
  run_oracle "$T" Initial "$d"; expect "$T" "good: initial oracle" PASS $? "$d.oracle-Initial.log"
  dexpect "$T" "good: new DET sev>=2 vs start (policy + probes)" zero "$d" "$base" "$C"
  run_oracle "$T" Followup "$d"; expect "$T" "good: follow-up oracle (not yet solved)" FAIL $? "$d.oracle-Followup.log" built
  d=$(repo "$T" good-fvisible "$T/good"); with_tests "$d" "$T/acceptance" "$T/followup-acceptance"
  run_tests "$d"; expect "$T" "good: follow-up visible tests (not yet solved)" FAIL $? "$d.tests.log" built

  if echo "$variants" | grep -qx trap; then
    d=$(repo "$T" trap "$T/trap"); with_tests "$d" "$T/acceptance"
    run_tests "$d"; expect "$T" "trap: visible tests" PASS $? "$d.tests.log"
    run_oracle "$T" Initial "$d"; expect "$T" "trap: initial oracle (functionally correct)" PASS $? "$d.oracle-Initial.log"
    dexpect "$T" "trap: new DET sev>=2 vs start (policy + probes)" some "$d" "$base" "$C"
  else
    printf '%-3s %-56s none (control task)\n' "$T" "trap"
  fi

  if echo "$variants" | grep -qx conflict; then
    d=$(repo "$T" conflict "$T/conflict"); with_tests "$d" "$T/acceptance"
    run_tests "$d"; expect "$T" "conflict: visible tests" PASS $? "$d.tests.log"
    run_oracle "$T" Initial "$d"; expect "$T" "conflict: initial oracle" FAIL $? "$d.oracle-Initial.log" built
    local re failed bad mark=ok
    re=$(jq -r '.conflictTests' "$M")
    failed=$(outcomes "$d.oracle-Initial.trx" | awk -F'\t' '$1 != "Passed" {print $2}')
    bad=$(echo "$failed" | grep -vE "$re" | grep -c . || true)
    { [ -n "$failed" ] && [ "$bad" -eq 0 ]; } || mark=MISMATCH
    printf '%-3s %-56s expected only conflictTests fail  %-8s (%s failing, %s outside conflictTests)\n' "$T" "conflict: failing oracle tests" "$mark" "$(echo "$failed" | grep -c .)" "$bad"
  fi

  d=$(repo "$T" followup "$T/good" "$T/followup-good"); with_tests "$d" "$T/acceptance" "$T/followup-acceptance"
  run_tests "$d"; expect "$T" "followup-good: visible tests" PASS $? "$d.tests.log"
  run_oracle "$T" Followup "$d"; expect "$T" "followup-good: follow-up oracle" PASS $? "$d.oracle-Followup.log"
  run_oracle "$T" Initial "$d"
  local passing listed mark=ok
  passing=$(outcomes "$d.oracle-Initial.trx" | awk -F'\t' '$1 == "Passed" {print $2}' | sort)
  listed=$(jq -r '.regression[]' "$M" | sort)
  { [ -n "$listed" ] && [ "$passing" = "$listed" ]; } || mark=MISMATCH
  printf '%-3s %-56s expected all pass %-9s (%s regression tests; %s superseded)\n' "$T" "followup-good: regression list (initial oracle)" "$mark" \
    "$(echo "$listed" | grep -c .)" "$(jq -r '.superseded | length' "$M")"
  dexpect "$T" "followup-good: new DET sev>=2 vs start" zero "$d" "$base" "$FC"

  ordo_expect "$T" "$C" "$(jq -r 'if .conflict then "false" else "true" end' "$FIX/tasks/$T/task.json")" "ordo admits contract.json"
  ordo_expect "$T" "$FC" true "ordo admits followup-contract.json"
}

# ---- static checks ---------------------------------------------------------------------------------------
STATIC="$WORK/static.out"
{
  echo "ARCH-002 fixture F1 (lending-brownfield) check"
  echo "fixture tree: $(cd "$FIX" && find repo pack tasks make-contracts.py policy.json -type f -not -path '*/bin/*' -not -path '*/obj/*' | sort | xargs sha256sum | sha256sum | cut -c1-64)"
  echo "sealed tree:  $(cd "$SEALED" && find oracle reference task-private seeded.json tasks-meta.json -type f | sort | xargs sha256sum | sha256sum | cut -c1-64)"
  echo "dotnet $(dotnet --version); ordo $(sha256sum "$ORDO" | cut -c1-16)…; archcheck $(sha256sum "$VERIFIER" | cut -c1-16)… ($VERIFIER); policy ${POLICY#$EXP/}"
  doctrine=$(sha256sum "$FIX/pack/FOUR-TIER-ARCHITECTURE.md" | cut -c1-64)
  if [ "$doctrine" = 725cb3d97b56142a4de07ea6cbbdafbbb421735b79e375aa10fd40308d08775b ]; then mark="ok  "; else mark=MISMATCH; fi
  echo "$mark S1 pack/FOUR-TIER-ARCHITECTURE.md sha256 $doctrine (SDE-DOCTRINE-003 v0.2.1, byte for byte as ARCH-001)"
  leaks=$(grep -rlE 'OracleKit|module OracleT[0-9]|LENDING_HOST_PROJECT_PATH|seeded\.json|tasks-meta|"trap"|sealed:reference' "$FIX/repo" "$FIX/pack" "$FIX/tasks" 2>/dev/null)
  if [ -z "$leaks" ]; then echo "ok   S2 no oracle, reference, trap or seeded content in repo/, pack/ or tasks/"; else echo "MISMATCH S2 sealed content found in: $leaks"; fi
  bad=0
  for t in $TASKS; do
    for f in $(jq -r '[.files.requirement, .files.followup] + .files.visibleTests + .files.followupVisibleTests | .[] | .source + "=" + .sha256' "$FIX/tasks/$t/task.json") \
             $(jq -r '[.contract, .followupContract] | .[] | .path + "=" + .sha256' "$FIX/tasks/$t/task.json") \
             $(jq -r '.files.oracle.initial, .files.oracle.followup, .files.oracle.manifest, .files.probes | .path + "=" + .sha256' "$FIX/tasks/$t/task.json"); do
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
  run_verifier none "$d" - noprobes
  python3 -I - "$d.report.json" "$SEALED/seeded.json" <<'PY'
import collections, json, sys
try: r = json.load(open(sys.argv[1]))
except Exception: print("MISMATCH S6 start commit not evaluated by the verifier"); sys.exit()
s = json.load(open(sys.argv[2]))
key = lambda f: (f.get("ruleId") or f.get("rule"), f["file"], f["symbol"])
for cls, label in (("DET", "S6 start DET findings (policy only) equal seeded.json DET entries"), ("HEU", "S7 start HEU findings equal seeded.json HEU entries")):
    got = collections.Counter(key(f) for f in r["findings"] if f["class"] == cls)
    want = collections.Counter(key(f) for f in s["findings"] if f["class"] == cls)
    rules = collections.Counter(k[0] for k in got.elements())
    print(("ok  " if got == want else "MISMATCH"), label, f"({sum(got.values())} findings: " + ", ".join(f"{k} x{v}" for k, v in sorted(rules.items())) + ")")
    for k in sorted((got - want) | (want - got)): print("       differs:", *k)
viol = collections.Counter(r for v in s["violations"] for r in v["rules"])
print("     seeded violations:", len(s["violations"]), "(" + ", ".join(f"{k} x{v}" for k, v in sorted(viol.items())) + ")")
PY
  echo
} > "$STATIC" 2>&1
cat "$STATIC"

export -f overlay repo with_tests summary run_tests run_oracle outcomes run_verifier newdet expect dexpect ordo_expect check_task
export FIX EXP SEALED ORDO WORK VERIFIER POLICY
for t in $TASKS; do echo "$t"; done | xargs -P "$JOBS" -I{} bash -c 'check_task {} > "$WORK/{}.out" 2>&1'
for t in $TASKS; do cat "$WORK/$t.out"; echo; done

ALL=$(cat "$STATIC"; for t in $TASKS; do cat "$WORK/$t.out"; done)
FAILURES=$(echo "$ALL" | grep -cE 'MISMATCH')
CHECKS=$(echo "$ALL" | grep -cE '(^| )(ok|MISMATCH[A-Z-]*)( |$)')
if [ "$FAILURES" -eq 0 ]; then echo "RESULT: PASS (every expectation held: $CHECKS checks)"; else echo "RESULT: FAIL ($FAILURES mismatches of $CHECKS checks)"; fi
[ -z "${CHECK_WORK:-}" ] && rm -rf "${WORK:?}"
exit $([ "$FAILURES" -eq 0 ] && echo 0 || echo 1)
