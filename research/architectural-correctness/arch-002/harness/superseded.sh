#!/usr/bin/env bash
# ARCH-001 amendment A3, built in for ARCH-002 (adapted from ARCH-001 harness/amendments/superseded.sh; see
# ../PROVENANCE.md): the initial-oracle tests a task's follow-up supersedes = the InitialOracle tests that FAIL on the
# sealed follow-up-good reference (good overlay, then followup-good overlay, over fixtures/<fixture>/repo). Arm-blind:
# reads only the public fixtures and the sealed references and oracles. Run once after the fixtures are frozen and
# before any confirmatory trial; score.py reads the result.
#   usage: superseded.sh [OUT.json] [FIXTURE...]      (default OUT harness/superseded.json; default every fixture)
source "$(dirname "$0")/lib.sh"
OUT="${1:-$H/superseded.json}"; shift || true
export DOTNET_ROOT="$DOTNET_ROOT_DIR" PATH="$DOTNET_ROOT_DIR:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 NUGET_PACKAGES="$NUGET_CACHE"
W=$(mktemp -d); [ -f "$OUT" ] || echo '{}' > "$OUT"
apply() { cp -r "$1/." "$2/"; [ -f "$1/.delete" ] && (cd "$2" && xargs -a "$1/.delete" rm -f) || true; rm -f "$2/.delete"; }
FIXS=("$@"); [ ${#FIXS[@]} -gt 0 ] || mapfile -t FIXS < <(cd "$FIXTURES" && ls -d */ | tr -d /)
for FX in "${FIXS[@]}"; do
  fixture_paths "$FX"; [ -d "$SEALED/oracle" ] || { echo "$FX: no sealed oracle, skipped"; continue; }
  HOST_PROJECT=$(fixture_field .oracleHostProject src/Lending.Host/Lending.Host.fsproj)
  for TD in "$FIX"/tasks/T*; do
    T=$(basename "$TD"); R="$SEALED/reference/$T"
    [ -d "$R/good" ] && [ -d "$R/followup-good" ] || { echo "$FX/$T: no good + followup-good reference, skipped"; continue; }
    d="$W/$FX-$T"; mkdir -p "$d/src" "$d/oracle"; cp -r "$FIX/repo/." "$d/src/"
    apply "$R/good" "$d/src"; apply "$R/followup-good" "$d/src"
    if [ -f "$SEALED/oracle/Oracle.fsproj" ]; then
      for f in $(grep -o 'Compile Include="[^"]*"' "$SEALED/oracle/Oracle.fsproj" | cut -d'"' -f2); do [ "$f" = OracleTests.fs ] || cp "$SEALED/oracle/$f" "$d/oracle/$f"; done
      cp "$SEALED/oracle/$T/InitialOracleTests.fs" "$d/oracle/OracleTests.fs"
      sed -e "s#LENDING_HOST_PROJECT_PATH#$d/src/$HOST_PROJECT#" -e "s#__SRC_ROOT__#$d/src#g" "$SEALED/oracle/Oracle.fsproj" > "$d/oracle/Oracle.fsproj"
    else
      cp "$SEALED/oracle/$T/InitialOracleTests.fs" "$d/oracle/"
      refs=""; while read -r p; do refs+="    <ProjectReference Include=\"$d/src/$p\" />"$'\n'; done < <(cd "$d/src" && find src -name '*.fsproj' | LC_ALL=C sort)
      python3 -I -c 'import sys; t=open(sys.argv[1]).read(); print(t.replace("__COMPILE__\n", sys.argv[2]).replace("__REFERENCES__\n", sys.argv[3]), end="")' \
        "$H/oracle-template/Oracle.fsproj" '    <Compile Include="InitialOracleTests.fs" />'$'\n' "$refs" > "$d/oracle/Oracle.fsproj"
    fi
    (cd "$d/oracle" && dotnet test -nologo --logger "trx;LogFileName=o.trx" --results-directory "$d/res" > "$d/out.txt" 2>&1) || true
    trx=$(ls "$d"/res/*.trx 2>/dev/null | head -1)
    [ -n "$trx" ] || { echo "$FX/$T: no trx (build failed?)"; tail -5 "$d/out.txt"; exit 2; }
    python3 -I - "$trx" "$FX/$T" "$OUT" <<'PY'
import json, sys, xml.etree.ElementTree as ET
trx, key, out = sys.argv[1:4]
ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
rows = [(r.get("testName"), r.get("outcome")) for r in ET.parse(trx).getroot().iterfind(".//t:UnitTestResult", ns)]
doc = json.load(open(out))
doc[key] = {"total": len(rows), "superseded": sorted(n for n, o in rows if o != "Passed")}
json.dump(doc, open(out, "w"), indent=2, sort_keys=True)
print(key, len(rows), "superseded:", doc[key]["superseded"])
PY
  done
done
rm -rf "$W"
