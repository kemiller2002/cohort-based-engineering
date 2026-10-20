#!/usr/bin/env bash
# REL-001 Experiment A: concurrent ownership. usage: harness/a/run.sh baseline|treatment
# One JSON line per case -> results/a/<arm>.jsonl. Gate metrics per case:
#   duplicateActiveOwners  processes that concurrently hold ownership beyond the first
#   staleCompletionsAccepted  completions accepted from a non-current owner
#   lostWork  1 when the item ends neither completed nor recoverable by a new worker
source "$(dirname "$0")/../lib.sh"
arm_init "$1"
OUT_FILE="$REL/results/a/$ARM${REL001_RESULTS_TAG:+-$REL001_RESULTS_TAG}.jsonl"; mkdir -p "$(dirname "$OUT_FILE")"; : > "$OUT_FILE"  # A5: REL001_RESULTS_TAG names a re-run file, never overwriting
K=8; CLONES=4; ROUNDS="${ROUNDS:-5}"

# race N CMD-FN: N background workers block on a barrier file, then run "CMD-FN i" together.
race() { local n="$1" fn="$2" i; rm -f "$RUN_DIR/go"
  for i in $(seq 1 "$n"); do ( while [ ! -f "$RUN_DIR/go" ]; do :; done; "$fn" "$i" ) & done
  sleep 0.3; touch "$RUN_DIR/go"; wait; }

record() { # record CASE START_MS EXPECTED OBSERVED-JSON METRICS-JSON MATCH
  emit "$OUT_FILE" "$(jq -cn --arg c "$1" --argjson w $(( $(now_ms) - $2 )) --arg e "$3" --argjson o "$4" --argjson m "$5" --argjson p "$6" \
    '{experiment:"A", case:$c, status:"executed", expected:$e, observed:$o, metrics:$m, matchesPrediction:$p, wallMs:$w}')"; }
na() { emit "$OUT_FILE" "$(jq -cn --arg c "$1" --arg r "$2" '{experiment:"A", case:$c, status:"not-applicable", reason:$r, metrics:null, matchesPrediction:null, wallMs:0}')"; }

# ---------------------------------------------------------------- treatment
t_local_worker() { t_claim "$REPO" "w$1" --id ITEM-A --token "tok-$1" --store local
  printf '%s' "$OUT" > "$RUN_DIR/logs/claim-$1.json"; echo "$RC" > "$RUN_DIR/logs/claim-$1.rc"
  # retries: a refused worker retries 3 times with backoff; a winner never retries.
  if [ "$RC" -ne 0 ]; then for r in 1 2 3; do sleep 0.1; t_claim "$REPO" "w$1" --id ITEM-A --token "tok-$1" --store local
    printf '%s' "$OUT" > "$RUN_DIR/logs/claim-$1-retry$r.json"; done; fi; }

t_race_local() { local round="$1" s; s=$(now_ms); new_run A "local-race-r$round"; init_repo "$REPO" ITEM-A
  race "$K" t_local_worker
  local winners retryWins state
  winners=$(cat "$RUN_DIR"/logs/claim-[0-9].json | jq -s '[.[] | select(.outcome=="recorded")] | length' 2>/dev/null || echo -1)
  retryWins=$(ls "$RUN_DIR"/logs/claim-*-retry*.json 2>/dev/null | xargs -r cat | jq -s '[.[] | select(.outcome=="recorded")] | length')
  local codes; codes=$(cat "$RUN_DIR"/logs/claim-[0-9].json | jq -sc 'map(.outcome + ":" + (.code // "")) | group_by(.) | map({(.[0]): length}) | add')
  state=$(claim_state "$REPO" ITEM-A)
  local holders; holders=$(( winners + retryWins ))
  record "A1-local-race-K$K-round$round" "$s" "exactly one recorded claim among $K concurrent workers; retries refused" \
    "$(jq -cn --argjson c "$codes" --argjson st "$state" --argjson rw "$retryWins" '{claimOutcomes:$c, retryAcquisitions:$rw, finalClaim:$st}')" \
    "$(jq -cn --argjson h "$holders" '{workers:8, owners:$h, duplicateActiveOwners:([0,$h-1]|max), staleCompletionsAccepted:0, lostWork:0}')" \
    "$( [ "$holders" -eq 1 ] && echo true || echo false )"; }

