#!/usr/bin/env bash
# NX-1 on a `praxis init`-installed repository (default scaffold ros.json): fabricated evidence completes an item.
# usage: nx1-installed.sh PRAXIS WORKDIR
set -euo pipefail; P="$1"; W="$2"; rm -rf "$W"; mkdir -p "$W"; cd "$W"
git init -q -b main; "$P" init >/dev/null 2>&1; git -c commit.gpgsign=false -c user.email=e@x.invalid -c user.name=e add -A
git -c commit.gpgsign=false -c user.email=e@x.invalid -c user.name=e commit -qm init
"$P" work capture --title "Implement thing" --id WI-1 --occurred-at 2026-11-08T19:00:00Z >/dev/null 2>&1
"$P" work backlog-transition --id WI-1 --action ready --occurred-at 2026-11-08T19:00:30Z >/dev/null
"$P" work start --id WI-1 --occurred-at 2026-11-08T19:01:00Z >/dev/null
echo "--- complete without evidence"; "$P" work complete --id WI-1 --occurred-at 2026-11-08T19:02:00Z 2>&1 | tail -1 || true
echo "--- complete citing README.md as implementation and /etc/hostname as tests"
set +e; "$P" work complete --id WI-1 --occurred-at 2026-11-08T19:02:00Z --evidence implementation=README.md --evidence tests=/etc/hostname --conclusion "all tests pass" > "$W.out.json" 2>&1; echo "exit=$?"; set -e
jq -c '.workItems[] | select(.id=="WI-1") | {state, evidence, conclusion}' "$W.out.json"
echo "verify-exit=$("$P" verify >/dev/null 2>&1; echo $?)"; "$P" work validate | jq -c '{valid, findings: (.findings|length)}'
