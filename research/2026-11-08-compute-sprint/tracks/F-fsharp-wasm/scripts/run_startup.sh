set -u
T=/home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm
O=$T/measurements/startup.jsonl
for x in "fixture 4804 data-fixture-ready" "r008 4802 data-engine=ready" "r009 4803 data-causa-ready=running" "r010 4801 data-causa-started-ms"; do
  set -- $x
  node $T/scripts/startup.mjs $O $1 http://127.0.0.1:$2/ $3 --reps 7 --timeout 60000
  node $T/scripts/startup.mjs $O $1 http://127.0.0.1:$2/ $3 --reps 7 --warm --timeout 60000
  node $T/scripts/startup.mjs $O $1 http://127.0.0.1:$2/ $3 --reps 5 --throttle 4g --timeout 90000
done
echo DONE
