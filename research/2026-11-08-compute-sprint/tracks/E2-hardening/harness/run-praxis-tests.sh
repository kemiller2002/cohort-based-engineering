#!/usr/bin/env bash
# usage: run-tests.sh LABEL [FILTER]   -- runs Praxis.Tests from the scratch clone; output in logs/tests-LABEL.log
set -u
cd "/home/user/sprint-scratch/E2/${TREE:-praxis}" || exit 9
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_ROLL_FORWARD=Major
export TMPDIR=/home/user/sprint-scratch/E2/tmp PRAXIS_TEST_DOKIMOS_DLL=/home/user/sprint-scratch/E2/dokimos-bin/Dokimos.Cli.dll
export PRAXIS_TEST_FILTER="${2:-}"
L=/home/user/sprint-scratch/E2/logs/tests-$1.log
s=$(date +%s); dotnet tests/Praxis.Tests/bin/Release/net10.0/Praxis.Tests.dll > "$L" 2>&1; rc=$?; e=$(date +%s)
echo "exit=$rc seconds=$((e-s)) filter='${2:-}'" >> "$L"