t_git_worker() { t_claim "$RUN_DIR/clone$1" "w$1" --id ITEM-A --token "tok-$1" --store git --remote origin
  printf '%s' "$OUT" > "$RUN_DIR/logs/claim-$1.json"; }

setup_clones() { git init -q --bare "$RUN_DIR/origin.git"; init_repo "$REPO" ITEM-A
  git -C "$REPO" remote add origin "$RUN_DIR/origin.git"; git -C "$REPO" push -q origin HEAD:refs/heads/main
  for i in $(seq 1 "$CLONES"); do git clone -q -b main "$RUN_DIR/origin.git" "$RUN_DIR/clone$i"
    git -C "$RUN_DIR/clone$i" config user.email "c$i@example.invalid"; git -C "$RUN_DIR/clone$i" config user.name "c$i"; done; }

t_race_git() { local round="$1" s; s=$(now_ms); new_run A "git-race-r$round"; setup_clones
  race "$CLONES" t_git_worker
  local winners codes refs
  winners=$(cat "$RUN_DIR"/logs/claim-[0-9].json | jq -s '[.[] | select(.outcome=="recorded")] | length' 2>/dev/null || echo -1)
  codes=$(cat "$RUN_DIR"/logs/claim-[0-9].json | jq -sc 'map(.outcome + ":" + (.code // "")) | group_by(.) | map({(.[0]): length}) | add' 2>/dev/null || echo null)
  refs=$(git --git-dir "$RUN_DIR/origin.git" for-each-ref --format='%(refname)' 'refs/praxis/claims/*' | jq -Rsc 'split("\n")|map(select(.!=""))')
  record "A2-git-ref-race-clones$CLONES-round$round" "$s" "exactly one clone acquires through the bare origin" \
    "$(jq -cn --argjson c "$codes" --argjson r "$refs" '{claimOutcomes:$c, originClaimRefs:$r}')" \
    "$(jq -cn --argjson h "$winners" '{workers:4, owners:$h, duplicateActiveOwners:([0,$h-1]|max), staleCompletionsAccepted:0, lostWork:0}')" \
    "$( [ "$winners" -eq 1 ] && echo true || echo false )"; }

t_retry_replay() { local s; s=$(now_ms); new_run A retry-replay; init_repo "$REPO" ITEM-A
  t_claim "$REPO" w1 --id ITEM-A --token tok-1; local first rev1; first=$(summ "$OUT"); rev1=$(printf '%s' "$OUT" | jq '.claim.revision')
  t_claim "$REPO" w1 --id ITEM-A --token tok-1; local again rev2; again=$(summ "$OUT"); rev2=$(printf '%s' "$OUT" | jq '.claim.revision')
  t_claim "$REPO" w2 --id ITEM-A --token tok-2; local other; other=$(summ "$OUT")
  t_claim "$REPO" w1 --id ITEM-A --token tok-1b; local newtoken; newtoken=$(summ "$OUT")
  local acq; acq=$(count_events "$REPO" work.claim.acquired)
  record A3-retry-and-replay "$s" "same acquisition re-sent is replayed without a new revision or event; other claimant and new token refused" \
    "$(jq -cn --argjson a "$first" --argjson b "$again" --argjson c "$other" --argjson d "$newtoken" --argjson r1 "$rev1" --argjson r2 "$rev2" --argjson e "$acq" \
      '{first:$a, resent:$b, otherClaimant:$c, sameClaimantNewToken:$d, revisionBefore:$r1, revisionAfterResend:$r2, acquiredEvents:$e}')" \
    "$(jq -cn --argjson e "$acq" '{owners:1, duplicateActiveOwners:0, duplicateAcquiredEvents:([0,$e-1]|max), staleCompletionsAccepted:0, lostWork:0}')" \
    "$(printf '%s' "$again" | jq -r '.outcome=="replayed"' )"; }

