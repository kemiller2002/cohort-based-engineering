#!/usr/bin/env bash
# SPR-E2-01 attacks (E-F-03, E-F-11) and positive controls against one Praxis build.
# usage: spr-e2-01.sh LABEL PRAXIS_DLL > raw/spr-e2-01-LABEL.jsonl
# Every repository is a fresh fixture under /home/user/sprint-scratch/E2/fixtures/spr-e2-01-LABEL/ with its own .git
# (guarded by lib.sh px/assert_fixture). One JSON line per case.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); . "$HERE/lib.sh"
LABEL=$1; P=$2; RUN="spr-e2-01-$LABEL"
rm -rf "${E2_FIXTURES:?}/$RUN"; mkdir -p "$E2_FIXTURES/$RUN/host"; H="$E2_FIXTURES/$RUN/host"
CONTRACT=/home/user/ordo/examples/ecir/consumer/valid-contract.json; cp "$CONTRACT" "$H/contract.json"
REQS=(--requirement "requirements/domain.md#R-001" --requirement "requirements/operations.md#R-001" --decision DEC-CONFIRM)
jq -n '{OrdoContractVersion:"",OrdoContractDigest:"",SupportedOrdoContractVersions:["ecir/1"],RequiredRequirementIds:[],
  RequiredDecisionIds:["DEC-CONFIRM"],RequiredConflictResolutionIds:[],RequiredValidationNames:["unit-tests"],RequiredEvidenceIds:["EV-TESTS"]}' > "$H/authority.json"

