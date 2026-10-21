#!/usr/bin/env bash
# ARCH-001 harness smoke test (adapted from REL-001 run-03 harness/smoke.sh; never observations).
#   usage: smoke.sh [CASE...]      CASE = TASK:ARM[:VARIANT]   default: T0:A T0:D (good reference)
# Runs the REAL trial driver (setup -> phase 1 -> transition -> phase 2 -> score, real dotnet, real ordo, real
# submit gate) with the no-model stand-in agent (smoke-agent.sh). Unless ARCH001_SMOKE_REAL=1, the stand-in
# fixtures/sealed store/verifier under harness/smoke/ are used (Workers B and C not needed).
# The live K1 check is separate: smoke-live.sh.
H0="$(cd "$(dirname "$0")" && pwd)"
if [ "${ARCH001_SMOKE_REAL:-0}" != 1 ]; then
  export ARCH001_FIXTURES="$H0/smoke/fixtures" ARCH001_SEALED_DIR="$H0/smoke/sealed"
  export ARCH001_ARCHCHECK="$H0/smoke/archcheck/archcheck.py" ARCH001_POLICY="$H0/smoke/fixtures/policy/lending.policy.json"
fi
export ARCH001_AGENT_CMD="$H0/smoke-agent.sh"
source "$H0/lib.sh"
TAG="${SMOKE_TAG:-$(date -u +%H%M%S)}"
CASES=("$@"); [ ${#CASES[@]} -gt 0 ] || CASES=(T0:A T0:D)
for c in "${CASES[@]}"; do
  IFS=: read -r TASK ARM VARIANT <<<"$c"
  ID="ARCH-001-SMOKE-$TASK-r1-$ARM-${VARIANT:-good}$TAG"
  SMOKE_VARIANT="${VARIANT:-good}" bash "$H/trial.sh" run "$ID" > /dev/null || { echo "$c: trial.sh failed (see $RUNS/$ID/state)"; continue; }
  OBS="$RUNS/$ID/state/score/observation.json"
  jq -r --arg c "$c" --arg id "$ID" '[$c, $id, .status,
     "R1 func " + (.requirements[0].functionalPass|tostring) + " arch " + (.requirements[0].archAccept|tostring),
     "R2 func " + (.requirements[1].functionalPass|tostring) + " arch " + (.requirements[1].archAccept|tostring),
     "accepted " + (.acceptedRequirements|tostring) + "/2",
     "submits " + ([.phases[] | select(.) | .submit.verdicts | join(",")] | join(" / ")),
     "oracle p1 " + ((.oracle.p1.passed // 0)|tostring) + "/" + ((.oracle.p1.total // 0)|tostring)
       + " p2 " + ((.oracle.p2.passed // 0)|tostring) + "/" + ((.oracle.p2.total // 0)|tostring)
       + " reg " + ((.regression.passed // 0)|tostring) + "/" + ((.regression.total // 0)|tostring),
     "DET>=2 p1 " + ((.architecture.p1.detSev2plus // "n/a")|tostring) + " p2 " + ((.architecture.p2.detSev2plus // "n/a")|tostring)
       + " new " + ((.architecture.newDetViolations.count // "n/a")|tostring),
     "TRC p1 " + ((.decisionFidelity.trc.p1 // "-")|tostring) + " p2 " + ((.decisionFidelity.trc.p2 // "-")|tostring),
     "dec-tests " + (.decisionFidelity.decisionTests.passed|tostring) + "/" + (.decisionFidelity.decisionTests.total|tostring),
     "rework " + ((.diff.phase2.all.rework // "n/a")|tostring) + " broken " + ((.visibleTests.preexistingBroken.count // "n/a")|tostring),
     "cost " + (.cost.totalUsd|tostring) + " xcheck " + (.cost.agrees|tostring),
     "firstPass " + (.firstPassCorrect.p1|tostring) + "," + (.firstPassCorrect.p2|tostring),
     "x4 " + (.exclusions.x4.contaminated|tostring) + " integ " + (.exclusions.xIntegrity.tampered|tostring) + " x5 " + (.exclusions.x5.timedOut|tostring)]
     | join(" | ")' "$OBS"
done
