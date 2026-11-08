#!/usr/bin/env bash
# Track E governance-bypass cases NOT covered by REL-001 gate-evidence-binding-v319.sh.
# usage: bypass-cases.sh PRAXIS DOKIMOS ORDO ORDO_CONTRACT WORKDIR
# Every repository is a fresh local fixture under WORKDIR; host files live in WORKDIR/host. Nothing else is touched.
# One JSON line per case on stdout: {case, attempt, expected, exit, outcome, codes, note}.
#   NX-1  default ros.json (as in all 45 surveyed repos): plain `work complete` citing /etc/hostname as "tests"
#   NX-2  item has a claim (plain complete refused); agent deletes <git-common-dir>/praxis/claims/ID, retries
#   NX-3  requireVerifiedCompletion on origin/main; worktree commit drops it -> plain `work complete`
#   NX-4  NX-3 plus `git update-ref refs/remotes/origin/main HEAD` (moves the local protected ref) -> plain complete
#   NX-5  requireAttestedEvidence+pin on origin/main; agent commits weakened ros.json, moves origin/main+origin/HEAD
#         locally, forges result+event, complete-verified (documented residual limit; checks it still holds)
#   NX-6  requireAttestedEvidence in a repo with NO remote (history binding); agent rewrites history into an orphan
#         root without the flag, forges result+event, complete-verified
#   NX-7  requireVerifiedCompletion+allowUnattestedEvidence (non-attested): caller-chosen authority requiring NO
#         validations and NO evidence -> complete-verified with zero evidence
#   NX-8  validate-run at commit A, new source commit B, complete-verified at B citing A's result (other revision)
#   NX-9  hand-edited .ros/work/queue.json marks an item complete (no transition) -> do status/verify/validate notice?
#   NX-10 `work evidence --kind owner-approval` recorded by the agent claiming --actor-kind human --actor the owner
set -euo pipefail
PRAXIS="$1"; DOKIMOS="$2"; ORDO="$3"; CONTRACT="$4"; W="$5"
rm -rf "${W:?}"; mkdir -p "$W/host"; H="$W/host"; cp "$CONTRACT" "$H/contract.json"
DIGEST=$("$ORDO" ecir check --blueprint "$H/contract.json" --json | jq -r .contractDigest)
export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=e-track/agent PRAXIS_TELEMETRY_PROVIDER=test PRAXIS_TELEMETRY_RUNTIME=test PRAXIS_DOKIMOS_EXECUTABLE="$DOKIMOS"
unset PRAXIS_VERIFIER_SOCKET PRAXIS_COMPLETION_AUTHORITY PRAXIS_ORDO_CONTRACT
REQS=(--requirement "requirements/domain.md#R-001" --requirement "requirements/operations.md#R-001" --decision DEC-CONFIRM)
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
gitc() { git -C "$1" -c commit.gpgsign=false -c push.negotiate=false -c user.email=e@example.invalid -c user.name=e "${@:2}"; }

