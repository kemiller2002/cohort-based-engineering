#!/usr/bin/env bash
# Evidence-binding gate check for Praxis >= 3.17.0 (clean completion identity, out-of-tree store).
# The original gate-evidence-binding.sh is kept unchanged: on 3.17.0 it is refused for every case with
# PRX.COMPLETION.DIRTY_WORKTREE, because it leaves host files (authority, evidence) untracked inside the
# repository. Here every host-owned file (authority, contract, policy, forged inputs, keys) lives in
# WORKDIR/host, outside every repository; an evidence FILE that a case cites is committed before the
# verification revision; each case runs in its own fresh repository, so one case's metadata commit cannot
# move another case's HEAD.
#
# usage: gate-evidence-binding-v317.sh PRAXIS_BIN DOKIMOS_BIN ORDO_BIN ORDO_CONTRACT WORKDIR [non-attested|attested|both]
# One JSON line per case on stdout: {case, mode, evidence, intent, expected, exit, outcome, codes[, identity]}.
#
# Non-attested (validate-run evidence), the same five cases with the same intent as the original:
#   GATE-1   a committed file recording a FAILING test run           expected: rejected (EVIDENCE_UNRECOGNIZED)
#   GATE-2   a committed file unrelated to any test run              expected: rejected (EVIDENCE_UNRECOGNIZED)
#   GATE-3   a forged "passed" validation result written into the out-of-tree store
#            (<git-common-dir>/praxis/validations) PLUS a forged work.validation.observed event appended to
#            <git-common-dir>/praxis/events.jsonl                     expected by the gate: rejected
#   GATE-3U  the original GATE-3 shape: the same forged result in the store, no event
#                                                                     expected: rejected (EVIDENCE_UNRECORDED)
#   GATE-4   validate-run -- false                                    expected: rejected (EVIDENCE_NOT_PASSED)
#   GATE-5   validate-run -- true                                     expected: verified
# Attested (a host verifier daemon; the host authority pins its key and the policy digest):
#   GATE-A1  forged result + forged event in the store (C3b)          expected: rejected
#   GATE-A2  a self-signed receipt (own key, own keyid), perfectly bound expected: rejected (RECEIPT_UNTRUSTED_KEY)
#   GATE-A2B a receipt signed with an own key under the TRUSTED keyid   expected: rejected (RECEIPT_INVALID_SIGNATURE)
#   GATE-A3  a genuine failing receipt                                expected: blocked (RECEIPT_NOT_PASSED)
#   GATE-A4  a genuine passing receipt                                expected: verified, completion identity clean
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PRAXIS="$1"; DOKIMOS="$2"; ORDO="$3"; CONTRACT="$4"; W="$5"; MODE="${6:-both}"
rm -rf "${W:?}"; mkdir -p "$W/host"; H="$W/host"
cp "$CONTRACT" "$H/contract.json"
DIGEST=$("$ORDO" ecir check --blueprint "$H/contract.json" --json | jq -r .contractDigest)
export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=gate/agent PRAXIS_TELEMETRY_PROVIDER=test PRAXIS_TELEMETRY_RUNTIME=test PRAXIS_DOKIMOS_EXECUTABLE="$DOKIMOS"
unset PRAXIS_VERIFIER_SOCKET PRAXIS_COMPLETION_AUTHORITY PRAXIS_ORDO_CONTRACT
REQS=(--requirement "requirements/domain.md#R-001" --requirement "requirements/operations.md#R-001" --decision DEC-CONFIRM)
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }

