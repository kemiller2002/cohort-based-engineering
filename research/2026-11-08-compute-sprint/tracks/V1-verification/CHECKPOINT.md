# V1-verification checkpoint

Worker V1-001 (independent verifier). Outputs: `verdicts.json`, `scripts/` (own code, tests in `scripts/tests`), `data/` (own recomputation outputs).

| Claim | Status | Verdict |
|---|---|---|
| A-F-01 | done | VERIFIED |
| A-F-03 | done | VERIFIED |
| A-F-08 | done | PARTIALLY VERIFIED |
| A-F-07 | done | PARTIALLY VERIFIED (app-code conflicts found branch-side) |
| A-F-12 | pending | |
| A-F-13 | pending | |
| A-F-11 | pending | |
| G-F-07 | done | VERIFIED |
| G-F-08 | done | VERIFIED (output tokens lower bound caveat) |
| G-F-10 | done | VERIFIED |

Tests: `python3 -I scripts/tests/test_v1lib.py`
