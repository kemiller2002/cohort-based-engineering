#!/usr/bin/env bash
# REL-001 run-03 harness library (sourced by run-03/harness/*.sh). Self-contained: it carries over the run-01
# helpers (harness/lib.sh: utc, now_ms, write_authority, contract_decisions) and the run-02 helpers
# (run-02/harness/lib.sh: shims, copy_tool, tool_version, run_paths, verifier_stop) with provenance in
# run-03/PROVENANCE.md. Every path and pin is an environment override; pins.json is the source of truth.
#
# REL003_DRY_RUN=1 (smoke only): no dotnet and no Echelon binaries are needed. Setup records "dry-run" for
# the tool versions, the scorer skips the hidden oracle (recorded as not run) and uses only the harness
# cross-check of tokens and cost. Dry-run ids must contain -SMOKE-; they never become observations.
set -euo pipefail

H3="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # run-03/harness
R3="$(cd "$H3/.." && pwd)"                            # run-03
FIX3="$R3/fixtures"
CBE="$(cd "$R3/../../../.." && pwd)"                 # cohort-based-engineering checkout
PINS="${REL003_PINS:-$H3/pins.json}"
DRY_RUN="${REL003_DRY_RUN:-0}"

RUNS="${REL003_RUNS:-/tmp/claude-0/rel003/runs}"      # agent workspaces
HOSTS="${REL003_HOST:-/tmp/claude-0/rel003/host}"     # host-owned inputs and the D verifier (C, D)
STATES="${REL003_STATE:-/tmp/claude-0/rel003/state}"  # harness state: run.json, digests, transcripts, scoring
OBSERVATIONS="${REL003_OBSERVATIONS:-$R3/observations}"

pin() { local v; v=$(jq -r "$1 // \"TBD\"" "$PINS"); echo "$v"; }
PRAXIS_C="${REL003_PRAXIS_C:-$(pin .arms.C.praxis.path)}"
DOKIMOS_C="${REL003_DOKIMOS_C:-$(pin .arms.C.dokimos.path)}"
ORDO_C="${REL003_ORDO_C:-$(pin .arms.C.ordo.path)}"
PRAXIS_D="${REL003_PRAXIS_D:-$(pin .arms.D.praxis.path)}"
DOKIMOS_D="${REL003_DOKIMOS_D:-$(pin .arms.D.dokimos.path)}"
ORDO_D="${REL003_ORDO_D:-$(pin .arms.D.ordo.path)}"
MEASURE_PRAXIS="${REL003_MEASURE_PRAXIS:-$(pin .measurement.path)}"
PRICE_TABLE="${REL003_PRICE_TABLE:-$R3/pricing/anthropic.price-table.json}"
AGENT_CONFIG="${REL003_MODEL_CONFIG:-$H3/agent-config.json}"
MODEL_PROVIDER="${REL003_MODEL_PROVIDER:-anthropic}"
MODEL="${REL003_MODEL:-$(jq -r .model "$AGENT_CONFIG")}"
CACHE_CONDITION="${REL003_CACHE_CONDITION:-$(pin .launcher.cacheCondition)}"
DOTNET_ROOT_DIR="${REL003_DOTNET_ROOT:-/root/.dotnet}"
REAL_DOTNET="${REL003_DOTNET:-$DOTNET_ROOT_DIR/dotnet}"
DIRECTIVES="$R3/directives/DIRECTIVES.md"
LEASE_SECONDS=3600

ARMS="bare directives echelon-original echelon-optimized"
arm_letter() { case "$1" in bare) echo A;; directives) echo B;; echelon-original) echo C;; echelon-optimized) echo D;; *) return 1;; esac; }
is_echelon() { [ "$1" = echelon-original ] || [ "$1" = echelon-optimized ]; }
has_directives() { [ "$1" != bare ]; }
is_tbd() { [ -z "$1" ] || [[ "$1" == TBD* ]]; }

utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
now_ms() { date +%s%3N; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
tree_sha() { (cd "$1" && find . -type f | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -d' ' -f1); }

# run-01 harness/lib.sh write_authority (amendment A2) and contract_decisions, unchanged.
write_authority() {
  jq -n --argjson dec "${2:-[]}" --argjson cr "${3:-[]}" '{OrdoContractVersion:"",OrdoContractDigest:"",SupportedOrdoContractVersions:["ecir/1"],RequiredRequirementIds:[],RequiredDecisionIds:$dec,RequiredConflictResolutionIds:$cr,RequiredValidationNames:["unit-tests"],RequiredEvidenceIds:["EV-TESTS"]}' > "$1"
}
contract_decisions() { jq -c '[.nodes[]? | select(.kind=="decision") | .id]' "$1" 2>/dev/null || echo '[]'; }

# label_of RUNID: trial | pilot | smoke (from the id; run-02 convention).
label_of() { case "$1" in *-SMOKE-*) echo smoke;; *-PILOT-*) echo pilot;; *) echo trial;; esac; }

# require_pins ARM: a pilot or confirmatory run needs every pin the arm uses frozen (gate G4).
require_pins() {
  local arm="$1" missing=()
  is_tbd "$(pin .launcher.cacheCondition)" && missing+=(launcher.cacheCondition)
  is_tbd "$(pin .measurement.sha256)" && missing+=(measurement.sha256)
  is_tbd "$(pin .dotnet.sdk)" && missing+=(dotnet.sdk)
  if is_echelon "$arm"; then
    local L; [ "$arm" = echelon-original ] && L=C || L=D
    for k in praxis.version praxis.sha256 praxis.path dokimos.version dokimos.sha256 dokimos.path ordo.version ordo.sha256 ordo.path sha256Entry; do
      is_tbd "$(pin ".arms.$L.$k")" && missing+=("arms.$L.$k")
    done
  fi
  [ ${#missing[@]} -eq 0 ] || { echo "pins not frozen (gate G4): ${missing[*]}" >&2; return 1; }
}

launcher() {
  case "$1" in
    *.dll) printf '#!/usr/bin/env bash\nexec "%s" "%s" "$@"\n' "$REAL_DOTNET" "$1" > "$2" ;;
    *) printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$1" > "$2" ;;
  esac
  chmod +x "$2"
}