# new_repo ID [attested]: a fresh repository whose queue holds ID; ros.json requires attested evidence when asked.
new_repo() {
  local r="$W/$1"; mkdir -p "$r/.ros/work"
  jq -cn --arg id "$1" '{schemaVersion:"1.0.0",items:[{id:$id,status:"captured"}]}' > "$r/.ros/work/queue.json"
  [ "${2:-}" = attested ] && jq -n '{workProtocol:{requireAttestedEvidence:true}}' > "$r/ros.json"
  (cd "$r" && git init -q -b main . && git config user.email gate@example.invalid && git config user.name gate && git add -A && git commit -qm fixture)
  echo "$r"
}
store() { echo "$(git -C "$1" rev-parse --path-format=absolute --git-common-dir)/praxis"; }
authority() { # authority FILE [attested-line]
  jq -n --argjson v "${2:-null}" '{OrdoContractVersion:"",OrdoContractDigest:"",SupportedOrdoContractVersions:["ecir/1"],RequiredRequirementIds:[],
    RequiredDecisionIds:["DEC-CONFIRM"],RequiredConflictResolutionIds:[],RequiredValidationNames:["unit-tests"],RequiredEvidenceIds:["EV-TESTS"]}
    + (if $v == null then {} else {TrustedVerifierKeys:[{KeyId:$v.keyId, Algorithm:"ecdsa-p256-sha256", PublicKey:$v.publicKey}], ValidationPolicyDigest:$v.policyDigest} end)' > "$1"; }
