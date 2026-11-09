#!/usr/bin/env bash
# Read-only: fetch all GitHub Actions workflow runs for a repo into compact JSONL.
# usage: fetch_runs.sh REPO OUTFILE
set -euo pipefail
repo=$1; out=$2; : > "$out.tmp"
page=1
while :; do
  body=$(curl -sS --fail "https://api.github.com/repos/kemiller2002/$repo/actions/runs?per_page=100&page=$page")
  n=$(printf '%s' "$body" | python3 -I -c 'import sys,json;d=json.load(sys.stdin);rs=d["workflow_runs"]
for r in rs: print(json.dumps({k:r.get(k) for k in ("id","name","event","status","conclusion","head_branch","head_sha","created_at","updated_at","run_started_at","run_attempt")}))
print(len(rs),file=sys.stderr)' 2>&1 >>"$out.tmp")
  [ "$n" -lt 100 ] && break
  page=$((page+1))
done
mv "$out.tmp" "$out"; wc -l "$out"
