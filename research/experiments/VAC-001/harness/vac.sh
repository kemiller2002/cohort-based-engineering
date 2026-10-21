#!/usr/bin/env bash
# VAC-001 harness: chained work units in four arms, verified by a host-held oracle the agent never sees.
#
#   vac.sh setup  RUN ARM                 create the arm's workspace from the REL-001 run-03 fixture
#   vac.sh stage  RUN ARM UNIT TASK [FAULT]   stage one work unit (requirement, visible tests, contract) and
#                                         render its brief to $STATE/RUN/ARM/unit-UNIT.brief.md
#   vac.sh verify RUN ARM UNIT            independent verification of the committed HEAD after the agent's turn
#   vac.sh state  RUN ARM UNIT            (arm D) write the verified state from the latest verification
#
# Three trees, as in REL-001 run-03:
#   $VAC_WORK/RUN/ARM/repo     the agent workspace (the only path any brief names)
#   $VAC_STATE/RUN/ARM         harness state: briefs, verifier copies, logs. Never named to an agent.
#   $VAC_RESULTS/RUN/ARM       observations (committed to the experiment)
# The oracle, task.json and the reference solutions are never copied into a workspace.
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
EXP="$(cd "$H/.." && pwd)"
FIX="${VAC_FIXTURE:-$(cd "$EXP/../REL-001/run-03/fixtures" && pwd)}"
VAC_WORK="${VAC_WORK:-/home/user/vac-work}"
VAC_STATE="${VAC_STATE:-/home/user/.vac-state}"
VAC_RESULTS="${VAC_RESULTS:-$EXP/results}"
export DOTNET_ROOT="${DOTNET_ROOT:-/root/.dotnet}" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
export PATH="$DOTNET_ROOT:$PATH"
ORDO_BIN="${VAC_ORDO:-/home/user/ordo/src/Sde.Cli/bin/Release/net8.0/sde}"
PRAXIS_DLL="${VAC_PRAXIS_DLL:-/home/user/praxis/src/Praxis.Cli/bin/Release/net10.0/praxis.dll}"
FSX="$H/vac.fsx"
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
git_h() { git -C "$1" -c user.name=vac-harness -c user.email=harness@vac.invalid "${@:2}"; }
paths() { RUN="$1"; ARM="$2"; WS="$VAC_WORK/$RUN/$ARM"; REPO="$WS/repo"; ST="$VAC_STATE/$RUN/$ARM"; RS="$VAC_RESULTS/$RUN/$ARM"; }
arm_ok() { case "$1" in A|B|C|D|DR) return 0;; *) echo "unknown arm $1 (A B C D DR)" >&2; return 2;; esac; }
echelon() { case "$1" in C|D|DR) return 0;; *) return 1;; esac; }
praxis_arm() { case "$1" in D|DR) return 0;; *) return 1;; esac; }