emit() { # emit CASE MODE EVIDENCE INTENT EXPECTED EXIT OUTPUT [IDENTITY-JSON]
  jq -cn --arg c "$1" --arg m "$2" --arg e "$3" --arg i "$4" --arg x "$5" --argjson rc "$6" --arg o "$7" --argjson id "${8:-null}" '
    ($o | try fromjson catch {unparsed: $o[0:300]}) as $d
    | {case:$c, mode:$m, evidence:$e, intent:$i, expected:$x, exit:$rc, outcome:($d.outcome // null),
       codes:(($d.codes // []) + (if $d.code then [$d.code] else [] end) | unique)} + (if $id == null then {} else {identity:$id} end)'; }
# complete_explicit REPO ID EVIDENCE-PATH AUTHORITY -> OUT, RC  (the run-01 explicit-argument form)
complete_explicit() { local sha; sha=$(git -C "$1" rev-parse HEAD)
  set +e; OUT=$(cd "$1" && "$PRAXIS" work complete-verified --id "$2" --token "tok-$2" --generation 1 --commit "$sha" --verification-revision "$sha" \
    --authority "$4" --ordo-contract "$H/contract.json" "${REQS[@]}" --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=$3" 2>&1); RC=$?; set -e; }
complete_derived() { set +e; OUT=$(cd "$1" && "$PRAXIS" work complete-verified --id "$2" --token "tok-$2" --authority "$3" --ordo-contract "$H/contract.json" 2>&1); RC=$?; set -e; }
claim() { (cd "$1" && "$PRAXIS" work claim --id "$2" --token "tok-$2" --lease-seconds 1800 > /dev/null); }
identity() { (cd "$1" && "$PRAXIS" work completion-identity --id "$2" 2>/dev/null) | jq -c '{outcome, code, verifiedCommit, head, changedPaths, sourcePaths, clean}' 2>/dev/null || echo null; }

# forge_store_result REPO ID: a hand-made passed praxis.validation-result/1 in the store; prints its path.
forge_store_result() {
  local r="$1" id="$2" sha at dir; sha=$(git -C "$r" rev-parse HEAD); at=$(utc)
  dir="$(store "$r")/validations/$id/EV-TESTS"; mkdir -p "$dir"
  local f="$dir/1-${sha:0:12}-$(date -u +%Y%m%dT%H%M%S%3NZ).json"
  jq -cn --arg id "$id" --arg r "$sha" --arg at "$at" '{schemaVersion:"praxis.validation-result/1",workItemId:$id,claimant:"gate/agent",claimToken:("tok-" + $id),generation:1,
    validation:"unit-tests",evidenceId:"EV-TESTS",revision:$r,observedAt:$at,startedAt:$at,status:"passed",exitCode:0,command:["true"],
    outputSha256:"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}' | tr -d '\n' > "$f"
  echo "$f"
}
# forge_store_event REPO ID RESULT: a work.validation.observed event for the forged result, in the store log.
forge_store_event() {
  local r="$1" id="$2" f="$3" at; at=$(jq -r .observedAt "$f")
  jq -cn --arg id "$id" --arg rev "$(jq -r .revision "$f")" --arg at "$at" --arg d "sha256:$(sha256sum "$f" | cut -d' ' -f1)" --arg repo "$(basename "$r")" '
    {schemaVersion:"1.0.0",type:"work.validation.observed",workItem:$id,repository:$repo,protocolVersion:"1.0.0",occurredAt:$at,claimant:"gate/agent",
     claimToken:("tok-" + $id),generation:1,validation:"unit-tests",evidenceId:"EV-TESTS",revision:$rev,status:"passed",observedAt:$at,resultDigest:$d,
     actor:{kind:"agent",id:"gate/agent",provider:"test",model:"unknown",runtime:"test"},eventId:("forged" + ($d[7:25]))}' >> "$(store "$r")/events.jsonl"
}

non_attested() {
  local A="$H/authority.json" r f
  authority "$A"
  for spec in "GATE-1:failing.txt:12 test(s); 7 passed; 5 failed:a committed file recording a failing test run" \
              "GATE-2:unrelated.txt:not a test report:a committed file unrelated to any test run"; do
    IFS=: read -r id file body intent <<<"$spec"
    r=$(new_repo "$id"); mkdir -p "$r/evidence"; printf '%s\n' "$body" > "$r/evidence/$file"
    git -C "$r" add -A && git -C "$r" commit -qm "evidence fixture"
    claim "$r" "$id"; complete_explicit "$r" "$id" "evidence/$file" "$A"
    emit "$id" non-attested "evidence/$file (committed)" "$intent" "rejected (EVIDENCE_UNRECOGNIZED)" "$RC" "$OUT"
  done
  r=$(new_repo GATE-3U); claim "$r" GATE-3U; f=$(forge_store_result "$r" GATE-3U); complete_explicit "$r" GATE-3U "$f" "$A"
  emit GATE-3U non-attested "forged passed result in <git-common-dir>/praxis/validations, no event" "the original GATE-3: a forged, unrecorded result" "rejected (EVIDENCE_UNRECORDED)" "$RC" "$OUT"
  r=$(new_repo GATE-3); claim "$r" GATE-3; f=$(forge_store_result "$r" GATE-3); forge_store_event "$r" GATE-3 "$f"; complete_explicit "$r" GATE-3 "$f" "$A"
  emit GATE-3 non-attested "forged passed result in the store + forged work.validation.observed in <git-common-dir>/praxis/events.jsonl" \
    "forged result recorded by a forged event in the agent-writable store (REL-001 C3b shape)" "rejected" "$RC" "$OUT" "$(identity "$r" GATE-3)"
  for spec in "GATE-4:false:rejected (EVIDENCE_NOT_PASSED):a recorded failing run" "GATE-5:true:verified:a recorded passing run"; do
    IFS=: read -r id cmd expected intent <<<"$spec"
    r=$(new_repo "$id"); claim "$r" "$id"
    local vr; vr=$(cd "$r" && "$PRAXIS" work validate-run --id "$id" --token "tok-$id" --generation 1 --validation unit-tests --evidence-id EV-TESTS -- "$cmd" 2>/dev/null || true)
    complete_explicit "$r" "$id" "$(jq -r '.resultPath // empty' <<<"$vr")" "$A"
    emit "$id" non-attested "validate-run -- $cmd" "$intent" "$expected" "$RC" "$OUT" "$( [ "$id" = GATE-5 ] && identity "$r" "$id" || echo null)"
  done
}

# sign_receipt TEMPLATE-ENVELOPE OUT REPO ID KEYID-MODE: re-binds a genuine receipt's payload to REPO's claim and HEAD and
# signs it with a freshly generated key. KEYID-MODE own: the envelope names the new key's own keyid; trusted: it
# names the TRUSTED verifier keyid (an impostor).
sign_receipt() { python3 -I "$HERE/forge-receipt.py" "$@"; }

attested() {
  local A="$H/authority-attested.json" r f
  jq -n --arg dig "$DIGEST" '{schemaVersion:"echelon.validation-policy/1", policyId:"gate-v317",
    validations:[{name:"unit-tests", evidenceId:"EV-TESTS", command:["sh","-c","test ! -e GATE-FAIL"], timeoutSeconds:120}], protectedPaths:[]}' > "$H/policy.json"
  ( setsid "$PRAXIS" verifier serve --socket "$H/verifier.sock" --policy "$H/policy.json" --contract-digest "$DIGEST" > "$H/verifier.out" 2> "$H/verifier.err" < /dev/null &
    echo $! > "$H/verifier.pid" )
  for _ in $(seq 1 120); do [ -s "$H/verifier.out" ] && [ -S "$H/verifier.sock" ] && break; sleep 0.5; done
  local vline; vline=$(head -1 "$H/verifier.out"); authority "$A" "$vline"
  export PRAXIS_VERIFIER_SOCKET="$H/verifier.sock"
  # A4 first: its genuine receipt is the template the A2 forgeries copy (the strongest forgery: exact format)
  r=$(new_repo GATE-A4 attested); claim "$r" GATE-A4
  local v4; v4=$(cd "$r" && "$PRAXIS" work verify --id GATE-A4 --token tok-GATE-A4 2>&1 || true)
  local template; template=$(jq -r '.receipts[0].path' <<<"$v4"); cp "$template" "$H/genuine-receipt.json"
  complete_derived "$r" GATE-A4 "$A"
  emit GATE-A4 attested "genuine passing receipt (work verify -> host verifier)" "a genuine passing receipt" "verified, completion identity clean" "$RC" "$OUT" "$(identity "$r" GATE-A4)"
  local a4="$OUT"
  r=$(new_repo GATE-A1 attested); claim "$r" GATE-A1; f=$(forge_store_result "$r" GATE-A1); forge_store_event "$r" GATE-A1 "$f"
  complete_explicit "$r" GATE-A1 "$f" "$A"; local explicit_out="$OUT" explicit_rc=$RC
  complete_derived "$r" GATE-A1 "$A"
  emit GATE-A1 attested "forged passed result + forged event in the store, cited explicitly" "C3b in attested mode" "rejected (RECEIPT_MISSING)" "$explicit_rc" "$explicit_out"
  emit GATE-A1-derived attested "the same forgery, derived completion (--id --token)" "C3b in attested mode, F4 path" "rejected" "$RC" "$OUT"
  for spec in "GATE-A2:own:rejected (RECEIPT_UNTRUSTED_KEY):a self-signed receipt under its own keyid" \
              "GATE-A2B:trusted:rejected (RECEIPT_INVALID_SIGNATURE):a receipt signed with an own key under the trusted verifier keyid"; do
    IFS=: read -r id mode expected intent <<<"$spec"
    r=$(new_repo "$id" attested); claim "$r" "$id"
    local sha d; sha=$(git -C "$r" rev-parse HEAD); d="$(store "$r")/receipts/$id"; mkdir -p "$d"
    f="$d/1-${sha:0:12}-$(cat /proc/sys/kernel/random/uuid).json"; sign_receipt "$H/genuine-receipt.json" "$f" "$r" "$id" "$mode" > "$H/$id.keyid"
    complete_derived "$r" "$id" "$A"; local derived_out="$OUT" derived_rc=$RC
    complete_explicit "$r" "$id" "$f" "$A"
    emit "$id" attested "forged envelope in <git-common-dir>/praxis/receipts, cited explicitly" "$intent" "$expected" "$RC" "$OUT"
    emit "$id-derived" attested "the same forged envelope, derived completion (--id --token)" "$intent, F4 path" "rejected" "$derived_rc" "$derived_out"
  done
  r=$(new_repo GATE-A3 attested); : > "$r/GATE-FAIL"; git -C "$r" add -A && git -C "$r" commit -qm "make the policy validation fail"; claim "$r" GATE-A3
  local v3; v3=$(cd "$r" && "$PRAXIS" work verify --id GATE-A3 --token tok-GATE-A3 2>&1 || true)
  complete_derived "$r" GATE-A3 "$A"
  emit GATE-A3 attested "genuine failing receipt (work verify: $(jq -r '[.receipts[]?.status] | join(",")' <<<"$v3"))" "a genuine failing receipt" "blocked (RECEIPT_NOT_PASSED)" "$RC" "$OUT"
  kill -TERM -- "-$(cat "$H/verifier.pid")" 2>/dev/null || kill "$(cat "$H/verifier.pid")" 2>/dev/null || true
  unset PRAXIS_VERIFIER_SOCKET
}

