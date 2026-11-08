#!/usr/bin/env bash
# Regenerates data/ from the read-only clones. Usage: tools/run.sh
set -euo pipefail
T="$(cd "$(dirname "$0")/.." && pwd)"
python3 -I "$T/tools/test_archgraph.py"
python3 -I "$T/tools/archgraph.py" --repos-root /home/user/ext \
  --repos praxis ordo dokimos aegis vigila tutela vitium fides conditor iter arca percepta limen forma forma-studio folio \
          specula signal mercatus echelon-registry observer census summa chrona tekmerion strata armamentarium \
          echelon-diagnostic-framework echelon-engineering-system echelon-foundry causa visual-engineering communication-engineering \
  --extra /home/user/Indy-init /home/user/indy-init-rehearsal-010 \
  --registry /home/user/ext/echelon-registry \
  --approved-set /home/user/ext/echelon-registry/sets/echelon-current/1.37.0.json \
  --latest "$T/data/latest-releases.json" --out "$T/data"
