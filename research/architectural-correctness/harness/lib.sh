#!/usr/bin/env bash
# ARCH-001 harness library (sourced by harness/*.sh). Adapted from REL-001 run-03 harness/lib.sh (see PROVENANCE.md):
# prefix ARCH001_, state outside every repository, no Praxis/Echelon parts, run ids ARCH-001-{PILOT|CONF|SMOKE}-T<n>-r<k>-<arm>.
# Every path is an ARCH001_* override so the harness works before and after Workers B (fixtures) and C (verifier) land.
set -euo pipefail

H="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"            # research/architectural-correctness/harness
X="$(cd "$H/.." && pwd)"                                      # research/architectural-correctness

FIX="${ARCH001_FIXTURES:-$X/fixtures}"                        # INTERFACES §6 (repo, pack, policy, tasks)
SEALED="${ARCH001_SEALED_DIR:-/home/user/arch001-sealed}"     # oracle/, reference/ (plaintext only at scoring time)
SEALED_ARCHIVE="${ARCH001_SEALED_ARCHIVE:-}"                  # optional: the sealed archive file hashed for integrity
RUNS="${ARCH001_RUNS:-/home/user/arch001-runs}"               # one directory per run id
OBSERVATIONS="${ARCH001_OBSERVATIONS:-$X/observations}"
POLICY_SRC="${ARCH001_POLICY:-$FIX/policy/lending.policy.json}"
VERIFIER_DIST="${ARCH001_VERIFIER_DIST:-$X/verifier/dist}"
ARCHCHECK_SRC="${ARCH001_ARCHCHECK:-$VERIFIER_DIST/archcheck}"
VERIFIER_SRC_DIR="${ARCH001_VERIFIER_SRC:-$X/verifier}"       # never shown to an agent (X4 pattern)
ORDO_SRC="${ARCH001_ORDO:-/home/user/.tools/ordo/ordo-linux-x64/ordo}"
DOTNET_ROOT_DIR="${ARCH001_DOTNET_ROOT:-/home/user/.tools/dotnet}"
REAL_DOTNET="$DOTNET_ROOT_DIR/dotnet"
NUGET_CACHE="${ARCH001_NUGET_PACKAGES:-${NUGET_PACKAGES:-/root/.nuget/packages}}"
CLAUDE_BIN="${ARCH001_CLAUDE:-/opt/node22/bin/claude}"
AGENT_CONFIG="${ARCH001_AGENT_CONFIG:-$H/agent-config.json}"
PRICE_TABLE="${ARCH001_PRICE_TABLE:-$H/pricing/anthropic.price-table.json}"
DOCTRINE="${ARCH001_DOCTRINE:-$FIX/pack/FOUR-TIER-ARCHITECTURE.md}"
AGENT_CMD="${ARCH001_AGENT_CMD:-$H/launch-agent.sh}"          # the per-phase agent runner (smoke: smoke-agent.sh)
MODEL="${ARCH001_MODEL:-$(jq -r .model "$AGENT_CONFIG")}"
BUDGET_MINUTES="${ARCH001_BUDGET_MINUTES:-$(jq -r .budgetMinutes "$AGENT_CONFIG")}"
MAX_SUBMITS="${ARCH001_MAX_SUBMITS:-$(jq -r .maxSubmits "$AGENT_CONFIG")}"
FIXED_DATE="2026-01-01T00:00:00Z"                             # base commit date: identical base commit per task in every arm

ARMS="A B C D"
has_pack()     { [ "$1" != A ]; }
has_contract() { [ "$1" = C ] || [ "$1" = D ]; }
has_verifier() { [ "$1" = D ]; }

utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
tree_sha() { (cd "$1" && find . -type f | LC_ALL=C sort | xargs -r -d '\n' sha256sum | sha256sum | cut -d' ' -f1); }
any_sha() { if [ -d "$1" ]; then tree_sha "$1"; elif [ -f "$1" ]; then sha "$1"; else echo missing; fi; }

RUNID_RE='^ARCH-001-(PILOT|CONF|SMOKE)-T[0-9]+-r[0-9]+-[ABCD](-[A-Za-z0-9]+)*$'
label_of() { case "$1" in ARCH-001-SMOKE-*) echo smoke;; ARCH-001-PILOT-*) echo pilot;; *) echo confirmatory;; esac; }
task_of() { sed -nE 's/^ARCH-001-[A-Z]+-(T[0-9]+)-r[0-9]+-[ABCD].*$/\1/p' <<<"$1"; }
rep_of() { sed -nE 's/^ARCH-001-[A-Z]+-T[0-9]+-r([0-9]+)-[ABCD].*$/\1/p' <<<"$1"; }
arm_of() { sed -nE 's/^ARCH-001-[A-Z]+-T[0-9]+-r[0-9]+-([ABCD]).*$/\1/p' <<<"$1"; }

# run_paths RUNID: ROOT (run root), REPO (agent workspace), TOOLS (workspace-external tools), BRIEFS, ST (harness state).
run_paths() {
  RUN_ID="$1"; ROOT="$RUNS/$RUN_ID"; REPO="$ROOT/repo"; TOOLS="$ROOT/tools"; BRIEFS="$ROOT/brief"; ST="$ROOT/state"
  PRISTINE="$ST/pristine"; LEDGER="$ST/submit-ledger.jsonl"
}

# git with a fixed harness identity (agent commits use the repository's own user config).
hgit() { GIT_AUTHOR_NAME="arch001 harness" GIT_AUTHOR_EMAIL="harness@arch001.invalid" \
         GIT_COMMITTER_NAME="arch001 harness" GIT_COMMITTER_EMAIL="harness@arch001.invalid" git "$@"; }

# The single task-metadata reader: task.json field or a default.
task_field() { jq -r "$2 // empty" "$FIX/tasks/$1/task.json" 2>/dev/null || true; }

# The environment every agent phase and the submit gate see (identical in every arm; PATH holds the arm's tools).
agent_path() { echo "$TOOLS/bin:$DOTNET_ROOT_DIR:$PATH"; }

# load_run_config: after run_paths, take fixtures/sealed/verifier/policy/doctrine from the run's run.json unless the
# caller set the ARCH001_* variable explicitly (so scoring and review use what the trial was set up with).
load_run_config() {
  local rj="$ST/run.json" v
  [ -f "$rj" ] || return 0
  v=$(jq -r '.config.fixtures // empty' "$rj");  [ -z "${ARCH001_FIXTURES+x}" ] && [ -n "$v" ] && FIX="$v"
  v=$(jq -r '.config.sealed // empty' "$rj");    [ -z "${ARCH001_SEALED_DIR+x}" ] && [ -n "$v" ] && SEALED="$v"
  v=$(jq -r '.config.archcheck // empty' "$rj"); [ -z "${ARCH001_ARCHCHECK+x}" ] && [ -n "$v" ] && ARCHCHECK_SRC="$v"
  v=$(jq -r '.config.policy // empty' "$rj");    [ -z "${ARCH001_POLICY+x}" ] && [ -n "$v" ] && POLICY_SRC="$v"
  v=$(jq -r '.config.doctrine // empty' "$rj");  [ -z "${ARCH001_DOCTRINE+x}" ] && [ -n "$v" ] && DOCTRINE="$v"
  return 0
}
