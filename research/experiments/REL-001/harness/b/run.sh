#!/usr/bin/env bash
# REL-001 Experiment B: contract and decision admission. usage: harness/b/run.sh baseline|treatment
# For each case of fixtures/b/cases.json: Ordo `sde ecir check` (both arms, to classify the input),
# Praxis `ordo contract check`, then the arm's completion workflow in a fresh repository.
# invalidAccepted = 1 when a case deemed invalid reaches a recorded completion.
source "$(dirname "$0")/../lib.sh"
arm_init "$1"
FIX="$REL/fixtures/b"
OUT_FILE="$REL/results/b/$ARM.jsonl"; mkdir -p "$(dirname "$OUT_FILE")"; : > "$OUT_FILE"

resolve() { case "$1" in ordo:*) echo "$ORDO_FIXTURES/${1#ordo:}" ;; *) echo "$FIX/$1" ;; esac; }

n=$(jq '.cases|length' "$FIX/cases.json")
for i in $(seq 0 $((n-1))); do
  c=$(jq -c ".cases[$i]" "$FIX/cases.json"); name=$(jq -r .name <<<"$c")
  contract=$(resolve "$(jq -r .contract <<<"$c")"); valid=$(jq -r .deemedValid <<<"$c")
  pin=$(jq -r '.expectedDigest // empty' <<<"$c")
  s=$(now_ms); new_run B "$name"
  cp "$contract" "$RUN_DIR/inputs/contract.json"; C="$RUN_DIR/inputs/contract.json"
  csha=$(sha256sum "$C" | cut -d' ' -f1)

  # Ordo's own check (the same pinned build for both arms).
  set +e; ordo_out=$("$SDE" ecir check --blueprint "$C" ${pin:+--expected-digest "$pin"} --json 2>&1); ordo_rc=$?; set -e
  ordo=$(jq -cn --argjson rc $ordo_rc --argjson o "$(json_or_null "$ordo_out")" '{exit:$rc, admitted:($rc==0), digest:($o.contractDigest // null), decisionIds:($o.decisionIds // null), conflictIds:($o.conflictIds // null), codes:[($o.diagnostics // [])[] | .code + (if .subject then " " + .subject else "" end)]}')

  # Praxis's consumer check.
  set +e; px_out=$(cd "$RUN_DIR" && "$PRAXIS" ordo contract check --contract "$C" ${pin:+--expected-digest "$pin"} 2>&1); px_rc=$?; set -e
  px=$(jq -cn --argjson rc $px_rc --argjson o "$(json_or_null "${px_out:0:600}")" '{exit:$rc, admitted:($rc==0), output:$o}')

  init_repo "$REPO" ITEM-B
  if [ "$ARM" = treatment ]; then
    write_authority "$RUN_DIR/inputs/authority.json" "$(jq -c '.requiredDecisionIds // []' <<<"$c")" "$(jq -c '.requiredConflictResolutionIds // []' <<<"$c")"
    t_claim "$REPO" w1 --id ITEM-B --token tok-1; claim=$(summ "$OUT")
    t_validate "$REPO" w1 ITEM-B tok-1 1 true; val=$(summ "$OUT")
    if [ -n "$pin" ]; then t_complete "$REPO" w1 ITEM-B tok-1 1 "$EVPATH" "$C" "$RUN_DIR/inputs/authority.json" --expected-ordo-digest "$pin"
    else t_complete "$REPO" w1 ITEM-B tok-1 1 "$EVPATH" "$C" "$RUN_DIR/inputs/authority.json"; fi
    comp_rc=$RC; comp=$(printf '%s' "$OUT" | jq -c '{outcome, code, codes, detail: (.detail // .reason // null)}' 2>/dev/null || jq -cn --arg t "${OUT:0:400}" '{unparsed:$t}')
    accepted=$( [ "$(jq -r .outcome <<<"$comp")" = verified ] && echo 1 || echo 0 )
    dok=$(count_events "$REPO" work.completion.verified)
    flow=$(jq -cn --argjson a "$claim" --argjson b "$val" --argjson c "$comp" --argjson rc $comp_rc --argjson d "$dok" '{claim:$a, validateRun:$b, completeVerified:($c + {exit:$rc}), verifiedEvents:$d}')
  else
    baseline_ready "$REPO" ITEM-B
    cp "$C" "$REPO/contract.json"; printf 'impl\n' > "$REPO/impl.txt"; printf 'all tests passed\n' > "$REPO/tests.log"
    set +e; st=$(cd "$REPO" && "$PRAXIS" work start --id ITEM-B --occurred-at "$(utc)" 2>&1); st_rc=$?
    co=$(cd "$REPO" && "$PRAXIS" work complete --id ITEM-B --occurred-at "$(utc)" --evidence implementation=impl.txt --evidence tests=tests.log --evidence ordo-contract=contract.json 2>&1); comp_rc=$?; set -e
    accepted=$( [ $comp_rc -eq 0 ] && echo 1 || echo 0 )
    flow=$(jq -cn --argjson a $st_rc --argjson rc $comp_rc --argjson o "$(printf '%s' "$co" | jq -c '{state: .workItems[0].state}' 2>/dev/null || jq -cn --arg t "${co:0:300}" '{error:$t}')" --argjson e "$(count_events "$REPO" work.completed)" '{workStartExit:$a, workCompleteExit:$rc, workCompleteOutput:$o, completedEvents:$e}')
  fi
  invalid_acc=$( [ "$valid" = false ] && [ "$accepted" = 1 ] && echo 1 || echo 0 )
  layer=$(jq -r '.invalidityLayer' <<<"$c")
  ordo_finding=$( [ "$valid" = false ] && [ "$layer" = contract ] && [ "$ordo_rc" = 0 ] && echo true || echo false )
  if [ "$ARM" = treatment ]; then match=$( { [ "$valid" = true ] && [ "$accepted" = 1 ]; } || { [ "$valid" = false ] && [ "$accepted" = 0 ]; } && echo true || echo false )
  else match=$( [ "$accepted" = 1 ] && echo true || echo false ); fi
  emit "$OUT_FILE" "$(jq -cn --arg c "$name" --argjson case "$c" --arg sha "$csha" --argjson o "$ordo" --argjson p "$px" --argjson f "$flow" \
     --argjson acc "$accepted" --argjson ia "$invalid_acc" --argjson of "$ordo_finding" --argjson m "$match" --argjson w $(( $(now_ms) - s )) \
     '{experiment:"B", case:$c, status:"executed", input:($case + {contractSha256:$sha}), ordoCheck:$o, praxisContractCheck:$p, workflow:$f,
       metrics:{completionAccepted:$acc, invalidAccepted:$ia, ordoAdmittedDeemedInvalid:$of}, matchesPrediction:$m, wallMs:$w}')"
done
echo "wrote $OUT_FILE ($(wc -l < "$OUT_FILE") cases)"
