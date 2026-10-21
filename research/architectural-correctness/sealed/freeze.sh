#!/usr/bin/env bash
# ARCH-001 preregistration freeze (coordinator only): seal the hidden material and write pins.json.
#   usage: freeze.sh   (from any directory; writes research/architectural-correctness/{pins.json,sealed/*})
set -euo pipefail
AC=$(cd "$(dirname "$0")/.." && pwd); ROOT=$(cd "$AC/../.." && pwd)
SEALED=${ARCH001_SEALED_DIR:-/home/user/arch001-sealed}; KEY=${ARCH001_SEAL_KEY:-/home/user/.arch001-sealed-key}
ORDO=${ARCH001_ORDO:-/home/user/.tools/ordo/ordo-linux-x64/ordo}; DOTNET=${ARCH001_DOTNET_ROOT:-/home/user/.tools/dotnet}/dotnet
grep -q "RESULT: PASS" "$AC/fixtures/check-output.txt" || { echo "fixtures/check-output.txt is not a PASS" >&2; exit 2; }
bash "$AC/sealed/seal.sh" "$SEALED" "$KEY" "$AC/sealed" > /dev/null
sha() { sha256sum "$1" | cut -c1-64; }
tree() { (cd "$1" && find . -type f -not -path '*/bin/*' -not -path '*/obj/*' | LC_ALL=C sort | xargs -d '\n' sha256sum | sha256sum | cut -c1-64); }
repo_head() { git -C "$1" rev-parse HEAD; }
jq -n \
  --arg cohort "$(repo_head "$ROOT")" --arg ordo "$(repo_head /home/user/ordo)" --arg praxis "$(repo_head /home/user/praxis)" \
  --arg dokimos "$(repo_head /home/user/dokimos)" \
  --arg ordoBin "$(sha "$ORDO")" --arg ordoVer "$("$ORDO" --version 2>/dev/null | head -1)" \
  --arg dist "$(tree "$AC/verifier/dist")" --arg dll "$(sha "$AC/verifier/dist/archcheck.dll")" \
  --arg policy "$(sha "$AC/verifier/policy/lending.policy.json")" \
  --arg doctrine "$(sha "$AC/fixtures/pack/FOUR-TIER-ARCHITECTURE.md")" --arg packInst "$(sha "$AC/fixtures/pack/LENDING-ARCHITECTURE.md")" \
  --arg fixtureTree "$(sed -n 's/^fixture tree: //p' "$AC/fixtures/check-output.txt")" --arg sealedTree "$(sed -n 's/^sealed tree: *//p' "$AC/fixtures/check-output.txt")" \
  --argjson seal "$(cat "$AC/sealed/SEAL.json")" \
  --arg briefs "$(tree "$AC/harness/briefs")" --arg harness "$(cd "$AC/harness" && ls *.sh *.py | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -c1-64)" \
  --arg agentCfg "$(sha "$AC/harness/agent-config.json")" --arg price "$(sha "$ROOT/research/pricing/anthropic.price-table.json")" \
  --arg analysis "$(cd "$AC/analysis" && ls *.py | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -c1-64)" \
  --arg scoring "$(sha "$AC/scoring-spec.json")" --arg protocol "$(sha "$AC/PROTOCOL.md")" \
  --arg sdk "$("$DOTNET" --version)" --arg claude "$(claude --version | head -1)" \
  --arg order "$(sha "$AC/harness/order.json")" --arg pilot "$(sha "$AC/harness/pilot-order.json")" --arg at "$(date -u +%FT%TZ)" \
  '{schema:"arch001.pins/1", frozenAt:$at,
    repositories:{"cohort-based-engineering (parent of the freeze commit)":$cohort, ordo:$ordo, praxis:$praxis, dokimos:$dokimos},
    tools:{ordo:{sha256:$ordoBin, version:$ordoVer, release:"v1.17.0 ordo-linux-x64.tar.gz sha256 ab9437f5b4c72e86eaf1a25bfa7dc167e548be91ff9112df65bee678c5fb1b5d"},
           archcheck:{distTreeSha256:$dist, dllSha256:$dll}, dotnetSdk:$sdk, claudeCode:$claude, model:"claude-opus-5-5"},
    instruments:{policySha256:$policy, doctrineSha256:$doctrine, lendingArchitectureSha256:$packInst, fixtureTree:$fixtureTree,
                 sealedTree:$sealedTree, seal:$seal, briefsTree:$briefs, harnessScripts:$harness, agentConfigSha256:$agentCfg,
                 priceTableSha256:$price, analysisCode:$analysis, scoringSpecSha256:$scoring, protocolSha256:$protocol,
                 orderSha256:$order, pilotOrderSha256:$pilot}}' > "$AC/pins.json"
cat "$AC/pins.json"