t_expiry_recovery() { local s; s=$(now_ms); new_run A lease-expiry-recovery; init_repo "$REPO" ITEM-A
  t_claim "$REPO" w1 --id ITEM-A --token tok-1 --lease-seconds 2; local c1; c1=$(summ "$OUT")
  sleep 3
  t_cmd "$REPO" w1 work renew --id ITEM-A --token tok-1 --generation 1; local renew; renew=$(summ "$OUT")
  t_cmd "$REPO" w2 work recover --id ITEM-A --token tok-2; local rec gen; rec=$(summ "$OUT"); gen=$(printf '%s' "$OUT" | jq '.claim.generation // null')
  t_validate "$REPO" w1 ITEM-A tok-1 1 true; local oldval; oldval=$(summ "$OUT")
  t_validate "$REPO" w2 ITEM-A tok-2 2 true; local newval; newval=$(summ "$OUT")
  t_complete "$REPO" w2 ITEM-A tok-2 2 "$EVPATH"; local done_; done_=$(summ "$OUT")
  local st; st=$(claim_state "$REPO" ITEM-A)
  local stale=0 lost=1; [ "$(printf '%s' "$oldval" | jq -r .outcome)" = recorded ] && stale=1
  [ "$(printf '%s' "$done_" | jq -r .outcome)" = verified ] && lost=0
  record A4-short-lease-expiry-recovery "$s" "expired owner cannot renew or validate; new claimant recovers at generation 2 and completes" \
    "$(jq -cn --argjson a "$c1" --argjson b "$renew" --argjson c "$rec" --argjson g "$gen" --argjson d "$oldval" --argjson e "$newval" --argjson f "$done_" --argjson st "$st" \
       '{claim:$a, expiredRenew:$b, recover:$c, recoveredGeneration:$g, expiredOwnerValidate:$d, newOwnerValidate:$e, newOwnerComplete:$f, finalClaim:$st}')" \
    "$(jq -cn --argjson s $stale --argjson l $lost '{owners:1, duplicateActiveOwners:0, staleCompletionsAccepted:$s, lostWork:$l}')" \
    "$( [ $stale -eq 0 ] && [ $lost -eq 0 ] && echo true || echo false )"; }

t_kill_validate() { local s; s=$(now_ms); new_run A sigkill-during-validate-run; init_repo "$REPO" ITEM-A
  t_claim "$REPO" w1 --id ITEM-A --token tok-1 --lease-seconds 4
  ( cd "$REPO" && PRAXIS_ACTOR=w1 setsid "$PRAXIS" work validate-run --id ITEM-A --token tok-1 --generation 1 --validation unit-tests --evidence-id EV-TESTS -- sleep 30 > "$RUN_DIR/logs/killed.out" 2>&1 ) &
  local pid=$!; sleep 1.5; local pg; pg=$(pgrep -f "evidence-id EV-TESTS -- sleep 30" | head -1 || true)
  [ -n "$pg" ] && kill -9 -- "-$(ps -o pgid= "$pg" | tr -d ' ')" 2>/dev/null || true; wait $pid 2>/dev/null || true
  local after; after=$(claim_state "$REPO" ITEM-A)
  local observed; observed=$(count_events "$REPO" work.validation.observed)
  sleep 3.5
  t_cmd "$REPO" w2 work recover --id ITEM-A --token tok-2; local rec; rec=$(summ "$OUT")
  t_validate "$REPO" w2 ITEM-A tok-2 2 true; t_complete "$REPO" w2 ITEM-A tok-2 2 "$EVPATH"; local done_; done_=$(summ "$OUT")
  t_complete "$REPO" w1 ITEM-A tok-1 1 "$EVPATH"; local old; old=$(summ "$OUT")
  local lost=1 stale=0; [ "$(printf '%s' "$done_" | jq -r .outcome)" = verified ] && lost=0
  case "$(printf '%s' "$old" | jq -r .outcome)" in verified|replayed) stale=1;; esac
  record A5-sigkill-during-validate-run "$s" "killed validate-run leaves no passing evidence; after expiry a new claimant recovers and completes; old owner refused" \
    "$(jq -cn --argjson a "$after" --argjson o "$observed" --argjson r "$rec" --argjson d "$done_" --argjson x "$old" '{claimAfterKill:$a, validationObservedEventsAfterKill:$o, recover:$r, newOwnerComplete:$d, oldOwnerComplete:$x}')" \
    "$(jq -cn --argjson s $stale --argjson l $lost '{owners:1, duplicateActiveOwners:0, staleCompletionsAccepted:$s, lostWork:$l}')" \
    "$( [ $stale -eq 0 ] && [ $lost -eq 0 ] && echo true || echo false )"; }

