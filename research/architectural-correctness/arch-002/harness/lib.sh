#!/usr/bin/env bash
# ARCH-002 harness library (sourced by harness/*.sh). Adapted from ARCH-001 harness/lib.sh (see ../PROVENANCE.md):
# prefix ARCH002_, state in /home/user/arch002-runs, several fixtures, two models, sealed store per fixture,
# run ids ARCH-002-{CAL|PILOT|CONF|SMOKE}-<fixture>-T<n>-<model>-r<k>-<arm>[-suffix] (model: opus | sonnet).
# Every path is an ARCH002_* override.
set -euo pipefail

H="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"            # research/architectural-correctness/arch-002/harness
X="$(cd "$H/.." && pwd)"                                      # research/architectural-correctness/arch-002

FIXTURES="${ARCH002_FIXTURES:-$X/fixtures}"                   # <fixture>/{repo,pack,policy.json,fixture.json,tasks/T<n>}
SEALED_ROOT="${ARCH002_SEALED_DIR:-/home/user/arch002-sealed}" # <fixture>/{oracle,reference,task-private,seeded.json}
SEALED_ARCHIVE="${ARCH002_SEALED_ARCHIVE:-}"                  # optional: the encrypted sealed archive, hashed for integrity
RUNS="${ARCH002_RUNS:-/home/user/arch002-runs}"               # one directory per run id (outside every repository)
OBSERVATIONS="${ARCH002_OBSERVATIONS:-$X/observations}"       # git-ignored until every trial has ended
VERIFIER_DIST="${ARCH002_VERIFIER_DIST:-$X/verifier/dist}"
ARCHCHECK_SRC="${ARCH002_ARCHCHECK:-$VERIFIER_DIST/archcheck.dll}"
VERIFIER_SRC_DIR="${ARCH002_VERIFIER_SRC:-$X/verifier}"       # never shown to an agent (X4 pattern)
ORDO_SRC="${ARCH002_ORDO:-/home/user/.tools/ordo/ordo-linux-x64/ordo}"
DOTNET_ROOT_DIR="${ARCH002_DOTNET_ROOT:-/home/user/.tools/dotnet}"
REAL_DOTNET="$DOTNET_ROOT_DIR/dotnet"
NUGET_CACHE="${ARCH002_NUGET_PACKAGES:-${NUGET_PACKAGES:-/root/.nuget/packages}}"
CLAUDE_BIN="${ARCH002_CLAUDE:-/opt/node22/bin/claude}"
AGENT_CONFIG="${ARCH002_AGENT_CONFIG:-$H/agent-config.json}"
PRICE_TABLE="${ARCH002_PRICE_TABLE:-$H/pricing/anthropic.price-table.json}"
AGENT_CMD="${ARCH002_AGENT_CMD:-$H/launch-agent.sh}"          # the per-phase agent runner (smoke: smoke-agent.sh)
BUDGET_MINUTES="${ARCH002_BUDGET_MINUTES:-$(jq -r .budgetMinutes "$AGENT_CONFIG")}"
MAX_SUBMITS="${ARCH002_MAX_SUBMITS:-$(jq -r .maxSubmits "$AGENT_CONFIG")}"
FIXED_DATE="2026-01-01T00:00:00Z"                             # base commit date: identical base commit per task in every arm

ARMS="A B C D"
has_pack()     { [ "$1" != A ]; }
has_contract() { [ "$1" = C ] || [ "$1" = D ]; }
has_verifier() { [ "$1" = D ]; }

utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
tree_sha() { (cd "$1" && find . -type f -not -path '*/bin/*' -not -path '*/obj/*' | LC_ALL=C sort | xargs -r -d '\n' sha256sum | sha256sum | cut -d' ' -f1); }
any_sha() { if [ -d "$1" ]; then tree_sha "$1"; elif [ -f "$1" ]; then sha "$1"; else echo missing; fi; }

