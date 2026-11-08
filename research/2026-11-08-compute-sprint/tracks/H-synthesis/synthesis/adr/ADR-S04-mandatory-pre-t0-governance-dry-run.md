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

**Independent check (V2, PARTIALLY VERIFIED).** V2 confirms that governance machinery was the *first* refusal that ended the governed verdict from R8 onward. It does **not** confirm that it was the dominant blocker:
- R8: with valid approvals the ledger is still FAILED (G3, G7, G8 FAIL; 346/613 P0 obligations not run).
- R9: 0/541 executable obligations implemented; the agent stopped at about T+115 by choice.
- R10: several work items never started, plus browser-suite failures.

B's category is also broad: it includes spec contradictions and an SDK incompatibility, not only approval or process records. See matrix X-23. **This ADR therefore claims only that a dry run removes the first point of failure and returns window time. It does not claim the dry run would have produced acceptance.**

**Prevalence.** B ranks this mechanism first: present in 10 of 11 runs, primary cause in 29 of 116 failure events. Track B curated the events with a single analyst, so the counts are ESTIMATES. From R8 on it was the terminal blocker in every run.

**CI data shows the cost.**
- R10 had 88% of CI minutes in failed or cancelled runs (A-F-12).
- R10 commit latency was 2,470 s (A-F-14).
- R10's verification gate had 45 cancelled runs, 20 failed and 1 success (B-F-08; V2 VERIFIED the counts, but 36 of 45 cancellations fit the gate's 40-minute job timeout, so "deadlock" is interpretive).

**Owner readiness is a related gap.** Secrets, Pages, rulesets and approvals were not ready at T0 in 10 of 11 runs (B-F-12, SUPPORTED).

## B2 replay result (2026-11-08, B2-dryrun)

Track B2 ran the dry run retrospectively on T0-era artefacts for R4, R8, R9, R10 and Causa (`B2-dryrun/findings.json`, `results.csv`).

**Catch rate:**
- 4/8 of the brief's blockers were caught. Only 2/8 are robust (R9 MSB1008 and R10 authorize-implementation, reproduced exactly with 55/55 causes).
- On the extended list, 7/11 were caught, 5/11 robustly (B2-F-01, SUPPORTED; small sample, and some matching rules were finalised after first runs).

**Caught:**
- Approvals format, R4 and R8 (B2-F-03).
- Frozen-plan suite commands failing on the pinned SDK, R8 and R9 (B2-F-04).
- R10 authorize-implementation (B2-F-02).
- As a by-product, the FSharp.Core test-assembly skip that hit R8 and R10 (B2-F-05).

**Not caught:**
- R8's command-body and INV-04 contradictions. These are semantic and pass the whole pinned pipeline (B2-F-08).
- The Causa T18↔T20 cycle. It is not present in pre-T0 artefacts (B2-F-07; matrix X-24).
- The R10 gate deadlock, whose causes need hosted CI (B2-F-11).

**Cost:** seconds of tool time per rehearsal, and about 199 s for a full rerun of all replays (B2-F-10, VERIFIED).

DECISION-LOG D-022 narrows B's recommendation on this basis.

## Semantic checks (B3, B4)

- **B3 catches what B2 missed.** B3's preregistered semantic checks catch both R8 semantic blockers in under a second: INV-04 against SM-SAVE (B3-F-01) and the CommandEnvelope without a command body (B3-F-02).
- **B3 settles the Causa cycle.** Its C4 check derives the Causa T18↔T20 cycle from pre-T0 artefacts (B3-F-06, which contradicts B2-F-07). The check is noisy.
- **The tooling already existed.** percepta spec-preflight 0.4.0 reproduces the R8 catches exactly, with 0 control false alarms (B4-F-01). It was built after R8 and pinned for R9.
- **Caveats:**
  - Both tools were designed knowing the answer, and both are lexically tuned. Paraphrased defects evade them (B3-F-03/F-04, B4-F-06/F-07).
  - Indy-init's CI runs spec-preflight without `--catalog`, which drops the carrier rule (B4-F-05).
- **Decisions taken.** DECISION-LOG D-025 and D-029: reuse spec-preflight, and contribute B3's C4 slice-cycle check upstream instead of building a parallel tool (matrix X-26).

## Decision (proposed)

Before any timed run, execute the whole governance pipeline end to end:
- in a throwaway repository;
- with stub implementations;
- using the exact frozen package and lock.

The run is a GO only if all of the following pass:
1. `authorize-implementation` against the real approved plan.
2. Suite preflight: every frozen suite command executes on the pinned SDK.
3. Semantic package checks: percepta spec-preflight run **with `--catalog`**, failing on any blocking section (B4-F-05). Plus a slice-dependency cycle check that follows invariant sources (B3 C4, B3-F-06).
4. The release or acceptance gate, including the trusted job of ADR-S03 once it exists.
5. Approvals in the verifier's exact format, with process rules bound to the target repository.
6. Job time budgets: suite duration against the job cap, which addresses the R10 20-minute cap against a 29-minute suite.
7. Machine-checked owner readiness (B-F-12): secrets, Pages, rulesets and approvals.

No kickoff unless the dry run is GO (compare R7, which started while its audit verdict was NOT READY; KD-001).

## Consequences

**Expected:** mechanical, format and tool-mismatch defects in governance artefacts are found before T0 instead of inside the window. B2 measured this as 2–4 of 8 brief-list blockers, at negligible cost. Semantic package defects stay uncovered and need a separate check: B3-semantic is testing generic semantic checks.

**Costs:**
- Pre-T0 compute and wall time: one full CI cycle plus a stub implementation. This is NOT measured.
- Maintaining the stub implementation.

**Limits:**
- A stub cannot exercise defects that depend on real application behaviour. Persistence invariants (B-F-05) and fake-provider divergence (B-F-06) remain.
- A dry run exercises the gates. It does not make them independent (ADR-S03).

## Evidence

| Finding | Class | Independent check |
|---|---|---|
| B-F-03 | SUPPORTED (B) | V2 PARTIALLY VERIFIED (first blocker yes, dominant blocker no) |
| B2-F-01..F-11 | VERIFIED/SUPPORTED/INCONCLUSIVE (B2) | none; B2 is itself a direct test of this ADR |
| B-F-12 | SUPPORTED (B) | V2 pending |
| B-F-08 | VERIFIED (B) | V2 pending |
| A-F-12, A-F-14 | VERIFIED (A) | V1 VERIFIED A-F-12 (65.6%, range 54–76% by definition); A-F-14 not independently verified |
| C-F-12 | SUPPORTED: a bespoke toolchain changed between runs, so gates were new each time | — |

Files: `B-forensics/findings.json#B-F-03`, `B-forensics/data/event-analysis.json`, `B-forensics/REPORT.md` §5, `A-economics/analysis/ci-overhead.json`. Matrix themes X-08, X-09.

## Open questions

1. ~~What fraction would a stub dry run catch?~~ Answered by B2: 4/8 (robust 2/8). Is a semantic check, such as a model check of state machines against invariants, worth adding? See B3-semantic.
2. The cost is measured as negligible (B2-F-10). The window time saved per caught defect has not been measured. For example, R4's approvals issue was found at T+60 and R8's MSB1008 was fixed at T+94, but downstream effects are not quantified.
3. Should the dry run be a Praxis/Dokimos-native capability, or remain Indy-init tooling (C-F-12, CR-07)?
4. How much acceptance headroom does the dry run buy, given V2's finding that R8–R10 were also far from product-complete (X-23)?
5. B's event curation was done by one analyst. Would a second coder reproduce the "10 of 11 runs" prevalence?
