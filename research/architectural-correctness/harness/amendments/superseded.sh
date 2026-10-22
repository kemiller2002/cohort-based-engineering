#!/usr/bin/env bash
# Amendment A3: initial-oracle tests superseded by each task's follow-up = the InitialOracle tests that FAIL on the
# sealed follow-up-good reference (good overlay, then followup-good overlay, over fixtures/repo). Arm-blind.
#   usage: superseded.sh OUT.json
set -euo pipefail
AC=/home/user/cohort-based-engineering/research/architectural-correctness; SEALED=/home/user/arch001-sealed
export DOTNET_ROOT=/home/user/.tools/dotnet PATH=/home/user/.tools/dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
W=$(mktemp -d); OUT=${1:?out}; echo '{}' > "$OUT"
apply() { cp -r "$1/." "$2/"; [ -f "$1/.delete" ] && (cd "$2" && xargs -a "$1/.delete" rm -f) || true; rm -f "$2/.delete"; }
for T in T1 T2 T3 T4 T5 T6 T7 T8; do
  d="$W/$T"; mkdir -p "$d/src" "$d/oracle"; cp -r "$AC/fixtures/repo/." "$d/src/"
  apply "$SEALED/reference/$T/good" "$d/src"; apply "$SEALED/reference/$T/followup-good" "$d/src"
  for f in $(grep -o 'Compile Include="[^"]*"' "$SEALED/oracle/Oracle.fsproj" | cut -d'"' -f2); do [ "$f" = OracleTests.fs ] || cp "$SEALED/oracle/$f" "$d/oracle/$f"; done
  cp "$SEALED/oracle/$T/InitialOracleTests.fs" "$d/oracle/OracleTests.fs"
  sed "s#LENDING_HOST_PROJECT_PATH#$d/src/src/Lending.Host/Lending.Host.fsproj#" "$SEALED/oracle/Oracle.fsproj" > "$d/oracle/Oracle.fsproj"
  (cd "$d/oracle" && dotnet test -nologo --logger "trx;LogFileName=o.trx" --results-directory "$d/res" > "$d/out.txt" 2>&1) || true
  trx=$(ls "$d"/res/*.trx 2>/dev/null | head -1)
  [ -n "$trx" ] || { echo "$T: no trx (build failed?)"; tail -5 "$d/out.txt"; exit 2; }
  python3 -I - "$trx" "$T" "$OUT" <<'PY'
import json, sys, xml.etree.ElementTree as ET
trx, task, out = sys.argv[1:4]
ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
rows = [(r.get("testName"), r.get("outcome")) for r in ET.parse(trx).getroot().iterfind(".//t:UnitTestResult", ns)]
doc = json.load(open(out))
doc[task] = {"total": len(rows), "superseded": sorted(n for n, o in rows if o != "Passed")}
json.dump(doc, open(out, "w"), indent=2, sort_keys=True)
print(task, len(rows), "superseded:", doc[task]["superseded"])
PY
done
