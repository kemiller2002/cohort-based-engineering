#!/usr/bin/env bash
# REL-001 Experiment C: completion verification. usage: harness/c/run.sh baseline|treatment
# One JSON line per case -> results/c/<arm>.jsonl.
#   completionAccepted  the arm recorded the item as completed by this attempt
#   unverifiedCompletion  accepted although the evidence does not prove a passing run of the
#                         required validation, by the owner, at the completed revision
source "$(dirname "$0")/../lib.sh"
arm_init "$1"
OUT_FILE="$REL/results/c/$ARM${REL001_RESULTS_TAG:+-$REL001_RESULTS_TAG}.jsonl"; mkdir -p "$(dirname "$OUT_FILE")"; : > "$OUT_FILE"  # A5: REL001_RESULTS_TAG names a re-run file, never overwriting

record() { # record CASE START VALID(true|false) EXPECTED ACCEPTED(0|1) OBSERVED-JSON
  local ua=0; [ "$3" = false ] && [ "$5" = 1 ] && ua=1
  local m; if [ "$ARM" = treatment ]; then m=$( { [ "$3" = true ] && [ "$5" = 1 ]; } || { [ "$3" = false ] && [ "$5" = 0 ]; } && echo true || echo false ); else m=$( [ "$5" = 1 ] && echo true || echo false ); fi  # HC baseline prediction: every case accepted
  emit "$OUT_FILE" "$(jq -cn --arg c "$1" --argjson w $(( $(now_ms) - $2 )) --argjson v "$3" --arg e "$4" --argjson a "$5" --argjson ua $ua --argjson o "$6" --argjson m "$m" \
    '{experiment:"C", case:$c, status:"executed", evidenceValid:$v, expected:$e, observed:$o, metrics:{completionAccepted:$a, unverifiedCompletion:$ua}, matchesPrediction:$m, wallMs:$w}')"; }
blocked() { emit "$OUT_FILE" "$(jq -cn --arg c "$1" --arg r "$2" '{experiment:"C", case:$c, status:"blocked", reason:$r, metrics:null, matchesPrediction:null, wallMs:0}')"; }
accepted_t() { [ "$(printf '%s' "$1" | jq -r .outcome 2>/dev/null)" = verified ] && echo 1 || echo 0; }

