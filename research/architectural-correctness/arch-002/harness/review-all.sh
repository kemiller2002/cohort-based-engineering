#!/usr/bin/env bash
# Run the blinded review (review.sh) for every finished confirmatory trial that has no valid review yet. Resumable.
#   usage: review-all.sh [PARALLEL]
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd); R=/home/user/arch002-runs; P=${1:-4}
export DOTNET_ROOT=/home/user/.tools/dotnet PATH=/home/user/.tools/dotnet:$PATH ARCH002_SEALED_DIR=/home/user/arch002-sealed
todo() { for d in "$R"/ARCH-002-CONF-*; do [ -f "$d/state/done" ] || continue
  jq -e '.valid == true' "$d/state/review/result.json" >/dev/null 2>&1 || basename "$d"; done; }
one() { bash "$H/review.sh" "$1" > "/home/user/arch002-runs/$1/state/review-run.log" 2>&1; echo "$(date -u +%T) $1 exit=$?"; }
export -f one; export H
todo | xargs -P "$P" -I{} bash -c 'one {}'
echo "remaining without a valid review: $(todo | wc -l)"
