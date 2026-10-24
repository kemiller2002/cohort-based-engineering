#!/usr/bin/env bash
# ARCH-002 completion gate (adapted from ARCH-001 harness/submit.sh; see ../PROVENANCE.md). Copied by setup.sh to
# RUN/tools/lib/submit.sh; the agent runs it as `submit`.
#   usage: submit.sh RUN_ROOT            (the tools/bin/submit wrapper passes RUN_ROOT)
# Identical behaviour in every arm apart from the arm's extra checks:
#   all arms : committed clean tree; `dotnet build` and the visible tests on a fresh clone of HEAD
#   C, D     : every contract in docs/contracts/ is byte-identical to the harness's pristine copy, and
#              `ordo ecir check` gives the same verdict as on the pristine copy (a refused contract stays refused)
#   D        : `archcheck verify` with the PRISTINE policy, the phase's PRISTINE contract and the PRISTINE gate baseline
#              (state/pristine/baseline-gate.json, the base commit's report) exits 0: no NEW DET violation of
#              severity >= 2. Pre-existing violations never fail the gate (INTERFACES §3). Options are pinned (no
#              `--help | grep` feature detection; ARCH-001 A4): --require-clean is always passed. When archcheck cannot
#              evaluate (exit 2), its own error text is printed verbatim (ARCH-001 A1).
# Appends {attempt, phase, gitHead, treeHash, checks, verdict, at} to the harness-side ledger (RUN/state). At most
# maxSubmits PASS/FAIL attempts per phase; further calls are refused (recorded as REFUSED, not counted).
set -uo pipefail
ROOT="${1:?usage: submit.sh RUN_ROOT}"
CFG="$ROOT/state/submit-config.json"
j() { jq -r "$1" "$CFG"; }
REPO=$(j .repo); ARM=$(j .arm); TASK=$(j .task); LEDGER=$(j .ledger); ST=$(j .state); MAX=$(j .maxSubmits)
PHASE=$(cat "$ST/current-phase" 2>/dev/null || echo 0)
export DOTNET_ROOT="$(j .dotnetRoot)" NUGET_PACKAGES="$(j .nugetPackages)" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 \
       MSBUILDDISABLENODEREUSE=1 DOTNET_CLI_USE_MSBUILD_SERVER=0 UseSharedCompilation=false
export PATH="$ROOT/tools/bin:$DOTNET_ROOT:$PATH"
utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
touch "$LEDGER"
USED=$(jq -s --argjson p "$PHASE" '[.[] | select(.phase == $p and (.verdict == "PASS" or .verdict == "FAIL"))] | length' "$LEDGER")
if [ "$USED" -ge "$MAX" ]; then
  echo "submit: REFUSED - all $MAX submits for this task have been used; stop now and write your final message."
  jq -cn --argjson p "$PHASE" --arg at "$(utc)" --arg h "$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" \
    '{schema:"arch002.submit/1", phase:$p, attempt:null, gitHead:$h, verdict:"REFUSED", reason:"limit", at:$at}' >> "$LEDGER"
  exit 3
fi
N=$((USED + 1)); W="$ST/submit/p$PHASE-a$N"; rm -rf "$W"; mkdir -p "$W"
START=$(date +%s%3N)
HEAD=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo ""); TREE=$(git -C "$REPO" rev-parse "HEAD^{tree}" 2>/dev/null || echo "")
REASONS=(); CHECKS='{}'
check() { CHECKS=$(jq -c --arg k "$1" --argjson v "$2" '. + {($k): $v}' <<<"$CHECKS"); }
fail() { REASONS+=("$1"); }
tailf() { tail -n "${2:-40}" "$1" | sed 's/^/    /'; }

DIRTY=$(git -C "$REPO" status --porcelain 2>/dev/null | head -20)
if [ -z "$HEAD" ]; then check clean '{"pass":false}'; fail "no commit in the repository"
elif [ -n "$DIRTY" ]; then check clean '{"pass":false}'; fail "working tree is not clean (commit or remove these):"$'\n'"$(sed 's/^/    /' <<<"$DIRTY")"
else check clean '{"pass":true}'; fi