# A Dokimos wrapper that keeps a copy of the packet/authority Praxis sends (Praxis deletes its scratch dir).
capturing_dokimos() { cat > "$RUN_DIR/inputs/capture-dokimos" <<EOF
#!/usr/bin/env bash
n=\$(ls "$RUN_DIR/inputs" | grep -c '^sent-' || true)
for ((i=1;i<=\$#;i++)); do a="\${!i}"; j=\$((i+1)); case "\$a" in --packet) cp "\${!j}" "$RUN_DIR/inputs/sent-\$n-packet.json";; --authority) cp "\${!j}" "$RUN_DIR/inputs/sent-\$n-authority.json";; esac; done
exec "$DOKIMOS" "\$@"
EOF
  chmod +x "$RUN_DIR/inputs/capture-dokimos"; export PRAXIS_DOKIMOS_EXECUTABLE="$RUN_DIR/inputs/capture-dokimos"; }

forge_result() { # forge_result ID TOKEN GEN REV OBSERVED-AT -> path of a hand-made praxis.validation-result/1
  local f="$RUN_DIR/inputs/forged-$1.json"
  jq -cn --arg id "$1" --arg t "$2" --argjson g "$3" --arg r "$4" --arg at "$5" '{schemaVersion:"praxis.validation-result/1",workItemId:$id,claimant:"w1",claimToken:$t,generation:$g,validation:"unit-tests",evidenceId:"EV-TESTS",revision:$r,observedAt:$at,startedAt:$at,status:"passed",exitCode:0,command:["dotnet","test"],outputSha256:("sha256:" + ("0" * 64))}' > "$f"; echo "$f"; }

# ------------------------------------------------------------ treatment
treatment() {
  local s o ev ev1 head prev
  # C1 valid
  s=$(now_ms); new_run C valid; init_repo "$REPO" ITEM-C; capturing_dokimos
  t_claim "$REPO" w1 --id ITEM-C --token tok-1; t_validate "$REPO" w1 ITEM-C tok-1 1 true; ev="$EVPATH"; local vr; vr=$(summ "$OUT")
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev"; o="$OUT"; local valid_dir="$RUN_DIR" valid_repo="$REPO" valid_ev="$ev"
  record C1-valid-validate-run "$s" true "verified" "$(accepted_t "$o")" "$(jq -cn --argjson v "$vr" --argjson c "$(summ "$o")" '{validateRun:$v, completeVerified:$c}')"
  # C4a replay: the same complete-verified again
  s=$(now_ms); local before; before=$(count_events "$REPO" work.completion.verified)
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev"; o="$OUT"; local after; after=$(count_events "$REPO" work.completion.verified)
  local acc=0; [ "$after" -gt "$before" ] && acc=1
  record C4a-replay-same-packet "$s" false "replayed idempotently: no second completion, no new verified event" "$acc" \
    "$(jq -cn --argjson c "$(summ "$o")" --argjson b "$before" --argjson a "$after" --argjson r "$(count_events "$REPO" work.completion.replayed)" '{completeVerified:$c, verifiedEventsBefore:$b, verifiedEventsAfter:$a, replayedEvents:$r}')"
  # C4b consumed packet straight to Dokimos, with the authority the claim now implies (packet consumed)
  s=$(now_ms)
  if [ -f "$RUN_DIR/inputs/sent-0-packet.json" ]; then
    local consumed; consumed=$(claim_state "$REPO" ITEM-C)
    local digests; digests=$(cd "$REPO" && "$PRAXIS" work claims ITEM-C | jq -c '(.claim // .claims[0]).consumedPacketDigests')
    jq --argjson d "$digests" 'if has("ConsumedPacketDigests") then .ConsumedPacketDigests = $d elif has("consumedPacketDigests") then .consumedPacketDigests = $d else . + {consumedPacketDigests:$d} end' \
      "$RUN_DIR/inputs/sent-0-authority.json" > "$RUN_DIR/inputs/replay-authority.json"
    set +e; o=$("$DOKIMOS" completion verify --packet "$RUN_DIR/inputs/sent-0-packet.json" --authority "$RUN_DIR/inputs/replay-authority.json" 2>&1); local rc=$?; set -e
    local fresh; set +e; fresh=$("$DOKIMOS" completion verify --packet "$RUN_DIR/inputs/sent-0-packet.json" --authority "$RUN_DIR/inputs/sent-0-authority.json" 2>&1); local frc=$?; set -e
    record C4b-consumed-packet-direct-to-dokimos "$s" false "Dokimos refuses (REPLAYED_PACKET)" "$( [ $rc -eq 0 ] && echo 1 || echo 0 )" \
      "$(jq -cn --argjson rc $rc --argjson o "$(json_or_null "${o:0:1500}")" --argjson d "$digests" --argjson frc $frc --argjson fo "$(json_or_null "${fresh:0:600}")" '{dokimosExit:$rc, dokimos:$o, consumedPacketDigests:$d, control_originalAuthorityExit:$frc, control_originalAuthority:$fo}')"
  else blocked C4b-consumed-packet-direct-to-dokimos "no packet was captured from the C1 verification"; fi
  # C4c replay of C1's evidence on another item
  s=$(now_ms); new_run C replay-evidence-other-item; init_repo "$REPO" ITEM-C ITEM-D; cp "$valid_ev" "$RUN_DIR/inputs/foreign.json"
  t_claim "$REPO" w1 --id ITEM-D --token tok-1; t_complete "$REPO" w1 ITEM-D tok-1 1 "$RUN_DIR/inputs/foreign.json"; o="$OUT"
  record C4c-replay-evidence-on-other-item "$s" false "refused (EVIDENCE_FOREIGN_CLAIM or EVIDENCE_UNRECORDED)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"

  # C2 missing
  s=$(now_ms); new_run C missing; init_repo "$REPO" ITEM-C
  t_claim "$REPO" w1 --id ITEM-C --token tok-1; t_complete "$REPO" w1 ITEM-C tok-1 1 ""; o="$OUT"
  record C2a-missing-no-evidence "$s" false "refused (EVIDENCE_MISSING / VALIDATION_UNPROVEN)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  s=$(now_ms); t_complete "$REPO" w1 ITEM-C tok-1 1 "$REPO/.ros/claims/ITEM-C/validations/EV-TESTS/none.json"; o="$OUT"
  record C2b-missing-nonexistent-path "$s" false "refused (EVIDENCE_UNREADABLE / EVIDENCE_MISSING)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"

  # C3 forged
  s=$(now_ms); new_run C forged; init_repo "$REPO" ITEM-C; head=$(git -C "$REPO" rev-parse HEAD)
  t_claim "$REPO" w1 --id ITEM-C --token tok-1; ev=$(forge_result ITEM-C tok-1 1 "$head" "$(utc)")
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev"; o="$OUT"
  record C3a-forged-result-document "$s" false "refused (EVIDENCE_UNRECORDED)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  # C3b forged result + forged work.validation.observed event appended to the repository event log
  s=$(now_ms); new_run C forged-with-event; init_repo "$REPO" ITEM-C; head=$(git -C "$REPO" rev-parse HEAD)
  t_claim "$REPO" w1 --id ITEM-C --token tok-1
  # Amendment A5: Praxis >= 3.17.0 keeps validation events in the out-of-tree store log; the forger copies and appends there.
  local evlog="$REPO/.ros/events/events.jsonl" common; common=$(git -C "$REPO" rev-parse --path-format=absolute --git-common-dir)
  [ -f "$common/praxis/events.jsonl" ] && evlog="$common/praxis/events.jsonl"
  t_validate "$REPO" w1 ITEM-C tok-1 1 true; local template; template=$(grep '"type":"work.validation.observed"' "$evlog" | tail -1)
  local at; at=$(utc); ev=$(forge_result ITEM-C tok-1 1 "$head" "$at")
  local fdig; fdig="sha256:$(sha256sum "$ev" | cut -d' ' -f1)"
  if [ -n "$template" ]; then
    printf '%s' "$template" | jq -c --arg d "$fdig" --arg at "$at" '
      def setd: if type=="object" then with_entries(if .key=="resultDigest" then .value=$d elif .key=="observedAt" then .value=$at elif .key=="eventId" then .value=("forged" + ($d[7:23])) else .value |= setd end) elif type=="array" then map(setd) else . end; setd' >> "$evlog"
    t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev"; o="$OUT"
    record C3b-forged-result-and-forged-observed-event "$s" false "refused; Praxis docs list this as residual risk (repository-writable event log)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c, note:"forger appended a work.validation.observed event copied from a real one with the forged result digest"}')"
  else blocked C3b-forged-result-and-forged-observed-event "no work.validation.observed event to copy the envelope from"; fi

  # C5 stale
  s=$(now_ms); new_run C stale-lease-expired; init_repo "$REPO" ITEM-C
  t_claim "$REPO" w1 --id ITEM-C --token tok-1 --lease-seconds 3; t_validate "$REPO" w1 ITEM-C tok-1 1 true; ev="$EVPATH"; sleep 4
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev"; o="$OUT"
  record C5a-stale-lease-expired "$s" false "refused (PRX.CLAIM.EXPIRED)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  s=$(now_ms); new_run C stale-pre-claim; init_repo "$REPO" ITEM-C
  t_claim "$REPO" w1 --id ITEM-C --token tok-1; t_validate "$REPO" w1 ITEM-C tok-1 1 true; ev1="$EVPATH"
  t_cmd "$REPO" w1 work release --id ITEM-C --token tok-1 --generation 1; local rel; rel=$(summ "$OUT")
  t_claim "$REPO" w1 --id ITEM-C --token tok-2; local gen; gen=$(printf '%s' "$OUT" | jq '.claim.generation // 2')
  t_complete "$REPO" w1 ITEM-C tok-2 "$gen" "$ev1"; o="$OUT"
  record C5b-stale-result-from-before-current-claim "$s" false "refused (EVIDENCE_FOREIGN_CLAIM / EVIDENCE_STALE)" "$(accepted_t "$o")" "$(jq -cn --argjson r "$rel" --argjson g "$gen" --argjson c "$(summ "$o")" '{release:$r, reclaimGeneration:$g, completeVerified:$c}')"
  s=$(now_ms); ev=$(forge_result ITEM-C tok-2 "$gen" "$(git -C "$REPO" rev-parse HEAD)" "2026-01-01T00:00:00.000Z")
  t_complete "$REPO" w1 ITEM-C tok-2 "$gen" "$ev"; o="$OUT"
  record C5c-stale-observed-before-claim-forged "$s" false "refused (EVIDENCE_UNRECORDED or EVIDENCE_STALE)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  s=$(now_ms); new_run C stale-revision-mismatch; init_repo "$REPO" ITEM-C
  t_claim "$REPO" w1 --id ITEM-C --token tok-1; t_validate "$REPO" w1 ITEM-C tok-1 1 true; ev="$EVPATH"
  printf 'changed after the run\n' >> "$REPO/README.md"; git -C "$REPO" commit -qam "change after validation"
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev"; o="$OUT"
  record C5d-stale-commit-after-run "$s" false "refused (EVIDENCE_REVISION_MISMATCH)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"

  # C6 commit-to-evidence binding
  s=$(now_ms); new_run C binding; init_repo "$REPO" ITEM-C ITEM-E ITEM-F
  printf 'v2\n' >> "$REPO/README.md"; git -C "$REPO" commit -qam v2; prev=$(git -C "$REPO" rev-parse HEAD~1); head=$(git -C "$REPO" rev-parse HEAD)
  t_claim "$REPO" w1 --id ITEM-C --token tok-c; t_validate "$REPO" w1 ITEM-C tok-c 1 true
  T_COMMIT=$head T_VREV=$head t_complete "$REPO" w1 ITEM-C tok-c 1 "$EVPATH"; o="$OUT"
  record C6a-binding-valid-commit-equals-evidence-revision "$s" true "verified" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  s=$(now_ms); t_claim "$REPO" w1 --id ITEM-E --token tok-e; t_validate "$REPO" w1 ITEM-E tok-e 1 true
  T_COMMIT=$prev T_VREV=$head t_complete "$REPO" w1 ITEM-E tok-e 1 "$EVPATH"; o="$OUT"
  record C6b-binding-invalid-commit-older-than-evidence "$s" false "refused (commit is not the verified/expected revision)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  s=$(now_ms); t_claim "$REPO" w1 --id ITEM-F --token tok-f; t_validate "$REPO" w1 ITEM-F tok-f 1 true
  T_COMMIT=$prev T_VREV=$prev t_complete "$REPO" w1 ITEM-F tok-f 1 "$EVPATH"; o="$OUT"
  record C6c-binding-invalid-evidence-from-other-revision "$s" false "refused (EVIDENCE_REVISION_MISMATCH)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"

  # C7 gate regressions (REL-GATE-001): failing run, failing log text, unrelated file, dirty worktree
  s=$(now_ms); new_run C gate-regressions; init_repo "$REPO" ITEM-G1 ITEM-G2 ITEM-G3 ITEM-G4
  t_claim "$REPO" w1 --id ITEM-G1 --token tok-g1; t_validate "$REPO" w1 ITEM-G1 tok-g1 1 false; local vf; vf=$(summ "$OUT"); t_complete "$REPO" w1 ITEM-G1 tok-g1 1 "$EVPATH"; o="$OUT"
  record C7a-recorded-failing-run "$s" false "refused (EVIDENCE_NOT_PASSED)" "$(accepted_t "$o")" "$(jq -cn --argjson v "$vf" --argjson c "$(summ "$o")" '{validateRun:$v, completeVerified:$c}')"
  s=$(now_ms); printf '12 test(s); 7 passed; 5 failed\n' > "$RUN_DIR/inputs/failing.txt"
  t_claim "$REPO" w1 --id ITEM-G2 --token tok-g2; t_complete "$REPO" w1 ITEM-G2 tok-g2 1 "$RUN_DIR/inputs/failing.txt"; o="$OUT"
  record C7b-failing-test-log-text "$s" false "refused (EVIDENCE_UNRECOGNIZED)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  s=$(now_ms); printf 'not a test report\n' > "$RUN_DIR/inputs/unrelated.txt"
  t_claim "$REPO" w1 --id ITEM-G3 --token tok-g3; t_complete "$REPO" w1 ITEM-G3 tok-g3 1 "$RUN_DIR/inputs/unrelated.txt"; o="$OUT"
  record C7c-unrelated-file "$s" false "refused (EVIDENCE_UNRECOGNIZED)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  s=$(now_ms); t_claim "$REPO" w1 --id ITEM-G4 --token tok-g4; printf 'uncommitted\n' >> "$REPO/README.md"
  t_validate "$REPO" w1 ITEM-G4 tok-g4 1 true; local vd; vd=$(summ "$OUT"); local dirty_ev="$EVPATH"
  if [ -n "$dirty_ev" ]; then t_complete "$REPO" w1 ITEM-G4 tok-g4 1 "$dirty_ev"; o="$OUT"; else o='{"outcome":"not-attempted","reason":"validate-run produced no result"}'; fi
  git -C "$REPO" checkout -q README.md
  record C7d-validate-run-on-dirty-worktree "$s" false "validate-run refused (PRX.VALIDATION.DIRTY_WORKTREE); nothing to complete with" "$(accepted_t "$o")" "$(jq -cn --argjson v "$vd" --argjson c "$(summ "$o")" '{validateRun:$v, completeVerified:$c}')"
}

# ------------------------------------------------------------ treatment, attested mode (amendment A5; Praxis >= 3.17.0)
# A host verifier daemon (key in memory, socket outside the repository) and a host authority that pins its
# key and the policy digest; ros.json requires attested evidence. The policy validation fails when a file
# named FAIL is tracked, so one daemon produces genuine passing and genuine failing receipts.
attested_repo() { init_repo "$REPO" "$@"; jq -n '{workProtocol:{requireAttestedEvidence:true}}' > "$REPO/ros.json"
  git -C "$REPO" add ros.json && git -C "$REPO" commit -qm "require attested evidence"; }
attested() {
  local s o ev head A dig vline
  new_run C attested-verifier; A="$RUN_DIR/inputs/authority-attested.json"
  dig=$("$SDE" ecir check --blueprint "$VALID_CONTRACT" --json | jq -r .contractDigest)
  jq -n '{schemaVersion:"echelon.validation-policy/1", policyId:"rel001-c-attested",
    validations:[{name:"unit-tests", evidenceId:"EV-TESTS", command:["sh","-c","test ! -e FAIL"], timeoutSeconds:120}], protectedPaths:[]}' > "$RUN_DIR/inputs/policy.json"
  ( setsid "$PRAXIS" verifier serve --socket "$RUN_DIR/inputs/verifier.sock" --policy "$RUN_DIR/inputs/policy.json" --contract-digest "$dig" \
      > "$RUN_DIR/logs/verifier.out" 2> "$RUN_DIR/logs/verifier.err" < /dev/null & echo $! > "$RUN_DIR/logs/verifier.pid" )
  for _ in $(seq 1 120); do [ -s "$RUN_DIR/logs/verifier.out" ] && [ -S "$RUN_DIR/inputs/verifier.sock" ] && break; sleep 0.5; done
  vline=$(head -1 "$RUN_DIR/logs/verifier.out")
  write_authority "$A" "$(contract_decisions "$VALID_CONTRACT")"
  jq --argjson v "$vline" '. + {TrustedVerifierKeys:[{KeyId:$v.keyId, Algorithm:"ecdsa-p256-sha256", PublicKey:$v.publicKey}], ValidationPolicyDigest:$v.policyDigest}' "$A" > "$A.tmp" && mv "$A.tmp" "$A"
  local VDIR="$RUN_DIR" VSOCK="$RUN_DIR/inputs/verifier.sock"
  verify() { set +e; OUT=$(cd "$1" && PRAXIS_ACTOR="$2" PRAXIS_VERIFIER_SOCKET="$VSOCK" "$PRAXIS" work verify --id "$3" --token "$4" 2>&1); RC=$?; set -e; }
  identity() { (cd "$1" && "$PRAXIS" work completion-identity --id "$2" 2>/dev/null) | jq -c '{outcome, code, changedPaths, sourcePaths, clean}' 2>/dev/null || echo null; }

  # C8d genuine passing receipt (first: its envelope is the format template for C8b)
  s=$(now_ms); new_run C attested-genuine-pass; attested_repo ITEM-C
  t_claim "$REPO" w1 --id ITEM-C --token tok-1; verify "$REPO" w1 ITEM-C tok-1; local vr; vr=$(printf '%s' "$OUT" | jq -c '{outcome, receipts:[.receipts[]?.status]}')
  ev=$(printf '%s' "$OUT" | jq -r '.receipts[0].path'); cp "$ev" "$VDIR/inputs/genuine-receipt.json"
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev" "$VALID_CONTRACT" "$A"; o="$OUT"
  record C8d-attested-genuine-passing-receipt "$s" true "verified; completion identity consistent and clean" "$(accepted_t "$o")" \
    "$(jq -cn --argjson v "$vr" --argjson c "$(summ "$o")" --argjson i "$(identity "$REPO" ITEM-C)" '{verify:$v, completeVerified:$c, completionIdentity:$i}')"
  # C8a C3b in attested mode: forged result + forged validation event in the out-of-tree store
  s=$(now_ms); new_run C attested-forged-with-event; attested_repo ITEM-C; head=$(git -C "$REPO" rev-parse HEAD)
  t_claim "$REPO" w1 --id ITEM-C --token tok-1
  local common; common=$(git -C "$REPO" rev-parse --path-format=absolute --git-common-dir); mkdir -p "$common/praxis/validations/ITEM-C/EV-TESTS"
  local at; at=$(utc); ev=$(forge_result ITEM-C tok-1 1 "$head" "$at"); cp "$ev" "$common/praxis/validations/ITEM-C/EV-TESTS/1-${head:0:12}-forged.json"; ev="$common/praxis/validations/ITEM-C/EV-TESTS/1-${head:0:12}-forged.json"
  jq -cn --arg rev "$head" --arg at "$at" --arg d "sha256:$(sha256sum "$ev" | cut -d' ' -f1)" '{schemaVersion:"1.0.0",type:"work.validation.observed",workItem:"ITEM-C",repository:"repo",protocolVersion:"1.0.0",
    occurredAt:$at,claimant:"w1",claimToken:"tok-1",generation:1,validation:"unit-tests",evidenceId:"EV-TESTS",revision:$rev,status:"passed",observedAt:$at,resultDigest:$d,
    actor:{kind:"agent",id:"w1",provider:"test",model:"unknown",runtime:"test"},eventId:("forged" + ($d[7:25]))}' >> "$common/praxis/events.jsonl"
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev" "$VALID_CONTRACT" "$A"; o="$OUT"
  record C8a-attested-C3b-forged-result-and-event "$s" false "refused (RECEIPT_MISSING): only verifier-signed receipts complete" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" '{completeVerified:$c}')"
  # C8b self-signed receipt: the genuine receipt's exact format, re-bound to this claim and HEAD, signed with an own key
  s=$(now_ms); new_run C attested-self-signed; attested_repo ITEM-C; t_claim "$REPO" w1 --id ITEM-C --token tok-1
  head=$(git -C "$REPO" rev-parse HEAD); common=$(git -C "$REPO" rev-parse --path-format=absolute --git-common-dir); mkdir -p "$common/praxis/receipts/ITEM-C"
  ev="$common/praxis/receipts/ITEM-C/1-${head:0:12}-selfsigned.json"
  local kid; kid=$(python3 -I "$REL/gate/scripts/forge-receipt.py" "$VDIR/inputs/genuine-receipt.json" "$ev" "$REPO" ITEM-C own w1)
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev" "$VALID_CONTRACT" "$A"; o="$OUT"
  record C8b-attested-self-signed-receipt "$s" false "refused (RECEIPT_UNTRUSTED_KEY)" "$(accepted_t "$o")" "$(jq -cn --argjson c "$(summ "$o")" --arg k "$kid" '{completeVerified:$c, forgerKeyId:$k}')"
  # C8c genuine failing receipt
  s=$(now_ms); new_run C attested-genuine-fail; attested_repo ITEM-C; : > "$REPO/FAIL"; git -C "$REPO" add FAIL && git -C "$REPO" commit -qm "failing state"
  t_claim "$REPO" w1 --id ITEM-C --token tok-1; verify "$REPO" w1 ITEM-C tok-1; vr=$(printf '%s' "$OUT" | jq -c '{outcome, receipts:[.receipts[]?.status]}')
  ev=$(printf '%s' "$OUT" | jq -r '.receipts[0].path')
  t_complete "$REPO" w1 ITEM-C tok-1 1 "$ev" "$VALID_CONTRACT" "$A"; o="$OUT"
  record C8c-attested-genuine-failing-receipt "$s" false "refused (RECEIPT_NOT_PASSED)" "$(accepted_t "$o")" "$(jq -cn --argjson v "$vr" --argjson c "$(summ "$o")" '{verify:$v, completeVerified:$c}')"
  local pid; pid=$(cat "$VDIR/logs/verifier.pid"); kill -TERM -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
}

