#!/usr/bin/env bash
# Stand-in for `claude -p` in the P3 harness smoke (no model). The agent environment is an allowlist, so the stand-in's
# settings (FAKE_VARIANT, FAKE_PLAN) are read from the execution's harness state ($HOME is $ST/agent/home), then
# P2's stand-in runs unchanged.
set -euo pipefail
[ -f "$HOME/../../smoke.env" ] && . "$HOME/../../smoke.env"
exec "$(cd "$(dirname "$0")" && pwd)/../../../P2/harness/smoke/fake-claude.sh" "$@"
