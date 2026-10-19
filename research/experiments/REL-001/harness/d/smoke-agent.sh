#!/usr/bin/env bash
# REL-001 D HARNESS CHECK ONLY: a scripted stand-in "agent" that applies the reference
# solution and follows AGENT_BRIEF.md's workflow for the run's arm. Its runs are harness
# checks, never observations. usage: harness/d/smoke-agent.sh RUNID
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REL="$(cd "$HERE/../.." && pwd)"
RUN_DIR="${REL001_RUNS:-/tmp/claude-0/rel001/runs}/$1"
source "$RUN_DIR/env.sh"   # PATH shims, identity, cwd = repo
ARM=$(jq -r .arm "$RUN_DIR/run.json"); ITEM=$(jq -r .workItem "$RUN_DIR/run.json")
started=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
if [ "$ARM" = baseline ]; then
  praxis work start --id "$ITEM" --occurred-at "$(now)" > /dev/null
  cp "$REL/fixtures/d/reference/Domain.fs" "$REL/fixtures/d/reference/Ledger.fs" src/Ledger/
  dotnet test Ledger.slnx > test-output.txt 2>&1
  git add -A -- src tests && git commit -qm "$ITEM: reference solution (harness check)"
  praxis work complete --id "$ITEM" --occurred-at "$(now)" --evidence implementation=src/Ledger/Ledger.fs --evidence tests=test-output.txt > /dev/null
else
  TOK="tok-$1"
  praxis work claim --id "$ITEM" --token "$TOK" --lease-seconds 3600 > /dev/null
  cp "$REL/fixtures/d/reference/Domain.fs" "$REL/fixtures/d/reference/Ledger.fs" src/Ledger/
  git add -A -- src tests && git commit -qm "$ITEM: reference solution (harness check)"
  RESULT=$(praxis work validate-run --id "$ITEM" --token "$TOK" --generation 1 --validation unit-tests --evidence-id EV-TESTS -- dotnet test Ledger.slnx | jq -r .resultPath)
  mapfile -t REQS < <(jq -r '.requirements[].source.key | "--requirement\n" + .' contract.json)
  praxis work complete-verified --id "$ITEM" --token "$TOK" --generation 1 --commit "$(git rev-parse HEAD)" --verification-revision "$(git rev-parse HEAD)" \
    --authority authority.json --ordo-contract contract.json "${REQS[@]}" --validation unit-tests=passed:EV-TESTS --evidence "EV-TESTS=$RESULT" | jq -c '{outcome, codes}'
fi
jq -cn --arg s "$started" --arg e "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" '{startedAt:$s, endedAt:$e, agent:"harness/d/smoke-agent.sh (scripted reference solution; harness check)"}' > "$RUN_DIR/logs/agent.json"
