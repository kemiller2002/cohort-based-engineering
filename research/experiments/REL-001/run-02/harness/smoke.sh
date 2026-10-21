#!/usr/bin/env bash
# REL-001 run-02 harness smoke test (never observations): trial.sh start -> smoke-agent.sh -> trial.sh finish
# for U1 and U2 in all four arms and U6 in arms A and D, then one line per run from its observation.
#   usage: smoke.sh [CASE...]   CASE = TASK:ARM (default: the full smoke set)
# Run ids contain -SMOKE-, so trial.sh keeps the observations in the harness state directory.
source "$(dirname "$0")/lib.sh"
TAG="${SMOKE_TAG:-$(date -u +%H%M%S)}"
CASES=("$@")
[ ${#CASES[@]} -gt 0 ] || CASES=(U1:bare U1:directives U1:echelon-original U1:echelon-optimized
                                 U2:bare U2:directives U2:echelon-original U2:echelon-optimized
                                 U6:bare U6:echelon-optimized)
for c in "${CASES[@]}"; do
  TASK="${c%%:*}"; ARM="${c#*:}"; ID="REL-001-R2-SMOKE-$TASK-r1-$ARM-$TAG"
  bash "$H2/trial.sh" start "$ARM" "$TASK" "$ID" > /dev/null
  run_paths "$ID"
  IDS=()
  for n in $(workspace_names); do IDS+=("$(bash "$H2/smoke-agent.sh" "$ID" "$n")"); done
  OBS=$(bash "$H2/trial.sh" finish "$ID" "$HS/smoke-src" "${IDS[@]}")
  jq -r --arg c "$c" '[$c, .status,
     "units " + (.run02.units.correct|tostring) + "/" + (.run02.units.total|tostring),
     "oracle " + ([.scoring.requirements[] | .pass] | map(tostring) | join(",")),
     "recorded " + (.run02.completionEvidence.recorded|tostring),
     "outcome " + ([.run02.agents[] | .outcome.value // "none"] | join(",")),
     "u2 " + (if .run02.u2Rubric then (.run02.u2Rubric.correct|tostring) else "-" end),
     "u6 " + (if .run02.u6 then ("completions " + (.run02.u6.completions|tostring) + " dup " + (.run02.u6.duplicateOwner|tostring) + " lost " + (.run02.u6.lostWork|tostring) + " conflicting " + (.run02.u6.conflictingCompletions|tostring)) else "-" end),
     "tests " + (.run02.tests.total|tostring) + " (verifier " + ((.run02.tests.bySource.verifier.full // 0)|tostring) + ")",
     "identity " + ([.run02.workspaces[] | .completionIdentity.praxis.outcome? // "-"] | join(",")),
     "tokens " + ((.metrics.tokensTotal.value // "n/a")|tostring) + " [" + .metrics.tokensTotal.availability + "]",
     "cost " + ((.metrics.costEstimated.value // "n/a")|tostring),
     "attributed " + (.run02.tokens.attribution.agentsFound|length|tostring) + "/" + (.run02.agents|length|tostring),
     "x2 " + (.run02.exclusions.x2.mismatch|tostring), "x4 " + (.run02.exclusions.x4.contaminated|tostring),
     "x6 " + (.run02.exclusions.x6.tampered|tostring)] | join(" | ")' "$OBS"
done
