set -u
S=/home/user/sprint-scratch/F
T=/home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm
O=$T/measurements/startup.jsonl
until grep -q "^DONE" $S/run_phase2.log; do sleep 10; done
echo "phase3 start $(date -u +%T)"
node $T/scripts/startup.mjs $O r010-wasmtools http://127.0.0.1:4807/ data-causa-started-ms --reps 7 --server python-http-rerun
node $T/scripts/startup.mjs $O r010-wasmtools http://127.0.0.1:4857/ data-causa-started-ms --reps 5 --server gzip-rerun
node $T/scripts/startup.mjs $O r010-wasmtools http://127.0.0.1:4857/ data-causa-started-ms --reps 5 --throttle 4g --server gzip-rerun --timeout 90000
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
cd $S/r010-full
for run in 1 2; do
  start=$(date +%s)
  CAUSA_TEST_PORT=4935 CAUSA_DOUBLE_PORT=4613 PLAYWRIGHT_JSON_OUTPUT_NAME=$S/pw/r010-fullclean-run$run.json timeout 3000 npx playwright test -c playwright.config.ts --project chromium --trace off --reporter=json > $S/pw/r010-fullclean-run$run.stdout 2> $S/pw/r010-fullclean-run$run.stderr
  echo "r010-fullclean run$run exit=$? wall=$(( $(date +%s) - start ))s load=$(cut -d' ' -f1 /proc/loadavg)"
  for p in $(pgrep -f "Causa.FakeGitHub.*--port 4613|http.server 4935"); do echo "leaked $p $(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-100)"; kill $p; done
done
echo DONE
