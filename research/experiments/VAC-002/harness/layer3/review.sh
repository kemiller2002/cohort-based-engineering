#!/usr/bin/env bash
# VAC-002 Layer 3: blinded decision review by isolated K1 reviewer sessions (never an implementing session).
#   review.sh BUNDLE_DIR REVIEWER(R1|R2|R3) [ITEMS_FILE]
# The bundle holds items.jsonl (keys, statements, evidence, tree paths) and trees/ (repository snapshots without arm
# markers). Each reviewer is a fresh `claude -p` with its own config dir, cwd = the bundle, tools Read/Bash/Write.
# Output: BUNDLE_DIR/labels-REVIEWER-batch-NN.jsonl (one JSON object per item, as RUBRIC.md says).
set -euo pipefail
B="$(cd "$1" && pwd)"; R="$2"; ITEMS="${3:-$B/items.jsonl}"
H="$(cd "$(dirname "$0")" && pwd)"
CFG="$B/.reviewers/$R"; mkdir -p "$CFG/config" "$CFG/home"
cp "$H/RUBRIC.md" "$B/RUBRIC.md"
split -l 25 -d -a 2 "$ITEMS" "$B/.reviewers/$R/batch-"
for f in "$B/.reviewers/$R"/batch-??; do
  n=$(basename "$f" | sed 's/batch-//'); cp "$f" "$B/items-$R-batch-$n.jsonl"
  out="$B/labels-$R-batch-$n.jsonl"; [ -s "$out" ] && continue
  prompt="You are an independent reviewer. Read RUBRIC.md in the current directory and follow it exactly. Review every item in items-$R-batch-$n.jsonl (one JSON object per line); each item's tree is a repository snapshot under trees/. Inspect only files under the current directory. Write your labels to labels-$R-batch-$n.jsonl, one JSON object per line with the fields the rubric names, one line for every item. Then reply with the number of items labelled."
  ( cd "$B" && env -u CLAUDE_ADDITIONAL_DIRECTORIES -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_CHILD_SESSION \
      -u CLAUDE_CODE_REMOTE_SESSION_ID -u CLAUDE_CODE_REMOTE_SDK_URL -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_MESSAGING_TOKEN -u GH_TOKEN -u GITHUB_TOKEN \
      HOME="$CFG/home" CLAUDE_CONFIG_DIR="$CFG/config" timeout 2700 /opt/node22/bin/claude -p "$prompt" --model claude-opus-5-5 \
      --session-id "$(python3 -I -c 'import uuid; print(uuid.uuid4())')" --output-format stream-json --verbose --permission-mode bypassPermissions \
      --tools "Read,Bash,Write" --strict-mcp-config --mcp-config '{"mcpServers":{}}' > "$B/.reviewers/$R/batch-$n.stream.jsonl" 2> "$B/.reviewers/$R/batch-$n.err" < /dev/null ) || true
  echo "$R batch $n: $(wc -l < "$out" 2>/dev/null || echo 0) labels"
done
