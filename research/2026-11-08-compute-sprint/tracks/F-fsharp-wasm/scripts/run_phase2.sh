set -u
S=/home/user/sprint-scratch/F
T=/home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm
O=$T/measurements/startup.jsonl
until grep -q DONE $S/run_suites.log; do sleep 10; done
echo "phase2 start $(date -u +%T)"
# 1. wasm-tools variant startup (same harness as the other variants)
(python3 -m http.server 4807 --bind 127.0.0.1 --directory $S/r010-wt/dist >/dev/null 2>&1 &)
(node $T/scripts/static_gzip_server.mjs $S/r010-wt/dist 4857 >/dev/null 2>&1 &)
sleep 2
node $T/scripts/startup.mjs $O r010-wasmtools http://127.0.0.1:4807/ data-causa-started-ms --reps 7
node $T/scripts/startup.mjs $O r010-wasmtools http://127.0.0.1:4857/ data-causa-started-ms --reps 5 --server gzip
node $T/scripts/startup.mjs $O r010-wasmtools http://127.0.0.1:4857/ data-causa-started-ms --reps 5 --throttle 4g --server gzip --timeout 90000
# 2. r010-full (TrimMode=full) correctness: run the chromium suite twice against its own build
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
cd $S/r010-full
for run in 1 2; do
  start=$(date +%s)
  CAUSA_TEST_PORT=4934 CAUSA_DOUBLE_PORT=4612 PLAYWRIGHT_JSON_OUTPUT_NAME=$S/pw/r010-full-run$run.json timeout 3000 npx playwright test -c playwright.config.ts --project chromium --trace off --reporter=json > $S/pw/r010-full-run$run.stdout 2> $S/pw/r010-full-run$run.stderr
  echo "r010-full run$run exit=$? wall=$(( $(date +%s) - start ))s load=$(cut -d' ' -f1 /proc/loadavg)"
done
grep -h "TrimMode" $S/r010-full/src/Causa.Host/Causa.Host.csproj
# 3. build batch 2, interleaved across repos
for rep in 1 2 3; do
  for r in r008 r009 r010; do
    SPRINT_BATCH=batch2 python3 $T/scripts/measure_build.py $T/measurements/build-times-batch2.csv $S/$r $r --reps 1 --modes publish-cold,publish-incr
  done
done
echo DONE