# ------------------------------------------------------------ baseline (Praxis 3.12.0: work complete --evidence)
b_complete() { # b_complete REPO ID TESTS-EVIDENCE-PATH|"" ACTOR -> sets OUT RC
  local args=(--evidence implementation=impl.txt); [ -n "$3" ] && args+=(--evidence "tests=$3")
  set +e; OUT=$(cd "$1" && PRAXIS_ACTOR="${4:-w1}" "$PRAXIS" work complete --id "$2" --occurred-at "$(utc)" "${args[@]}" 2>&1); RC=$?; set -e; }
b_new() { new_run C "$1"; shift; init_repo "$REPO" "$@"; printf 'impl\n' > "$REPO/impl.txt"; mkdir -p "$REPO/evidence"
  local id; for id in "$@"; do baseline_ready "$REPO" "$id"; (cd "$REPO" && PRAXIS_ACTOR=w1 "$PRAXIS" work start --id "$id" --occurred-at "$(utc)" >/dev/null); done; }
b_obs() { local st; st=$(printf '%s' "$OUT" | jq -c '[.workItems[]? | {id, state}]' 2>/dev/null) || st=null
  jq -cn --argjson rc "$RC" --argjson st "${st:-null}" --arg o "$(printf '%s' "$OUT" | head -c 200)" '{workCompleteExit:$rc} + (if $st != null then {items:$st} else {error:$o} end)'; }