cmd_setup() {
  paths "$1" "$2"; arm_ok "$ARM"
  [ -e "$WS" ] && { echo "exists: $WS (every run needs a fresh RUN id)" >&2; exit 2; }
  mkdir -p "$WS/tools/bin" "$ST" "$RS"
  cp -r "$FIX/repo" "$REPO"
  mkdir -p "$REPO/requirements" "$REPO/.vac/reports"
  cp "$EXP/directives/DIRECTIVES.md" "$WS/DIRECTIVES.md"
  if echelon "$ARM"; then
    mkdir -p "$REPO/contracts" "$REPO/docs/decisions" "$REPO/docs/architecture"
    cp "$EXP/arm-files/RULES.md" "$REPO/docs/architecture/RULES.md"
    cp "$EXP/arm-files/DECISIONS.md" "$REPO/docs/decisions/DECISIONS.md"
    # ordo (released 1.17.0 sources, built from ordo@bb43c26) and the four-tier rule check
    printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$ORDO_BIN" > "$WS/tools/bin/ordo"
    printf '#!/usr/bin/env bash\nexec dotnet fsi --quiet --exec "%s" archcheck "${1:-.}"\n' "$FSX" > "$WS/tools/bin/archcheck"
  fi
  if praxis_arm "$ARM"; then
    printf '#!/usr/bin/env bash\nexec dotnet "%s" "$@"\n' "$PRAXIS_DLL" > "$WS/tools/bin/praxis"
    chmod +x "$WS/tools/bin/praxis"
    (cd "$REPO" && "$WS/tools/bin/praxis" init --project ledger > "$ST/praxis-init.log" 2>&1)
    # the scaffolded ./praxis launcher would download a native release; point it at the source build instead
    printf '#!/usr/bin/env sh\nexec dotnet "%s" "$@"\n' "$PRAXIS_DLL" > "$REPO/praxis"
  fi
  chmod +x "$WS"/tools/bin/* 2>/dev/null || true
  cat > "$WS/env.sh" <<ENV
export PATH="$WS/tools/bin:$DOTNET_ROOT:\$PATH" DOTNET_ROOT="$DOTNET_ROOT" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
cd "$REPO"
ENV
  git -C "$REPO" init -q -b main
  git_h "$REPO" add -A && git_h "$REPO" commit -qm "VAC-001: starting state ($ARM)"
  # every workspace has its own bare remote, so Praxis durable checkpoints (commit, push, checkpoint) work offline
  git init -q --bare -b main "$WS/origin.git"
  git -C "$REPO" remote add origin "$WS/origin.git" && git -C "$REPO" push -q -u origin main
  jq -n --arg run "$RUN" --arg arm "$ARM" --arg at "$(utc)" --arg base "$(git -C "$REPO" rev-parse HEAD)" \
    --arg fix "$FIX" --arg ordo "$(sha "$ORDO_BIN" 2>/dev/null || echo unavailable)" \
    --arg px "$( praxis_arm "$ARM" && sha "$PRAXIS_DLL" || echo none)" \
    '{schema:"cbe.vac-001.setup/1", run:$run, arm:$arm, createdAt:$at, baseCommit:$base, fixture:$fix,
      ordoSha256:$ordo, praxisDllSha256:$px, units:[]}' > "$ST/setup.json"
  cp "$ST/setup.json" "$RS/setup.json"
  echo "$WS"
}

# Render a brief from a template: {{KEY}} placeholders, values from the environment of this function.
render() { python3 -I "$H/render.py" "$@"; }

cmd_stage() {
  paths "$1" "$2"; UNIT="$3"; TASK="$4"; FAULT="${5:-none}"
  [ -d "$REPO" ] || { echo "no workspace for $RUN/$ARM" >&2; exit 2; }
  [ -f "$FIX/tasks/$TASK/requirement.md" ] || { echo "unknown task $TASK" >&2; exit 2; }
  cp "$FIX/tasks/$TASK/requirement.md" "$REPO/requirements/$TASK.md"
  cp "$FIX/tasks/$TASK/${TASK}AcceptanceTests.fs" "$REPO/tests/Ledger.Tests/Acceptance/"
  echelon "$ARM" && cp "$FIX/tasks/$TASK/contract.json" "$REPO/contracts/$TASK.json"
  [ -n "$(git -C "$REPO" status --porcelain)" ] && { git_h "$REPO" add -A && git_h "$REPO" commit -qm "VAC-001 harness: stage unit $UNIT ($TASK)"; }
  local prev=$(( UNIT - 1 ))
  render --arm "$ARM" --unit "$UNIT" --task "$TASK" --fault "$FAULT" --workspace "$WS" --repo "$REPO" \
    --env "$WS/env.sh" --directives "$WS/DIRECTIVES.md" --briefs "$EXP/briefs" --faults "$EXP/faults/faults.json" \
    --previous-report "$( [ "$prev" -ge 1 ] && echo ".vac/reports/unit-$prev.json" || echo none)" \
    --first "$( { [ "$UNIT" -eq 1 ] || [ "$ARM" = A ] || [ "$ARM" = DR ]; } && echo yes || echo no)" > "$ST/unit-$UNIT.brief.md"
  jq --argjson u "$UNIT" --arg t "$TASK" --arg f "$FAULT" --arg at "$(utc)" --arg c "$(git -C "$REPO" rev-parse HEAD)" \
    '.units += [{unit:$u, task:$t, fault:$f, stagedAt:$at, stagedCommit:$c}]' "$ST/setup.json" > "$ST/setup.json.tmp" \
    && mv "$ST/setup.json.tmp" "$ST/setup.json"
  cp "$ST/setup.json" "$RS/setup.json"
  mkdir -p "$WS/briefs" && cp "$ST/unit-$UNIT.brief.md" "$WS/briefs/unit-$UNIT.md"
  echo "$WS/briefs/unit-$UNIT.md"
}

# Independent verification. Runs on an exported copy of HEAD in harness state, never in the workspace.
cmd_verify() {
  paths "$1" "$2"; UNIT="$3"; ATTEMPT="${4:-1}"
  local V="$ST/verify-$UNIT-$ATTEMPT"; rm -rf "$V"; mkdir -p "$V/tree"
  local head; head=$(git -C "$REPO" rev-parse HEAD)
  local dirty; dirty=$(git -C "$REPO" status --porcelain | wc -l)
  git -C "$REPO" archive "$head" | tar -x -C "$V/tree"
  # tasks staged so far, in staging order; V7 has no oracle (its correct outcome is a stop)
  local tasks; tasks=$(jq -r --argjson u "$UNIT" '[.units[] | select(.unit <= $u) | .task] | unique | join(" ")' "$ST/setup.json")
  local start=$(date +%s%3N)
  local trc=0; ( cd "$V/tree" && timeout 900 dotnet test Ledger.slnx > "$V/tests.log" 2>&1 ) || trc=$?
  # cumulative oracle: every staged task's hidden tests, compiled together against this tree
  mkdir -p "$V/oracle"
  sed "s#LEDGER_PROJECT_PATH#$V/tree/src/Ledger/Ledger.fsproj#; s#<Compile Include=\"OracleTests.fs\" />#ORACLE_FILES#" "$FIX/oracle/Oracle.fsproj" > "$V/oracle/Oracle.fsproj.tmpl"
  local inc=""
  for t in $tasks; do [ -f "$FIX/oracle/$t/OracleTests.fs" ] || continue; cp "$FIX/oracle/$t/OracleTests.fs" "$V/oracle/Oracle$t.fs"; inc="$inc<Compile Include=\"Oracle$t.fs\" />"; done
  sed "s#ORACLE_FILES#$inc#" "$V/oracle/Oracle.fsproj.tmpl" > "$V/oracle/Oracle.fsproj"; rm "$V/oracle/Oracle.fsproj.tmpl"
  local orc=0
  if [ -n "$inc" ]; then ( cd "$V/oracle" && timeout 900 dotnet test --logger "trx;LogFileName=oracle.trx" > "$V/oracle.log" 2>&1 ) || orc=$?; fi
  dotnet fsi --quiet --exec "$FSX" archcheck "$V/tree" --json > "$V/arch.json" 2> "$V/arch.err" || true
  dotnet fsi --quiet --exec "$FSX" evidence "$V/tree" "$UNIT" > "$V/evidence.json" 2> "$V/evidence.err" || true
  local ms=$(( $(date +%s%3N) - start ))
  dotnet fsi --quiet --exec "$FSX" observe --run "$RUN" --arm "$ARM" --unit "$UNIT" --attempt "$ATTEMPT" --head "$head" \
    --dirty "$dirty" --tests-rc "$trc" --tests-log "$V/tests.log" --oracle-rc "$orc" --oracle-dir "$V/oracle" \
    --arch "$V/arch.json" --evidence "$V/evidence.json" --setup "$ST/setup.json" --fixture "$FIX" --verify-ms "$ms" \
    --report "$V/tree/.vac/reports/unit-$UNIT.json" > "$RS/verify-$UNIT-$ATTEMPT.json"
  echo "$RS/verify-$UNIT-$ATTEMPT.json"
}

# Arm D: persist verified state. Only verified facts are promoted; everything else stays provisional or rejected.
cmd_state() {
  paths "$1" "$2"; UNIT="$3"
  local obs; obs=$(ls "$RS"/verify-"$UNIT"-*.json | sort -V | tail -1)
  local prev="$REPO/.vac/verified-state.json"
  dotnet fsi --quiet --exec "$FSX" state --observation "$obs" --previous "$prev" --report "$REPO/.vac/reports/unit-$UNIT.json" \
    --rules "$EXP/arm-files/RULES.md" > "$ST/verified-state.json"
  cp "$ST/verified-state.json" "$prev"; cp "$ST/verified-state.json" "$RS/verified-state-$UNIT.json"
  git_h "$REPO" add .vac/verified-state.json && git_h "$REPO" commit -qm "VAC-001 harness: verified state after unit $UNIT"
  git -C "$REPO" push -q origin HEAD 2>/dev/null || true
  echo "$prev"
}

# After the agent's turn: verify, then usage for the unit window, then (D, DR) verified state.
#   vac.sh finish RUN ARM UNIT AGENT_ID [ATTEMPT]
cmd_finish() {
  paths "$1" "$2"; UNIT="$3"; AGENT="$4"; ATTEMPT="${5:-1}"
  local obs; obs=$(cmd_verify "$RUN" "$ARM" "$UNIT" "$ATTEMPT")
  local from; from=$(jq -r --argjson u "$UNIT" '.units[] | select(.unit == $u) | .stagedAt' "$ST/setup.json")
  # a repair attempt's window starts where the previous attempt's ended, so no request is counted twice
  [ "$ATTEMPT" -gt 1 ] && from=$(jq -rs --argjson u "$UNIT" --argjson t "$(( ATTEMPT - 1 ))" '[.[] | select(.unit == $u and .attempt == $t)][-1].finishedAt' "$ST/finish.jsonl")
  local tr="${VAC_TRANSCRIPTS:-/root/.claude/projects/-home-user/33f5e1ff-fd17-5061-b88b-9980676c7c5b/subagents}/agent-$AGENT.jsonl"
  dotnet fsi --quiet --exec "$FSX" usage --transcript "$tr" --from "$from" --to "$(utc)" --workspace "$WS" \
    --prices "$EXP/../../pricing/anthropic.price-table.json" > "$RS/usage-$UNIT-$ATTEMPT.json"
  jq -n --arg a "$AGENT" --argjson u "$UNIT" --argjson t "$ATTEMPT" --arg at "$(utc)" '{agentId:$a, unit:$u, attempt:$t, finishedAt:$at}' >> "$ST/finish.jsonl"
  jq -c '{unit, attempt, task, accepted: .verdict.accepted, claim: .claim.outcome, falseCompletion: .verdict.falseCompletion,
          earlierFailing: .verdict.earlierTasksFailing, oracleFailed: .oracle.failed, arch: .architecture.passed, dirty: .uncommittedPaths,
          build: .build.ok}' "$obs"
  jq -c '{tokens: .tokens.total, cost: .costUsd, req: .requests, ctx: .context.last, compactions, models, x4: (.contaminationHits | length)}' "$RS/usage-$UNIT-$ATTEMPT.json"
}

# Amendment A1: after the V7 unit (an unresolvable conflict; the correct outcome is a stop), the harness descopes V7
# in every arm by removing its visible acceptance tests, which otherwise keep the test project from compiling.
cmd_descope() {
  paths "$1" "$2"; TASK="$3"
  rm -f "$REPO/tests/Ledger.Tests/Acceptance/${TASK}AcceptanceTests.fs"
  [ -n "$(git -C "$REPO" status --porcelain)" ] && git_h "$REPO" add -A && git_h "$REPO" commit -qm "VAC-001 harness: descope $TASK (blocked on an unresolved decision conflict; amendment A1)"
  git -C "$REPO" push -q origin HEAD 2>/dev/null || true
  echo "descoped $TASK in $RUN/$ARM"
}

case "${1:-}" in
  descope) shift; cmd_descope "$@";;
  finish) shift; cmd_finish "$@";;
  setup)  shift; cmd_setup "$@";;
  stage)  shift; cmd_stage "$@";;
  verify) shift; cmd_verify "$@";;
  state)  shift; cmd_state "$@";;
  *) sed -n '2,8p' "$0"; exit 2;;
esac
