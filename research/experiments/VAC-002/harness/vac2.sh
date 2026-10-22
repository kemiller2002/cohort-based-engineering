#!/usr/bin/env bash
# VAC-002 harness: six arms working a chain of Lending units, K1 isolated agents, host gate, post-hoc hidden scoring.
# Adapted from VAC-001 harness/vac.sh (unit lifecycle) and ARCH-001 harness/launch-agent.sh (K1 launcher).
#
#   vac2.sh setup  RUN ARM                    create the arm's workspace from fixture/repo
#   vac2.sh stage  RUN ARM UNIT TASK          harness changes (before/), requirement, visible tests, contract; brief
#   vac2.sh turn   RUN ARM UNIT KIND BRIEF    one agent turn (KIND: new | resume); K1 `claude -p`
#   vac2.sh gate   RUN ARM UNIT ATTEMPT TIER  host gate (no hidden oracle); writes results gate-UNIT-ATTEMPT.json
#   vac2.sh state  RUN ARM UNIT               verified state (D, F) from the unit's last gate
#   vac2.sh unit   RUN ARM UNIT TASK          the whole unit for the arm (stage, turn, gate/repair, state)
#   vac2.sh chain  RUN ARM TASK...            units 1..N in order (stops at the budget stop file)
#   vac2.sh score  RUN ARM UNIT [ATTEMPT]     post-hoc scoring with the hidden oracle (harness only)
#
# Trees (never inside each other):
#   $VAC2_WORK/RUN/ARM      agent workspace: repo/, tools/, env.sh, DIRECTIVES.md, briefs/
#   $VAC2_STATE/RUN/ARM     harness state: agent config dirs, streams, verifier copies, logs (never named to an agent)
#   $VAC2_RESULTS/RUN/ARM   committed observations
#   $VAC2_SEALED            hidden oracle (plaintext only while scoring; encrypted at rest during agent turns)
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
EXP="$(cd "$H/.." && pwd)"
FIX="${VAC2_FIXTURE:-$EXP/fixture}"
VAC2_WORK="${VAC2_WORK:-/home/user/vac-work}"
VAC2_STATE="${VAC2_STATE:-/home/user/.vac2-state}"
VAC2_RESULTS="${VAC2_RESULTS:-$EXP/results}"
VAC2_SEALED="${VAC2_SEALED:-/home/user/.vac2-sealed}"
VAC1_FSX="$EXP/../VAC-001/harness/vac.fsx"
DIRECTIVES_SRC="$EXP/../VAC-001/directives/DIRECTIVES.md"
PRICES="$EXP/../../pricing/anthropic.price-table.json"
POLICY="$H/policy/adaptive-policy.json"
ARCH_POLICY="${VAC2_ARCH_POLICY:-$EXP/../../architectural-correctness/verifier/policy/lending.policy.json}"
CONFIG="$H/agent-config.json"
export DOTNET_ROOT="${DOTNET_ROOT:-/root/.dotnet}" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
export PATH="$DOTNET_ROOT:$PATH"
ARCHCHECK_DLL="${VAC2_ARCHCHECK:-/home/user/.vac2-tools/archcheck/archcheck.dll}"
ORDO_BIN="${VAC2_ORDO:-/home/user/.vac2-tools/ordo-src/src/Sde.Cli/bin/Release/net8.0/sde}"
PRAXIS_DLL="${VAC2_PRAXIS_DLL:-/home/user/.vac2-tools/praxis-src/src/Praxis.Cli/bin/Release/net10.0/praxis.dll}"
CLAUDE_BIN="${VAC2_CLAUDE:-/opt/node22/bin/claude}"
FSX="$H/vac2.fsx"
fsx() { dotnet fsi --quiet --exec "$FSX" "$@"; }
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
hgit() { git -C "$1" -c user.name="vac2 harness" -c user.email=harness@vac2.invalid -c commit.gpgsign=false "${@:2}"; }
paths() { RUN="$1"; ARM="$2"; WS="$VAC2_WORK/$RUN/$ARM"; REPO="$WS/repo"; ST="$VAC2_STATE/$RUN/$ARM"; RS="$VAC2_RESULTS/$RUN/$ARM"; }
arm_ok() { case "$1" in A|B|C|D|E|F) return 0;; *) echo "unknown arm $1 (A B C D E F)" >&2; return 2;; esac; }
echelon() { case "$1" in C|D|E|F) return 0;; *) return 1;; esac; }
praxis_arm() { case "$1" in D|F) return 0;; *) return 1;; esac; }
gated() { case "$1" in D|E|F) return 0;; *) return 1;; esac; }
long_lived() { case "$1" in B|C|D|E|F) return 0;; *) return 1;; esac; }
# Arm F: the agent is restarted (a new session that reconstructs from verified state) every RESTART_EVERY units.
RESTART_EVERY="${VAC2_RESTART_EVERY:-4}"
restart_unit() { [ "$1" = F ] && [ $(( ($2 - 1) % RESTART_EVERY )) -eq 0 ]; }
jset() { local f="$1"; shift; jq "$@" "$f" > "$f.tmp" && mv "$f.tmp" "$f"; }

