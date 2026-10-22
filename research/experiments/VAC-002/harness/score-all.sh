#!/usr/bin/env bash
# After every chain of RUN has ended: unseal the hidden material, score every unit's final attempt (and attempt 1
# where a repair happened), then summarise, plot and build the Layer 2 dataset. Harness only.
#   score-all.sh RUN KEY_FILE
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"; EXP="$(cd "$H/.." && pwd)"; RUN="$1"; KEY="$2"
SEALED="${VAC2_SEALED:-/home/user/.vac2-sealed}"
export VAC2_RESULTS="${VAC2_RESULTS:-$EXP/results}"
pgrep -f "vac2.sh chain $RUN " >/dev/null && { echo "chains of $RUN still running; refusing to unseal" >&2; exit 2; }
mkdir -p "$SEALED"
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass "file:$KEY" -in "$EXP/sealed/vac002-sealed.tar.gz.enc" | tar -xz -C "$SEALED"
for d in "$VAC2_RESULTS/$RUN"/*/; do
  arm=$(basename "$d")
  for u in $(jq -r '.units[] | select((.attempts | length) > 0) | .unit' "$d/setup.json"); do
    "$H/vac2.sh" score "$RUN" "$arm" "$u" | sed "s/^/$arm /"
    n=$(jq --argjson u "$u" '[.units[] | select(.unit == $u) | .attempts[]] | length' "$d/setup.json")
    [ "$n" -gt 1 ] && "$H/vac2.sh" score "$RUN" "$arm" "$u" 1 | sed "s/^/$arm first-pass /"
  done
done
dotnet fsi --quiet --exec "$H/analyze.fsx" summary "$VAC2_RESULTS" "$RUN" "$EXP/fixture" "$SEALED"
dotnet fsi --quiet --exec "$H/analyze.fsx" phaseg /home/user/.vac2-state "$VAC2_RESULTS" "$RUN" "$EXP/fixture"
dotnet fsi --quiet --exec "$H/analyze.fsx" dataset "$VAC2_RESULTS" "$RUN"
dotnet fsi --quiet --exec "$H/plots.fsx" "$VAC2_RESULTS/$RUN/analysis.json" "$VAC2_RESULTS/$RUN/figures"