b_acc() { [ "$RC" -eq 0 ] && echo 1 || echo 0; }

baseline() {
  local s
  s=$(now_ms); b_new valid ITEM-C; (cd "$REPO" && true > evidence/tests.log 2>&1; echo "exit 0" >> evidence/tests.log)
  b_complete "$REPO" ITEM-C evidence/tests.log; record C1-valid-test-log "$s" true "accepted" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); b_complete "$REPO" ITEM-C evidence/tests.log; record C4a-replay-same-completion "$s" false "no second completion" "$(b_acc)" "$(b_obs)"
  blocked C4b-consumed-packet-direct-to-dokimos "baseline has no completion packet or Dokimos step"
  s=$(now_ms); b_new replay-evidence-other-item ITEM-C ITEM-D; printf 'exit 0\n' > "$REPO/evidence/tests.log"; b_complete "$REPO" ITEM-C evidence/tests.log
  b_complete "$REPO" ITEM-D evidence/tests.log; record C4c-replay-evidence-on-other-item "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); b_new missing ITEM-C ITEM-D; b_complete "$REPO" ITEM-C ""; record C2a-missing-no-evidence "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); b_complete "$REPO" ITEM-D evidence/none.log; record C2b-missing-nonexistent-path "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); b_new forged ITEM-C; cp "$(forge_result ITEM-C none 1 "$(git -C "$REPO" rev-parse HEAD)" "$(utc)")" "$REPO/evidence/forged.json"
  b_complete "$REPO" ITEM-C evidence/forged.json; record C3a-forged-result-document "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  blocked C3b-forged-result-and-forged-observed-event "baseline has no validation-observed events to forge (C3a already covers a forged document)"
  s=$(now_ms); b_new stale-old-log ITEM-C; printf 'exit 0 (run 2026-01-01 at an unrelated commit)\n' > "$REPO/evidence/tests.log"
  b_complete "$REPO" ITEM-C evidence/tests.log; record C5a-stale-old-log-no-lease "$s" false "prediction: accepted (no lease or freshness)" "$(b_acc)" "$(b_obs)"
  blocked C5b-stale-result-from-before-current-claim "baseline has no claim generations"
  s=$(now_ms); b_new stale-pre-start ITEM-C; printf 'exit 0\n' > "$REPO/evidence/tests.log"
  b_complete "$REPO" ITEM-C evidence/tests.log; record C5c-stale-observed-before-start "$s" false "prediction: accepted (log predates work start)" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); b_new stale-revision-mismatch ITEM-C; printf 'exit 0\n' > "$REPO/evidence/tests.log"; git -C "$REPO" add -A; git -C "$REPO" commit -qm run
  printf 'changed after the run\n' >> "$REPO/README.md"; git -C "$REPO" commit -qam "change after validation"
  b_complete "$REPO" ITEM-C evidence/tests.log; record C5d-stale-commit-after-run "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); b_new binding ITEM-C; printf 'exit 0\n' > "$REPO/evidence/tests.log"
  b_complete "$REPO" ITEM-C evidence/tests.log; record C6a-binding-valid "$s" true "accepted" "$(b_acc)" "$(b_obs)"
  blocked C6b-binding-invalid-commit-older-than-evidence "baseline work complete takes no commit or revision; covered by C5d"
  blocked C6c-binding-invalid-evidence-from-other-revision "baseline work complete takes no commit or revision; covered by C5d"
  s=$(now_ms); b_new gate-regressions ITEM-G1 ITEM-G2 ITEM-G3; (cd "$REPO" && { false || echo "exit $?"; } > evidence/failing-run.log)
  b_complete "$REPO" ITEM-G1 evidence/failing-run.log; record C7a-recorded-failing-run "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); printf '12 test(s); 7 passed; 5 failed\n' > "$REPO/evidence/failing.txt"
  b_complete "$REPO" ITEM-G2 evidence/failing.txt; record C7b-failing-test-log-text "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  s=$(now_ms); printf 'not a test report\n' > "$REPO/evidence/unrelated.txt"
  b_complete "$REPO" ITEM-G3 evidence/unrelated.txt; record C7c-unrelated-file "$s" false "prediction: accepted" "$(b_acc)" "$(b_obs)"
  blocked C7d-validate-run-on-dirty-worktree "baseline has no validate-run"
}

"$ARM"
# Amendment A5: attested-mode cases run when the treatment Praxis provides the verifier (>= 3.17.0).
if [ "$ARM" = treatment ] && { "$PRAXIS" verifier 2>&1 || true; } | grep -q "verifier serve"; then attested; fi
echo "wrote $OUT_FILE ($(wc -l < "$OUT_FILE") cases)"
