# ADR-S04: Mandatory pre-T0 governance dry run

- **Status:** Proposed — EXPERIMENTAL evidence
- **Date:** 2026-11-08
- **Drafted by:** Track H (H-001), from Track B prevention-plan item 1. Track B2 (dry-run replay) is the pending test. This is a candidate, not a decision.
- **Paths:** relative to `research/2026-11-08-compute-sprint/tracks/`.

## Context

**Governance defects surface inside the timed window.** Gates, frozen plans, suite commands, approval formats, process rules and interface contracts had been checked only on synthetic fixtures, or not at all, before T0. Their defects then appeared inside the 420-minute window (B-F-03, SUPPORTED):

| Run | Defect found inside the window |
|---|---|
| R4 | Approvals in the wrong schema, found at T+60 |
| R8 | Live suites never ran until T+94 (MSB1008); the frozen IF41-DOMAIN has no command body; INV-04 contradicts SM-SAVE |
| R9 | The frozen suite commands cannot execute on the pinned SDK |
| R10 | `authorize-implementation` refused the real approved plan with 55 causes, having been tested only on a synthetic plan; the governed gate then deadlocked (45 of 66 runs cancelled) |
| Causa | A T18↔T20 cycle in the slice plan; process rules bound to the R10 repository |

**Prevalence.** B ranks this mechanism first: present in 10 of 11 runs, primary cause in 29 of 116 failure events. Track B curated the events with a single analyst, so the counts are ESTIMATES. From R8 on it was the terminal blocker in every run.

**CI data shows the cost.**
- R10 had 88% of CI minutes in failed or cancelled runs (A-F-12).
- R10 commit latency was 2,470 s (A-F-14).
- R10's verification gate had 45 cancelled runs, 20 failed and 1 success (B-F-08).

**Owner readiness is a related gap.** Secrets, Pages, rulesets and approvals were not ready at T0 in 10 of 11 runs (B-F-12, SUPPORTED).

## Decision (proposed)

Before any timed run, execute the whole governance pipeline end to end:
- in a throwaway repository;
- with stub implementations;
- using the exact frozen package and lock.

The run is a GO only if all of the following pass:
1. `authorize-implementation` against the real approved plan.
2. Suite preflight: every frozen suite command executes on the pinned SDK.
3. A dependency-cycle check on the slice plan.
4. The release or acceptance gate, including the trusted job of ADR-S03 once it exists.
5. Approvals in the verifier's exact format, with process rules bound to the target repository.
6. Job time budgets: suite duration against the job cap, which addresses the R10 20-minute cap against a 29-minute suite.
7. Machine-checked owner readiness (B-F-12): secrets, Pages, rulesets and approvals.

No kickoff unless the dry run is GO (compare R7, which started while its audit verdict was NOT READY; KD-001).

## Consequences

**Expected:** the governance-artefact failure class is found before T0 instead of inside the window. The benefit is an ESTIMATE; B2 is measuring how many of the recorded defects a dry run would have caught.

**Costs:**
- Pre-T0 compute and wall time: one full CI cycle plus a stub implementation. This is NOT measured.
- Maintaining the stub implementation.

**Limits:**
- A stub cannot exercise defects that depend on real application behaviour. Persistence invariants (B-F-05) and fake-provider divergence (B-F-06) remain.
- A dry run exercises the gates. It does not make them independent (ADR-S03).

## Evidence

| Finding | Class | Independent check |
|---|---|---|
| B-F-03 | SUPPORTED (B) | V2 pending; B2 replay pending |
| B-F-12 | SUPPORTED (B) | V2 pending |
| B-F-08 | VERIFIED (B) | V2 pending |
| A-F-12, A-F-14 | VERIFIED (A) | V1 queued for A-F-12 |
| C-F-12 | SUPPORTED: a bespoke toolchain changed between runs, so gates were new each time | — |

Files: `B-forensics/findings.json#B-F-03`, `B-forensics/data/event-analysis.json`, `B-forensics/REPORT.md` §5, `A-economics/analysis/ci-overhead.json`. Matrix themes X-08, X-09.

## Open questions

1. What fraction of the recorded in-window governance defects would a stub dry run have caught? B2 is testing this. Reconsider this ADR when B2 reports.
2. Does a dry run cost less than the window time it saves? Neither cost nor saving is measured.
3. Should the dry run be a Praxis/Dokimos-native capability, or remain Indy-init tooling (C-F-12, CR-07)?
4. B's event curation was done by one analyst. Would a second coder reproduce the "10 of 11 runs" prevalence?