# A6: a delaying wrapper in front of the real Dokimos opens a window to SIGKILL complete-verified.
make_slow_dokimos() { cat > "$RUN_DIR/inputs/slow-dokimos" <<EOF
#!/usr/bin/env bash
sleep \${SLOW_DOKIMOS_SECONDS:-0}
exec "$DOKIMOS" "\$@"
EOF
  chmod +x "$RUN_DIR/inputs/slow-dokimos"; }

kill_complete() { # kill_complete ACTOR TOKEN GEN EV
  ( export PRAXIS_DOKIMOS_EXECUTABLE="$RUN_DIR/inputs/slow-dokimos" SLOW_DOKIMOS_SECONDS=6
    exec setsid bash -c 'source "$1/lib.sh"; arm_init treatment; RUN_DIR="$2"; export PRAXIS_DOKIMOS_EXECUTABLE="$2/inputs/slow-dokimos"; t_complete "$3" "$4" ITEM-A "$5" "$6" "$7"; printf "%s" "$OUT" > "$2/logs/killed-complete.out"' _ "$REL/harness" "$RUN_DIR" "$REPO" "$1" "$2" "$3" "$4" ) &
  local pid=$!; sleep 2.5; kill -9 -- "-$pid" 2>/dev/null || true; wait $pid 2>/dev/null || true
  pkill -9 -f "$RUN_DIR/inputs/slow-dokimos" 2>/dev/null || true; }

t_kill_complete_same_holder() { local s; s=$(now_ms); new_run A sigkill-during-complete-verified-retry; init_repo "$REPO" ITEM-A; make_slow_dokimos
  t_claim "$REPO" w1 --id ITEM-A --token tok-1 --lease-seconds 120; t_validate "$REPO" w1 ITEM-A tok-1 1 true; local ev="$EVPATH"
  kill_complete w1 tok-1 1 "$ev"; local after; after=$(claim_state "$REPO" ITEM-A)
  t_complete "$REPO" w1 ITEM-A tok-1 1 "$ev"; local retry; retry=$(summ "$OUT")
  t_complete "$REPO" w1 ITEM-A tok-1 1 "$ev"; local again; again=$(summ "$OUT")
  local verified; verified=$(count_events "$REPO" work.completion.verified); local st; st=$(claim_state "$REPO" ITEM-A)
  local lost=1; [ "$(printf '%s' "$st" | jq -r .status)" = completed ] && lost=0
  record A6a-sigkill-during-complete-verified-holder-retries "$s" "kill leaves awaiting-verification; same holder retrying the same packet completes exactly once" \
    "$(jq -cn --argjson a "$after" --argjson r "$retry" --argjson g "$again" --argjson v "$verified" --argjson st "$st" '{claimAfterKill:$a, retry:$r, secondRetry:$g, verifiedEvents:$v, finalClaim:$st}')" \
    "$(jq -cn --argjson l $lost --argjson v "$verified" '{owners:1, duplicateActiveOwners:0, duplicateCompletions:([0,$v-1]|max), staleCompletionsAccepted:0, lostWork:$l}')" \
    "$( [ $lost -eq 0 ] && [ "$verified" -eq 1 ] && echo true || echo false )"; }

