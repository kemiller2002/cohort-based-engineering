#!/usr/bin/env bash
# Reproduces the evidence-binding gate check with the RELEASED binaries.
# usage: gate-evidence-binding.sh PRAXIS_BIN DOKIMOS_BIN ORDO_CONTRACT WORKDIR
set -euo pipefail
PRAXIS="$1"; DOKIMOS="$2"; CONTRACT="$3"; W="$4"
rm -rf "$W"; mkdir -p "$W"; cd "$W"
git init -q . && git config user.email gate@example.invalid && git config user.name gate
mkdir -p .ros/work evidence
echo '{"schemaVersion":"1.0.0","items":[{"id":"GATE-1","status":"captured"},{"id":"GATE-2","status":"captured"}]}' > .ros/work/queue.json
cp "$CONTRACT" contract.json
git add -A && git commit -qm "fixture" && SHA=$(git rev-parse HEAD)
export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=gate/agent PRAXIS_TELEMETRY_PROVIDER=test PRAXIS_TELEMETRY_RUNTIME=test PRAXIS_DOKIMOS_EXECUTABLE="$DOKIMOS"
cat > authority.json <<JSON
{"OrdoContractVersion":"","OrdoContractDigest":"","SupportedOrdoContractVersions":["ecir/1"],"RequiredRequirementIds":[],"RequiredValidationNames":["unit-tests"],"RequiredEvidenceIds":["EV-TESTS"],"ExpectedCommit":"$SHA","ExpectedVerificationRevision":"$SHA"}
JSON
run() { local id=$1 evidence=$2; "$PRAXIS" work claim --id $id --token tok-$id >/dev/null
  set +e; out=$("$PRAXIS" work complete-verified --id $id --token tok-$id --generation 1 --commit $SHA --verification-revision $SHA \
     --authority authority.json --ordo-contract contract.json \
     --requirement "requirements/domain.md#R-001" --requirement "requirements/operations.md#R-001" \
     --validation unit-tests=passed:EV-TESTS --evidence EV-TESTS=$evidence); code=$?; set -e
  echo "{\"case\":\"$id\",\"evidence\":\"$evidence\",\"exit\":$code,\"outcome\":$(echo "$out" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(json.dumps({"outcome":d.get("outcome"),"codes":d.get("codes",[])}))')}"; }
# Case 1: evidence that records a FAILING test run, produced before the claim and at no particular revision.
printf '12 test(s); 7 passed; 5 failed\n' > evidence/failing.txt
run GATE-1 evidence/failing.txt
# Case 2: an evidence file unrelated to any test run at all.
printf 'not a test report\n' > evidence/unrelated.txt
run GATE-2 evidence/unrelated.txt
