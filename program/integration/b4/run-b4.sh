#!/usr/bin/env bash
# B4 integration run for the invoice vertical slice (IMPLEMENTATION-PLAN.md B4).
# Usage: run-b4.sh ORDO_CHECKOUT DOKIMOS_CHECKOUT [OUT_DIR]
# Both checkouts must be on a revision that contains the experiments (ordo#105, dokimos#53 or later).
set -euo pipefail
ORDO=${1:?ordo checkout}; DOK=${2:?dokimos checkout}; OUT=${3:-$(pwd)/out}
O="$ORDO/experiments/verified-construction"
mkdir -p "$OUT"
echo "== 1-3: Ordo admission, construction, build and tests"
(cd "$O" && ./run.sh)
echo "== 4: Dokimos provenance audit and invariant oracle against the built Invoice.Slice.dll"
set +e
(cd "$DOK/experiments/rule-provenance" && ./run.sh integrate \
   --ordo-src "$O/src/Invoice.Slice" --source "$O/src/Invoice.Slice.PaymentsService" \
   --trace "$O/out/construction-trace.json" \
   --dll "$O/src/Invoice.Slice/bin/Release/net10.0/Invoice.Slice.dll" \
   --root "$O" --out "$OUT/provenance-audit.json")
code=$?
set -e
echo "== 5: evidence bundle"
sha() { sha256sum "$1" | cut -d' ' -f1; }
cat > "$OUT/evidence-bundle.json" <<JSON
{
  "schema": "echelon.slice-evidence",
  "schemaVersion": "0.1",
  "ordoRevision": "$(git -C "$ORDO" rev-parse HEAD)",
  "dokimosRevision": "$(git -C "$DOK" rev-parse HEAD)",
  "handoffSha256": "$(sha "$O/fixture/handoff.json")",
  "traceSha256": "$(sha "$O/out/construction-trace.json")",
  "auditSha256": "$(sha "$OUT/provenance-audit.json")",
  "dokimosExitCode": $code
}
JSON
cat "$OUT/evidence-bundle.json"
exit $code
