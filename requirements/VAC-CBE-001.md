---
id: VAC-CBE-001
title: Continuity operating model and the next continuity experiments
status: implemented
version: 1.0.0
owners: [cohort-based-engineering]
created: 2026-10-22
updated: 2026-10-22
research_area: verified-agent-continuity
priority: P2
related_documents: [VAC-001, VAC-002]
tags: [continuity, operating-model, experiments, preregistration]
provenance:
  contributions:
    CTB-20261022-775b20e1:
      operations: [created]
      at: 2026-10-22T20:20:42.455Z
      actor:
        kind: agent
        id: anthropic/claude-code
        provider: anthropic
        model: unknown
        runtime: claude-code
      reason: "Derived from input VAC-CBE-001 (runtime-free; this repository has no Praxis executable)"
    CTB-20261022-b8b147ef:
      operations: [approved]
      at: 2026-10-22T20:20:42.455Z
      actor:
        kind: human
        id: kemiller2002
      reason: "Owner approved the input (merged via PR #14) and all recommendations in engineering-recommendations.md"
derived_from: [INPUT-29db4a38cf86a56b]
---

# VAC-CBE-001: continuity operating model and the next continuity experiments

**Source.** Input `2026-10-21-VAC-CBE-001-continuity-operating-model-and-next-experiments.md`, claim
`INPUT-29db4a38cf86a56b`, SHA-256 `0240ebea52a00a1ccf3f33f21fd4df7827ac9a4f4915336c67effd0e685a2fe5`. The claim
record is `.praxis/processed/INPUT-29db4a38cf86a56b/claim.json` once completed, and
`.praxis/processing/INPUT-29db4a38cf86a56b/` before that.

**Finding it rests on.** VAC-001 (`research/verified-agent-continuity/`, `research/experiments/VAC-001/`).

**Lifecycle note.** This repository has no Praxis runtime (`./praxis`). The input was therefore claimed, derived and
completed through the plain-file lifecycle in Praxis `docs/fallback-reconciliation.md` ("Input documents"). Provenance
is recorded in the Praxis front-matter form, under contribution keys (`CTB-…`), because no execution exists. No
GitHub issues were opened.

## Requirements and dispositions

| ID | Requirement | Disposition | Evidence |
|---|---|---|---|
| **VAC-CBE-001-R1** | In `docs/operating-model.md`, state that a cohort's agent continues across its successive work items by default and restarts only on events: context pressure, a change of repository or ownership, or a gate failure that repair does not fix. Cite VAC-001 with its scope | **Implemented** | [`docs/operating-model.md`](../docs/operating-model.md) §4 |
| **VAC-CBE-001-R2** | Agents must record any extension of a rule to behaviour no requirement names as an assumption or open question, never as settled | **Implemented** | [`docs/operating-model.md`](../docs/operating-model.md) §5 and §2; README principle 3 |
| **VAC-CBE-001-R3** | Design R-EXP-1: a fixture whose baseline fails (the four candidate kinds); preregister H3, H5 and H6 against it | **Implemented (design); trials not run** | [`r-exp-1-protocol.md`](../research/verified-agent-continuity/r-exp-1-protocol.md), committed before any trial |
| **VAC-CBE-001-R4** | Run chains of ≥ 24 changes past the compaction threshold, in K1, with Layer 3 reviewers from another model family, to test H2 and the compaction questions | **Design implemented; run not authorized.** A confirmatory run needs an explicit owner spending ceiling | [`r-exp-2-protocol.md`](../research/verified-agent-continuity/r-exp-2-protocol.md), committed before any trial |

**Acceptance evidence named by the input:**

- **An operating-model diff citing VAC-001.** Present: `docs/operating-model.md` is new.
- **Preregistered protocols for R-EXP-1 and R-EXP-2, committed before any trial.** Present: commit `17a0cbc`. No
  VAC-003 or VAC-004 trial exists.
- **Canonical work items created by Praxis with provenance linking to this input.** Satisfied only in the
  runtime-free form: this record (`derived_from: [INPUT-29db4a38cf86a56b]`) plus the claim's derivations. Native
  Praxis work items need a Praxis instance in this repository, and there is none.

## Engineering recommendations applied here (approved with the input)

| Recommendation | Where |
|---|---|
| R-OPS-1 (continue by default; event-driven restart) | Operating model §4 (= R1) |
| R-OPS-2 (no full Echelon protocol on simple chains purely for reliability) | Operating model §6 |
| R-OPS-3 (extensions are assumptions, never settled) | Operating model §5 (= R2) |
| R-ORDO-1, R-ORDO-2 (computed "verified"; agent records enter as `proposed`) | Operating model §3, as method rules. Enforcement is Ordo's (follow-up) |
| R-EXP-1, R-EXP-2 | The two protocols (= R3, R4) |
| R-EXP-3 (no token totals as a cost proxy) | Operating model §7 |
| "Not recommended now" | Operating model §8 |

## Follow-ups owned by other repositories (not edited here)

| Recommendation | Owner | Ask |
|---|---|---|
| R-ORDO-1 | Ordo | Decision records name the independent checks that cover them. `verified` is computed, never asserted |
| R-ORDO-2 | Ordo | Agent-written decision records enter as `proposed`. Only an authorizing actor or an independent check accepts them |
| R-PRAXIS-1 | Praxis | Per-work-item usage windows, continuation index, prompt size, compactions and restart trigger, when one agent session spans successive work items outside a group |
| R-OPS-1 routing | Praxis | Route the continuity evidence into the DF-ROS-2026-A053 / PRAXIS-PLAN-11 review of grouped execution by default |
| R-DOK-1 | Dokimos | Chained re-verification of every earlier accepted requirement, with isolated per-requirement checks |
