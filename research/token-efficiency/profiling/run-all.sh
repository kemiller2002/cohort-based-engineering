#!/usr/bin/env bash
# Reproduce every output under profiling/out/. Inputs are read only.
#   CBE      cohort-based-engineering checkout at main (run-01 D observations)
#   RUN02    read-only snapshot of the REL-001 run-02 branch (pinned in research/coordination/manifest.json)
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE=$(cd "$(dirname "$0")" && pwd)
CBE=${CBE:-$(cd "$HERE/../../.." && pwd)}
RUN02=${RUN02:-/home/user/wt/cbe-run02-readonly}
PRICE="$RUN02/research/pricing/anthropic.price-table.json"
P="python3 $HERE/profile.py"

python3 "$HERE/selfcheck.py"

$P observations --dataset run-01-D --label "run-01 Experiment D (complete, analysed); both arms" \
  --root "$CBE" --glob 'research/experiments/REL-001/observations/*/REL-001-D-*.json' \
  --price-table "$PRICE" --config "$HERE/config.json" --out "$HERE/out/run-01-D.json"

$P observations --dataset run-02-echelon \
  --label "run-02 committed Echelon-arm trials: EXPLORATORY PROFILING, within-arm only; not a preregistered analysis; no arm comparison" \
  --root "$RUN02" --glob 'research/experiments/REL-001/run-02/observations/echelon-*/*.json' \
  --arms echelon-original,echelon-optimized --within-arm-only \
  --price-table "$PRICE" --config "$HERE/config.json" --out "$HERE/out/run-02-echelon.json"

$P briefs --root "$RUN02" --profile "$HERE/out/run-02-echelon.json" --out "$HERE/out/run-02-context-sizes.json"

$P transcripts --dataset fixture --label "synthetic fixture (format check only)" \
  --root "$HERE" --glob 'fixtures/*.jsonl' --price-table "$PRICE" --out "$HERE/out/fixture-transcript.json"

$P check "$HERE/out/run-01-D.json" "$HERE/out/run-02-echelon.json" "$HERE/out/fixture-transcript.json"
