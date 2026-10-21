#!/usr/bin/env bash
# REL-001 run-02 harness library (sourced by run-02/harness/*.sh).
# Reuses the run-01 helpers (harness/lib.sh: utc, now_ms, write_authority, contract_decisions,
# contract_req_args, json_or_null) and adds what four arms need. Every pin is overridable.
set -euo pipefail
# shellcheck source=../../harness/lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../harness/lib.sh"

H2="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # run-02/harness
R2="$(cd "$H2/.." && pwd)"                            # run-02
FIX2="$R2/fixtures"
CBE="$(cd "$REL/../../.." && pwd)"                    # cohort-based-engineering checkout

# Workspaces (what the agent sees) and host state (what it never needs) are separate trees.
RUNS="${REL002_RUNS:-/tmp/claude-0/rel002/runs}"
HOSTS="${REL002_HOST:-/tmp/claude-0/rel002/host}"     # host-owned inputs and the D verifier (C/D)
STATES="${REL002_STATE:-/tmp/claude-0/rel002/state}"  # harness state: run.json, digests, transcripts, scoring
OBSERVATIONS="${REL002_OBSERVATIONS:-$R2/observations}"

# Pins (finalized by the coordinator; each one is an environment override).
PRAXIS_C="${REL002_PRAXIS_C:-$BIN/praxis-3.16.0/x/praxis-linux-x64/praxis}"
DOKIMOS_C="${REL002_DOKIMOS_C:-$BIN/dokimos-0.6.0/x/dokimos}"
ORDO="${REL002_ORDO:-$BIN/ordo-1.17.0/x/ordo-linux-x64/ordo}"
PRAXIS_D="${REL002_PRAXIS_D:-$BIN/praxis-3.17.0/x/praxis-linux-x64/praxis}"   # released 3.17.0 (tag aea29b4a)
DOKIMOS_D="${REL002_DOKIMOS_D:-$BIN/dokimos-0.7.0/x/dokimos}"                  # released 0.7.0
MEASURE_PRAXIS="${REL002_MEASURE_PRAXIS:-$PRAXIS_D}"
PRICE_TABLE="${REL002_PRICE_TABLE:-$CBE/research/pricing/anthropic.price-table.json}"
AGENT_CONFIG="${REL002_MODEL_CONFIG:-$H2/agent-config.json}"
MODEL_PROVIDER="${REL002_MODEL_PROVIDER:-anthropic}"
MODEL="${REL002_MODEL:-$(jq -r .model "$AGENT_CONFIG")}"
REAL_DOTNET="${REL002_DOTNET:-/root/.dotnet/dotnet}"
DIRECTIVES="$R2/directives/DIRECTIVES.md"
LEASE_SECONDS=3600

ARMS="bare directives echelon-original echelon-optimized"
arm_letter() { case "$1" in bare) echo A;; directives) echo B;; echelon-original) echo C;; echelon-optimized) echo D;; *) return 1;; esac; }
is_echelon() { [ "$1" = echelon-original ] || [ "$1" = echelon-optimized ]; }
has_directives() { [ "$1" != bare ]; }

sha() { sha256sum "$1" | cut -d' ' -f1; }
# tree_sha DIR: digest of every file's sha256 in a stable order (run-01 fixtureDigest style).
tree_sha() { (cd "$1" && find . -type f | LC_ALL=C sort | xargs -r sha256sum | sha256sum | cut -d' ' -f1); }

# launcher TARGET OUT: an executable script that runs TARGET (a .dll through the real dotnet, never the logging shim).
launcher() {
  case "$1" in
    *.dll) printf '#!/usr/bin/env bash\nexec "%s" "%s" "$@"\n' "$REAL_DOTNET" "$1" > "$2" ;;
    *) printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$1" > "$2" ;;
  esac
  chmod +x "$2"
}

# copy_tool SRC DEST_DIR NAME: private copy of a binary (and, for a .dll or a launcher script, its directory)
# into DEST_DIR, plus DEST_DIR/NAME as the entry point. Prints the entry point's identity file (sha basis).
copy_tool() {
  local src="$1" dest="$2" name="$3"
  mkdir -p "$dest"
  case "$src" in
    *.dll) cp -r "$(dirname "$src")/." "$dest/lib"; launcher "$dest/lib/$(basename "$src")" "$dest/$name"; echo "$dest/lib/$(basename "$src")" ;;
    *) if [ -f "$(dirname "$src")/praxis-bin" ]; then cp -r "$(dirname "$src")/." "$dest/lib"; launcher "$dest/lib/$(basename "$src")" "$dest/$name"; echo "$dest/lib/praxis-bin"
       else cp "$src" "$dest/lib-$name"; launcher "$dest/lib-$name" "$dest/$name"; echo "$dest/lib-$name"; fi ;;
  esac
}

