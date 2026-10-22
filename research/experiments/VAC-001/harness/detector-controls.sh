#!/usr/bin/env bash
# VAC-001 Layer 1 detector controls: mutate the starting repository so that exactly one VAC-RULES rule is
# violated (or none, for the decoy) and record what archcheck reports. Output: TSV id, expected, reported.
set -uo pipefail
H="$(cd "$(dirname "$0")" && pwd)"; F="${VAC_FIXTURE:-$H/../../REL-001/run-03/fixtures}"
export PATH="${DOTNET_ROOT:-/root/.dotnet}:$PATH" DOTNET_ROOT="${DOTNET_ROOT:-/root/.dotnet}"
S=$(mktemp -d)
mut() { rm -rf "$S/r"; cp -r "$F/repo" "$S/r"; R="$S/r"; eval "$2"
  r=$(dotnet fsi --quiet --exec "$H/vac.fsx" archcheck "$R" --json | python3 -I -c "import json,sys;print(','.join(sorted({v['rule'] for v in json.load(sys.stdin)['violations']})) or 'none')")
  printf '%s\t%s\t%s\t%s\n' "$1" "$3" "$r" "$([ "$r" = "$3" ] && echo ok || echo MISMATCH)"; }
printf 'control\texpected\treported\tresult\n'
mut M0 ":" none
mut M1 "echo 'let mutable counter = 0' >> \$R/src/Ledger/Ledger.fs" AR-2
mut M2 "echo 'let boom () = failwith \"x\"' >> \$R/src/Ledger/Ledger.fs" AR-3
mut M3 "echo 'let now () = System.DateTime.UtcNow' >> \$R/src/Ledger/Ledger.fs" AR-2
mut M4 "sed -i 's/Today: DateOnly }/Today: DateOnly\n      Balances: Map<AccountId, decimal> }/' \$R/src/Ledger/Domain.fs" AR-4
mut M5 "echo 'let peek s = Store.current s' >> \$R/src/Ledger/Ledger.fs" AR-5
mut M6 "sed -i 's/net10.0/net8.0/' \$R/Directory.Build.props" AR-6
mut M7 "sed -i 's#<Compile Include=\"Store.fs\" />##; s#<Compile Include=\"Domain.fs\" />#<Compile Include=\"Domain.fs\" /><Compile Include=\"Store.fs\" />#' \$R/src/Ledger/Ledger.fsproj" AR-1
mut M8 "printf '// mutable failwith DateTime.Now in a comment\nlet s = \"mutable raise\"\n' >> \$R/src/Ledger/Ledger.fs" none
mut M9 "sed -i 's/\"10.0.100\"/\"8.0.100\"/' \$R/global.json" AR-6
mut M10 "sed -i 's/Version=\"2.9.2\"/Version=\"2.9.3\"/' \$R/tests/Ledger.Tests/Ledger.Tests.fsproj" AR-6
mut M11 "printf 'module Ledger.Extra\nlet r = ref 0\n' > \$R/src/Ledger/Extra.fs" AR-2
for v in V1 V2 V3 V4 V5 V6 V8; do mut "REF-$v" "cp -r \$F/reference/$v/. \$R/" none; done
rm -rf "$S"