emit() { # CASE ATTEMPT EXPECTED EXIT OUTPUT [NOTE]
  jq -cn --arg l "$LABEL" --arg c "$1" --arg a "$2" --arg x "$3" --argjson rc "$4" --arg o "$5" --arg n "${6:-}" '
    {build:$l, case:$c, attempt:$a, expected:$x, exit:$rc,
     codes:([$o | scan("PRX\\.[A-Z_]+\\.[A-Z_]+")] | unique), output_tail:($o[-500:]), note:$n}'; }
run() { OUT=$("$@" 2>&1); RC=$?; }

# plain repo (queue only, no init) as in E bypass-cases / V2 case B
plain_repo() { local r="$E2_FIXTURES/$RUN/$1"; mkdir -p "$r/.ros/work"; git init -q -b main "$r"
  jq -cn --arg id "$1" '{schemaVersion:"1.0.0",items:[{id:$id,status:"captured"}]}' > "$r/.ros/work/queue.json"
  printf '{}\n' > "$r/ros.json"; echo "# $1" > "$r/README.md"; gitc "$r" add -A; gitc "$r" commit -qm fixture; echo "$r"; }
plain_complete() { # ready -> start (best effort, as in E bypass-cases) -> complete with in-repo evidence
  px "$P" "$1" work backlog-transition --id "$2" --action ready --occurred-at "$(utc)" >/dev/null 2>&1
  px "$P" "$1" work start --id "$2" --occurred-at "$(utc)" >/dev/null 2>&1
  px "$P" "$1" work complete --id "$2" --occurred-at "$(utc)" --evidence implementation=README.md --evidence tests=README.md --conclusion "all tests pass"; }
store() { echo "$1/.git/praxis"; }

# ---- A1: E NX-2b / V2 case B
r=$(plain_repo E2-1); run px "$P" "$r" work claim --id E2-1 --token tok-E2-1 --lease-seconds 1800
emit A1-claim "work claim" "exit 0" "$RC" "$OUT" "tracked marker present: $(grep -c work.claim.recorded "$r/.ros/events/events.jsonl" 2>/dev/null || echo 0); token in tracked log: $(grep -c tok-E2-1 "$r/.ros/events/events.jsonl" 2>/dev/null || echo 0)"
run plain_complete "$r" E2-1; emit A1-pre "claimed item; plain work complete" "refused VERIFIED_COMPLETION_REQUIRED" "$RC" "$OUT"
rm -rf "$(store "$r")/claims/E2-1"; run plain_complete "$r" E2-1
emit A1 "after rm -rf <git-common-dir>/praxis/claims/E2-1; plain work complete" "baseline: accepted (E-F-03); patched: refused CLAIM_RECORD_MISSING" "$RC" "$OUT"

# ---- A1b: claim marker committed, then store deleted AND marker line removed from working-tree log
r=$(plain_repo E2-2); px "$P" "$r" work claim --id E2-2 --token tok-E2-2 >/dev/null 2>&1; gitc "$r" add -A; gitc "$r" commit -qm "commit after claim" >/dev/null 2>&1
rm -rf "$(store "$r")/claims/E2-2"; [ -f "$r/.ros/events/events.jsonl" ] && sed -i '/work.claim.recorded/d' "$r/.ros/events/events.jsonl"
run plain_complete "$r" E2-2; emit A1b "committed claim marker; store deleted + working-tree marker line deleted; plain complete" "patched: refused (HEAD blob)" "$RC" "$OUT"

# ---- A1c: marker never committed; store deleted + working-tree marker deleted (expected residual bypass)
r=$(plain_repo E2-3); px "$P" "$r" work claim --id E2-3 --token tok-E2-3 >/dev/null 2>&1
rm -rf "$(store "$r")/claims/E2-3"; [ -f "$r/.ros/events/events.jsonl" ] && sed -i '/work.claim.recorded/d' "$r/.ros/events/events.jsonl"
run plain_complete "$r" E2-3; emit A1c "uncommitted claim marker deleted with the store; plain complete" "expected residual: accepted" "$RC" "$OUT"

# ---- A2: E NX-9 hand-edited queue.json
r=$(new_fixture "$P" E2-4); px "$P" "$r" work capture --title t --id E2-4 --occurred-at "$(utc)" >/dev/null 2>&1
jq '(.items[] | select(.id=="E2-4") | .status) = "complete"' "$r/.ros/work/queue.json" > "$H/q.json" && cp "$H/q.json" "$r/.ros/work/queue.json"
run px "$P" "$r" work validate; emit A2-work-validate "queue.json status hand-edited to complete; work validate" "baseline: valid; patched: UNRECORDED_COMPLETION exit 1" "$RC" "$OUT"
run px "$P" "$r" work backlog-validate; emit A2-backlog-validate "same; work backlog-validate" "patched: finding" "$RC" "$OUT"
run px "$P" "$r" validate; emit A2-validate "same; praxis validate" "patched: finding" "$RC" "$OUT"
run px "$P" "$r" verify; emit A2-verify "same; praxis verify (not changed by the patch)" "info" "$RC" "$OUT"

# ---- C1: claim -> validate-run (real command) -> complete-verified (real Dokimos)
r=$(plain_repo E2-5); px "$P" "$r" work claim --id E2-5 --token tok-E2-5 --lease-seconds 1800 >/dev/null 2>&1
printf '#!/bin/sh\n# tiny real test: README must mention the item\ngrep -q E2-5 README.md && echo "1 test passed"\n' > "$r/test.sh"; chmod +x "$r/test.sh"
gitc "$r" add -A; gitc "$r" commit -qm "add test"
run px "$P" "$r" work validate-run --id E2-5 --token tok-E2-5 --generation 1 --validation unit-tests --evidence-id EV-TESTS -- sh test.sh
VR=$OUT; emit C1-validate-run "validate-run -- sh test.sh" "exit 0" "$RC" "$OUT"
ev=$(jq -r '.resultPath // empty' <<<"$VR" 2>/dev/null); case "$ev" in /*) ;; "") ;; *) ev="$r/$ev";; esac
sha=$(git -C "$r" rev-parse HEAD)
run px "$P" "$r" work complete-verified --id E2-5 --token tok-E2-5 --generation 1 --commit "$sha" --verification-revision "$sha" \
  --authority "$H/authority.json" --ordo-contract "$H/contract.json" "${REQS[@]}" --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=$ev"
emit C1 "claim -> validate-run -> complete-verified (real Dokimos)" "accepted on both builds" "$RC" "$OUT"
run plain_complete "$r" E2-5; emit C1-after "plain work complete after verified completion (legacy transition)" "info" "$RC" "$OUT"
run px "$P" "$r" work validate; emit C1-validate "work validate after verified completion" "no UNRECORDED_COMPLETION" "$RC" "$OUT"

# ---- C2: unclaimed item, default policy, plain complete with in-repo evidence
r=$(plain_repo E2-6); run plain_complete "$r" E2-6; emit C2 "unclaimed item, default policy, plain complete (in-repo evidence)" "accepted on both builds" "$RC" "$OUT"

# ---- C3: legitimately completed item -> no queue finding
r=$(new_fixture "$P" E2-7); px "$P" "$r" work capture --title t --id E2-7 --occurred-at "$(utc)" >/dev/null 2>&1
px "$P" "$r" work backlog-transition --id E2-7 --action ready --occurred-at "$(utc)" >/dev/null 2>&1; px "$P" "$r" work start --id E2-7 --occurred-at "$(utc)" >/dev/null 2>&1
run plain_complete "$r" E2-7; emit C3-complete "start -> plain complete" "exit 0" "$RC" "$OUT"
run px "$P" "$r" work validate; emit C3 "work validate after legitimate completion" "valid, exit 0 on both builds" "$RC" "$OUT"
run px "$P" "$r" work backlog-validate; emit C3-backlog "work backlog-validate after legitimate completion" "valid" "$RC" "$OUT"

# ---- C1b: the normal flow with NO commit after the claim (claim marker stays uncommitted until the metadata commit)
r=$(plain_repo E2-8); printf '#!/bin/sh\ngrep -q E2-8 README.md && echo "1 test passed"\n' > "$r/test.sh"; gitc "$r" add -A; gitc "$r" commit -qm "add test"
px "$P" "$r" work claim --id E2-8 --token tok-E2-8 --lease-seconds 1800 >/dev/null 2>&1
run px "$P" "$r" work validate-run --id E2-8 --token tok-E2-8 --generation 1 --validation unit-tests --evidence-id EV-TESTS -- sh test.sh
ev=$(jq -r '.resultPath // empty' <<<"$OUT" 2>/dev/null); case "$ev" in /*) ;; "") ;; *) ev="$r/$ev";; esac; sha=$(git -C "$r" rev-parse HEAD)
run px "$P" "$r" work complete-verified --id E2-8 --token tok-E2-8 --generation 1 --commit "$sha" --verification-revision "$sha" \
  --authority "$H/authority.json" --ordo-contract "$H/contract.json" "${REQS[@]}" --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=$ev"
emit C1b "claim (marker uncommitted) -> validate-run -> complete-verified" "accepted on both builds; patched: marker committed in metadata commit" "$RC" "$OUT" \
  "status=[$(git -C "$r" status --porcelain | tr '\n' ';')] head-log-types=$(git -C "$r" show HEAD:.ros/events/events.jsonl 2>/dev/null | jq -r .type | tr '\n' ',')"
