#!/usr/bin/env bash
# ARCH-002 harness smoke test (adapted from ARCH-001 harness/smoke.sh; never observations).
#   usage: smoke.sh [CASE...]      CASE = TASK:ARM[:VARIANT[:MODEL]]   default: T0:A T0:D T0:D:trap
# Runs the REAL trial driver (setup with the brownfield baseline -> phase 1 -> transition -> phase 2 -> score; real
# dotnet, real ordo, real submit gate, the REAL arch-002 archcheck with --baseline) with the no-model stand-in agent
# (smoke-agent.sh) on the brownfield stand-in fixture smoke/fixtures/lending-smoke, whose start commit already holds
# one ARC-SYM-02 violation (Fees.stampedAt). Expected: good -> the pre-existing violation fails nothing (submit PASS,
# requirements accepted); trap -> the trap's NEW ARC-SYM-02 violation fails arm D's submit and is not accepted.
# The live K1 check is separate: smoke-live.sh.
H0="$(cd "$(dirname "$0")" && pwd)"
# SMOKE_FIXTURES_DIR / SMOKE_SEALED_DIR point the smoke at a real fixture (stand-in agent, no model calls).
export ARCH002_FIXTURES="${SMOKE_FIXTURES_DIR:-$H0/smoke/fixtures}" ARCH002_SEALED_DIR="${SMOKE_SEALED_DIR:-$H0/smoke/sealed}"
export ARCH002_AGENT_CMD="$H0/smoke-agent.sh"
source "$H0/lib.sh"
FIXTURE="${SMOKE_FIXTURE:-lending-smoke}"
TAG="${SMOKE_TAG:-$(date -u +%H%M%S)}"
CASES=("$@"); [ ${#CASES[@]} -gt 0 ] || CASES=(T0:A T0:D T0:D:trap)
for c in "${CASES[@]}"; do
  IFS=: read -r TASK ARM VARIANT MKEY <<<"$c"
  ID="ARCH-002-SMOKE-$FIXTURE-$TASK-${MKEY:-opus}-r1-$ARM-${VARIANT:-good}$TAG"
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
     "baseline DET " + ((.architecture.baseline.scoringDetFindings // "n/a")|tostring),
     "S1 new/pre/fixed " + ((.architecture.p1.detNew // "n/a")|tostring) + "/" + ((.architecture.p1.detPreexisting // "n/a")|tostring) + "/" + ((.architecture.p1.detFixed // "n/a")|tostring),
     "S2 new/pre/fixed " + ((.architecture.p2.detNew // "n/a")|tostring) + "/" + ((.architecture.p2.detPreexisting // "n/a")|tostring) + "/" + ((.architecture.p2.detFixed // "n/a")|tostring),
     "S2 new rules " + ((.architecture.p2.newByRule // {}) | tostring),
     "TRC p1 " + ((.decisionFidelity.trc.p1 // "-")|tostring) + " p2 " + ((.decisionFidelity.trc.p2 // "-")|tostring),
     "rework " + ((.diff.phase2.all.rework // "n/a")|tostring),
     "cost " + (.cost.totalUsd|tostring) + " xcheck " + (.cost.agrees|tostring),
     "x4 " + (.exclusions.x4.contaminated|tostring) + " integ " + (.exclusions.xIntegrity.tampered|tostring) + " x5 " + (.exclusions.x5.timedOut|tostring)]
     | join(" | ")' "$OBS"
done
