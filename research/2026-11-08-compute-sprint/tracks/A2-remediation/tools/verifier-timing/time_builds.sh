#!/usr/bin/env bash
# SPR-A2-02: time the exact CI build command for the pinned Praxis verifier. Serial; scratch only.
# Usage: time_builds.sh SRC_GIT_DIR PIN WORK_DIR OUT_JSONL N
set -euo pipefail
src=$1; pin=$2; work=$3; out=$4; n=${5:-3}
export PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
proj=src/Praxis.Cli/Praxis.Cli.fsproj
mkdir -p "$work"; : > "$out"
fresh_tree() { rm -rf "$1"; mkdir -p "$1"; git -C "$src" archive "$pin" | tar -x -C "$1"; }
timed_build() { # dir nugetdir mode run
  dotnet build-server shutdown >/dev/null 2>&1 || true
  local s e rc l0
  l0=$(cut -d' ' -f1 /proc/loadavg)
  s=$(date +%s.%N)
  set +e
  (cd "$1" && NUGET_PACKAGES="$2" dotnet build "$proj" --configuration Release > "$work/$3-$4.log" 2>&1)
  rc=$?; set -e
  e=$(date +%s.%N)
  local dll="$1/src/Praxis.Cli/bin/Release/net10.0/praxis.dll"
  local h=""; [ -f "$dll" ] && h=$(sha256sum "$dll" | cut -c1-64)
  local load; load=$(cut -d' ' -f1 /proc/loadavg)
  printf '{"mode":"%s","run":%s,"seconds":%s,"exit":%s,"praxisDllSha256":"%s","loadAvg1mAtEnd":%s,"loadAvg1mAtStart":%s}\n' "$3" "$4" "$(echo "$e - $s" | bc)" "$rc" "$h" "$load" "$l0" | tee -a "$out"
}
for i in $(seq 1 "$n"); do
  fresh_tree "$work/cold$i"; rm -rf "$work/nuget-cold$i"
  timed_build "$work/cold$i" "$work/nuget-cold$i" cold "$i"
done
for i in $(seq 1 "$n"); do  # NuGet cache warm (from cold1), fresh source tree: models caching ~/.nuget/packages
  fresh_tree "$work/warmrestore$i"
  timed_build "$work/warmrestore$i" "$work/nuget-cold1" warm-nuget "$i"
done
for i in $(seq 1 "$n"); do  # same tree, no change: models caching the build output (obj/bin)
  timed_build "$work/warmrestore1" "$work/nuget-cold1" warm-incremental "$i"
done
