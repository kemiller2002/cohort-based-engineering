#!/usr/bin/env bash
# ARCH-002 scoring, measurement half (adapted from ARCH-001 harness/score.sh; see ../PROVENANCE.md).
#   usage: score.sh RUNID [--assemble-only|--arch-only]
# Everything runs in RUN/state/score from PRISTINE harness-side inputs (sealed oracle and probes from
# ARCH002_SEALED_DIR/<fixture>, the pristine policy, contracts and baseline, the source verifier dist), never from the
# workspace.
# Commits scored, per phase k: S_k = the last submitted commit of phase k (or, with no submit, the phase-1
# transition commit / the phase-2 end HEAD), and F_k = the first submitted commit when its tree differs from S_k.
#   (a) hidden oracle: p1 InitialOracle@S1 (and @F1); p2 FollowupOracle@S2 and InitialOracle@S2 (regression),
#       FollowupOracle@F2; each in a fresh Oracle.fsproj referencing every src/**/*.fsproj of that commit, TRX.
#   (b) archcheck full policy + the sealed task probes (always passed; ARCH-001 A4) (+ contract for C/D) + the
#       scoring baseline (state/pristine/baseline-scoring.json: the base commit with the same policy and probes) at S1
#       and S2, so every finding carries `preexisting`; new = not preexisting, fixed = baseline keys left unmatched
#       (INTERFACES §3). C/D also S2 with the initial contract (decision preservation under ARC-TRC-01).
#   visible tests at S1 and S2 (TRX) for "pre-existing visible tests broken".
# Then score.py assembles the observation; non-smoke observations are copied to $ARCH002_OBSERVATIONS/RUNID.json.
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: score.sh RUNID [--assemble-only|--arch-only]}"
ASSEMBLE_ONLY=false; [ "${2:-}" = --assemble-only ] && ASSEMBLE_ONLY=true
# Amendment A4: --arch-only re-runs only the verifier steps at the commits already recorded in commits.json.
ARCH_ONLY=false; [ "${2:-}" = --arch-only ] && ARCH_ONLY=true
RJ="$ST/run.json"; [ -f "$RJ" ] || { echo "no run.json for $RUN_ID" >&2; exit 2; }
TASK=$(jq -r .task "$RJ"); ARM=$(jq -r .arm "$RJ"); LABEL=$(jq -r .label "$RJ")
load_run_config
SC="$ST/score"
export DOTNET_ROOT="$DOTNET_ROOT_DIR" NUGET_PACKAGES="$NUGET_CACHE" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 \
       MSBUILDDISABLENODEREUSE=1 DOTNET_CLI_USE_MSBUILD_SERVER=0 UseSharedCompilation=false
export PATH="$DOTNET_ROOT_DIR:$PATH"
ORACLE_DIR="$SEALED/oracle/$TASK"; MANIFEST="$ORACLE_DIR/oracle.json"
HOST_PROJECT=$(fixture_field .oracleHostProject src/Lending.Host/Lending.Host.fsproj)
# A fixture may name its own oracle-template placeholder for the exported tree (fixture.json .oraclePlaceholder,
# e.g. SUMMA_REPO); it is substituted like __SRC_ROOT__ in Oracle.fsproj and in an optional sealed NuGet.config.
ORACLE_PLACEHOLDER=$(fixture_field .oraclePlaceholder __SRC_ROOT__)

