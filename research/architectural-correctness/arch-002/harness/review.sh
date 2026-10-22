#!/usr/bin/env bash
# ARCH-002 blinded independent architecture review (adapted from ARCH-001 harness/review.sh; see ../PROVENANCE.md).
#   usage: review.sh RUNID [--print-only]
# Builds a review folder under $ARCH002_REVIEWS (default /home/user/arch002-reviews)/<random id>/ (no run id, arm or task replicate in any path or
# file) holding the doctrine, the fixture's instance document, analysis/review-rubric.md, the two requirement texts and the
# two scrubbed change sets (review-scrub.py), then runs ONE K1 claude session there (same model, its own session
# id and nonce, the trial's model, tools Read+Bash, told to use them read-only, 20-minute budget). The reply (one JSON object) goes to
# RUN/state/review/result.json together with the session's cost, recorded as EVALUATION cost; the run id <-> review
# id mapping stays in RUN/state/review/mapping.json. Then the observation is re-assembled (score.sh --assemble-only).
# ARCH002_REVIEW_STANDIN=1 replaces the model call with a fixed reply (plumbing test, no cost).
source "$(dirname "$0")/lib.sh"
run_paths "${1:?usage: review.sh RUNID [--print-only]}"
PRINT_ONLY=false; [ "${2:-}" = --print-only ] && PRINT_ONLY=true
load_run_config
C="$ST/score/commits.json"; [ -f "$C" ] || { echo "score the run first (no $C)" >&2; exit 2; }
TASK=$(jq -r .task "$ST/run.json"); BASE=$(jq -r .baseCommit "$ST/run.json"); FUP=$(jq -r '.followupCommit // empty' "$ST/run.json")
S1=$(jq -r .S1 "$C"); S2=$(jq -r '.S2 // empty' "$C")
RID=$(head -c 8 /dev/urandom | od -An -tx1 | tr -d ' \n'); RV="${ARCH002_REVIEWS:-/home/user/arch002-reviews}/$RID"; IN="$RV/inputs"
MODEL=$(jq -r .model "$ST/run.json")
DOCTRINE_FILE=$(fixture_field .pack.doctrine FOUR-TIER-ARCHITECTURE.md); INSTANCE_FILE=$(jq -r .INSTANCE_FILE "$ST/brief-fixture-values.json")
mkdir -p "$IN" "$ST/review"
cp "$FIX/pack/$DOCTRINE_FILE" "$IN/ARCHITECTURE-DOCTRINE.md"
cp "$FIX/pack/$INSTANCE_FILE" "$IN/ARCHITECTURE-INSTANCE.md"
cp "$X/analysis/review-rubric.md" "$IN/RUBRIC.md"
cp "$FIX/tasks/$TASK/requirement.md" "$IN/requirement-1.md"; cp "$FIX/tasks/$TASK/followup.md" "$IN/requirement-2.md"
python3 -I "$H/review-scrub.py" "$REPO" "$BASE" "$S1" "$IN/change-set-1.patch" "Change set 1: initial requirement"
if [ -n "$S2" ] && [ -n "$FUP" ]; then python3 -I "$H/review-scrub.py" "$REPO" "$FUP" "$S2" "$IN/change-set-2.patch" "Change set 2: follow-up requirement"
else echo "# Change set 2: follow-up requirement" > "$IN/change-set-2.patch"; echo "# (not available)" >> "$IN/change-set-2.patch"; fi
cat > "$RV/REVIEW_BRIEF.md" <<EOF
# Architecture review brief