t_kill_complete_recover() { local s; s=$(now_ms); new_run A sigkill-during-complete-verified-recover; init_repo "$REPO" ITEM-A; make_slow_dokimos
  t_claim "$REPO" w1 --id ITEM-A --token tok-1 --lease-seconds 5; t_validate "$REPO" w1 ITEM-A tok-1 1 true; local ev1="$EVPATH"
  kill_complete w1 tok-1 1 "$ev1"; local after; after=$(claim_state "$REPO" ITEM-A)
  sleep 4
  t_cmd "$REPO" w2 work recover --id ITEM-A --token tok-2; local rec; rec=$(summ "$OUT")
  t_validate "$REPO" w2 ITEM-A tok-2 2 true; t_complete "$REPO" w2 ITEM-A tok-2 2 "$EVPATH"; local done_; done_=$(summ "$OUT")
  t_complete "$REPO" w1 ITEM-A tok-1 1 "$ev1"; local old; old=$(summ "$OUT")
  local verified; verified=$(count_events "$REPO" work.completion.verified); local st; st=$(claim_state "$REPO" ITEM-A)
  local lost=1 stale=0; [ "$(printf '%s' "$st" | jq -r .status)" = completed ] && lost=0
  case "$(printf '%s' "$old" | jq -r .outcome)" in verified|replayed) stale=1;; esac
  record A6b-sigkill-during-complete-verified-then-recovery "$s" "after kill and expiry a new claimant recovers at generation 2 and completes; the old owner's retry is refused" \
    "$(jq -cn --argjson a "$after" --argjson r "$rec" --argjson d "$done_" --argjson o "$old" --argjson v "$verified" --argjson st "$st" '{claimAfterKill:$a, recover:$r, newOwnerComplete:$d, oldOwnerRetry:$o, verifiedEvents:$v, finalClaim:$st}')" \
    "$(jq -cn --argjson l $lost --argjson s $stale --argjson v "$verified" '{owners:1, duplicateActiveOwners:0, duplicateCompletions:([0,$v-1]|max), staleCompletionsAccepted:$s, lostWork:$l}')" \
    "$( [ $lost -eq 0 ] && [ $stale -eq 0 ] && echo true || echo false )"; }

t_stale_owner() { local s; s=$(now_ms); new_run A delayed-completion-stale-owner; init_repo "$REPO" ITEM-A ITEM-B
  # recovered: w1 validated within its lease, w2 recovered after expiry, then w1 tries to complete.
  t_claim "$REPO" w1 --id ITEM-A --token tok-1 --lease-seconds 3; t_validate "$REPO" w1 ITEM-A tok-1 1 true; local ev1="$EVPATH"
  sleep 4; t_cmd "$REPO" w2 work recover --id ITEM-A --token tok-2
  t_complete "$REPO" w1 ITEM-A tok-1 1 "$ev1"; local recovered; recovered=$(summ "$OUT")
  t_validate "$REPO" w2 ITEM-A tok-2 2 true; t_complete "$REPO" w2 ITEM-A tok-2 2 "$EVPATH"; local w2done; w2done=$(summ "$OUT")
  # unrecovered: lease expired, nobody recovered, owner completes late.
  t_claim "$REPO" w1 --id ITEM-B --token tok-b1 --lease-seconds 3; t_validate "$REPO" w1 ITEM-B tok-b1 1 true; local evb="$EVPATH"
  sleep 4; t_complete "$REPO" w1 ITEM-B tok-b1 1 "$evb"; local late; late=$(summ "$OUT")
  t_cmd "$REPO" w3 work recover --id ITEM-B --token tok-b3; local recb; recb=$(summ "$OUT")
  local stale=0
  for o in "$recovered" "$late"; do case "$(printf '%s' "$o" | jq -r .outcome)" in verified|replayed) stale=$((stale+1));; esac; done
  local lost=0; [ "$(printf '%s' "$w2done" | jq -r .outcome)" = verified ] || lost=$((lost+1)); [ "$(printf '%s' "$recb" | jq -r .outcome)" = recorded ] || lost=$((lost+1))
  record A7-delayed-completion-by-stale-owner "$s" "late completion by an expired owner is refused whether or not the item was recovered; the item stays completable/recoverable" \
    "$(jq -cn --argjson a "$recovered" --argjson b "$w2done" --argjson c "$late" --argjson d "$recb" '{staleOwnerAfterRecovery:$a, newOwnerComplete:$b, staleOwnerUnrecovered:$c, laterRecoverOfUnrecovered:$d}')" \
    "$(jq -cn --argjson s $stale --argjson l $lost '{owners:1, duplicateActiveOwners:0, staleCompletionsAccepted:$s, lostWork:$l}')" \
    "$( [ $stale -eq 0 ] && [ $lost -eq 0 ] && echo true || echo false )"; }

