#!/usr/bin/env bash
# ARCH-002 live K1 smoke (adapted from ARCH-001 harness/smoke-live.sh): one real, minimal model session per model
# (target total cost < $0.50).
#   usage: smoke-live.sh [opus|sonnet ...]      (default: opus sonnet)
# Per model: sets up a SMOKE run (brownfield stand-in fixture, arm A), replaces the phase-1 brief with a trivial one
# (run `git rev-parse HEAD`, run `submit` once, end with the ARCH002-DONE line), runs `trial.sh phase RUNID 1` with
# the REAL launcher (launch-agent.sh: --model from agent-config .models, fresh CLAUDE_CONFIG_DIR/HOME, fresh session
# id, nonce, --tools, stream-json), then assembles the observation and prints what the stream capture, ledger,
# contamination scan and cost extraction (priced with the run's model) produced.
H0="$(cd "$(dirname "$0")" && pwd)"
export ARCH002_FIXTURES="$H0/smoke/fixtures" ARCH002_SEALED_DIR="$H0/smoke/sealed"
source "$H0/lib.sh"
MODELS=("$@"); [ ${#MODELS[@]} -gt 0 ] || MODELS=(opus sonnet)
for M in "${MODELS[@]}"; do
  ID="ARCH-002-SMOKE-lending-smoke-T0-$M-r1-A-live${SMOKE_TAG:-$(date -u +%H%M%S)}"; run_paths "$ID"
  bash "$H/trial.sh" setup "$ID" || { echo "$M: setup failed"; continue; }
  B="$ST/live-brief.md"
  cat > "$B" <<BRIEF
# Agent brief (harness smoke)

You are in the git repository \`$REPO\`. Do exactly these three steps and nothing else:

1. Run \`git rev-parse HEAD\`.
2. Run \`submit\` once (it is on your PATH; it takes about a minute).
3. Reply with one short sentence saying what \`submit\` printed, then a last line \`ARCH002-DONE <gitHead>\` where
   \`<gitHead>\` is the hash from step 1.
BRIEF
  ARCH002_BRIEF_OVERRIDE="$B" bash "$H/trial.sh" phase "$ID" 1
  bash "$H/score.sh" "$ID" --assemble-only > /dev/null || true
  O="$ST/score/observation.json"
  echo "run: $ID (model $(jq -r .model "$ST/run.json"))"
  echo "launch exit: $(jq -r .exit "$ST/phase1/launch.json")  events: $(wc -l < "$ST/phase1/stream.jsonl")  transcripts: $(ls "$ST/phase1/transcripts" | wc -l)"
  echo "ledger: $(jq -c '{phase,attempt,verdict,checks}' "$ST/submit-ledger.jsonl" 2>/dev/null | tr '\n' ' ')"
  jq -c '.phases["1"] | {costUsd, costSource, recomputedMainModelUsd, reportedMainModelUsd, otherModels, crossCheck: .crossCheck | {mainModelCostRelativeGap, tokensTotalRelativeGap, agrees},
    tokens, requests, cache, toolCalls, byTool, verificationExecutions, wallMs, finalLine, contamination: .contamination.contaminated, integrity: .integrity.tampered}' "$O"
done
