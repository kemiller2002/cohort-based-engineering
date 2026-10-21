#!/usr/bin/env bash
# Record which agent runs unit UNIT of RUN/ARM. Without ID, the arm's unit-1 agent continues (long-lived arms).
#   agent.sh RUN ARM UNIT [ID]
S="${VAC_STATE:-/home/user/.vac-state}"; f="$S/$1/agents.json"
id="${4:-$(jq -r --arg a "$2" '.[$a]["1"]' "$f")}"
jq --arg a "$2" --arg u "$3" --arg id "$id" '.[$a][$u] = $id' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