t_git_expiry() { local s; s=$(now_ms); new_run A git-ref-expiry-recovery; setup_clones
  t_claim "$RUN_DIR/clone1" w1 --id ITEM-A --token tok-1 --lease-seconds 2 --store git --remote origin; local c1; c1=$(summ "$OUT")
  t_claim "$RUN_DIR/clone2" w2 --id ITEM-A --token tok-2 --store git --remote origin; local held; held=$(summ "$OUT")
  sleep 3
  t_cmd "$RUN_DIR/clone2" w2 work recover --id ITEM-A --token tok-2 --store git --remote origin; local rec gen; rec=$(summ "$OUT"); gen=$(printf '%s' "$OUT" | jq '.claim.generation // null')
  t_cmd "$RUN_DIR/clone1" w1 work renew --id ITEM-A --token tok-1 --generation 1 --store git --remote origin; local renew; renew=$(summ "$OUT")
  t_cmd "$RUN_DIR/clone3" w3 work recover --id ITEM-A --token tok-3 --store git --remote origin; local third; third=$(summ "$OUT")
  local owners=1; [ "$(printf '%s' "$third" | jq -r .outcome)" = recorded ] && owners=2
  local stale=0; [ "$(printf '%s' "$renew" | jq -r .outcome)" = recorded ] && stale=1
  record A8-git-ref-expiry-recovery "$s" "across clones: holder blocks others; after expiry one clone recovers at generation 2; old holder cannot renew; a third clone cannot also recover" \
    "$(jq -cn --argjson a "$c1" --argjson b "$held" --argjson c "$rec" --argjson g "$gen" --argjson d "$renew" --argjson e "$third" '{claim:$a, otherCloneWhileHeld:$b, recover:$c, recoveredGeneration:$g, oldHolderRenew:$d, thirdCloneRecover:$e}')" \
    "$(jq -cn --argjson o $owners --argjson s $stale '{owners:$o, duplicateActiveOwners:($o-1), staleCompletionsAccepted:$s, lostWork:0}')" \
    "$( [ $owners -eq 1 ] && [ $stale -eq 0 ] && echo true || echo false )"; }

# ---------------------------------------------------------------- baseline (Praxis 3.12.0: no claim primitive)
b_local_worker() { set +e; (cd "$REPO" && PRAXIS_ACTOR="w$1" "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" > "$RUN_DIR/logs/start-$1.out" 2>&1); echo $? > "$RUN_DIR/logs/start-$1.rc"; set -e; }

b_race_local() { local round="$1" s; s=$(now_ms); new_run A "local-start-race-r$round"; init_repo "$REPO" ITEM-A; baseline_ready "$REPO" ITEM-A
  race "$K" b_local_worker
  local ok; ok=$(cat "$RUN_DIR"/logs/start-*.rc | grep -c '^0$' || true)
  local started; started=$(count_events "$REPO" work.started)
  local actors; actors=$(grep '"type":"work.started"' "$REPO/.ros/events/events.jsonl" 2>/dev/null | jq -sc '[.[].actor.id] | unique' || echo '[]')
  local owners=$(( ok > started ? ok : started ))
  record "A1-local-start-race-K$K-round$round" "$s" "prediction: more than one process reports ownership (no claim primitive)" \
    "$(jq -cn --argjson ok "$ok" --argjson st "$started" --argjson a "$actors" '{startsExit0:$ok, workStartedEvents:$st, startedActors:$a}')" \
    "$(jq -cn --argjson h "$owners" '{workers:8, owners:$h, duplicateActiveOwners:([0,$h-1]|max), staleCompletionsAccepted:null, lostWork:0}')" \
    "$( [ "$owners" -gt 1 ] && echo true || echo false )"; }

b_git_worker() { local d="$RUN_DIR/clone$1"; set +e
  (cd "$d" && PRAXIS_ACTOR="w$1" "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" > "$RUN_DIR/logs/start-$1.out" 2>&1); echo $? > "$RUN_DIR/logs/start-$1.rc"
  (cd "$d" && git add -A && git commit -qm "w$1 start ITEM-A" && git push -q origin HEAD:main) > "$RUN_DIR/logs/push-$1.out" 2>&1; echo $? > "$RUN_DIR/logs/push-$1.rc"; set -e; }

