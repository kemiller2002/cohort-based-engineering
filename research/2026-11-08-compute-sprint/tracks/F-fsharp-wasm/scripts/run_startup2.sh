set -u
T=/home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm
O=$T/measurements/startup.jsonl
for x in "r010-sat 4805" "r010-full 4806"; do set -- $x
  node $T/scripts/startup.mjs $O $1 http://127.0.0.1:$2/ data-causa-started-ms --reps 7
  node $T/scripts/startup.mjs $O $1 http://127.0.0.1:$2/ data-causa-started-ms --reps 5 --throttle 4g --timeout 90000
done
for x in "fixture 4851 data-fixture-ready" "r008 4852 data-engine=ready" "r009 4853 data-causa-ready=running" "r010 4854 data-causa-started-ms" "r010-sat 4855 data-causa-started-ms" "r010-full 4856 data-causa-started-ms"; do set -- $x
  node $T/scripts/startup.mjs $O $1 http://127.0.0.1:$2/ $3 --reps 5 --server gzip
  node $T/scripts/startup.mjs $O $1 http://127.0.0.1:$2/ $3 --reps 5 --throttle 4g --server gzip --timeout 90000
done
echo DONE