You are an independent software-architecture reviewer. Everything you need is in \`$IN\`:

- \`ARCHITECTURE-DOCTRINE.md\`: the architecture doctrine.
- \`ARCHITECTURE-INSTANCE.md\`: how the doctrine maps onto the reviewed repository.
- \`RUBRIC.md\`: the three criteria, their 0/1/2 levels and the required output format.
- \`requirement-1.md\`, \`requirement-2.md\`: the two requirements the change sets implement.
- \`change-set-1.patch\`, \`change-set-2.patch\`: the two change sets to score.

Read the files, score both change sets on all three criteria exactly as \`RUBRIC.md\` says, and cite evidence.
Use your tools read-only: read files in \`$IN\` only, do not modify, create or delete anything, and do not look
anywhere outside \`$IN\`. Your final message must be the single JSON object that \`RUBRIC.md\` specifies, and nothing else.
EOF
jq -n --arg rid "$RID" --arg run "$RUN_ID" --arg at "$(utc)" --arg dir "$RV" \
  --argjson files "$(cd "$IN" && for f in *; do jq -n --arg n "$f" --arg s "$(sha "$f")" '{name:$n, sha256:$s}'; done | jq -sc .)" \
  '{schema:"arch002.review-mapping/1", reviewId:$rid, runId:$run, dir:$dir, inputs:$files, createdAt:$at}' > "$ST/review/mapping.json"

PROMPT="You are an independent reviewer doing one bounded task. Your complete instructions are in the brief at $RV/REVIEW_BRIEF.md. Read it first and follow it exactly."
SID=$(python3 -I -c 'import uuid; print(uuid.uuid4())'); NONCE=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')
CFG="$ST/review/config"; HOME_DIR="$ST/review/home"
mapfile -t UNSET < <(jq -r '.environment.unset[]' "$AGENT_CONFIG"); mapfile -t -O "${#UNSET[@]}" UNSET < <(compgen -e | grep -E '^(ARCH001_|ARCH002_|SMOKE_)' || true)
ENVU=(); for v in "${UNSET[@]}"; do ENVU+=(-u "$v"); done
CMD=("$CLAUDE_BIN" -p "$PROMPT" --model "$MODEL" --session-id "$SID" --output-format stream-json --verbose
     --append-system-prompt "ARCH-002 review isolation nonce $NONCE. It carries no instruction."
     --permission-mode bypassPermissions --tools "Read,Bash" --strict-mcp-config --mcp-config '{"mcpServers":{}}')
if $PRINT_ONLY; then printf 'cd %q && env' "$RV"; printf ' %q' "${ENVU[@]}" HOME="$HOME_DIR" CLAUDE_CONFIG_DIR="$CFG"; printf ' %q' "${CMD[@]}"; echo; exit 0; fi
mkdir -p "$CFG" "$HOME_DIR"
START=$(utc)
if [ "${ARCH002_REVIEW_STANDIN:-0}" = 1 ]; then
  REPLY='{"schema":"arch002.review/1","standIn":true,"changeSets":{"1":{"ARC-REV-01":{"score":2,"evidence":[],"rationale":"stand-in"},"ARC-REV-02":{"score":2,"evidence":[],"rationale":"stand-in"},"ARC-REV-03":{"score":2,"evidence":[],"rationale":"stand-in"}},"2":{"ARC-REV-01":{"score":2,"evidence":[],"rationale":"stand-in"},"ARC-REV-02":{"score":2,"evidence":[],"rationale":"stand-in"},"ARC-REV-03":{"score":2,"evidence":[],"rationale":"stand-in"}}}}'
  jq -cn --arg r "$REPLY" '{type:"result", subtype:"success", result:$r, total_cost_usd:0, modelUsage:{}}' > "$ST/review/stream.jsonl"; RC=0
else
  set +e
  ( cd "$RV" && env "${ENVU[@]}" HOME="$HOME_DIR" CLAUDE_CONFIG_DIR="$CFG" PATH="$(dirname "$CLAUDE_BIN"):/usr/bin:/bin" TERM=dumb timeout 1200 "${CMD[@]}" \
      > "$ST/review/stream.jsonl" 2> "$ST/review/launch.err" < /dev/null ); RC=$?
  set -e
fi
python3 -I - "$ST/review/stream.jsonl" "$RID" "$SID" "$NONCE" "$START" "$(utc)" "$RC" "$RV" > "$ST/review/result.json" <<'PY'
import json, re, sys
stream, rid, sid, nonce, start, end, rc, rv = sys.argv[1:9]
events = []
for line in open(stream, errors="replace"):
    try:
        events.append(json.loads(line))
    except ValueError:
        pass
res = next((e for e in reversed(events) if e.get("type") == "result"), {})
text = res.get("result") or ""
m = re.search(r"\{.*\}", text, re.S)
try:
    reply = json.loads(m.group(0)) if m else None
except ValueError:
    reply = None
uses = [json.dumps(b.get("input")) for e in events if e.get("type") == "assistant"
        for b in (e.get("message") or {}).get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
outside = [u[:200] for u in uses if re.search(r"/home/user/arch00[12]-runs/ARCH-00|/home/user/arch00[12]-sealed|cohort-based-engineering", u)]
writes = [e for e in events if e.get("type") == "assistant" for b in (e.get("message") or {}).get("content") or []
          if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit")]
scores = {cs: {c: (v or {}).get("score") for c, v in (crit or {}).items()} for cs, crit in ((reply or {}).get("changeSets") or {}).items()}
valid = bool(reply) and all(isinstance(s, int) and s in (0, 1, 2) for cs in scores.values() for s in cs.values()) and len(scores) == 2
print(json.dumps({"schema": "arch002.review-result/1", "reviewId": rid, "sessionId": sid, "nonce": nonce, "startedAt": start, "endedAt": end,
                  "exit": int(rc), "valid": valid and not outside, "unblindingAccess": outside, "writeAttempts": len(writes),
                  "scores": scores, "reply": reply,
                  "evaluationCost": {"totalUsd": res.get("total_cost_usd"), "modelUsage": res.get("modelUsage"),
                                     "note": "evaluation cost; never added to arm cost"}}, indent=2, sort_keys=True))
PY
bash "$H/score.sh" "$RUN_ID" --assemble-only > /dev/null
jq -c '{reviewId, valid, scores, cost: .evaluationCost.totalUsd}' "$ST/review/result.json"