# tool_version EXE: the version EXE reports (Praxis: `--version`; Dokimos: DokimosVersion of its JSON).
tool_version() {
  local o; o=$("$1" --version 2>/dev/null || true)
  if jq -e .DokimosVersion >/dev/null 2>&1 <<<"$o"; then jq -r .DokimosVersion <<<"$o"; else head -1 <<<"$o" | sed 's/^praxis //'; fi
}

# The dotnet logging shim. Every invocation -> one JSON line in LOG: at, ms, exit, argv, cwd, source
# (agent | validate-run | verifier | smoke), agent (workspace name) and kind:
#   test-full    `dotnet test` without a test filter (the whole suite of the target)
#   test-focused `dotnet test --filter ...` (or -t/--tests via vstest)
#   test-list    `dotnet test --list-tests`
#   build | restore | other
write_dotnet_shim() {
  local out="$1" log="$2" source_default="$3"
  cat > "$out" <<EOF
#!/usr/bin/env bash
# REL-001 run-02 shim: records each dotnet invocation to $log, then runs the real dotnet.
start=\$(date +%s%3N); set +e; "$REAL_DOTNET" "\$@"; rc=\$?
jq -cn --arg at "\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" --argjson ms \$(( \$(date +%s%3N) - start )) --argjson rc \$rc \\
  --arg cwd "\$PWD" --arg src "\${REL002_DOTNET_SOURCE:-$source_default}" --arg agent "\${REL002_AGENT:-}" '
  \$ARGS.positional as \$a
  | ([\$a[] | select(startswith("-") | not)][0] // "") as \$verb
  | (if \$verb == "test" or \$verb == "vstest" then
       (if any(\$a[]; . == "--list-tests" or . == "-lt") then "test-list"
        elif any(\$a[]; . == "--filter" or startswith("--filter=") or . == "--tests" or startswith("--tests:") or startswith("/Tests:") or startswith("/TestCaseFilter")) then "test-focused"
        else "test-full" end)
     elif \$verb == "build" then "build" elif \$verb == "restore" then "restore" else "other" end) as \$kind
  | {at:\$at, ms:\$ms, exit:\$rc, argv:\$a, cwd:\$cwd, source:\$src, agent:\$agent, kind:\$kind}' --args -- "\$@" >> "$log"
exit \$rc
EOF
  chmod +x "$out"
}

# The praxis logging shim (C and D): argv, exit, timing, HEAD at invocation, stdout captured per call.
# validate-run's own dotnet calls are tagged source=validate-run.
write_praxis_shim() {
  local out="$1" real="$2" logdir="$3"
  cat > "$out" <<EOF
#!/usr/bin/env bash
# REL-001 run-02 shim: records each praxis invocation to $logdir/praxis.jsonl, then runs the pinned Praxis.
mkdir -p "$logdir/praxis-out"; n="\$(date +%s%N)-\$\$"; head=\$(git rev-parse HEAD 2>/dev/null || true)
if [ "\${1:-}" = work ] && [ "\${2:-}" = validate-run ]; then export REL002_DOTNET_SOURCE=validate-run; fi
start=\$(date +%s%3N); set +e; "$real" "\$@" | tee "$logdir/praxis-out/\$n.out"; rc=\${PIPESTATUS[0]}
jq -cn --arg at "\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" --argjson ms \$(( \$(date +%s%3N) - start )) --argjson rc \$rc --arg head "\$head" \\
  --arg cwd "\$PWD" --arg agent "\${REL002_AGENT:-}" --arg out "praxis-out/\$n.out" \\
  '\$ARGS.positional as \$a | {at:\$at, ms:\$ms, exit:\$rc, argv:\$a, head:\$head, cwd:\$cwd, agent:\$agent, stdout:\$out}' --args -- "\$@" >> "$logdir/praxis.jsonl"
exit \$rc
EOF
  chmod +x "$out"
}

# task_field TASK JQ: a value from the task's task.json (harness input; never copied to a workspace).
task_field() { jq -r "$2" "$FIX2/tasks/$1/task.json"; }

# run_paths RUNID: sets RUN_DIR (workspace root), HD (host root: inputs, verifier), HI (host inputs) and
# HS (harness state; never named by a brief or an environment variable the agent sees).
run_paths() { RUN_ID="$1"; RUN_DIR="$RUNS/$RUN_ID"; HD="$HOSTS/$RUN_ID"; HI="$HD/inputs"; HS="$STATES/$RUN_ID"; }

# workspace_list: the agent workspaces of a run (RUN_DIR, or RUN_DIR/agent-1 and RUN_DIR/agent-2 for U6).
workspace_names() { jq -r '.workspaces[].name' "$HS/run.json"; }

# verifier_stop: stops the D verifier daemon of the current run (idempotent).
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