b_race_git() { local round="$1" s; s=$(now_ms); new_run A "git-start-race-r$round"; setup_clones
  baseline_ready "$REPO" ITEM-A; git -C "$REPO" add -A; git -C "$REPO" commit -qm ready; git -C "$REPO" push -q origin HEAD:main
  for i in $(seq 1 "$CLONES"); do git -C "$RUN_DIR/clone$i" pull -q origin main; done
  race "$CLONES" b_git_worker
  local ok pushed; ok=$(cat "$RUN_DIR"/logs/start-*.rc | grep -c '^0$' || true); pushed=$(cat "$RUN_DIR"/logs/push-*.rc | grep -c '^0$' || true)
  # Clones whose push was rejected integrate with a merge and push again (the existing workflow's only reconciliation).
  local conflicts=0
  for i in $(seq 1 "$CLONES"); do if [ "$(cat "$RUN_DIR/logs/push-$i.rc")" != 0 ]; then
    if ! (cd "$RUN_DIR/clone$i" && git pull -q --no-rebase --no-edit origin main >/dev/null 2>&1 && git push -q origin HEAD:main >/dev/null 2>&1); then conflicts=$((conflicts+1)); (cd "$RUN_DIR/clone$i" && git merge --abort >/dev/null 2>&1 || true); fi; fi; done
  local merged; merged=$(git --git-dir "$RUN_DIR/origin.git" show main:.ros/events/events.jsonl 2>/dev/null | grep '"type":"work.started"' | jq -sc '[.[].actor.id] | unique' || echo '[]')
  record "A2-git-clone-start-race-clones$CLONES-round$round" "$s" "prediction: every clone starts locally (each believes it owns the item)" \
    "$(jq -cn --argjson ok "$ok" --argjson p "$pushed" --argjson c "$conflicts" --argjson m "$merged" '{startsExit0:$ok, firstPushAccepted:$p, mergeConflictsOnIntegration:$c, startedActorsInOrigin:$m}')" \
    "$(jq -cn --argjson h "$ok" '{workers:4, owners:$h, duplicateActiveOwners:([0,$h-1]|max), staleCompletionsAccepted:null, lostWork:0}')" \
    "$( [ "$ok" -gt 1 ] && echo true || echo false )"; }

b_retry() { local s; s=$(now_ms); new_run A retry-start; init_repo "$REPO" ITEM-A; baseline_ready "$REPO" ITEM-A
  set +e; (cd "$REPO" && PRAXIS_ACTOR=w1 "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" >/dev/null 2>&1); local a=$?
  local again; again=$(cd "$REPO" && PRAXIS_ACTOR=w1 "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" 2>&1); local b=$?
  local other; other=$(cd "$REPO" && PRAXIS_ACTOR=w2 "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" 2>&1); local c=$?
  local res; res=$(cd "$REPO" && PRAXIS_ACTOR=w2 "$PRAXIS" work resume --id ITEM-A --occurred-at "$(utc)" 2>&1); local d=$?; set -e
  local owners=1; [ $d -eq 0 ] && owners=2
  record A3-retry-start "$s" "sequential: a second start is refused from active; record whether another actor can take over with work resume" \
    "$(jq -cn --argjson a $a --argjson b $b --arg bo "${again:0:200}" --argjson c $c --arg co "${other:0:200}" --argjson d $d --arg ro "${res:0:200}" '{firstStartExit:$a, resendExit:$b, resendOutput:$bo, otherActorStartExit:$c, otherActorStartOutput:$co, otherActorResumeExit:$d, otherActorResumeOutput:$ro}')" \
    "$(jq -cn --argjson h $owners '{owners:$h, duplicateActiveOwners:($h-1), staleCompletionsAccepted:null, lostWork:0}')" null; }

