set -u
T=/home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm
S=/home/user/sprint-scratch/F
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
mkdir -p $S/pw
for run in 1 2 3; do
  for r in r009 r008 r010; do
    cd $S/$r
    case $r in
      r008) CFG=playwright.sprint.config.ts; EXTRA="" ;;
      r009) CFG=playwright.sprint.config.js; EXTRA="" ;;
      r010) CFG=playwright.config.ts; EXTRA="--project chromium"; export CAUSA_TEST_PORT=4933 CAUSA_DOUBLE_PORT=4611 ;;
    esac
    start=$(date +%s)
    PLAYWRIGHT_JSON_OUTPUT_NAME=$S/pw/$r-run$run.json timeout 3000 npx playwright test -c $CFG $EXTRA --trace off --reporter=json > $S/pw/$r-run$run.stdout 2> $S/pw/$r-run$run.stderr
    echo "$r run$run exit=$? wall=$(( $(date +%s) - start ))s load=$(cut -d' ' -f1 /proc/loadavg)"
    unset CAUSA_TEST_PORT CAUSA_DOUBLE_PORT
  done
done
echo DONE
