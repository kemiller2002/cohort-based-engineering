#!/usr/bin/env bash
# REL-001 run-01 harness library (sourced by harness/{a,b,c,d}/*.sh).
# Every case runs in a fresh disposable directory under $RUNS/<runId>.
# Binaries live under $BIN (never committed); each result records their sha256.
set -euo pipefail

REL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${REL001_BIN:-/tmp/claude-0/rel001/bin}"
RUNS="${REL001_RUNS:-/tmp/claude-0/rel001/runs}"
ORDO_SRC="${REL001_ORDO_SRC:-/home/user/ordo}"
ORDO_FIXTURES="$ORDO_SRC/examples/ecir/consumer"
ORDO_COMMIT="e6fe390e47bf1d6d777017ced0b381f1c7d6acf7"
export PATH="/root/.dotnet:$PATH" DOTNET_ROOT=/root/.dotnet DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1

BASELINE_PRAXIS="$BIN/praxis-3.12.0/x/praxis-linux-x64/praxis"
TREATMENT_PRAXIS="${REL001_TREATMENT_PRAXIS:-$BIN/praxis-3.15.0/x/praxis-linux-x64/praxis}"
DOKIMOS="$BIN/dokimos-0.6.0/x/dokimos"
SDE="$BIN/ordo-sde/sde"

# arm_init ARM: sets PRAXIS and the runtime identity environment.
arm_init() {
  ARM="$1"
  case "$ARM" in
    baseline) PRAXIS="$BASELINE_PRAXIS" ;;
    treatment) PRAXIS="$TREATMENT_PRAXIS"; export PRAXIS_DOKIMOS_EXECUTABLE="$DOKIMOS" ;;
    *) echo "unknown arm $ARM" >&2; exit 2 ;;
  esac
  export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=rel001/agent PRAXIS_TELEMETRY_PROVIDER=test PRAXIS_TELEMETRY_RUNTIME=test
  PRAXIS_VERSION="$("$PRAXIS" --version 2>/dev/null | awk '{print $2}')"
  PRAXIS_SHA="$(sha256sum "$(dirname "$PRAXIS")/praxis-bin" | cut -d' ' -f1)"
  DOKIMOS_SHA="$(sha256sum "$DOKIMOS" | cut -d' ' -f1)"
  SDE_SHA="$(sha256sum "$(dirname "$SDE")/sde.dll" | cut -d' ' -f1)"
}

now_ms() { date +%s%3N; }
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }

# new_run EXP CASE: creates $RUNS/<runId> with repo/ and inputs/, sets RUN_ID, RUN_DIR, REPO.
new_run() {
  RUN_ID="REL-001-$1-$ARM-$2-$(date +%s%N | tail -c 7)"
  RUN_DIR="$RUNS/$RUN_ID"
  REPO="$RUN_DIR/repo"
  rm -rf "$RUN_DIR"; mkdir -p "$REPO" "$RUN_DIR/inputs" "$RUN_DIR/logs"
}

# init_repo DIR ID...: git repository with a work queue holding the given items (captured).
init_repo() {
  local dir="$1"; shift
  mkdir -p "$dir/.ros/work"
  ( cd "$dir"
    git init -q . && git config user.email rel001@example.invalid && git config user.name rel001
    printf '%s\n' "$@" | jq -R . | jq -sc '{schemaVersion:"1.0.0",items:[.[]|{id:.,status:"captured"}]}' > .ros/work/queue.json
    printf 'fixture\n' > README.md
    git add -A && git commit -qm "fixture" )
}

# baseline items must be ready before work start.
baseline_ready() { ( cd "$1" && "$PRAXIS" work backlog-transition --id "$2" --action ready --occurred-at "$(utc)" >/dev/null ); }

# write_authority FILE [required decision ids json array] [required conflict resolution ids json array]
write_authority() {
  jq -n --argjson dec "${2:-[]}" --argjson cr "${3:-[]}" '{OrdoContractVersion:"",OrdoContractDigest:"",SupportedOrdoContractVersions:["ecir/1"],RequiredRequirementIds:[],RequiredDecisionIds:$dec,RequiredConflictResolutionIds:$cr,RequiredValidationNames:["unit-tests"],RequiredEvidenceIds:["EV-TESTS"]}' > "$1"
}

# contract_keys FILE -> --requirement args for every requirement key in an ecir/1 contract.
contract_req_args() { jq -r '.requirements[]?.source.key | "--requirement\n" + .' "$1" 2>/dev/null || true; }

# json_or_null TEXT: the text if it parses as JSON, else a JSON string of it.
json_or_null() { if printf '%s' "$1" | jq -e . >/dev/null 2>&1; then printf '%s' "$1" | jq -c .; else jq -cn --arg t "$1" '{unparsed:$t}'; fi; }

