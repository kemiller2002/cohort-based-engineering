#!/usr/bin/env bash
# Shared guards for E2 harness scripts. Every Praxis invocation goes through px(), which
# refuses to run unless the target directory is a fixture under $E2_FIXTURES with its OWN .git
# (never a parent or shared repository). No `cd` leaks: px runs in its own subshell and
# re-checks the guard after cd, inside that same subshell.
E2_SCRATCH=/home/user/sprint-scratch/E2
E2_FIXTURES=$E2_SCRATCH/fixtures
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_ROLL_FORWARD=Major
export PRAXIS_ACTOR_KIND=agent PRAXIS_ACTOR=e2/agent PRAXIS_TELEMETRY_PROVIDER=test PRAXIS_TELEMETRY_RUNTIME=test
export PRAXIS_DOKIMOS_EXECUTABLE=$E2_SCRATCH/bin/dokimos
unset PRAXIS_VERIFIER_SOCKET PRAXIS_COMPLETION_AUTHORITY PRAXIS_ORDO_CONTRACT GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR

die() { echo "GUARD: $*" >&2; exit 97; }

# assert_fixture DIR : DIR is under $E2_FIXTURES, is its own work-tree root, and owns DIR/.git
assert_fixture() {
  local d; d=$(cd "$1" 2>/dev/null && pwd -P) || die "no such dir $1"
  case "$d/" in "$E2_FIXTURES"/*) ;; *) die "$d is not under $E2_FIXTURES";; esac
  [ -d "$d/.git" ] || die "$d has no own .git directory"
  [ "$(git -C "$d" rev-parse --show-toplevel)" = "$d" ] || die "$d is not its own repository root"
  [ "$(cd "$(git -C "$d" rev-parse --path-format=absolute --git-common-dir)" && pwd -P)" = "$d/.git" ] || die "$d uses a foreign git dir"
}

# px PRAXIS_DLL REPO args... : run praxis in REPO after the guard (subshell; cwd never leaks)
px() {
  local dll="$1" repo="$2"; shift 2
  assert_fixture "$repo"
  ( cd "$repo" || exit 98; assert_fixture "$(pwd -P)"; exec dotnet "$dll" "$@" )
}

gitc() { assert_fixture "$1"; git -C "$1" -c commit.gpgsign=false -c user.email=e2@example.invalid -c user.name=e2 "${@:2}"; }
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }

# new_fixture NAME : fresh repo under $E2_FIXTURES/$RUN/NAME with `praxis init` committed
new_fixture() {
  local dll="$1" r="$E2_FIXTURES/${RUN:?}/$2"
  case "$r" in "$E2_FIXTURES"/*) ;; *) die "bad fixture path";; esac
  rm -rf "$r"; mkdir -p "$r"; git init -q -b main "$r"
  echo "# fixture $2" > "$r/README.md"; gitc "$r" add -A; gitc "$r" commit -qm init
  px "$dll" "$r" init >/dev/null 2>&1 || die "praxis init failed in $r"
  gitc "$r" add -A; gitc "$r" commit -qm "praxis init" >/dev/null
  echo "$r"
}