emit() { # CASE ATTEMPT EXPECTED EXIT OUTPUT NOTE
  jq -cn --arg c "$1" --arg a "$2" --arg x "$3" --argjson rc "$4" --arg o "$5" --arg n "${6:-}" '
    ($o | try fromjson catch {unparsed: $o[0:400]}) as $d
    | {case:$c, attempt:$a, expected:$x, exit:$rc,
       outcome:($d.outcome // (if $rc == 0 then "accepted" else "refused" end)),
       codes:((($d.codes // []) + (if $d.code then [$d.code] else [] end) + ([$o | scan("PRX\\.[A-Z_]+\\.[A-Z_]+")])) | unique),
       detail:($d.unparsed // null), note:$n}'; }
run() { set +e; OUT=$("$@" 2>&1); RC=$?; set -e; }

# new_repo ID ROSJSON(or "") [remote]: fresh repo with queue item ID (ready->active not needed for claims)
new_repo() {
  local r="$W/$1"; mkdir -p "$r/.ros/work"
  jq -cn --arg id "$1" '{schemaVersion:"1.0.0",items:[{id:$id,status:"captured"}]}' > "$r/.ros/work/queue.json"
  [ -n "$2" ] && printf '%s\n' "$2" > "$r/ros.json"
  git -C "$r" init -q -b main . && gitc "$r" add -A && gitc "$r" commit -qm fixture
  if [ "${3:-}" = remote ]; then
    git init -q --bare "$W/$1.remote.git"; git -C "$r" remote add origin "$W/$1.remote.git"
    gitc "$r" push -q origin main; git -C "$r" remote set-head origin main
  fi
  echo "$r"
}
store() { echo "$(git -C "$1" rev-parse --path-format=absolute --git-common-dir)/praxis"; }
claim() { (cd "$1" && "$PRAXIS" work claim --id "$2" --token "tok-$2" --lease-seconds 1800 > /dev/null); }
authority() { # FILE REQUIRED-VALIDATIONS-JSON REQUIRED-EVIDENCE-JSON
  jq -n --argjson v "$2" --argjson e "$3" '{OrdoContractVersion:"",OrdoContractDigest:"",SupportedOrdoContractVersions:["ecir/1"],
    RequiredRequirementIds:[],RequiredDecisionIds:["DEC-CONFIRM"],RequiredConflictResolutionIds:[],RequiredValidationNames:$v,RequiredEvidenceIds:$e}' > "$1"; }
forge_result() { # REPO ID -> path of a hand-made passed praxis.validation-result/1 in the store
  local r="$1" id="$2" sha at dir f; sha=$(git -C "$r" rev-parse HEAD); at=$(utc)
  dir="$(store "$r")/validations/$id/EV-TESTS"; mkdir -p "$dir"; f="$dir/1-${sha:0:12}-$(date -u +%Y%m%dT%H%M%S%3NZ).json"
  jq -cn --arg id "$id" --arg r "$sha" --arg at "$at" '{schemaVersion:"praxis.validation-result/1",workItemId:$id,claimant:"e-track/agent",claimToken:("tok-"+$id),generation:1,
    validation:"unit-tests",evidenceId:"EV-TESTS",revision:$r,observedAt:$at,startedAt:$at,status:"passed",exitCode:0,command:["true"],
    outputSha256:"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}' | tr -d '\n' > "$f"; echo "$f"; }
forge_event() { # REPO ID RESULT
  local r="$1" id="$2" f="$3" at; at=$(jq -r .observedAt "$f")
  jq -cn --arg id "$id" --arg rev "$(jq -r .revision "$f")" --arg at "$at" --arg d "sha256:$(sha256sum "$f" | cut -d' ' -f1)" --arg repo "$(basename "$r")" '
    {schemaVersion:"1.0.0",type:"work.validation.observed",workItem:$id,repository:$repo,protocolVersion:"1.0.0",occurredAt:$at,claimant:"e-track/agent",
     claimToken:("tok-"+$id),generation:1,validation:"unit-tests",evidenceId:"EV-TESTS",revision:$rev,status:"passed",observedAt:$at,resultDigest:$d,
     actor:{kind:"agent",id:"e-track/agent",provider:"test",model:"unknown",runtime:"test"},eventId:("forged"+($d[7:25]))}' >> "$(store "$r")/events.jsonl"; }
complete_explicit() { # REPO ID EVIDENCE AUTHORITY [extra...]
  local sha; sha=$(git -C "$1" rev-parse HEAD)
  run bash -c 'cd "$1" && shift && "$@"' _ "$1" "$PRAXIS" work complete-verified --id "$2" --token "tok-$2" --generation 1 --commit "$sha" \
    --verification-revision "$sha" --authority "$4" --ordo-contract "$H/contract.json" "${REQS[@]}" \
    --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=$3"; }
plain_complete() { # REPO ID  (ready -> start -> complete with in-repo README as "implementation" and /etc/hostname as "tests")
  (cd "$1" && "$PRAXIS" work backlog-transition --id "$2" --action ready --occurred-at "$(utc)" >/dev/null 2>&1 || true
   "$PRAXIS" work start --id "$2" --occurred-at "$(utc)" >/dev/null 2>&1 || true)
  run bash -c 'cd "$1" && shift && "$@"' _ "$1" "$PRAXIS" work complete --id "$2" --occurred-at "$(utc)" \
    --evidence implementation=ros.json --evidence tests=/etc/hostname --conclusion "all tests pass"; }

# ---- NX-1
r=$(new_repo NX-1 '{}'); plain_complete "$r" NX-1
emit NX-1 "default policy; plain work complete citing /etc/hostname as tests evidence; no test run" "weakness if accepted" "$RC" "$OUT" \
  "$( (cd "$r" && "$PRAXIS" verify >/dev/null 2>&1 && echo verify=0 || echo verify!=0); (cd "$r" && "$PRAXIS" work validate 2>/dev/null | jq -c '{valid,findings:(.findings|length)}') )"

# ---- NX-2
r=$(new_repo NX-2 '{}'); claim "$r" NX-2; plain_complete "$r" NX-2
emit NX-2a "claimed item; plain work complete" "refused (VERIFIED_COMPLETION_REQUIRED)" "$RC" "$OUT"
rm -rf "$(store "$r")/claims/NX-2"; plain_complete "$r" NX-2
emit NX-2b "after deleting <git-common-dir>/praxis/claims/NX-2; plain work complete" "weakness if accepted" "$RC" "$OUT"

# ---- NX-3 / NX-4
r=$(new_repo NX-3 '{"workProtocol":{"requireVerifiedCompletion":true}}' remote)
printf '{}\n' > "$r/ros.json"; gitc "$r" commit -qam "drop requireVerifiedCompletion"; plain_complete "$r" NX-3
emit NX-3 "protected origin/main requires verified completion; worktree commit drops it; plain complete" "refused" "$RC" "$OUT"
git -C "$r" update-ref refs/remotes/origin/main HEAD; plain_complete "$r" NX-3
emit NX-4 "NX-3 then git update-ref refs/remotes/origin/main HEAD (local ref only, no push); plain complete" "documented residual limit" "$RC" "$OUT"

# ---- NX-5 / NX-6 need a pin; any well-formed key id serves (the authority below has no keys, so completion
# would be refused with ATTESTATION_REQUIRED if the policy were still in force).
PIN="sha256:$(printf host-verifier | sha256sum | cut -d' ' -f1)"
A="$H/authority-nokeys.json"; authority "$A" '["unit-tests"]' '["EV-TESTS"]'
r=$(new_repo NX-5 "$(jq -cn --arg p "$PIN" '{workProtocol:{requireAttestedEvidence:true,trustedVerifierKeyIds:[$p]}}')" remote)
claim "$r" NX-5; f=$(forge_result "$r" NX-5); forge_event "$r" NX-5 "$f"; complete_explicit "$r" NX-5 "$f" "$A"
emit NX-5a "attested policy on origin/main; forged result+event; keyless authority" "refused (ATTESTATION_REQUIRED)" "$RC" "$OUT"
r=$(new_repo NX-5B "$(jq -cn --arg p "$PIN" '{workProtocol:{requireAttestedEvidence:true,trustedVerifierKeyIds:[$p]}}')" remote)
printf '{}\n' > "$r/ros.json"; gitc "$r" commit -qam "weaken"; git -C "$r" update-ref refs/remotes/origin/main HEAD
claim "$r" NX-5B; f=$(forge_result "$r" NX-5B); forge_event "$r" NX-5B "$f"; complete_explicit "$r" NX-5B "$f" "$A"
emit NX-5B "weakened ros.json committed + local origin/main moved to HEAD; forged result+event; keyless authority" "documented residual limit" "$RC" "$OUT"

r=$(new_repo NX-6 "$(jq -cn --arg p "$PIN" '{workProtocol:{requireAttestedEvidence:true,trustedVerifierKeyIds:[$p]}}')")
printf '{}\n' > "$r/ros.json"; gitc "$r" commit -qam "weaken"; claim "$r" NX-6; f=$(forge_result "$r" NX-6); forge_event "$r" NX-6 "$f"
complete_explicit "$r" NX-6 "$f" "$A"
emit NX-6a "no remote; weakening commit on top of attested history; forged evidence" "refused (POLICY_CHANGED)" "$RC" "$OUT"
r=$(new_repo NX-6B "$(jq -cn --arg p "$PIN" '{workProtocol:{requireAttestedEvidence:true,trustedVerifierKeyIds:[$p]}}')")
printf '{}\n' > "$r/ros.json"; gitc "$r" checkout -q --orphan rewritten; gitc "$r" add -A; gitc "$r" commit -qm "rewritten root"
gitc "$r" branch -D main -q; gitc "$r" branch -m main; gitc "$r" reflog expire --expire=now --all; gitc "$r" gc -q --prune=now
claim "$r" NX-6B; f=$(forge_result "$r" NX-6B); forge_event "$r" NX-6B "$f"; complete_explicit "$r" NX-6B "$f" "$A"
emit NX-6B "no remote; history rewritten to an orphan root without the flag; forged evidence" "documented residual limit" "$RC" "$OUT"

# ---- NX-7
r=$(new_repo NX-7 '{"workProtocol":{"requireVerifiedCompletion":true,"allowUnattestedEvidence":true}}'); claim "$r" NX-7
A0="$H/authority-empty.json"; authority "$A0" '[]' '[]'; sha=$(git -C "$r" rev-parse HEAD)
run bash -c 'cd "$1" && shift && "$@"' _ "$r" "$PRAXIS" work complete-verified --id NX-7 --token tok-NX-7 --generation 1 --commit "$sha" \
  --verification-revision "$sha" --authority "$A0" --ordo-contract "$H/contract.json" "${REQS[@]}"
emit NX-7 "non-attested verified mode; caller-chosen authority requiring no validations/evidence; zero evidence" "weakness if verified" "$RC" "$OUT"

# ---- NX-8
r=$(new_repo NX-8 '{}'); claim "$r" NX-8
vr=$(cd "$r" && "$PRAXIS" work validate-run --id NX-8 --token tok-NX-8 --generation 1 --validation unit-tests --evidence-id EV-TESTS -- true 2>/dev/null || true)
ev=$(jq -r '.resultPath // empty' <<<"$vr"); case "$ev" in /*) ;; *) ev="$r/$ev";; esac
echo "changed" > "$r/src.txt"; gitc "$r" add -A; gitc "$r" commit -qm "new source after validation"
A1="$H/authority.json"; authority "$A1" '["unit-tests"]' '["EV-TESTS"]'; complete_explicit "$r" NX-8 "$ev" "$A1"
emit NX-8 "evidence observed at revision A cited for completion at revision B" "refused (EVIDENCE_REVISION_MISMATCH)" "$RC" "$OUT"

# ---- NX-9
r="$W/NX-9"; mkdir -p "$r"; git -C "$r" init -q -b main; (cd "$r" && "$PRAXIS" init >/dev/null 2>&1); gitc "$r" add -A; gitc "$r" commit -qm init
(cd "$r" && "$PRAXIS" work capture --title t --id NX-9 --occurred-at "$(utc)" >/dev/null 2>&1)
jq '(.items[] | select(.id=="NX-9") | .status) = "complete"' "$r/.ros/work/queue.json" > "$H/q.json" && cp "$H/q.json" "$r/.ros/work/queue.json"
run bash -c 'cd "$1" && "$2" work validate; echo "verify-exit=$("$2" verify >/dev/null 2>&1; echo $?)"; "$2" work show NX-9' _ "$r" "$PRAXIS"
emit NX-9 "queue.json status hand-edited to complete" "detected?" "$RC" "$OUT" "$(jq -c '.items[]|select(.id=="NX-9")' "$r/.ros/work/queue.json")"

# ---- NX-10
run bash -c 'cd "$1" && "$2" work backlog-transition --id NX-9b --action ready --occurred-at x >/dev/null 2>&1; true' _ "$r" "$PRAXIS"
(cd "$r" && "$PRAXIS" work capture --title t2 --id NX-10 --occurred-at "$(utc)" >/dev/null 2>&1 && "$PRAXIS" work backlog-transition --id NX-10 --action ready --occurred-at "$(utc)" >/dev/null 2>&1 && "$PRAXIS" work start --id NX-10 --occurred-at "$(utc)" >/dev/null 2>&1) || true
run bash -c 'cd "$1" && "$2" work evidence --id NX-10 --kind owner-approval --summary "Owner approves release" --occurred-at "$3" --outcome approved --actor-kind human --actor kemiller2002 --json' _ "$r" "$PRAXIS" "$(utc)"
emit NX-10 "agent records owner-approval evidence claiming actor-kind human / actor = owner login" "weakness if accepted without authentication" "$RC" "$OUT"
