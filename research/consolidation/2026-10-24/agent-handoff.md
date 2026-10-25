# Agent handoff: engineering consolidation, 2026-10-24

Read this first. It is enough to continue without repeating the investigation.

## Verified findings (each cites its evidence in engineering-findings.md)

1. **Rehearsal 3 ran and is NOT ACCEPTED; its remediation is BLOCKED.** It used the read-only scope on echelon-current
   1.25.0 (Praxis 3.16.0). The candidate was deployed and verified at T+118.9 min. What blocks acceptance is owner
   decisions, Percepta and preservation, not code. (R3 `docs/REHEARSAL-003-REPORT.md`, `docs/REHEARSAL-003-REMEDIATION-REPORT.md`)
2. **Rehearsal 2 declared itself accepted**, at 721.2 min, with writes, using its own tool. Under Indy-init's ledger contract the computed verdict is **not** ACCEPTED: the ledger is INVALID and P0 ADRP-016 is NOT_RUN (Indy-init PR #13).
3. **The read-only scope was the lead agent's own decision,** marked `accepted` (DF-CAUSA-2026-0001, actor
   `claude-code-lead`), against P0 write requirements EXT-DATA-006 and -009.
4. **The approved set 1.26.0 cannot attest completion.** It has Praxis 3.20.0 and no Dokimos 0.7.0.
5. **Guidance in the brief removes architecture violations** (ARCH-002, Supported). Contracts and enforcement add
   nothing measurable to that; enforcement costs +7%.
6. **Executable authorization is harmful** (P3). **Typed records do not reduce errors** and cost more (P3 arm D).
   **Structured handoffs** are not cheaper (A024).
7. **A continuous agent is cheapest** (VAC-001). A fresh independent reviewer caught what the lead missed (R3,
   observational).
8. **Verification selection and checkpoint CI are Contradicted** at the preregistered thresholds (EXP-2).
9. **Overclaiming is the most frequent recurring failure,** with 5+ instances across R1–R3.

## Artifacts written in this session

| File | Repository |
|---|---|
| `research/consolidation/2026-10-24/engineering-findings.md` | cohort-based-engineering |
| `research/consolidation/2026-10-24/engineering-improvement-priorities.md` | cohort-based-engineering |
| `research/consolidation/2026-10-24/indy-init-readiness.md` | cohort-based-engineering |
| `research/consolidation/2026-10-24/next-experiments.md` | cohort-based-engineering |
| `research/consolidation/2026-10-24/agent-handoff.md` (this file) | cohort-based-engineering |
| `program/CURRENT-STATE.md` §7 (corrections) | cohort-based-engineering |
| `.praxis/inbox/documents/2026-10-24-REQ-PRES-001-tamper-evident-requirements-preservation.md` | praxis |
| `.praxis/inbox/documents/2026-10-24-R3-PRX-001-qualification-defects.md` | praxis |
| `.praxis/inbox/documents/2026-10-24-REG-PAIR-001-capability-pairing-constraints.md` | echelon-registry |
| `.praxis/inbox/documents/2026-10-24-SD-1-REL-registry-distribution-scaffold-release.md` | conditor (new intake directory, the documented canonical path) |
| `.praxis/inbox/documents/2026-10-24-LIM-HTTP-001-http-cache-mode.md` | limen |
| `.praxis/inbox/documents/2026-10-24-DOK-SDK-001-managed-workflow-global-json.md` | dokimos |

Each intake was written to `.praxis/inbox/documents/`, not `input-documents/`. That follows the program rule in
CURRENT-STATE §1: legacy `input-documents/` folders are never written. The commits and their merge state are recorded
in `program/EXECUTION-STATE.md` under "Consolidation session 2026-10-24".

**Documented is not implemented.** None of these requirements is implemented. No production code was changed.

## Important locations

- **Rehearsal 3 evidence:** kemiller2002/indy-init-rehearsal-003
  - `docs/`
  - `research/` (defect analysis, independent review, hardening §7, preservation root cause)
  - `evidence/acceptance/LEDGER.md`
  - `research/decisions/DF-CAUSA-2026-0003--operator-decisions-requested.md`
- **Indy Init plan:** kemiller2002/Indy-init
  - `docs/REQUIREMENTS.md`
  - `docs/REHEARSAL-003-DEFERRED-VERIFICATION-EXPERIMENT.md`
  - `kickoff/indy-init.kickoff.json` (Percepta `required: true`)
  - `tools/validate-acceptance-ledger.py`
  - draft PR #12 (baseline manifest)
- **Release set:** kemiller2002/echelon-registry
  - `profiles/echelon-current.profile.json`
  - `snapshots/echelon-current.catalog.json`
- **Open work elsewhere:**
  - praxis#292 (preservation gate, draft; branch `claude/requirements-preservation-gate`)
  - conditor#108 (SD-1 fix, unreleased)
  - percepta#38 (semantic UI, unreleased)

## Known blockers

| Blocker | Owner |
|---|---|
| Competition scope: are writes P0 in the event? Ratify or reverse DF-CAUSA-2026-0001 | Owner |
| DF-CAUSA-2026-0003 items 2–5 | Owner |
| Percepta: release, or waive in the kickoff manifest | Owner / Percepta |
| Kickoff release set: 1.25.0 (rehearsed) or 1.26.0 (not rehearsed, cannot attest) | Owner (A6a) |
| OD-9 verifier key | Owner |
| No paid experiment budget (OD-1) | Owner |
| This session could not open pull requests (`gh` token invalid); see EXECUTION-STATE for how the commits were delivered | — |

## Work remaining

1. Implement priority item 1 (computed verdict) in Indy-init `tools/` and its CI. This is the cheapest change with the
   largest effect on overclaiming.
2. Triage the six new intakes in their owners' repositories.
3. Run NX-1 ($0) from `next-experiments.md`.
4. After the owner settles scope: design Rehearsal 4 (write path, frozen stack). Do not repeat the read path.
5. Apply EP-02 intake hygiene (still open from EXECUTION-STATE).

## Exact recommended next action

Get the owner's answers to the first four blockers above. These are decisions; no engineering unblocks them. While
waiting, implement the computed verdict in `Indy-init/tools/validate-acceptance-ledger.py`:

- compute ACCEPTED only when every mandatory gate is PASS on one SHA;
- check that each cited evidence path exists at that SHA;
- fail CI when the report's verdict line differs.

Test it against a ledger encoding R3's original results, which must yield BLOCKED, and R2's accepted candidate
`45644a7`. **Done in Indy-init PR #13:** R3 yields BLOCKED. R2 yields INVALID, not ACCEPTED, so a synthetic ledger is the positive control.
