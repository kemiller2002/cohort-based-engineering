#!/usr/bin/env bash
# Builds the blinded review bundle from completed executions of one or more RUNs (derived from P2 review/bundle.sh).
#   bundle.sh OUT_DIR MAPPING_FILE SEED RUN [RUN...]
# Per item: trees/KEY/after (final head, without .git, .decisions/, build output), trees/KEY/before (starting tree),
# trees/KEY/change.diff (start..final, without .decisions/), trees/KEY/report.json (checklist fields removed).
# Arm-revealing material (.decisions/, checklist answers) is removed; the key-to-execution mapping goes to
# MAPPING_FILE, outside the bundle. Items from every arm and run are shuffled together.
set -euo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"; EXP="$(cd "$H/.." && pwd)"
OUT="$1"; MAP="$2"; SEED="$3"; shift 3
P3_WORK="${P3_WORK:-/home/user/p3-work}"; P3_STATE="${P3_STATE:-/home/user/.p3-state}"; RESROOT="${P3_RESULTS:-$EXP/results}"
rm -rf "$OUT"; mkdir -p "$OUT/trees"; : > "$OUT/items.unsorted"; echo '{}' > "$MAP"
for RUN in "$@"; do
  for d in "$RESROOT/$RUN"/*-?-r*; do
    x=$(basename "$d"); [ "$(jq -r .status "$d/execution.json" 2>/dev/null)" = completed ] || continue
    key="K$(printf '%s:%s:%s' "$SEED" "$RUN" "$x" | sha256sum | cut -c1-10)"; t="$OUT/trees/$key"; mkdir -p "$t/after"
    repo="$P3_WORK/$RUN/$x/repo"; start=$(jq -r .startCommit "$d/setup.json"); final=$(jq -r .heads.final "$d/setup.json")
    git -C "$repo" archive "$final" | tar -x -C "$t/after"
    rm -rf "$t/after/.decisions"; find "$t/after" -type d \( -name bin -o -name obj \) -prune -exec rm -rf {} +
    cp -r "$P3_STATE/$RUN/$x/start" "$t/before"; find "$t/before" -type d \( -name bin -o -name obj \) -prune -exec rm -rf {} +
    git -C "$repo" diff "$start" "$final" -- . ':(exclude).decisions' > "$t/change.diff"
    if [ -f "$t/after/.work/report.json" ]; then
      jq 'walk(if type == "object" then del(.checklist) else . end)' "$t/after/.work/report.json" > "$t/report.json" 2>/dev/null || cp "$t/after/.work/report.json" "$t/report.json"
      rm -f "$t/after/.work/report.json"
    else echo '{"note":"no report"}' > "$t/report.json"; fi
    scen=$(jq -r .scenario "$d/setup.json"); arm=$(jq -r .arm "$d/setup.json"); rep=$(jq -r .replicate "$d/setup.json")
    jq -nc --arg k "$key" --arg req "$(jq -r .requirementFile "$EXP/scenarios/$scen/scenario.json")" \
      '{key:$k, tree:("trees/" + $k), requirement:("trees/" + $k + "/after/" + $req), report:("trees/" + $k + "/report.json"), diff:("trees/" + $k + "/change.diff")}' >> "$OUT/items.unsorted"
    jq --arg k "$key" --arg run "$RUN" --arg x "$x" --arg s "$scen" --arg a "$arm" --argjson r "$rep" \
      '.[$k] = {run:$run, execution:$x, scenario:$s, arm:$a, replicate:$r}' "$MAP" > "$MAP.tmp" && mv "$MAP.tmp" "$MAP"
  done
done
python3 -I -c 'import random,sys; l=open(sys.argv[1]).read().splitlines(); random.Random(int(sys.argv[2])).shuffle(l); open(sys.argv[3],"w").write("\n".join(l)+"\n")' "$OUT/items.unsorted" "$SEED" "$OUT/items.jsonl"
rm "$OUT/items.unsorted"; cp "$H/review/RUBRIC.md" "$OUT/RUBRIC.md"
echo "$(wc -l < "$OUT/items.jsonl") items"
