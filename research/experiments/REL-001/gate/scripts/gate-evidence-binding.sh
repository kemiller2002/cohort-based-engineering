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
{"OrdoContractVersion":"","OrdoContractDigest":"","SupportedOrdoContractVersions":["ecir/1"],"RequiredRequirementIds":[],"RequiredDecisionIds":["DEC-CONFIRM"],"RequiredValidationNames":["unit-tests"],"RequiredEvidenceIds":["EV-TESTS"],"ExpectedCommit":"$SHA","ExpectedVerificationRevision":"$SHA"}
JSON
run() { local id=$1 evidence=$2; "$PRAXIS" work claim --id $id --token tok-$id >/dev/null
  set +e; out=$("$PRAXIS" work complete-verified --id $id --token tok-$id --generation 1 --commit $SHA --verification-revision $SHA \
     --authority authority.json --ordo-contract contract.json \
     --requirement "requirements/domain.md#R-001" --requirement "requirements/operations.md#R-001" --decision DEC-CONFIRM \
     --validation unit-tests=passed:EV-TESTS --evidence EV-TESTS=$evidence); code=$?; set -e
  echo "{\"case\":\"$id\",\"evidence\":\"$evidence\",\"exit\":$code,\"outcome\":$(echo "$out" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(json.dumps({"outcome":d.get("outcome"),"codes":d.get("codes",[])}))')}"; }
# Case 1: evidence that records a FAILING test run, produced before the claim and at no particular revision.
printf '12 test(s); 7 passed; 5 failed\n' > evidence/failing.txt
run GATE-1 evidence/failing.txt
# Case 2: an evidence file unrelated to any test run at all.
printf 'not a test report\n' > evidence/unrelated.txt
run GATE-2 evidence/unrelated.txt
# --- Cases added after PRAXIS-REL-005 (Praxis >= 3.15.0 provides work validate-run) ---
if "$PRAXIS" work validate-run --help >/dev/null 2>&1 || "$PRAXIS" 2>&1 | grep -q "validate-run"; then
  git add -A >/dev/null 2>&1; git commit -qm "evidence fixtures" >/dev/null 2>&1 || true
  SHA=$(git rev-parse HEAD)
  sed -i "s/\"ExpectedCommit\":\"[0-9a-f]*\"/\"ExpectedCommit\":\"$SHA\"/; s/\"ExpectedVerificationRevision\":\"[0-9a-f]*\"/\"ExpectedVerificationRevision\":\"$SHA\"/" authority.json
  git add -A >/dev/null; git commit -qm "authority" >/dev/null 2>&1 || true; SHA=$(git rev-parse HEAD)
  sed -i "s/\"ExpectedCommit\":\"[0-9a-f]*\"/\"ExpectedCommit\":\"$SHA\"/; s/\"ExpectedVerificationRevision\":\"[0-9a-f]*\"/\"ExpectedVerificationRevision\":\"$SHA\"/" authority.json
  git update-index --assume-unchanged authority.json
  python3 - "$SHA" <<'PY' > .ros/work/queue.json
import json,sys
print(json.dumps({"schemaVersion":"1.0.0","items":[{"id":i,"status":"captured"} for i in ["GATE-1","GATE-2","GATE-3","GATE-4","GATE-5"]]}))
PY
  git update-index --assume-unchanged .ros/work/queue.json
  # GATE-3: forged "passed" validation-result document, never recorded by Praxis.
  "$PRAXIS" work claim --id GATE-3 --token tok-GATE-3 >/dev/null
  python3 - "$SHA" > evidence/forged.json <<'PY'
import json,sys,datetime
now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(json.dumps({"schemaVersion":"praxis.validation-result/1","workItemId":"GATE-3","claimant":"gate/agent","claimToken":"tok-GATE-3","generation":1,"validation":"unit-tests","evidenceId":"EV-TESTS","revision":sys.argv[1],"observedAt":now,"startedAt":now,"status":"passed","exitCode":0,"command":["true"],"outputSha256":"sha256:"+"0"*64}))
PY
  set +e; out=$("$PRAXIS" work complete-verified --id GATE-3 --token tok-GATE-3 --generation 1 --commit $SHA --verification-revision $SHA --authority authority.json --ordo-contract contract.json --requirement "requirements/domain.md#R-001" --requirement "requirements/operations.md#R-001" --decision DEC-CONFIRM --validation unit-tests=passed:EV-TESTS --evidence EV-TESTS=evidence/forged.json); code=$?; set -e
  echo "{\"case\":\"GATE-3\",\"evidence\":\"forged-passed-result\",\"exit\":$code,\"outcome\":$(echo "$out" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(json.dumps({"outcome":d.get("outcome"),"codes":d.get("codes",[])}))')}"
  # GATE-4 (recorded failing run) and GATE-5 (recorded passing run).
  for spec in "GATE-4:false" "GATE-5:true"; do id=${spec%%:*}; cmd=${spec#*:}
    "$PRAXIS" work claim --id $id --token tok-$id >/dev/null
    vr=$("$PRAXIS" work validate-run --id $id --token tok-$id --generation 1 --validation unit-tests --evidence-id EV-TESTS -- $cmd 2>/dev/null || true)
    path=$(echo "$vr" | python3 -c 'import json,sys
d=json.load(sys.stdin)
def find(o):
  if isinstance(o,dict):
    for k,v in o.items():
      if k in ("path","resultPath") and isinstance(v,str) and v.endswith(".json"): return v
      r=find(v)
      if r: return r
  return None
print(find(d) or "")')
    set +e; out=$("$PRAXIS" work complete-verified --id $id --token tok-$id --generation 1 --commit $SHA --verification-revision $SHA --authority authority.json --ordo-contract contract.json --requirement "requirements/domain.md#R-001" --requirement "requirements/operations.md#R-001" --decision DEC-CONFIRM --validation unit-tests=passed:EV-TESTS --evidence EV-TESTS=$path); code=$?; set -e
    echo "{\"case\":\"$id\",\"evidence\":\"validate-run -- $cmd\",\"exit\":$code,\"outcome\":$(echo "$out" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(json.dumps({"outcome":d.get("outcome"),"codes":d.get("codes",[])}))')}"
  done
fi
