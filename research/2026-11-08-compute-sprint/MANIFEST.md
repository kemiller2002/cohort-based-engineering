# Echelon Foundry compute-utilization research sprint — 2026-11-08

**Status:** COMPLETE (research). Final report: [FINAL-REPORT.md](FINAL-REPORT.md). Pushes to the public remote held since 20:37 pending owner decision (D-054). **Started:** 2026-11-08T13:35:13-05:00 (America/Indiana/Indianapolis). **Hard deadline:** 2026-11-08T23:00:00-05:00.
**Research Director:** Claude Code cloud session (identity per `get_session`; model identifiers are kept out of repository artifacts).
**Branch:** `claude/echelon-compute-sprint-nov8-bkaw2t` in `kemiller2002/cohort-based-engineering`.

## Why this repository

cohort-based-engineering is the cross-system Echelon program repository: it owns `program/` (CURRENT-STATE, EXPERIMENTS,
EXECUTION-STATE) and `research/` (VAC, ARCH, REL experiments, consolidation through Rehearsal 3). It uses the plain-file
Praxis lifecycle and so does not require the .NET runtime that was absent at session start. `research-documents` (private)
holds frozen raw evidence and was not chosen because it is the archival store, not the active program. No new repository
was created (DECISION-LOG D-001).

## Environment at start (measured)

| Item | Value |
|---|---|
| Machine | Linux 6.18 cloud container, 4 vCPU, 15 GiB RAM, ~30 GiB writable |
| node | v22.23.4 |
| python | 3.13.18 |
| git | 2.43.0 |
| dotnet | **absent at start**; .NET SDK 10.0.402 installed to /root/.dotnet at ~13:40 EST via dot.net/v1/dotnet-install.sh (D-004) |
| Playwright/Chromium | pre-installed (/opt/pw-browsers/chromium) |
| gh CLI | search API only; GitHub MCP for other operations |
| Compute quota | **not observable** from inside the session; no token meter is exposed to the Director (RESOURCE-BUDGET.json) |

Starting revisions of every checked-out repository: [inventory/starting-revisions.tsv](inventory/starting-revisions.tsv).
Additional public Echelon repositories (dokimos, conditor, forma, limen, etc.) are cloned read-only under `/home/user/ext/`
by tracks as needed; their revisions are recorded in each track's output.

## Layout

| File | Purpose |
|---|---|
| [RESEARCH-QUEUE.md](RESEARCH-QUEUE.md) | Scored, dynamic research queue |
| [RESOURCE-BUDGET.json](RESOURCE-BUDGET.json) | Quota, allocation, observed consumption |
| [AGENT-REGISTRY.json](AGENT-REGISTRY.json) | Every worker, parent, scope, status |
| [EXPERIMENT-REGISTRY.json](EXPERIMENT-REGISTRY.json) | Every experiment with ID and status |
| [EVIDENCE-INDEX.json](EVIDENCE-INDEX.json) | Finding → artifact traceability |
| [FINDINGS.md](FINDINGS.md) | Classified findings (VERIFIED / SUPPORTED / INCONCLUSIVE / CONTRADICTED / NOT TESTED) |
| [DECISION-LOG.md](DECISION-LOG.md) | Director decisions and priority changes |
| [CHECKPOINT.md](CHECKPOINT.md) | Rolling checkpoint log |
| [FINAL-REPORT.md](FINAL-REPORT.md) | Executive and per-track reports (A–H) |
| `tracks/<X>/` | Per-track working outputs, raw data, scripts |

## Governance boundaries

Read-only against all repositories except this sprint directory. No production deployment, no merges to protected branches,
no secrets disclosed, no third-party security testing, no spend beyond the existing allocation. Experimental material is
labelled EXPERIMENTAL. Findings are not public claims.
