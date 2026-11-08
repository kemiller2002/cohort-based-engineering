# Track B (forensics) checkpoints

## CP-B-01 (~13:55 EST)
- Read prior consolidation (CBE 2026-10-24), Indy-init REHEARSAL-003..006-RESULTS, R7/R8/R9/R10 and causa FINAL-REPORTs, R2/R3/R4 reports.
- Fetched read-only GitHub Actions run lists for indy-init-rehearsal-001..010 (3,222 runs) into raw/actions/ via scripts/fetch_runs.sh.
- Gaps: causa Actions API not reachable (session not attached; no push access requested); private repos research-documents, causa-acceptance-r10, Indy-init-audits not clonable.
- Next: ci_metrics script + tests, events.jsonl, findings.

## CP-B-02 (~14:10 EST)
- Private repos now readable: research-documents@b372a7f (R1 RESULT/ERRATA folded in), indy-init-audits@10aeded (R7 readiness audit, R6 provenance), causa-acceptance-r10@e1e7966 (only README on main; 116 live-probe branches dated 2026-11-06 from ls-remote).
- Full clones of shallow R3/R4/R5/R6/R8 under /home/user/ext/full for merge replay.
- Tooling: ci_metrics.py, merge_conflicts.py, events_tool.py (+20 unit/integration tests, all passing).
- events.jsonl (135 records), taxonomy.json, data/ci-metrics.json, data/merge-conflicts.json, data/event-analysis.json.
- Verified: R6 imported R5 app (99/99 source files identical); R2 historical ledger recomputes INVALID; R5 conflict list contains all 7 baseline conflicting merges.
- Note: REPORT.md cannot be written by subagents (harness); its content goes in the final reply.
- Next: findings.json, rehearsal-summary.csv.

## CP-B-03 (final data, ~14:00 EST)
- findings.json: 16 findings (5 VERIFIED, 9 SUPPORTED, 2 INCONCLUSIVE). rehearsal-summary.csv regenerated. events.jsonl 135 records.
- Added B-F-16: R1 R-21 confirmed from Actions (RC2-RC5 deploy/accept runs failed).
- data/revisions.tsv records every revision used.
- Gaps: causa Actions runs (API needs push attachment, not requested); causa-acceptance-r10 contents beyond branch list; SDE-Engineering-Trial-1/2 and holiday-list unreadable (not needed for this track); token data left to Track A.
- REPORT.md content delivered in the final reply (harness forbids subagent report files).
