#!/usr/bin/env bash
# Orchestration helper: finish unit UNIT of RUN/ARM using the agent id recorded in harness state.
#   fin.sh RUN ARM UNIT [ATTEMPT]
H="$(cd "$(dirname "$0")" && pwd)"; S="${VAC_STATE:-/home/user/.vac-state}"
id=$(jq -r --arg a "$2" --arg u "$3" '.[$a][$u]' "$S/$1/agents.json")
"$H/vac.sh" finish "$1" "$2" "$3" "$id" "${4:-1}" 2>&1 | tail -2 | sed "s/^/$1 $2 $3: /"
cp "$S/$1/agents.json" "$H/../results/$1/agents.json"
