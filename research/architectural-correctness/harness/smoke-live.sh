#!/usr/bin/env bash
# ARCH-001 live K1 smoke (one real, minimal model session; target cost < $0.50).
#   usage: smoke-live.sh
# Sets up a SMOKE run (stand-in fixtures, arm A), replaces the phase-1 brief with a trivial one (run `git rev-parse
# HEAD`, run `submit` once, end with the ARCH001-DONE line), runs `trial.sh phase RUNID 1` with the REAL launcher
# (launch-agent.sh: fresh CLAUDE_CONFIG_DIR/HOME, fresh session id, nonce, --tools, stream-json), then assembles the
# observation and prints what the stream capture, ledger, contamination scan and cost extraction produced.
H0="$(cd "$(dirname "$0")" && pwd)"
export ARCH001_FIXTURES="$H0/smoke/fixtures" ARCH001_SEALED_DIR="$H0/smoke/sealed"
export ARCH001_ARCHCHECK="$H0/smoke/archcheck/archcheck.py" ARCH001_POLICY="$H0/smoke/fixtures/policy/lending.policy.json"
source "$H0/lib.sh"
ID="ARCH-001-SMOKE-T0-r1-A-live${SMOKE_TAG:-$(date -u +%H%M%S)}"; run_paths "$ID"
bash "$H/trial.sh" setup "$ID" || exit 3
B="$ST/live-brief.md"
cat > "$B" <<BRIEF
# Agent brief (harness smoke)

You are in the git repository \`$REPO\`. Do exactly these three steps and nothing else:

1. Run \`git rev-parse HEAD\`.
2. Run \`submit\` once (it is on your PATH; it takes about a minute).
3. Reply with one short sentence saying what \`submit\` printed, then a last line \`ARCH001-DONE <gitHead>\` where
   \`<gitHead>\` is the hash from step 1.
BRIEF
ARCH001_BRIEF_OVERRIDE="$B" bash "$H/trial.sh" phase "$ID" 1
bash "$H/score.sh" "$ID" --assemble-only > /dev/null || true
O="$ST/score/observation.json"
echo "run: $ID"
echo "launch exit: $(jq -r .exit "$ST/phase1/launch.json")  events: $(wc -l < "$ST/phase1/stream.jsonl")  transcripts: $(ls "$ST/phase1/transcripts" | wc -l)"
echo "ledger: $(jq -c '{phase,attempt,verdict,checks}' "$ST/submit-ledger.jsonl" 2>/dev/null | tr '\n' ' ')"
jq -c '.phases["1"] | {costUsd, costSource, recomputedMainModelUsd, reportedMainModelUsd, otherModels, crossCheck: .crossCheck | {mainModelCostRelativeGap, tokensTotalRelativeGap, agrees},
  tokens, requests, cache, toolCalls, byTool, testExecutions, verificationExecutions, wallMs, finalLine, contamination: .contamination.contaminated, integrity: .integrity.tampered}' "$O"
