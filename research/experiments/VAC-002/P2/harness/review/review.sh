#!/usr/bin/env bash
# One blinded reviewer over the bundle, in batches; isolated K1 sessions that never implemented anything.
#   review.sh BUNDLE REVIEWER(R1|R2|R3) [ITEMS_FILE] [BATCH=6]
# Writes BUNDLE/labels-REVIEWER-batch-NN.jsonl and BUNDLE/.reviewers/REVIEWER/batch-NN.{stream.jsonl,usage.json}.
set -euo pipefail
B="$(cd "$1" && pwd)"; R="$2"; ITEMS="${3:-$B/items.jsonl}"; N="${4:-6}"
H="$(cd "$(dirname "$0")/.." && pwd)"; CFG="$B/.reviewers/$R"; mkdir -p "$CFG/config" "$CFG/home"
split -l "$N" -d -a 2 "$ITEMS" "$CFG/batch-"
for f in "$CFG"/batch-??; do
  n=$(basename "$f" | sed 's/batch-//'); cp "$f" "$B/items-$R-batch-$n.jsonl"; out="$B/labels-$R-batch-$n.jsonl"
  [ -s "$out" ] && continue
  prompt="You are an independent reviewer. Read RUBRIC.md in the current directory and follow it exactly. Review every item in items-$R-batch-$n.jsonl (one JSON object per line). For each item, its directory under trees/ holds before/ (the repository before the work), after/ (after the work), change.diff and report.json. Inspect only files under the current directory. Write your results to labels-$R-batch-$n.jsonl, one JSON object per line, one line per item, with the fields the rubric names. Then reply with the number of items reviewed."
  ( cd "$B" && env -u CLAUDE_ADDITIONAL_DIRECTORIES -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_CHILD_SESSION \
      -u CLAUDE_CODE_REMOTE_SESSION_ID -u CLAUDE_CODE_REMOTE_SDK_URL -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_MESSAGING_TOKEN -u GH_TOKEN -u GITHUB_TOKEN \
      -u CLAUDE_CODE_SYNC_SKILLS -u CLAUDE_CODE_SYNC_PLUGINS -u CLAUDE_AUTOCOMPACT_PCT_OVERRIDE \
      HOME="$CFG/home" CLAUDE_CONFIG_DIR="$CFG/config" timeout 2700 /opt/node22/bin/claude -p "$prompt" --model claude-opus-5-5 \
      --session-id "$(cat /proc/sys/kernel/random/uuid)" --output-format stream-json --verbose --permission-mode bypassPermissions \
      --tools "Read,Glob,Grep,Write" --strict-mcp-config --mcp-config '{"mcpServers":{}}' > "$CFG/batch-$n.stream.jsonl" 2> "$CFG/batch-$n.err" < /dev/null ) || true
  dotnet fsi --quiet --exec "$H/p2.fsx" stream "$CFG/batch-$n.stream.jsonl" "$B" > "$CFG/batch-$n.usage.json" 2>/dev/null || true
  echo "$R batch $n: $(wc -l < "$out" 2>/dev/null || echo 0) labels, \$$(jq -r '.costUsdCli // "?"' "$CFG/batch-$n.usage.json")"
done
