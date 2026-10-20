#!/usr/bin/env bash
# REL-001 run-03 harness smoke test (never observations): trial.sh start -> smoke-agent.sh -> trial.sh finish,
# then one line per run from its observation.
#   usage: smoke.sh [CASE...]   CASE = TASK:ARM[:VARIANT]   (VARIANT applies a wrong solution)
#   default cases: V1, V7 and V8 in arms A and B, plus V8 with the per-call wrong solution in arm A;
#   add C/D cases once their binaries are pinned (REL003_PRAXIS_C/D, REL003_DOKIMOS_C/D, REL003_ORDO_C/D).
#   REL003_DRY_RUN=1 runs without dotnet: the oracle is skipped and correctness is "not scored".
source "$(dirname "$0")/lib.sh"
TAG="${SMOKE_TAG:-$(date -u +%H%M%S)}"
export REL003_CACHE_CONDITION="${REL003_CACHE_CONDITION:-K0 subagent-shared (smoke)}"
CASES=("$@")
[ ${#CASES[@]} -gt 0 ] || CASES=(V1:bare V1:directives V7:bare V7:directives V8:bare V8:directives V8:bare:per-call)
for c in "${CASES[@]}"; do
  IFS=: read -r TASK ARM VARIANT <<<"$c"
  ID="REL-001-R3-SMOKE-$TASK-r1-$ARM${VARIANT:+-$VARIANT}-$TAG"
  bash "$H3/trial.sh" start "$ARM" "$TASK" "$ID" > /dev/null
  run_paths "$ID"
  AID=$(SMOKE_VARIANT="$VARIANT" bash "$H3/smoke-agent.sh" "$ID")
  OBS=$(bash "$H3/trial.sh" finish "$ID" "$HS/smoke-src" "$AID")
  jq -r --arg c "$c" '[$c, .status,
     "units " + ((.run03.units.correct // "n/a")|tostring) + "/" + (.run03.units.total|tostring),
     "oracle " + (if .run03.oracle.ran then ([.run03.units.perRequirement[] | .oraclePass] | map(tostring) | join(",")) else "not run" end),
     "recorded " + (.run03.completionEvidence.recorded|tostring),
     "outcome " + (.run03.agent.outcome.value // "none"),
     "conflict " + (if .run03.conflictRubric then (.run03.conflictRubric.correct|tostring) else "-" end),
     "escaped " + ((.run03.reliability.escapedDefects // "n/a")|tostring),
     "tests " + (.run03.tests.total|tostring),
     "xcheck tokens " + (.run03.crossCheck.tokens.total|tostring) + " cost " + ((.run03.crossCheck.costUsd // "n/a")|tostring),
     "cold-first " + (.cache.measured.firstRequestCold|tostring),
     "report " + (.metrics.costEstimated.availability),
     "x2 " + (.run03.exclusions.x2.mismatch|tostring), "x4 " + (.run03.exclusions.x4.contaminated|tostring),
     "x6 " + (.run03.exclusions.x6.tampered|tostring)] | join(" | ")' "$OBS"
done
