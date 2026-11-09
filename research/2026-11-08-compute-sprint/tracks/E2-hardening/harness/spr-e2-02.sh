#!/usr/bin/env bash
# SPR-E2-02 evidence-path attacks (E-F-01) and controls against one Praxis build.
# usage: spr-e2-02.sh LABEL PRAXIS_DLL > raw/spr-e2-02-LABEL.jsonl   (fixtures under $E2_FIXTURES/spr-e2-02-LABEL)
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); . "$HERE/lib.sh"
LABEL=$1; P=$2; RUN="spr-e2-02-$LABEL"; rm -rf "${E2_FIXTURES:?}/$RUN"; mkdir -p "$E2_FIXTURES/$RUN"
emit() { jq -cn --arg l "$LABEL" --arg c "$1" --arg a "$2" --arg x "$3" --argjson rc "$4" --arg o "$5" --arg n "${6:-}" '
  {build:$l, case:$c, attempt:$a, expected:$x, exit:$rc, codes:([$o | scan("PRX\\.[A-Z_]+\\.[A-Z_]+")] | unique),
   output_tail:($o[-400:]), note:$n}'; }
run() { OUT=$("$@" 2>&1); RC=$?; }
# fixture with a real tiny unittest run whose log is committed, item started
fixture() { local r; r=$(new_fixture "$P" "$1") || exit 97
  printf 'import unittest\nclass T(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(2 + 3, 5)\nif __name__ == "__main__":\n    unittest.main()\n' > "$r/test_add.py"
  mkdir -p "$r/logs"; ( cd "$r" && python3 -I test_add.py > logs/test-run.log 2>&1 )
  [ -n "${2:-}" ] && ( cd "$r" && eval "$2" )   # optional setup, before the item starts (avoids the durable-checkpoint guard)
  gitc "$r" add -A; gitc "$r" commit -qm "test + log"
  px "$P" "$r" work capture --title t --id "$1" --occurred-at "$(utc)" >/dev/null 2>&1
  px "$P" "$r" work backlog-transition --id "$1" --action ready --occurred-at "$(utc)" >/dev/null 2>&1
  px "$P" "$r" work start --id "$1" --occurred-at "$(utc)" >/dev/null 2>&1; echo "$r"; }
complete() { px "$P" "$1" work complete --id "$2" --occurred-at "$(utc)" --evidence implementation=README.md --evidence "tests=$3" --conclusion "all tests pass"; }
binding() { [ -f "$1/.ros/work/evidence-bindings.jsonl" ] && jq -c 'select(.type=="tests")' "$1/.ros/work/evidence-bindings.jsonl" | tail -1 || echo "none"; }

r=$(fixture E2-11); run complete "$r" E2-11 /etc/hostname; emit B1 "tests=/etc/hostname (E NX-1 / V2 case A)" "patched: refused OUTSIDE_REPOSITORY" "$RC" "$OUT"
r=$(fixture E2-12); run complete "$r" E2-12 ../../../../../../../../../../../../etc/hostname; emit B2 "tests=../(x12)etc/hostname" "patched: refused" "$RC" "$OUT"
r=$(fixture E2-13 'ln -s /etc/hostname t.log')
run complete "$r" E2-13 t.log; emit B3 "in-repo symlink t.log -> /etc/hostname" "patched: refused" "$RC" "$OUT"
r=$(fixture E2-14 'ln -s /etc d')
run complete "$r" E2-14 d/hostname; emit B4 "in-repo directory symlink d -> /etc, tests=d/hostname" "patched: refused" "$RC" "$OUT"
r=$(fixture E2-15); run complete "$r" E2-15 logs/test-run.log
emit P1 "tests=logs/test-run.log (real unittest output; logs/ is git-ignored by praxis init)" "accepted; binding digest/commit correct" "$RC" "$OUT" \
  "$(jq -cn --argjson b "$(binding "$r" | sed 's/^none$/null/')" --arg s "sha256:$(sha256sum "$r/logs/test-run.log" | cut -d' ' -f1)" --arg h "$(git -C "$r" rev-parse HEAD)" \
     '{binding:$b, sha256_matches:($b.sha256 == $s), commit_matches:($b.commit == $h)}')"
r=$(fixture E2-16 "jq '.workProtocol.allowExternalEvidence = true' ros.json > ros.tmp && mv ros.tmp ros.json")
run complete "$r" E2-16 /etc/hostname; emit P2 "workProtocol.allowExternalEvidence: true; tests=/etc/hostname" "accepted (explicit opt-out), binding insideRepository=false" "$RC" "$OUT" "$(binding "$r")"
r=$(fixture E2-18 'cp logs/test-run.log test-run.log'); run complete "$r" E2-18 test-run.log
emit P1b "tests=test-run.log (real unittest output, committed at HEAD)" "accepted; committedAtHead=true" "$RC" "$OUT" "$(binding "$r")"
r=$(fixture E2-17); run complete "$r" E2-17 logs/missing.log; emit P3 "tests=logs/missing.log (nonexistent, in repo)" "refused with the 3.25.0 message" "$RC" "$OUT"
