#!/usr/bin/env bash
# probe.sh: run the A4 probe (L04 oracle + probe facts) against each arm's unit-4 and unit-12 heads
set -uo pipefail
S="$(cd "$(dirname "$0")" && pwd)"; R=/home/user/cohort-based-engineering/research/experiments/VAC-002/results/P1
export PATH=/root/.dotnet:$PATH DOTNET_ROOT=/root/.dotnet DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
for a in A B C D E F; do for u in 4 12; do
  h=$(jq -r --argjson u $u '.units[]|select(.unit==$u)|.attempts[-1].head' $R/$a/setup.json)
  T=$S/work/$a-$u/tree; rm -rf $S/work/$a-$u; mkdir -p $T
  git -C /home/user/vac-work/P1/$a/repo archive $h | tar -x -C $T
  "$S/oracle/run.sh" "$T" L04 "$S/work/$a-$u/out" > /dev/null
  res=$(grep -o '<UnitTestResult [^>]*testName="[^"]*PROBE[^"]*"[^>]*outcome="[A-Za-z]*"' $S/work/$a-$u/out/L04.trx | sed -E 's/.*testName="([^"]*)".*outcome="([A-Za-z]*)"/\2 \1/' | tr '\n' ';')
  echo "$a unit$u $h $res"
  rm -rf $T
done; done
