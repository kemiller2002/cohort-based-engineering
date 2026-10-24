#!/usr/bin/env bash
# ARCH-002 instrument freeze (coordinator only): seal the hidden material and write pins.json (adapted from ARCH-001
# sealed/freeze.sh; see PROVENANCE.md).   usage: freeze.sh
set -euo pipefail
X=$(cd "$(dirname "$0")/.." && pwd); ROOT=$(cd "$X/../../.." && pwd)
SEALED=${ARCH002_SEALED_DIR:-/home/user/arch002-sealed}; KEY=${ARCH002_SEAL_KEY:-/home/user/.arch002-sealed-key}
ORDO=${ARCH002_ORDO:-/home/user/.tools/ordo/ordo-linux-x64/ordo}; DOTNET=${ARCH002_DOTNET_ROOT:-/home/user/.tools/dotnet}/dotnet
for f in lending-brownfield summa; do grep -q "RESULT: PASS" "$X/fixtures/$f/check-output.txt" || { echo "fixtures/$f/check-output.txt is not a PASS" >&2; exit 2; }; done
bash "$X/sealed/seal.sh" "$SEALED" "$KEY" "$X/sealed" > /dev/null
mv "$X/sealed/MANIFEST.sha256" /home/user/.arch002-sealed-manifest.sha256   # published with the results only
sha() { sha256sum "$1" | cut -c1-64; }
tree() { (cd "$1" && find . -type f -not -path '*/bin/*' -not -path '*/obj/*' -not -path '*/__pycache__/*' | LC_ALL=C sort | xargs -d '\n' sha256sum | sha256sum | cut -c1-64); }
jq -n --arg cohort "$(git -C "$ROOT" rev-parse HEAD)" --arg ordo "$(git -C /home/user/ordo rev-parse HEAD)" \
  --arg ordoBin "$(sha "$ORDO")" --arg dist "$(tree "$X/verifier/dist")" --arg dll "$(sha "$X/verifier/dist/archcheck.dll")" \
  --arg f1 "$(tree "$X/fixtures/lending-brownfield")" --arg f2 "$(tree "$X/fixtures/summa")" \
  --arg p1 "$(sha "$X/fixtures/lending-brownfield/policy.json")" --arg p2 "$(sha "$X/fixtures/summa/policy.json")" \
  --arg harness "$(tree "$X/harness")" --arg analysis "$(tree "$X/analysis")" --arg protocol "$(sha "$X/PROTOCOL.md")" \
  --argjson seal "$(cat "$X/sealed/SEAL.json")" --arg sdk "$("$DOTNET" --version)" --arg claude "$(claude --version | head -1)" \
  --arg cal "$(sha "$X/harness/calibration-order.json")" --arg pilot "$(sha "$X/harness/pilot-order.json")" --arg at "$(date -u +%FT%TZ)" \
  '{schema:"arch002.pins/1", frozenAt:$at, repositories:{"cohort-based-engineering (parent of the freeze commit)":$cohort, ordo:$ordo},
    tools:{ordo:{sha256:$ordoBin, version:"1.17.0"}, archcheck:{version:"0.2.0", distTreeSha256:$dist, dllSha256:$dll}, dotnetSdk:$sdk, claudeCode:$claude,
           models:["claude-opus-5-5","claude-sonnet-5-5"]},
    instruments:{fixtureTrees:{"lending-brownfield":$f1, summa:$f2}, policies:{"lending-brownfield":$p1, summa:$p2}, seal:$seal,
                 harnessTree:$harness, analysisTree:$analysis, protocolSha256:$protocol, calibrationOrderSha256:$cal, pilotOrderSha256:$pilot}}' > "$X/pins.json"
cat "$X/pins.json"