if [ ${#REASONS[@]} -eq 0 ]; then
  T="$W/tree"
  git clone -q --no-hardlinks "$REPO" "$T" 2>"$W/clone.err" && git -C "$T" checkout -q --detach "$HEAD" 2>>"$W/clone.err"
  ( cd "$T" && dotnet build -nologo > "$W/build.txt" 2>&1 ); rc=$?
  check build "{\"pass\":$([ $rc -eq 0 ] && echo true || echo false),\"exit\":$rc}"
  if [ $rc -ne 0 ]; then fail "dotnet build failed:"$'\n'"$(grep -E ' error ' "$W/build.txt" | sort -u | head -20 | sed 's/^/    /')"
  else
    ( cd "$T" && dotnet test --no-build -nologo --logger "trx;LogFileName=visible.trx" --results-directory "$W/results" > "$W/test.txt" 2>&1 ); rc=$?
    check tests "{\"pass\":$([ $rc -eq 0 ] && echo true || echo false),\"exit\":$rc}"
    [ $rc -eq 0 ] || fail "visible tests failed:"$'\n'"$(grep -E 'Failed |error|Total tests|Passed!|Failed!' "$W/test.txt" | head -30 | sed 's/^/    /')"
  fi
  if [ "$ARM" = C ] || [ "$ARM" = D ]; then
    OK=true; DETAIL='[]'
    for P in "$ST"/pristine/*.contract.json; do
      NAME=$(basename "$P"); [ "$PHASE" = 1 ] && [[ "$NAME" == *-followup.* ]] && continue
      F="$T/docs/contracts/$NAME"; WANT=$(jq -r .exit "$ST/pristine/ordo-${NAME%.contract.json}.json")
      if [ ! -f "$F" ]; then OK=false; fail "docs/contracts/$NAME is missing"; got=null; same=false
      else
        same=$([ "$(sha256sum "$F" | cut -d' ' -f1)" = "$(sha256sum "$P" | cut -d' ' -f1)" ] && echo true || echo false)
        $same || { OK=false; fail "docs/contracts/$NAME differs from the contract you were given (do not edit it)"; }
        ( cd "$T" && ordo ecir check --blueprint "docs/contracts/$NAME" > "$W/ordo-$NAME.txt" 2>&1 ); got=$?
        [ "$got" = "$WANT" ] || { OK=false; fail "ordo ecir check on docs/contracts/$NAME: exit $got, expected $WANT"; }
      fi
      DETAIL=$(jq -c --arg n "$NAME" --argjson s "$same" --argjson g "${got:-null}" --argjson w "$WANT" '. + [{contract:$n, unchanged:$s, exit:$g, expectedExit:$w}]' <<<"$DETAIL")
    done
    check ordo "{\"pass\":$OK,\"contracts\":$DETAIL}"
  fi
  if [ "$ARM" = D ]; then
    CN="$TASK.contract.json"; [ "$PHASE" = 2 ] && CN="$TASK-followup.contract.json"
    ( cd "$T" && archcheck verify --repo "$T" --policy "$ST/pristine/policy.json" --contract "$ST/pristine/$CN" \
        --baseline "$ST/pristine/baseline-gate.json" --require-clean --json --out "$W/archcheck.json" > "$W/archcheck.txt" 2> "$W/archcheck.err" ); rc=$?
    check archcheck "{\"pass\":$([ $rc -eq 0 ] && echo true || echo false),\"exit\":$rc,\"requireClean\":true,\"baseline\":true}"
    if [ $rc -eq 1 ]; then
      fail "archcheck: new DET violations of severity >= 2 (pre-existing violations are not counted):"$'\n'"$(jq -r '.findings[]? | select(.class=="DET" and .severity>=2 and (.preexisting | not)) | "    \(.ruleId) \(.file):\(.line) \(.symbol // "") - \(.message)"' "$W/archcheck.json" 2>/dev/null)"
    elif [ $rc -ne 0 ]; then
      ERRS=$(jq -r '.errors[]? | "    " + .' "$W/archcheck.json" 2>/dev/null)
      [ -n "$ERRS" ] || ERRS="$(sed 's/^/    /' "$W/archcheck.err" "$W/archcheck.txt")"
      fail "archcheck could not evaluate the repository (exit $rc). Its output, verbatim:"$'\n'"$ERRS"; fi
  fi
fi

VERDICT=$([ ${#REASONS[@]} -eq 0 ] && echo PASS || echo FAIL)
jq -cn --argjson p "$PHASE" --argjson n "$N" --arg h "$HEAD" --arg t "$TREE" --argjson c "$CHECKS" --arg v "$VERDICT" \
  --arg at "$(utc)" --argjson ms "$(( $(date +%s%3N) - START ))" \
  '{schema:"arch002.submit/1", phase:$p, attempt:$n, gitHead:$h, treeHash:$t, checks:$c, verdict:$v, ms:$ms, at:$at}' >> "$LEDGER"
rm -rf "$W/tree"   # Disk (pilot amendment P2): the evaluated clone is regenerable from HEAD; outputs above are kept.
echo "submit: $VERDICT (attempt $N of $MAX, HEAD $HEAD)"
for r in "${REASONS[@]}"; do echo "  - $r"; done
if [ "$VERDICT" = PASS ]; then echo "Stop now and write your final message."
elif [ "$N" -ge "$MAX" ]; then echo "That was your last submit. Stop now and write your final message."; fi
[ "$VERDICT" = PASS ]
