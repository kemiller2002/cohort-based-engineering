#!/usr/bin/env bash
# Stand-in for `claude -p` in the harness smoke (no model). It reads which brief it was given and:
#  plan.md        writes FAKE_PLAN to .decisions/decisions.json and commits;
#  work/implement/repair.md   copies FAKE_VARIANT's files into the repository, writes a report (and marks every
#                 non-rejected decision implemented), commits;
#  REVIEW-BRIEF.md writes FAKE_FINDINGS (default: no findings) to findings.json.
# It prints one stream-json result event, as the CLI does.
set -euo pipefail
prompt=""; sid=""
while [ $# -gt 0 ]; do case "$1" in -p) prompt="$2"; shift 2;; --session-id|--resume) sid="$2"; shift 2;; *) shift;; esac; done
brief=$(grep -oE '/[^ ]+\.md' <<< "$prompt" | head -1); name=$(basename "$brief")
commit() { git add -A && git -c user.name=engineer -c user.email=e@x -c commit.gpgsign=false commit -qm "$1" || true; }
case "$name" in
  plan.md) mkdir -p .decisions; cp "$FAKE_PLAN" .decisions/decisions.json; commit "plan"; msg="PLAN: ready";;
  work.md|implement.md|repair.md)
    [ -n "${FAKE_VARIANT:-}" ] && cp -r "$FAKE_VARIANT/." .
    if [ -f .decisions/decisions.json ] || grep -q 'decisions/decisions.json' "$brief"; then
      mkdir -p .decisions; [ -f .decisions/decisions.json ] || cp "$FAKE_PLAN" .decisions/decisions.json
      rejected=$(grep -oE '`[A-Za-z0-9-]+` \([a-z-]+\): \*\*rejected' "$brief" | grep -oE '^`[^`]+' | tr -d '`' || true)
      jq --arg r "$rejected" '.decisions |= map(if ($r | split("\n") | index(.decisionId)) then . else .implementedIn = ["src"] end)' .decisions/decisions.json > d.tmp && mv d.tmp .decisions/decisions.json
    fi
    mkdir -p .work
    jq -n '{schema:"p2.report/1", workItem:"X", outcome:"completed", blockedReason:null, requirements:[], decisions:[{id:"D1", statement:"stand-in", basis:"evidence", evidence:["README.md"], requirementIds:[]}], verification:[], openQuestions:["stand-in question"], handoff:""}' > .work/report.json
    commit "work"; msg="OUTCOME: completed";;
  REVIEW-BRIEF.md) echo "${FAKE_FINDINGS:-{\"findings\":[]\}}" > findings.json; msg="DONE";;
  *) msg="unknown brief $name";;
esac
jq -nc --arg sid "$sid" --arg m "$msg" '{type:"result", subtype:"success", is_error:false, num_turns:1, duration_ms:5, session_id:$sid, total_cost_usd:0, usage:{input_tokens:1, output_tokens:1, cache_read_input_tokens:0, cache_creation_input_tokens:0}, result:$m}'