# copy_tool SRC DEST_DIR NAME (run-02, unchanged): private copy of a binary plus DEST_DIR/NAME; prints its identity file.
copy_tool() {
  local src="$1" dest="$2" name="$3"
  mkdir -p "$dest"
  case "$src" in
    *.dll) cp -r "$(dirname "$src")/." "$dest/lib"; launcher "$dest/lib/$(basename "$src")" "$dest/$name"; echo "$dest/lib/$(basename "$src")" ;;
    *) if [ -f "$(dirname "$src")/praxis-bin" ]; then cp -r "$(dirname "$src")/." "$dest/lib"; launcher "$dest/lib/$(basename "$src")" "$dest/$name"; echo "$dest/lib/praxis-bin"
       else cp "$src" "$dest/lib-$name"; launcher "$dest/lib-$name" "$dest/$name"; echo "$dest/lib-$name"; fi ;;
  esac
}

tool_version() {
  local o; o=$("$1" --version 2>/dev/null || true)
  if jq -e .DokimosVersion >/dev/null 2>&1 <<<"$o"; then jq -r .DokimosVersion <<<"$o"; else head -1 <<<"$o" | sed 's/^praxis //'; fi
}

# The dotnet logging shim (run-02, unchanged apart from the variable prefix): one JSON line per invocation.
write_dotnet_shim() {
  local out="$1" log="$2" source_default="$3"
  cat > "$out" <<SHIM
#!/usr/bin/env bash
# REL-001 run-03 shim: records each dotnet invocation to $log, then runs the real dotnet.
start=\$(date +%s%3N); set +e; "$REAL_DOTNET" "\$@"; rc=\$?
jq -cn --arg at "\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" --argjson ms \$(( \$(date +%s%3N) - start )) --argjson rc \$rc \\
  --arg cwd "\$PWD" --arg src "\${REL003_DOTNET_SOURCE:-$source_default}" --arg agent "\${REL003_AGENT:-}" '
  \$ARGS.positional as \$a
  | ([\$a[] | select(startswith("-") | not)][0] // "") as \$verb
  | (if \$verb == "test" or \$verb == "vstest" then
       (if any(\$a[]; . == "--list-tests" or . == "-lt") then "test-list"
        elif any(\$a[]; . == "--filter" or startswith("--filter=") or . == "--tests" or startswith("--tests:") or startswith("/Tests:") or startswith("/TestCaseFilter")) then "test-focused"
        else "test-full" end)
     elif \$verb == "build" then "build" elif \$verb == "restore" then "restore" else "other" end) as \$kind
  | {at:\$at, ms:\$ms, exit:\$rc, argv:\$a, cwd:\$cwd, source:\$src, agent:\$agent, kind:\$kind}' --args -- "\$@" >> "$log"
exit \$rc
SHIM
  chmod +x "$out"
}

# The praxis logging shim (run-02, unchanged apart from the variable prefix).
write_praxis_shim() {
  local out="$1" real="$2" logdir="$3"
  cat > "$out" <<SHIM
#!/usr/bin/env bash
# REL-001 run-03 shim: records each praxis invocation to $logdir/praxis.jsonl, then runs the pinned Praxis.
mkdir -p "$logdir/praxis-out"; n="\$(date +%s%N)-\$\$"; head=\$(git rev-parse HEAD 2>/dev/null || true)
if [ "\${1:-}" = work ] && [ "\${2:-}" = validate-run ]; then export REL003_DOTNET_SOURCE=validate-run; fi
start=\$(date +%s%3N); set +e; "$real" "\$@" | tee "$logdir/praxis-out/\$n.out"; rc=\${PIPESTATUS[0]}
jq -cn --arg at "\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" --argjson ms \$(( \$(date +%s%3N) - start )) --argjson rc \$rc --arg head "\$head" \\
  --arg cwd "\$PWD" --arg agent "\${REL003_AGENT:-}" --arg out "praxis-out/\$n.out" \\
  '\$ARGS.positional as \$a | {at:\$at, ms:\$ms, exit:\$rc, argv:\$a, head:\$head, cwd:\$cwd, agent:\$agent, stdout:\$out}' --args -- "\$@" >> "$logdir/praxis.jsonl"
exit \$rc
SHIM
  chmod +x "$out"
}

task_field() { jq -r "$2" "$FIX3/tasks/$1/task.json"; }

# run_paths RUNID: RUN_DIR (workspace), HD (host root), HI (host inputs), HS (harness state; never named to the agent).
run_paths() { RUN_ID="$1"; RUN_DIR="$RUNS/$RUN_ID"; HD="$HOSTS/$RUN_ID"; HI="$HD/inputs"; HS="$STATES/$RUN_ID"; }

verifier_stop() {
  local pidf="$HS/verifier.pid"
  [ -f "$pidf" ] || return 0
  local pid; pid=$(cat "$pidf")
  if kill -0 "$pid" 2>/dev/null; then kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true; fi
  for _ in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
  kill -0 "$pid" 2>/dev/null && { kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true; }
  jq -n --arg at "$(utc)" --argjson pid "$pid" '{stoppedAt:$at, pid:$pid}' > "$HS/verifier-stopped.json"
  rm -f "$pidf" "$HD/verifier.sock"
}
