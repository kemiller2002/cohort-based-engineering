#!/usr/bin/env bash
# Builds the blinded review bundle from every completed execution of RUN.
#   bundle.sh RUN OUT_DIR MAPPING_FILE SEED
# Per item: trees/KEY/after (final head, without .git, .decisions/, build output), trees/KEY/before (starting tree),
# trees/KEY/change.diff (start..final, without .decisions/), trees/KEY/report.json (checklist fields removed).
# The key-to-execution mapping is written to MAPPING_FILE, outside the bundle.
set -euo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"; EXP="$(cd "$H/.." && pwd)"
RUN="$1"; OUT="$2"; MAP="$3"; SEED="$4"
P2_WORK="${P2_WORK:-/home/user/p2-work}"; P2_STATE="${P2_STATE:-/home/user/.p2-state}"; RES="${P2_RESULTS:-$EXP/results}/$RUN"
rm -rf "$OUT"; mkdir -p "$OUT/trees"; : > "$OUT/items.unsorted"; echo '{}' > "$MAP"
for d in "$RES"/S*-?; do
  x=$(basename "$d"); [ "$(jq -r .status "$d/execution.json" 2>/dev/null)" = completed ] || continue
  key="K$(printf '%s:%s' "$SEED" "$x" | sha256sum | cut -c1-10)"; t="$OUT/trees/$key"; mkdir -p "$t/after"
  repo="$P2_WORK/$RUN/$x/repo"; start=$(jq -r .startCommit "$d/setup.json"); final=$(jq -r .heads.final "$d/setup.json")
  git -C "$repo" archive "$final" | tar -x -C "$t/after"
  rm -rf "$t/after/.decisions"; find "$t/after" -type d \( -name bin -o -name obj \) -prune -exec rm -rf {} +
  cp -r "$P2_STATE/$RUN/$x/start" "$t/before"; find "$t/before" -type d \( -name bin -o -name obj \) -prune -exec rm -rf {} +
  git -C "$repo" diff "$start" "$final" -- . ':(exclude).decisions' > "$t/change.diff"
  if [ -f "$t/after/.work/report.json" ]; then
    jq 'walk(if type == "object" then del(.checklist) else . end)' "$t/after/.work/report.json" > "$t/report.json" 2>/dev/null || cp "$t/after/.work/report.json" "$t/report.json"
    rm -f "$t/after/.work/report.json"
  else echo '{"note":"no report"}' > "$t/report.json"; fi
  scen=${x%-*}
  jq -nc --arg k "$key" --arg req "$(jq -r .requirementFile "$EXP/scenarios/$scen/scenario.json")" \
    '{key:$k, tree:("trees/" + $k), requirement:("trees/" + $k + "/after/" + $req), report:("trees/" + $k + "/report.json"), diff:("trees/" + $k + "/change.diff")}' >> "$OUT/items.unsorted"
  jq --arg k "$key" --arg x "$x" --arg s "$scen" --arg a "${x##*-}" '.[$k] = {execution:$x, scenario:$s, arm:$a}' "$MAP" > "$MAP.tmp" && mv "$MAP.tmp" "$MAP"
done
python3 -I -c 'import random,sys; l=open(sys.argv[1]).read().splitlines(); random.Random(int(sys.argv[2])).shuffle(l); open(sys.argv[3],"w").write("\n".join(l)+"\n")' "$OUT/items.unsorted" "$SEED" "$OUT/items.jsonl"
rm "$OUT/items.unsorted"; cp "$H/review/RUBRIC.md" "$OUT/RUBRIC.md"
echo "$(wc -l < "$OUT/items.jsonl") items"