# Run-id grammar. Fixture ids are lower-case words joined by '-' and never contain "-T<digit>".
RUNID_RE='^ARCH-002-(CAL|PILOT|CONF|SMOKE)-([a-z0-9]+(-[a-z0-9]+)*)-T[0-9]+-(opus|sonnet)-r[0-9]+-[ABCD](-[A-Za-z0-9]+)*$'
_rid() { sed -nE 's/^ARCH-002-(CAL|PILOT|CONF|SMOKE)-([a-z0-9]+(-[a-z0-9]+)*)-(T[0-9]+)-(opus|sonnet)-r([0-9]+)-([ABCD])(-[A-Za-z0-9]+)*$/'"$2"'/p' <<<"$1"; }
label_of()   { case "$(_rid "$1" '\1')" in SMOKE) echo smoke;; PILOT) echo pilot;; CAL) echo calibration;; CONF) echo confirmatory;; *) echo unknown;; esac; }
fixture_of() { _rid "$1" '\2'; }
task_of()    { _rid "$1" '\4'; }
model_of()   { _rid "$1" '\5'; }               # opus | sonnet
rep_of()     { _rid "$1" '\6'; }
arm_of()     { _rid "$1" '\7'; }
model_id()   { jq -r --arg m "$1" '.models[$m] // empty' "$AGENT_CONFIG"; }   # opus -> claude-opus-5-5

# run_paths RUNID: ROOT (run root), REPO (agent workspace), TOOLS (workspace-external tools), BRIEFS, ST (harness state).
run_paths() {
  RUN_ID="$1"; ROOT="$RUNS/$RUN_ID"; REPO="$ROOT/repo"; TOOLS="$ROOT/tools"; BRIEFS="$ROOT/brief"; ST="$ROOT/state"
  PRISTINE="$ST/pristine"; LEDGER="$ST/submit-ledger.jsonl"
}

# fixture_paths FIXTURE: FIX (the fixture's public directory), SEALED (its sealed store), POLICY_SRC, FIXTURE_JSON.
fixture_paths() {
  FIXTURE="$1"; FIX="$FIXTURES/$FIXTURE"; SEALED="$SEALED_ROOT/$FIXTURE"
  POLICY_SRC="${ARCH002_POLICY:-$FIX/policy.json}"; FIXTURE_JSON="$FIX/fixture.json"
}

# fixture_field JQ_PATH DEFAULT: a fixture.json value (public fixture metadata read by the harness only).
fixture_field() { local v; v=$(jq -r "$1 // empty" "$FIXTURE_JSON" 2>/dev/null || true); echo "${v:-$2}"; }

# git with a fixed harness identity (agent commits use the repository's own user config).
hgit() { GIT_AUTHOR_NAME="arch002 harness" GIT_AUTHOR_EMAIL="harness@arch002.invalid" \
         GIT_COMMITTER_NAME="arch002 harness" GIT_COMMITTER_EMAIL="harness@arch002.invalid" git "$@"; }

# The environment every agent phase and the submit gate see (identical in every arm; PATH holds the arm's tools).
agent_path() { echo "$TOOLS/bin:$DOTNET_ROOT_DIR:$PATH"; }

# archcheck_cmd: the pinned verifier entry as an argv prefix (.dll and .py entries are wrapped).
archcheck_cmd() {
  case "$ARCHCHECK_SRC" in *.dll) echo "$REAL_DOTNET $ARCHCHECK_SRC";; *.py) echo "python3 -I $ARCHCHECK_SRC";; *) echo "$ARCHCHECK_SRC";; esac
}

# load_run_config: after run_paths, take fixtures/sealed/verifier/policy from the run's run.json unless the caller set
# the ARCH002_* variable explicitly (so scoring and review use what the trial was set up with).
load_run_config() {
  local rj="$ST/run.json" v
  [ -f "$rj" ] || return 0
  v=$(jq -r '.config.fixtures // empty' "$rj");  [ -z "${ARCH002_FIXTURES+x}" ] && [ -n "$v" ] && FIXTURES="$v"
  v=$(jq -r '.config.sealedRoot // empty' "$rj"); [ -z "${ARCH002_SEALED_DIR+x}" ] && [ -n "$v" ] && SEALED_ROOT="$v"
  v=$(jq -r '.config.archcheck // empty' "$rj"); [ -z "${ARCH002_ARCHCHECK+x}" ] && [ -n "$v" ] && ARCHCHECK_SRC="$v"
  fixture_paths "$(jq -r .fixture "$rj")"
  v=$(jq -r '.config.policy // empty' "$rj");    [ -z "${ARCH002_POLICY+x}" ] && [ -n "$v" ] && POLICY_SRC="$v"
  return 0
}
