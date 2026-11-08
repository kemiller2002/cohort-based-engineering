set -u
S=/home/user/sprint-scratch/F
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
one() { r=$1; run=$2; cd $S/$r
  case $r in
    r008) set -- -c playwright.sprint.config.ts --project chromium ;;
    r009) set -- -c playwright.sprint.config.js ;;
    r010) set -- -c playwright.config.ts --project chromium; export CAUSA_TEST_PORT=4933 CAUSA_DOUBLE_PORT=4611 ;;
  esac
  start=$(date +%s)
  PLAYWRIGHT_JSON_OUTPUT_NAME=$S/pw/$r-run$run.json timeout 3000 npx playwright test "$@" --trace off --reporter=json > $S/pw/$r-run$run.stdout 2> $S/pw/$r-run$run.stderr
  echo "$r run$run exit=$? wall=$(( $(date +%s) - start ))s load=$(cut -d' ' -f1 /proc/loadavg)" >> $S/run_suites.log
  unset CAUSA_TEST_PORT CAUSA_DOUBLE_PORT
}
one r010 2
one r009 3
one r008 3
one r010 3
echo DONE >> $S/run_suites.log
