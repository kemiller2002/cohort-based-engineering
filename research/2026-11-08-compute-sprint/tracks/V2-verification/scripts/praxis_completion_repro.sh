#!/usr/bin/env bash
# V2 claims 10 (E-F-01) and 12 (E-F-03): independent reproduction against a locally
# built Praxis CLI on a fresh fixture repository. Non-destructive: everything happens
# under WORK (a scratch directory), no remote, no network.
#
# usage: praxis_completion_repro.sh PRAXIS_DLL WORK OUT_JSONL
set -uo pipefail
DLL=$1; WORK=$2; OUT=$3
case "$WORK" in /home/user/sprint-scratch/*) ;; *) echo "WORK must be under /home/user/sprint-scratch" >&2; exit 2;; esac
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1
px() { dotnet "$DLL" "$@"; }
TS() { date -u +%Y-%m-%dT%H:%M:%SZ; }
: > "$OUT"
rec() { # case step exit detail
  python3 -I -c 'import json,sys; print(json.dumps({"case":sys.argv[1],"step":sys.argv[2],"exit":int(sys.argv[3]),"detail":sys.argv[4][-600:]}))' "$@" >> "$OUT"
}
fresh() { # dir  -- runs in the CURRENT shell (no command substitution) so cd persists
  rm -rf "$1"; mkdir -p "$1"; cd "$1" || exit 9
  git init -q -b main . && git config user.email v2@example.invalid && git config user.name V2
  # Safety: refuse to run unless the fixture is its own repository root (never a parent repo).
  [ "$(git rev-parse --show-toplevel)" = "$(pwd -P)" ] || { echo "fixture is not its own repo" >&2; exit 9; }
  [ "$(cd "$(git rev-parse --git-common-dir)" && pwd -P)" = "$(pwd -P)/.git" ] || { echo "foreign git dir" >&2; exit 9; }
  echo "# fixture" > README.md && git add README.md && git commit -qm init
  px init >/dev/null 2>&1; INIT_EXIT=$?
  git add -A && git commit -qm "praxis init" >/dev/null 2>&1
}
ready_start() { # id
  px work backlog-transition --id "$1" --action ready --occurred-at "$(TS)" >/dev/null 2>&1
  px work start --id "$1" --occurred-at "$(TS)" 2>&1
}

# ---- Case A (claim 10): plain completion with an out-of-repo file as tests evidence
A="$WORK/case-a"; fresh "$A"; rec A init "$INIT_EXIT" "praxis init in $(pwd)"
o=$(px work capture --title "V2 probe A" --id WI-V2A --occurred-at "$(TS)" 2>&1); rec A capture $? "$o"
o=$(ready_start WI-V2A); rec A start $? "$o"
o=$(px work complete --id WI-V2A --occurred-at "$(TS)" --evidence implementation=README.md \
     --evidence tests=/etc/hostname --conclusion "all tests pass" 2>&1); rec A complete $? "$o"
o=$(px work show WI-V2A 2>&1; grep -rl "WI-V2A" .ros/work 2>/dev/null | head -3); rec A item-files $? "$o"
o=$(px work validate --json 2>&1); rec A validate $? "$o"
o=$(px verify 2>&1); rec A verify $? "$o"
o=$(grep -h -o '"WI-V2A"[^}]*' .ros/events/*.jsonl 2>/dev/null | tail -2; grep -rh '/etc/hostname' .ros 2>/dev/null | head -1); rec A evidence-recorded 0 "$o"
o=$(px status --json 2>&1 | python3 -I -c 'import sys;t=sys.stdin.read();i=t.find("WI-V2A");print(t[max(0,i-200):i+400])'); rec A status 0 "$o"

# ---- Case A2: control - nonexistent evidence path must be refused
o=$(px work capture --title "V2 probe A2" --id WI-V2A2 --occurred-at "$(TS)" 2>&1)
o=$(ready_start WI-V2A2)
o=$(px work complete --id WI-V2A2 --occurred-at "$(TS)" --evidence implementation=README.md \
     --evidence tests=/nonexistent/v2-file --conclusion x 2>&1); rec A2 complete-missing-path $? "$o"

# ---- Case B (claim 12): claim record, plain completion refused, delete claim, retry
B="$WORK/case-b"; fresh "$B"; rec B init "$INIT_EXIT" "praxis init in $(pwd)"
o=$(px work capture --title "V2 probe B" --id WI-V2B --occurred-at "$(TS)" 2>&1); rec B capture $? "$o"
o=$(ready_start WI-V2B); rec B start $? "$o"
o=$(px work claim --id WI-V2B --claimant v2 2>&1); rec B claim $? "$o"
CD="$(git rev-parse --git-common-dir)/praxis/claims"
o=$(ls -la "$CD" 2>&1); rec B claim-store 0 "$o"
o=$(px work complete --id WI-V2B --occurred-at "$(TS)" --evidence implementation=README.md \
     --evidence tests=/etc/hostname --conclusion "all tests pass" 2>&1); rec B complete-with-claim $? "$o"
rm -rf "$CD/WI-V2B"; rec B delete-claim $? "rm -rf $CD/WI-V2B"
o=$(px work complete --id WI-V2B --occurred-at "$(TS)" --evidence implementation=README.md \
     --evidence tests=/etc/hostname --conclusion "all tests pass" 2>&1); rec B complete-after-delete $? "$o"
o=$(px work validate --json 2>&1); rec B validate $? "$o"
cat "$OUT"
