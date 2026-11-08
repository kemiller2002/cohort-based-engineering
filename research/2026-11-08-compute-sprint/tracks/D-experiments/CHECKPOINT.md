# Track D checkpoint log

## 2026-11-08T13:43:18-05:00 — CP-D-01
- Re-analysis tooling (reanalysis/stats.py, reanalyze.py, test_stats.py; 18 unit tests pass) and output reanalysis/outputs/reanalysis.json.
- VAC-001 cost contrasts, VAC-002 P3 H1/H4, A021 and A024 totals recomputed from raw records; all match published values (details in REPORT.md once written).
- No Agent/subagent tool in this worker's tool set -> workstream 2 falls back to deterministic verification-cost experiments.
- Next: classify claims (findings.json), then design SPR-D-02.. deterministic experiments.

## 2026-11-08T13:50:38-05:00 — CP-D-02
- research-documents checked (Director update): holds only narrative summaries for VAC-001/VAC-002 (FINDINGS.md, VAC-002-P3 md); raw data used is in cohort-based-engineering and praxis; no claim marked INCONCLUSIVE for missing data.
- Protocols for confirmatory SPR-D-03/04/05 + COMMON.md preregistered and committed before any confirmatory run; plans/ frozen; tooling/analyze_bench.py frozen (10 tooling tests pass).
- Exploratory pilot SPR-D-02 (1 clean build: 58.3 s wall, 78.9 s CPU, load 7.8) done; raw in raw/SPR-D-02-pilot.jsonl.
- REPORT.md will be delivered in the final reply text (harness refuses subagent report files; Director instruction).
