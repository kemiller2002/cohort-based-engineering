# Track B (forensics) checkpoints

## CP-B-01 (~13:55 EST)
- Read prior consolidation (CBE 2026-10-24), Indy-init REHEARSAL-003..006-RESULTS, R7/R8/R9/R10 and causa FINAL-REPORTs, R2/R3/R4 reports.
- Fetched read-only GitHub Actions run lists for indy-init-rehearsal-001..010 (3,222 runs) into raw/actions/ via scripts/fetch_runs.sh.
- Gaps: causa Actions API not reachable (session not attached; no push access requested); private repos research-documents, causa-acceptance-r10, Indy-init-audits not clonable.
- Next: ci_metrics script + tests, events.jsonl, findings.