b_foreign_completion() { local s; s=$(now_ms); new_run A stale-owner-completion; init_repo "$REPO" ITEM-A; baseline_ready "$REPO" ITEM-A
  printf 'impl\n' > "$REPO/impl.txt"; printf 'tests ok\n' > "$REPO/tests.txt"
  set +e; (cd "$REPO" && PRAXIS_ACTOR=w1 "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" >/dev/null 2>&1)
  # w1 "crashes" (no further action). w2, who never started the item, completes it; then w1 returns late and completes too.
  (cd "$REPO" && PRAXIS_ACTOR=w2 "$PRAXIS" work complete --id ITEM-A --occurred-at "$(utc)" --evidence implementation=impl.txt --evidence tests=tests.txt >/dev/null 2>&1); local a=$?
  local late; late=$(cd "$REPO" && PRAXIS_ACTOR=w1 "$PRAXIS" work complete --id ITEM-A --occurred-at "$(utc)" --evidence implementation=impl.txt --evidence tests=tests.txt 2>&1); local b=$?; set -e
  local actors; actors=$(grep '"type":"work.completed"' "$REPO/.ros/events/events.jsonl" | jq -sc '[.[].actor.id]')
  local stale=0; [ $a -eq 0 ] && stale=$((stale+1)); [ $b -eq 0 ] && stale=$((stale+1))
  record A7-completion-by-non-owner-and-late-owner "$s" "prediction: a worker that never started (or lost) the item can complete it" \
    "$(jq -cn --argjson a $a --argjson b $b --arg bo "${late:0:200}" --argjson ac "$actors" '{nonOwnerCompleteExit:$a, lateOwnerCompleteExit:$b, lateOwnerOutput:$bo, completedByActors:$ac}')" \
    "$(jq -cn --argjson s $stale '{owners:1, duplicateActiveOwners:0, staleCompletionsAccepted:$s, lostWork:0}')" \
    "$( [ $stale -ge 1 ] && echo true || echo false )"; }

b_crash_recovery() { local s; s=$(now_ms); new_run A crash-then-recovery; init_repo "$REPO" ITEM-A; baseline_ready "$REPO" ITEM-A
  printf 'impl\n' > "$REPO/impl.txt"; printf 'tests ok\n' > "$REPO/tests.txt"
  ( cd "$REPO" && PRAXIS_ACTOR=w1 setsid "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" >/dev/null 2>&1; exec sleep 30 ) & local pid=$!
  sleep 2; kill -9 -- "-$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true; wait $pid 2>/dev/null || true
  set +e; local st; st=$(cd "$REPO" && PRAXIS_ACTOR=w2 "$PRAXIS" work start --id ITEM-A --occurred-at "$(utc)" 2>&1); local a=$?
  (cd "$REPO" && PRAXIS_ACTOR=w2 "$PRAXIS" work resume --id ITEM-A --occurred-at "$(utc)" >/dev/null 2>&1); local b=$?
  (cd "$REPO" && PRAXIS_ACTOR=w2 "$PRAXIS" work complete --id ITEM-A --occurred-at "$(utc)" --evidence implementation=impl.txt --evidence tests=tests.txt >/dev/null 2>&1); local c=$?; set -e
  local lost=1; [ $c -eq 0 ] && lost=0
  record A5-worker-killed-then-recovered "$s" "worker SIGKILLed while owning the item; record how a second worker proceeds (no lease, no fencing)" \
    "$(jq -cn --argjson a $a --arg ao "${st:0:200}" --argjson b $b --argjson c $c '{secondWorkerStartExit:$a, secondWorkerStartOutput:$ao, secondWorkerResumeExit:$b, secondWorkerCompleteExit:$c}')" \
    "$(jq -cn --argjson l $lost --argjson b $b '{owners:(if $b==0 then 2 else 1 end), duplicateActiveOwners:(if $b==0 then 1 else 0 end), staleCompletionsAccepted:null, lostWork:$l}')" null; }

if [ "$ARM" = treatment ]; then
  for r in $(seq 1 "$ROUNDS"); do t_race_local "$r"; done
  for r in $(seq 1 "$ROUNDS"); do t_race_git "$r"; done
  t_retry_replay; t_expiry_recovery; t_kill_validate; t_kill_complete_same_holder; t_kill_complete_recover; t_stale_owner; t_git_expiry
else
  for r in $(seq 1 "$ROUNDS"); do b_race_local "$r"; done
  for r in $(seq 1 "$ROUNDS"); do b_race_git "$r"; done
  b_retry; b_crash_recovery; b_foreign_completion
  na A4-short-lease-expiry-recovery "Praxis 3.12.0 has no lease primitive"
  na A6-sigkill-during-complete-verified "Praxis 3.12.0 has no verified completion step"
  na A8-git-ref-expiry-recovery "Praxis 3.12.0 has no lease or git-ref claim store"
fi
echo "wrote $OUT_FILE ($(wc -l < "$OUT_FILE") cases)"