# emit FILE JSON-OBJECT-OF-CASE-FIELDS: appends one result line with run/binary metadata.
emit() {
  local out="$1" body="$2"
  mkdir -p "$(dirname "$out")"
  jq -cn --argjson b "$body" --arg arm "$ARM" --arg run "$RUN_ID" --arg pv "$PRAXIS_VERSION" --arg ps "$PRAXIS_SHA" \
     --arg ds "$DOKIMOS_SHA" --arg ss "$SDE_SHA" --arg oc "$ORDO_COMMIT" --arg at "$(utc)" '
    {schema:"cbe.rel-001.case-result/1", runId:$run, arm:$arm, recordedAt:$at,
     binaries:({praxis:{version:$pv, sha256:$ps}} +
       (if $arm=="treatment" then {dokimos:{version:"0.6.0", sha256:$ds}, ordo:{commit:$oc, sdeDllSha256:$ss}} else {} end))} + $b' >> "$out"
}

# ---- treatment helpers (Praxis >= 3.15.0). Output: JSON on stdout; exit code in $RC.
VALID_CONTRACT="$ORDO_FIXTURES/valid-contract.json"
t_claim() { local dir="$1" actor="$2"; shift 2; set +e; OUT=$(cd "$dir" && PRAXIS_ACTOR="$actor" "$PRAXIS" work claim "$@" 2>&1); RC=$?; set -e; }
t_cmd() { local dir="$1" actor="$2"; shift 2; set +e; OUT=$(cd "$dir" && PRAXIS_ACTOR="$actor" "$PRAXIS" "$@" 2>&1); RC=$?; set -e; }
# t_validate DIR ACTOR ID TOKEN GEN CMD... ; sets OUT RC EVPATH
t_validate() { local dir="$1" actor="$2" id="$3" tok="$4" gen="$5"; shift 5
  set +e; OUT=$(cd "$dir" && PRAXIS_ACTOR="$actor" "$PRAXIS" work validate-run --id "$id" --token "$tok" --generation "$gen" --validation unit-tests --evidence-id EV-TESTS -- "$@" 2>&1); RC=$?; set -e
  EVPATH=$(printf '%s' "$OUT" | jq -r '.resultPath // empty' 2>/dev/null || true)
  if [ -n "$EVPATH" ] && [ "${EVPATH#/}" = "$EVPATH" ]; then EVPATH="$dir/$EVPATH"; fi; }
# t_complete DIR ACTOR ID TOKEN GEN EVIDENCE-PATH [CONTRACT] [AUTHORITY] [extra args...]
t_complete() { local dir="$1" actor="$2" id="$3" tok="$4" gen="$5" ev="$6" contract="${7:-$VALID_CONTRACT}" auth="${8:-}"; shift 8 2>/dev/null || shift $#
  if [ -z "$auth" ]; then auth="$RUN_DIR/inputs/authority.json"; [ -f "$auth" ] || write_authority "$auth"; fi
  local sha vrev; sha=${T_COMMIT:-$(git -C "$dir" rev-parse HEAD)}; vrev=${T_VREV:-$sha}
  local -a reqs; mapfile -t reqs < <(contract_req_args "$contract")
  [ ${#reqs[@]} -gt 0 ] || reqs=(--requirement "requirements/domain.md#R-001")
  set +e; OUT=$(cd "$dir" && PRAXIS_ACTOR="$actor" "$PRAXIS" work complete-verified --id "$id" --token "$tok" --generation "$gen" \
     --commit "$sha" --verification-revision "$vrev" --authority "$auth" --ordo-contract "$contract" "${reqs[@]}" \
     --validation unit-tests=passed:EV-TESTS ${ev:+--evidence "EV-TESTS=$ev"} "$@" 2>&1); RC=$?; set -e; }
# claim_state DIR ID -> compact JSON of the current claim record.
claim_state() { (cd "$1" && "$PRAXIS" work claims "$2" 2>/dev/null) | jq -c '(.claim // .claims[0] // .) | {status, effectiveStatus, generation, revision, holder: (.holder.claimant // null), pendingPacketDigest, consumed: (.consumedPacketDigests|length? // null), completed: (.completion != null)}' 2>/dev/null || echo null; }
summ() { printf '%s' "$1" | jq -c '{outcome, code, codes: (.codes // null)} | with_entries(select(.value != null))' 2>/dev/null || jq -cn --arg t "${1:0:300}" '{unparsed:$t}'; }
count_events() { local f="$1/.ros/events/events.jsonl"; if [ -f "$f" ]; then grep -c "\"type\":\"$2\"" "$f" || true; else echo 0; fi; }
