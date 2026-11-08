set -u
for r in r010 r009 r008; do
  python3 /home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm/scripts/measure_build.py /home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm/measurements/build-times.csv /home/user/sprint-scratch/F/$r $r --reps 3 --modes publish-cold,publish-noop,publish-incr,sln-cold,sln-noop
done
echo DONE