submitted() {  # PHASE first|last -> gitHead
  [ -f "$LEDGER" ] || return 0
  local sel; [ "$2" = first ] && sel='[0]' || sel='[-1]'
  jq -rs --argjson p "$1" "[.[] | select(.phase == \$p and (.verdict == \"PASS\" or .verdict == \"FAIL\")) | .gitHead]$sel // empty" "$LEDGER"
}
export_tree() {  # COMMIT DIR [--git]: the commit's tree, from the workspace's object store
  mkdir -p "$2"
  if [ "${3:-}" = --git ]; then git clone -q --no-hardlinks "$REPO" "$2" && git -C "$2" checkout -q --detach "$1"
  else git -C "$REPO" archive "$1" | tar -x -C "$2"; fi
}
oracle_files() {  # initial|followup -> file names (manifest .<kind>.files, else the INTERFACES §6 default)
  local def; [ "$1" = initial ] && def=InitialOracleTests.fs || def=FollowupOracleTests.fs
  if [ -f "$MANIFEST" ] && jq -e ".$1.files" "$MANIFEST" >/dev/null 2>&1; then jq -r ".$1.files[]" "$MANIFEST"; else echo "$def"; fi
}
oracle() {  # LABEL COMMIT KIND
  local d="$SC/oracle-$1" c="$2" kind="$3" comp="" refs="" f p
  rm -rf "$d"; mkdir -p "$d/oracle"; export_tree "$c" "$d/src"
  while read -r f; do
    [ -n "$f" ] || continue
    if [ -f "$ORACLE_DIR/$f" ]; then cp "$ORACLE_DIR/$f" "$d/oracle/$(basename "$f")"; comp+="    <Compile Include=\"$(basename "$f")\" />"$'\n'; fi
  done < <(oracle_files "$kind")
  if [ -f "$SEALED/oracle/Oracle.fsproj" ] && grep -qE "LENDING_HOST_PROJECT_PATH|__SRC_ROOT__|$ORACLE_PLACEHOLDER" "$SEALED/oracle/Oracle.fsproj"; then
    # The fixture's sealed template: shared helpers (Compile items other than OracleTests.fs, e.g. OracleKit.fs) are
    # copied from the sealed oracle root; the task's oracle files are concatenated into OracleTests.fs in manifest
    # order. Placeholders: LENDING_HOST_PROJECT_PATH (ARCH-001 form) = <tree>/<fixture.json .oracleHostProject>;
    # __SRC_ROOT__ = the exported tree of the scored commit.
    rm -f "$d/oracle"/*.fs
    for f in $(grep -o 'Compile Include="[^"]*"' "$SEALED/oracle/Oracle.fsproj" | cut -d'"' -f2); do
      [ "$f" = OracleTests.fs ] || cp "$SEALED/oracle/$f" "$d/oracle/$f"
    done
    ( while read -r f; do [ -n "$f" ] && [ -f "$ORACLE_DIR/$f" ] && cat "$ORACLE_DIR/$f" && echo; done < <(oracle_files "$kind") ) > "$d/oracle/OracleTests.fs"
    sed -e "s#LENDING_HOST_PROJECT_PATH#$d/src/$HOST_PROJECT#" -e "s#__SRC_ROOT__#$d/src#g" -e "s#$ORACLE_PLACEHOLDER#$d/src#g" "$SEALED/oracle/Oracle.fsproj" > "$d/oracle/Oracle.fsproj"
    [ -f "$SEALED/oracle/NuGet.config" ] && sed -e "s#__SRC_ROOT__#$d/src#g" -e "s#$ORACLE_PLACEHOLDER#$d/src#g" "$SEALED/oracle/NuGet.config" > "$d/oracle/NuGet.config"
    echo sealed-template > "$d/template"
  else
    while read -r p; do refs+="    <ProjectReference Include=\"$d/src/$p\" />"$'\n'; done < <(cd "$d/src" && find src -name '*.fsproj' | LC_ALL=C sort)
    python3 -I -c 'import sys; t=open(sys.argv[1]).read(); print(t.replace("__COMPILE__\n", sys.argv[2]).replace("__REFERENCES__\n", sys.argv[3]), end="")' \
      "$H/oracle-template/Oracle.fsproj" "$comp" "$refs" > "$d/oracle/Oracle.fsproj"
    echo harness-template > "$d/template"
  fi
  echo "$c" > "$d/commit"; echo "$kind" > "$d/kind"
  [ -n "$comp" ] || { echo "no oracle files for $TASK/$kind under $ORACLE_DIR" > "$d/oracle-output.txt"; echo missing > "$d/exit"; return 0; }
  set +e; ( cd "$d/oracle" && "$REAL_DOTNET" test -nologo --logger "trx;LogFileName=oracle.trx" --results-directory "$d/results" > "$d/oracle-output.txt" 2>&1 ); echo $? > "$d/exit"; set -e
  rm -rf "$d/src" "$d/oracle/bin" "$d/oracle/obj"   # keep outcomes, not the agent's tree copy or build output
}
visible() {  # LABEL COMMIT
  local d="$SC/visible-$1"; rm -rf "$d"; export_tree "$2" "$d/src"; echo "$2" > "$d/commit"
  set +e; ( cd "$d/src" && "$REAL_DOTNET" test -nologo --logger "trx;LogFileName=visible.trx" --results-directory "$d/results" > "$d/output.txt" 2>&1 ); echo $? > "$d/exit"; set -e
  rm -rf "$d/src"
}
archcheck() {  # LABEL COMMIT [CONTRACT_NAME]
  local d="$SC/arch-$1" c="$2" cn="${3:-}" AC extra=()
  rm -rf "$d"; mkdir -p "$d"; echo "$c" > "$d/commit"
  [ -e "$ARCHCHECK_SRC" ] && [ -f "$PRISTINE/policy.json" ] && [ -f "$PRISTINE/baseline-scoring.json" ] \
    || { echo "archcheck, policy or scoring baseline missing" > "$d/output.txt"; echo missing > "$d/exit"; return 0; }
  export_tree "$c" "$d/tree" --git
  AC=$(archcheck_cmd)
  [ -n "$cn" ] && [ -f "$PRISTINE/$cn" ] && extra+=(--contract "$PRISTINE/$cn")
  # Options are pinned (ARCH-001 A4: no `--help | grep` feature detection). Probes are passed whenever the sealed
  # store has them; the baseline is always passed.
  if [ -f "$ORACLE_DIR/probes.json" ]; then extra+=(--probes "$ORACLE_DIR/probes.json"); echo true > "$d/probes"; else echo false > "$d/probes"; fi
  set +e; ( cd "$d/tree" && $AC verify --repo "$d/tree" --policy "$PRISTINE/policy.json" "${extra[@]}" --baseline "$PRISTINE/baseline-scoring.json" \
              --require-clean --json --out "$d/report.json" > "$d/output.txt" 2>&1 ); echo $? > "$d/exit"; set -e
  rm -rf "$d/tree"
}

if $ARCH_ONLY; then
  S1=$(jq -r '.S1 // empty' "$SC/commits.json"); S2=$(jq -r '.S2 // empty' "$SC/commits.json")
  C1=""; C2=""; has_contract "$ARM" && { C1="$TASK.contract.json"; C2="$TASK-followup.contract.json"; }
  archcheck p1 "$S1" "$C1"
  if [ -n "$S2" ]; then archcheck p2 "$S2" "$C2"; has_contract "$ARM" && archcheck p2-initial-contract "$S2" "$C1"; fi
elif ! $ASSEMBLE_ONLY; then
  rm -rf "${SC:?}"; mkdir -p "$SC"
  S1=$(submitted 1 last); [ -n "$S1" ] || S1=$(jq -r '.phase1Commit // .phases["1"].endHead' "$RJ")
  S2=$(submitted 2 last); [ -n "$S2" ] || S2=$(jq -r '.phases["2"].endHead // empty' "$RJ")
  F1=$(submitted 1 first); F2=$(submitted 2 first)
  same_tree() { [ "$(git -C "$REPO" rev-parse "$1^{tree}")" = "$(git -C "$REPO" rev-parse "$2^{tree}")" ]; }
  jq -n --arg s1 "$S1" --arg s2 "$S2" --arg f1 "$F1" --arg f2 "$F2" 'def nn: if . == "" then null else . end; {S1:($s1|nn), S2:($s2|nn), F1:($f1|nn), F2:($f2|nn)}' > "$SC/commits.json"
  oracle p1 "$S1" initial
  [ -n "$F1" ] && ! same_tree "$F1" "$S1" && oracle p1-first "$F1" initial
  visible p1 "$S1"
  C1=""; C2=""; has_contract "$ARM" && { C1="$TASK.contract.json"; C2="$TASK-followup.contract.json"; }
  archcheck p1 "$S1" "$C1"
  if [ -n "$S2" ]; then
    oracle p2 "$S2" followup
    oracle p2-regression "$S2" initial
    [ -n "$F2" ] && ! same_tree "$F2" "$S2" && oracle p2-first "$F2" followup
    visible p2 "$S2"
    archcheck p2 "$S2" "$C2"
    has_contract "$ARM" && archcheck p2-initial-contract "$S2" "$C1"
  fi
fi
mkdir -p "$SC"
ARCH002_SEALED_DIR="$SEALED" python3 -I "$H/score.py" "$RJ" "$SC" > "$SC/observation.json.tmp" && mv "$SC/observation.json.tmp" "$SC/observation.json"
if [ "$LABEL" != smoke ]; then mkdir -p "$OBSERVATIONS"; cp "$SC/observation.json" "$OBSERVATIONS/$RUN_ID.json"; echo "$OBSERVATIONS/$RUN_ID.json"
else echo "$SC/observation.json"; fi