cmd_setup() {
  paths "$1" "$2"; arm_ok "$ARM"
  [ -e "$WS" ] && { echo "exists: $WS (every run needs a fresh RUN id)" >&2; exit 2; }
  mkdir -p "$WS/tools/bin" "$WS/briefs" "$ST" "$RS"
  cp -r "$FIX/repo" "$REPO"
  mkdir -p "$REPO/requirements" "$REPO/.vac/reports"
  cp "$DIRECTIVES_SRC" "$WS/DIRECTIVES.md"
  if echelon "$ARM"; then
    mkdir -p "$REPO/contracts" "$WS/tools/policy"
    cp "$ARCH_POLICY" "$WS/tools/policy/lending.policy.json"
    printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$ORDO_BIN" > "$WS/tools/bin/ordo"
    printf '#!/usr/bin/env bash\nexec dotnet "%s" verify --repo "${1:-.}" --policy "%s"\n' "$ARCHCHECK_DLL" "$WS/tools/policy/lending.policy.json" > "$WS/tools/bin/archcheck"
  fi
  if praxis_arm "$ARM"; then
    printf '#!/usr/bin/env bash\nexec dotnet "%s" "$@"\n' "$PRAXIS_DLL" > "$WS/tools/bin/praxis"
    chmod +x "$WS/tools/bin/praxis"
    (cd "$REPO" && "$WS/tools/bin/praxis" init --project lending > "$ST/praxis-init.log" 2>&1) || true
    printf '#!/usr/bin/env sh\nexec dotnet "%s" "$@"\n' "$PRAXIS_DLL" > "$REPO/praxis"; chmod +x "$REPO/praxis"
  fi
  chmod +x "$WS"/tools/bin/* 2>/dev/null || true
  cat > "$WS/env.sh" <<ENV
export PATH="$WS/tools/bin:$DOTNET_ROOT:\$PATH" DOTNET_ROOT="$DOTNET_ROOT" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
cd "$REPO"
ENV
  git -C "$REPO" init -q -b main
  git -C "$REPO" config user.name "engineer"; git -C "$REPO" config user.email "engineer@lending.invalid"; git -C "$REPO" config commit.gpgsign false
  hgit "$REPO" add -A && hgit "$REPO" commit -qm "VAC-002: starting state ($ARM)"
  git init -q --bare -b main "$WS/origin.git"
  git -C "$REPO" remote add origin "$WS/origin.git" && git -C "$REPO" push -q -u origin main
  jq -n --arg run "$RUN" --arg arm "$ARM" --arg at "$(utc)" --arg base "$(git -C "$REPO" rev-parse HEAD)" --arg fix "$FIX" \
    --arg ordo "$(sha "$ORDO_BIN")" --arg arch "$(sha "$ARCHCHECK_DLL")" --arg px "$( praxis_arm "$ARM" && sha "$PRAXIS_DLL" || echo none)" \
    --arg claude "$("$CLAUDE_BIN" --version 2>/dev/null | head -1)" --arg policy "$(sha "$POLICY")" --arg brief "$(sha "$H/briefs/brief.md")" \
    '{schema:"cbe.vac-002.setup/1", run:$run, arm:$arm, createdAt:$at, baseCommit:$base, fixture:$fix, ordoSha256:$ordo,
      archcheckSha256:$arch, praxisDllSha256:$px, claudeCode:$claude, adaptivePolicySha256:$policy, briefTemplateSha256:$brief,
      lastVerifiedHead:$base, sessions:[], units:[]}' > "$ST/setup.json"
  cp "$ST/setup.json" "$RS/setup.json"
  echo "$WS"
}

# Pre-decision signals for the adaptive policy; computed for every arm (only Arm E acts on them).
pre_signals() {  # TASK STAGED_FROM STAGED_TO -> json on stdout
  local task="$1" from="$2" to="$3" req="$FIX/tasks/$1/requirement.md"
  local refused=false; [ "$(jq -r '.contract.ordoAdmits' "$FIX/tasks/$task/task.json")" = false ] && refused=true
  local decisions; decisions=$(git -C "$REPO" diff --name-only "$from" "$to" -- docs/decisions | wc -l)
  local last; last=$(jq -r .lastVerifiedHead "$ST/setup.json")
  local external; external=$(git -C "$REPO" log --format=%H "$last..$to" --author=harness@vac2.invalid | while read -r c; do git -C "$REPO" diff-tree --no-commit-id --name-only -r "$c" -- src; done | sort -u | wc -l)
  local sensitive=false; grep -qiE '\b(fine|fines|pay|payment|amount|waive|waiver|approver|owes)\b' "$req" && sensitive=true
  local newcmds; newcmds=$(grep -ciE 'a new command|new commands' "$req" || true)
  jq -n --argjson refused "$refused" --argjson dec "$decisions" --argjson ext "$external" --argjson sens "$sensitive" --argjson cmds "${newcmds:-0}" \
    '{contractRefused:$refused, decisionFilesStaged:$dec, externalSrcChanges:$ext, sensitive:$sens, newCommands:$cmds}'
}

cmd_stage() {
  paths "$1" "$2"; UNIT="$3"; TASK="$4"; local T="$FIX/tasks/$TASK"
  [ -d "$REPO" ] || { echo "no workspace for $RUN/$ARM" >&2; exit 2; }
  local from; from=$(git -C "$REPO" rev-parse HEAD)
  local fault; fault=$(jq -r --arg t "$TASK" '[.faults[] | select(.task == $t) | .id][0] // "none"' "$EXP/faults/faults.json")
  # 1. changes made by others before the unit (dependency updates and the like), as their own harness commit
  # (only the harness's own paths are added and committed: an agent's uncommitted work is never swept into them)
  if [ -d "$T/before" ]; then
    cp -r "$T/before/." "$REPO/"
    local msg; msg=$(jq -r --arg t "$TASK" '[.dependencyChanges[] | select(.before == $t) | .commit][0] // "VAC-002 harness: repository change"' "$EXP/faults/faults.json")
    local -a bp=(); while read -r f; do bp+=("$f"); done < <(cd "$T/before" && find . -type f | sed 's|^\./||')
    hgit "$REPO" add -- "${bp[@]}" && { hgit "$REPO" diff --cached --quiet -- "${bp[@]}" || hgit "$REPO" commit -qm "$msg" -- "${bp[@]}"; }
  fi
  # 2. the unit: decision revisions, requirement, visible tests, contract
  local -a sp=("requirements/$TASK.md")
  if [ -d "$T/stage" ]; then cp -r "$T/stage/." "$REPO/"; while read -r f; do sp+=("$f"); done < <(cd "$T/stage" && find . -type f | sed 's|^\./||'); fi
  cp "$T/requirement.md" "$REPO/requirements/$TASK.md"
  local f; for f in "$T"/acceptance/*.fs; do cp "$f" "$REPO/tests/Lending.Tests/Acceptance/"; sp+=("tests/Lending.Tests/Acceptance/$(basename "$f")"); done
  if echelon "$ARM"; then cp "$T/contract.json" "$REPO/contracts/$TASK.json"; sp+=("contracts/$TASK.json"); fi
  hgit "$REPO" add -- "${sp[@]}" && { hgit "$REPO" diff --cached --quiet -- "${sp[@]}" || hgit "$REPO" commit -qm "VAC-002 harness: stage unit $UNIT ($TASK)" -- "${sp[@]}"; }
  git -C "$REPO" push -q origin HEAD 2>/dev/null || true
  local to; to=$(git -C "$REPO" rev-parse HEAD)
  pre_signals "$TASK" "$from" "$to" > "$ST/pre-$UNIT.json"
  local restart=no; restart_unit "$ARM" "$UNIT" && restart=yes
  fsx render --arm "$ARM" --unit "$UNIT" --task "$TASK" --fault "$fault" --workspace "$WS" --repo "$REPO" --env "$WS/env.sh" \
    --directives "$WS/DIRECTIVES.md" --briefs "$H/briefs" --faults "$EXP/faults/faults.json" --restart "$restart" > "$WS/briefs/unit-$UNIT.md"
  jset "$ST/setup.json" --argjson u "$UNIT" --arg t "$TASK" --arg f "$fault" --arg at "$(utc)" --arg c "$to" --arg from "$from" --slurpfile pre "$ST/pre-$UNIT.json" \
    '.units += [{unit:$u, task:$t, fault:$f, stagedAt:$at, stagedFrom:$from, stagedCommit:$c, pre:$pre[0], attempts:[]}]'
  cp "$ST/setup.json" "$RS/setup.json"
  echo "$WS/briefs/unit-$UNIT.md"
}

# One K1 agent turn. new: fresh session (own CLAUDE_CONFIG_DIR and HOME). resume: continue the arm's current session.
cmd_turn() {
  paths "$1" "$2"; UNIT="$3"; KIND="$4"; BRIEF="$5"; local LABEL="${6:-unit-$UNIT}"
  local sid cfg home prompt
  if [ "$KIND" = new ]; then
    sid=$(python3 -I -c 'import uuid; print(uuid.uuid4())')
    cfg="$ST/agents/$sid/config"; home="$ST/agents/$sid/home"; mkdir -p "$cfg" "$home"
    jset "$ST/setup.json" --arg s "$sid" --argjson u "$UNIT" '.sessions += [{sessionId:$s, startedAtUnit:$u}] | .currentSession = $s'
    prompt=$(jq -r .prompt "$CONFIG")
  else
    sid=$(jq -r .currentSession "$ST/setup.json"); cfg="$ST/agents/$sid/config"; home="$ST/agents/$sid/home"
    prompt=$(jq -r .continuePrompt "$CONFIG")
  fi
  prompt=${prompt//\{BRIEF\}/$BRIEF}
  local tools; tools=$(jq -r '.tools.builtIn | join(",")' "$CONFIG")
  local budget=$(( $(jq -r .budgetMinutesPerTurn "$CONFIG") * 60 ))
  local window; window=$(jq -r .autoCompactWindowTokens "$CONFIG")
  local model; model=$(jq -r .model "$CONFIG")
  local -a unset=(); while read -r v; do unset+=(-u "$v"); done < <(jq -r '.environment.unset[]' "$CONFIG"; compgen -e | grep -E '^VAC2_' || true)
  local -a sess=(--session-id "$sid"); [ "$KIND" = resume ] && sess=(--resume "$sid")
  mkdir -p "$ST/turns"; local out="$ST/turns/$LABEL"
  local start; start=$(utc)
  set +e
  ( cd "$REPO" && env "${unset[@]}" HOME="$home" CLAUDE_CONFIG_DIR="$cfg" PATH="$WS/tools/bin:$DOTNET_ROOT:/usr/local/bin:/usr/bin:/bin" \
      DOTNET_ROOT="$DOTNET_ROOT" NUGET_PACKAGES="${NUGET_PACKAGES:-/root/.nuget/packages}" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 \
      MSBUILDDISABLENODEREUSE=1 DOTNET_CLI_USE_MSBUILD_SERVER=0 UseSharedCompilation=false TERM=dumb CLAUDE_CODE_AUTO_COMPACT_WINDOW="$window" \
      timeout "$budget" "$CLAUDE_BIN" -p "$prompt" --model "$model" "${sess[@]}" --output-format stream-json --verbose \
      --permission-mode bypassPermissions --tools "$tools" --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
      > "$out.stream.jsonl" 2> "$out.err" < /dev/null )
  local rc=$?; set -e
  local end; end=$(utc)
  fsx stream --stream "$out.stream.jsonl" --workspace "$WS" > "$out.usage.json" || echo '{}' > "$out.usage.json"
  local tr; tr=$(find "$cfg/projects" -name "$sid.jsonl" 2>/dev/null | head -1 || true)
  if [ -n "$tr" ]; then
    mkdir -p "$ST/transcripts"; cp "$tr" "$ST/transcripts/$sid.jsonl"
    dotnet fsi --quiet --exec "$VAC1_FSX" usage --transcript "$tr" --from "$start" --to "$end" --workspace "$WS" --prices "$PRICES" > "$out.requests.json" 2>/dev/null || echo '{}' > "$out.requests.json"
  fi
  jq -n --arg label "$LABEL" --arg sid "$sid" --arg kind "$KIND" --arg brief "$BRIEF" --arg bsha "$(sha "$BRIEF")" --arg s "$start" --arg e "$end" \
     --argjson rc "$rc" --slurpfile u "$out.usage.json" --slurpfile r <(cat "$out.requests.json" 2>/dev/null || echo '{}') \
     '{schema:"cbe.vac-002.turn/1", label:$label, sessionId:$sid, kind:$kind, brief:$brief, briefSha256:$bsha, startedAt:$s, endedAt:$e,
       exit:$rc, timedOut:($rc == 124), usage:$u[0],
       requests:($r[0] | {requests, tokens, context, compactions, models, efforts, contaminationHits, outsideWorkspace, costUsdLowerBound:.costUsd})}' > "$RS/turn-$LABEL.json"
  echo "$RS/turn-$LABEL.json"
}

# Export HEAD to a fresh clone in harness state (never the workspace). Prints the clone dir.
export_head() {  # DIR HEAD
  rm -rf "$1"; git clone -q --no-hardlinks "$REPO" "$1" && git -C "$1" checkout -q "$2"
}

cmd_gate() {
  paths "$1" "$2"; UNIT="$3"; ATTEMPT="$4"; TIER="$5"
  local V="$ST/gate-$UNIT-$ATTEMPT"; local head; head=$(git -C "$REPO" rev-parse HEAD)
  local dirty; dirty=$(git -C "$REPO" status --porcelain | wc -l)
  local task; task=$(jq -r --argjson u "$UNIT" '.units[] | select(.unit == $u) | .task' "$ST/setup.json")
  export_head "$V/tree" "$head"
  local start; start=$(date +%s%3N)
  ( cd "$V/tree" && timeout 900 dotnet test Lending.slnx > "$V/tests.log" 2>&1 ) || true
  local checks; checks=$(jq -r --arg t "$TIER" '.tiers[$t].checks | join(" ")' "$POLICY")
  if [[ " $checks " == *" architecture "* ]]; then
    dotnet "$ARCHCHECK_DLL" verify --repo "$V/tree" --policy "$ARCH_POLICY" --json > "$V/arch.json" 2> "$V/arch.err" || true
  fi
  fsx evidence "$V/tree" "$UNIT" > "$V/evidence.json" 2> "$V/evidence.err" || true
  local admits; admits=$(jq -r '.contract.ordoAdmits' "$FIX/tasks/$task/task.json")
  local ms=$(( $(date +%s%3N) - start ))
  fsx gate --policy "$POLICY" --tier "$TIER" --unit "$UNIT" --attempt "$ATTEMPT" --head "$head" --dirty "$dirty" --tests-log "$V/tests.log" \
    --arch "$V/arch.json" --evidence "$V/evidence.json" --report "$V/tree/.vac/reports/unit-$UNIT.json" --task "$FIX/tasks/$task/task.json" \
    --ordo-admits "$admits" --verify-ms "$ms" > "$RS/gate-$UNIT-$ATTEMPT.json"
  rm -rf "$V/tree/bin" "$V/tree/obj"
  jq -r .passed "$RS/gate-$UNIT-$ATTEMPT.json"
}

cmd_state() {
  paths "$1" "$2"; UNIT="$3"
  local g; g=$(ls "$RS"/gate-"$UNIT"-*.json | sort -V | tail -1); local att; att=$(jq -r .attempt "$g")
  local task; task=$(jq -r --argjson u "$UNIT" '.units[] | select(.unit == $u) | .task' "$ST/setup.json")
  local V="$ST/gate-$UNIT-$att"
  local ids; ids=$(grep -ohE 'LEND-L[0-9]+-R[0-9]+' "$REPO"/tests/Lending.Tests/Acceptance/*.fs 2>/dev/null | sort -u | paste -sd, -)
  local last; last=$(jq -r .lastVerifiedHead "$ST/setup.json")
  git -C "$REPO" log --format='%h %s' "$last..HEAD" --author=harness@vac2.invalid | grep -v 'stage unit\|verified state' > "$ST/external-$UNIT.txt" || true
  local prev="$REPO/.vac/verified-state.json"
  fsx state --gate "$g" --previous "$prev" --report "$V/tree/.vac/reports/unit-$UNIT.json" --evidence "$V/evidence.json" \
    --unit "$UNIT" --task "$task" --visible-ids "$ids" --external "$ST/external-$UNIT.txt" > "$ST/verified-state.json"
  cp "$ST/verified-state.json" "$prev"; cp "$ST/verified-state.json" "$RS/verified-state-$UNIT.json"
  hgit "$REPO" add -- .vac/verified-state.json && hgit "$REPO" commit -qm "VAC-002 harness: verified state after unit $UNIT" -- .vac/verified-state.json
  git -C "$REPO" push -q origin HEAD 2>/dev/null || true
}

# Post-turn signals for the adaptive policy (from the agent's own diff and report).
post_signals() {  # UNIT -> json
  local u="$1"; local from; from=$(jq -r --argjson u "$u" '.units[] | select(.unit == $u) | .stagedCommit' "$ST/setup.json")
  local files; files=$(git -C "$REPO" diff --name-only "$from" HEAD -- src | wc -l)
  local lines; lines=$(git -C "$REPO" diff --numstat "$from" HEAD -- src | awk '{s+=$1+$2} END {print s+0}')
  local tiers; tiers=$(git -C "$REPO" diff --name-only "$from" HEAD -- src | cut -d/ -f2 | sort -u | wc -l)
  local surface=false; git -C "$REPO" diff --name-only "$from" HEAD | grep -qE '\.fsproj$|global\.json$|Directory\.Build\.props$|/Vendor/' && surface=true
  local decedit=false; git -C "$REPO" diff --name-only "$from" HEAD -- docs/decisions | grep -qv 'DECISIONS.md' && decedit=true
  local rep="$REPO/.vac/reports/unit-$u.json"
  local assumptions=false blocked=false
  if [ -f "$rep" ]; then
    jq -e '([.decisions[]? | select(.basis == "assumption")] | length) > 0 or ((.openQuestions // []) | length) > 0 or ((.knownIssues // []) | length) > 0' "$rep" >/dev/null 2>&1 && assumptions=true
    [ "$(jq -r .outcome "$rep" 2>/dev/null)" = blocked ] && blocked=true
  fi
  local prevu=false; [ -f "$ST/unresolved" ] && prevu=true
  jq -n --argjson f "$files" --argjson l "$lines" --argjson t "$tiers" --argjson s "$surface" --argjson d "$decedit" --argjson a "$assumptions" \
     --argjson b "$blocked" --argjson p "$prevu" \
     '{filesChanged:$f, linesChanged:$l, tiersTouched:$t, buildSurfaceChanged:$s, decisionRecordEdited:$d, assumptions:$a, blocked:$b, previousUnresolved:$p}'
}

cmd_unit() {
  paths "$1" "$2"; UNIT="$3"; TASK="$4"
  local brief; brief=$(cmd_stage "$RUN" "$ARM" "$UNIT" "$TASK")
  local kind=resume
  { [ "$ARM" = A ] || [ "$UNIT" -eq 1 ] || restart_unit "$ARM" "$UNIT"; } && kind=new
  cmd_turn "$RUN" "$ARM" "$UNIT" "$kind" "$brief" > /dev/null
  git -C "$REPO" status --porcelain | wc -l > "$ST/dirty-$UNIT-1"
  local head; head=$(git -C "$REPO" rev-parse HEAD)
  jset "$ST/setup.json" --argjson u "$UNIT" --arg h "$head" --arg at "$(utc)" '(.units[] | select(.unit == $u) | .attempts) += [{attempt:1, head:$h, finishedAt:$at}]'
  if gated "$ARM"; then
    local tier=high
    if [ "$ARM" = E ]; then
      post_signals "$UNIT" > "$ST/post-$UNIT.json"
      fsx policy --policy "$POLICY" --pre "$ST/pre-$UNIT.json" --post "$ST/post-$UNIT.json" > "$RS/policy-$UNIT.json"
      tier=$(jq -r .tier "$RS/policy-$UNIT.json")
    fi
    local ok; ok=$(cmd_gate "$RUN" "$ARM" "$UNIT" 1 "$tier")
    if [ "$ok" != true ]; then
      local rb="$WS/briefs/unit-$UNIT-repair-1.md"
      fsx repair --briefs "$H/briefs" --gate "$RS/gate-$UNIT-1.json" --unit "$UNIT" --praxis "$(praxis_arm "$ARM" && echo yes || echo no)" > "$rb"
      cmd_turn "$RUN" "$ARM" "$UNIT" resume "$rb" "unit-$UNIT-repair-1" > /dev/null
      git -C "$REPO" status --porcelain | wc -l > "$ST/dirty-$UNIT-2"
      head=$(git -C "$REPO" rev-parse HEAD)
      jset "$ST/setup.json" --argjson u "$UNIT" --arg h "$head" --arg at "$(utc)" '(.units[] | select(.unit == $u) | .attempts) += [{attempt:2, head:$h, finishedAt:$at, repair:true}]'
      ok=$(cmd_gate "$RUN" "$ARM" "$UNIT" 2 "$tier")
    fi
    if [ "$ok" = true ]; then rm -f "$ST/unresolved"; else touch "$ST/unresolved"; fi
    praxis_arm "$ARM" && cmd_state "$RUN" "$ARM" "$UNIT"
  fi
  jset "$ST/setup.json" --arg h "$(git -C "$REPO" rev-parse HEAD)" '.lastVerifiedHead = $h'
  cp "$ST/setup.json" "$RS/setup.json"
  echo "$RUN $ARM unit $UNIT ($TASK) done at $(utc)"
}

# Runs units 1..N. Before each unit it checks the budget stop file; the orchestrator creates it to stop all chains
# at a unit boundary (BUDGET.md stopping rule).
cmd_chain() {
  paths "$1" "$2"; shift 2
  local u=0
  for task in "$@"; do
    u=$(( u + 1 ))
    [ -f "$VAC2_STATE/$RUN/STOP" ] && { echo "$RUN $ARM stopped before unit $u (budget stop)"; break; }
    if [ "$(jq --argjson u "$u" '[.units[]? | select(.unit == $u and (.attempts | length) > 0)] | length' "$ST/setup.json" 2>/dev/null || echo 0)" -gt 0 ]; then continue; fi
    cmd_unit "$RUN" "$ARM" "$u" "$task"
  done
}

# Post-hoc scoring: the hidden oracle of every task staged so far, against the unit's recorded head. Harness only.
cmd_score() {
  paths "$1" "$2"; UNIT="$3"
  local ATTEMPT="${4:-$(jq -r --argjson u "$UNIT" '[.units[] | select(.unit == $u) | .attempts[].attempt] | max' "$ST/setup.json")}"
  local head; head=$(jq -r --argjson u "$UNIT" --argjson a "$ATTEMPT" '.units[] | select(.unit == $u) | .attempts[] | select(.attempt == $a) | .head' "$ST/setup.json")
  local task; task=$(jq -r --argjson u "$UNIT" '.units[] | select(.unit == $u) | .task' "$ST/setup.json")
  local fault; fault=$(jq -r --argjson u "$UNIT" '.units[] | select(.unit == $u) | .fault' "$ST/setup.json")
  local staged; staged=$(jq -r --argjson u "$UNIT" '[.units[] | select(.unit <= $u) | .task] | join(",")' "$ST/setup.json")
  [ -d "$VAC2_SEALED/oracle" ] || { echo "the hidden oracle is sealed; unseal it before scoring" >&2; exit 2; }
  local V="$ST/score-$UNIT-$ATTEMPT"; export_head "$V/tree" "$head"
  local dirty=0
  # a unit whose agent left uncommitted work is recorded at turn end; committed state is what is scored
  [ -f "$ST/dirty-$UNIT-$ATTEMPT" ] && dirty=$(cat "$ST/dirty-$UNIT-$ATTEMPT")
  local start; start=$(date +%s%3N)
  ( cd "$V/tree" && timeout 900 dotnet test Lending.slnx > "$V/tests.log" 2>&1 ) || true
  mkdir -p "$V/oracle"
  local t; for t in ${staged//,/ }; do "$VAC2_SEALED/oracle/run.sh" "$V/tree" "$t" "$V/oracle" > /dev/null; done
  dotnet "$ARCHCHECK_DLL" verify --repo "$V/tree" --policy "$ARCH_POLICY" --json > "$V/arch.json" 2> "$V/arch.err" || true
  fsx evidence "$V/tree" "$UNIT" > "$V/evidence.json" 2> "$V/evidence.err" || true
  local ms=$(( $(date +%s%3N) - start ))
  local final; final=$(ls "$ST"/turns/unit-"$UNIT"*.stream.jsonl 2>/dev/null | sort -V | tail -1)
  jq -rs '[.[] | select(.type == "result") | .result][-1] // ""' "$final" > "$V/final.txt" 2>/dev/null || true
  fsx observe --run "$RUN" --arm "$ARM" --unit "$UNIT" --attempt "$ATTEMPT" --task "$task" --fault "$fault" --head "$head" --staged "$staged" \
    --fixture "$FIX" --tests-log "$V/tests.log" --oracle-dir "$V/oracle" --arch "$V/arch.json" --evidence "$V/evidence.json" \
    --report "$V/tree/.vac/reports/unit-$UNIT.json" --final "$V/final.txt" --dirty "$dirty" --verify-ms "$ms" > "$RS/score-$UNIT-$ATTEMPT.json"
  rm -rf "$V/tree" "$V/oracle"/*/bin "$V/oracle"/*/obj
  jq -c '{unit, attempt, task, accepted: .verdict.accepted, functional: .verdict.functional, surfaced: .verdict.conflictSurfaced,
          falseCompletion: .verdict.falseCompletion, earlier: .verdict.earlierTasksFailing, arch: .architecture.pass, failing: [.oracle.failing[].test]}' "$RS/score-$UNIT-$ATTEMPT.json"
}

case "${1:-}" in
  setup) shift; cmd_setup "$@";;
  stage) shift; cmd_stage "$@";;
  turn) shift; cmd_turn "$@";;
  gate) shift; cmd_gate "$@";;
  state) shift; cmd_state "$@";;
  unit) shift; cmd_unit "$@";;
  chain) shift; cmd_chain "$@";;
  score) shift; cmd_score "$@";;
  *) sed -n '2,12p' "$0"; exit 2;;
esac
