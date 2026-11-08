# V1-verification checkpoint

Worker V1-001 (independent verifier). Outputs: `verdicts.json`, `scripts/` (own code, tests in `scripts/tests`), `data/` (own recomputation outputs).

| Claim | Status | Verdict |
|---|---|---|
| A-F-01 | done | VERIFIED |
| A-F-03 | done | VERIFIED |
| A-F-08 | done | PARTIALLY VERIFIED |
| A-F-07 | done | PARTIALLY VERIFIED (app-code conflicts found branch-side) |
| A-F-12 | done | VERIFIED (sample) |
| A-F-13 | done | PARTIALLY VERIFIED (about 607 min, not 688) |
| A-F-11 | done | VERIFIED (sample) |
| G-F-07 | done | VERIFIED |
| G-F-08 | done | VERIFIED (output tokens lower bound caveat) |
| G-F-10 | done | VERIFIED |

Tests: `python3 -I scripts/tests/test_v1lib.py`

## Reproduction (from this directory; outputs in data/)
- `python3 -I scripts/verify_r8_tokens.py /home/user/indy-init-rehearsal-008 /home/user/indy-init-rehearsal-003 /home/user/cohort-based-engineering/research/pricing/anthropic.price-table.json data/r8-recompute.json`
- `git clone --no-local /home/user/indy-init-rehearsal-008 /home/user/sprint-scratch/V1/r8; python3 -I scripts/replay_merges.py /home/user/sprint-scratch/V1/r8 /home/user/indy-init-rehearsal-008/evidence/telemetry/merges.jsonl data/r8-merge-replay.json`
- `python3 -I scripts/fetch_ci_sample.py data/ci-sample-100 100 20261108` (and `data/ci-sample 40 20261108`) then `analyze_ci_sample.py`, `poststrat_verifier.py`, `queue_ci.py`
- `python3 -I scripts/verify_rel001.py /home/user/cohort-based-engineering/research/experiments/REL-001/run-02/observations <price table> data/rel001-run02-recompute.json`
- Tests: `python3 -I scripts/tests/test_v1lib.py && python3 -I scripts/tests/test_analyze.py`

## Process notes
- One read-only `git fetch` of praxis commit aa7c7ca was run by mistake in /home/user/praxis (adds objects and FETCH_HEAD; no refs or worktree changed). All later Praxis reads used the scratch clone /home/user/sprint-scratch/V1/praxis.
- The Actions API was read with curl GET through the session proxy (the gh CLI token was invalid). Same read-only endpoints as the MCP tools.
