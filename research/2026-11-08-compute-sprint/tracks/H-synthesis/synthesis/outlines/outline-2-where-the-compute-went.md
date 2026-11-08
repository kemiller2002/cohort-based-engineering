# Outline 2: "Where the compute went: a token and CI audit of a six-lane agent rehearsal"

- **Type:** Engineering blog post.
- **Status:** OUTLINE ONLY. Not cleared for publication.
- **Prerequisites:**
  - V1 verdicts on A-F-12 and A-F-13 (queued).
  - FX-09 reconciles the merge and run counts.
  - Owner decisions on model identifiers and private-repository data (datasets.json globalCaveats).

**Evidence classes:**

| Class | Meaning |
|---|---|
| VERIFIED+IV | Reproduced by the track and by an independent verification track |
| VERIFIED | Reproduced by the track only |
| SUPPORTED | Based on documents or code reading |
| INCONCLUSIVE | Evidence does not settle it |
| NOT TESTED | No one tested it |
| ESTIMATE | A modelled number |

Every USD figure is a list-price **ESTIMATE**: there is no provider bill. Claims marked **[DO NOT STATE]** are tempting framings the evidence does not support.

## Thesis

In the one rehearsal with full telemetry (R8), most tokens were cache reads of a coordinator's growing context. Most wasted CI time came from harness semantics, not from slow tests. Merge friction came from shared tool state rather than shared code.

## 1. Data and method

- R8 used 533.8M tokens across 56 execution records. The total reproduces exactly. **VERIFIED+IV**, A-F-01 / V1.
- Estimated list price: $193.74 using the 5m/1h cache-write split, or $190.51 if all cache writes are priced at the 5m rate. **ESTIMATE**; V1 discrepancy note.
- The total is a lower bound: 8 executions have no transcript and the coordinator's late turns are missing (A-F-01).

## 2. The coordinator

- The coordinator accounts for 44% of tokens and about 32% of estimated cost. Its mean context per request is 3.6 times a task agent's (416,786 vs 116,721 tokens). **VERIFIED+IV**, A-F-03 / V1.
- Cache reads are 98% of tokens and 54% of cost. **VERIFIED**, A-F-04.
- About 48.7k tokens of fixed startup prefix make up roughly 30% of context processed. **ESTIMATE**, A-F-05 (carry model).
- **[DO NOT STATE]** "Capping coordinator context would save 15%." **NOT TESTED**, and contrary evidence exists: VAC-001 continuity was cheaper (matrix X-12; ADR-S05; FX-04).

## 3. CI: two-thirds of minutes in red or cancelled runs

- Across R2–R10, about two-thirds of job-minutes were in failed or cancelled runs. **VERIFIED+IV**, A-F-12 / V1 (65.6%, CI 56.5–71.9%).
  - The figure ranges from 54% to 76% depending on the definition, and is 37–38% excluding R6 and R10.
  - "Red" includes superseded cancellations and successful jobs inside failed runs. **[DO NOT STATE]** "two-thirds of CI was waste".
- Two harness mechanisms explain the outliers, with corroboration from separate data:
  - R6: a per-commit concurrency group combined with `if: always()`, giving 116 of 132 runs cancelled.
  - R10: a 20-minute job cap against a roughly 29-minute browser suite.

  **VERIFIED**, B-F-08 + A-F-12 + A-F-11; matrix X-08.
- Browser suites take 28–51% of step time. Rebuilding the pinned Praxis verifier from source took about 604–607 min, 7.4–8.0% of step time. **VERIFIED+IV**, A-F-13 / V1 PARTIALLY VERIFIED: A's 688 included an unrelated R5 step.
- Caching or fetching the pinned verifier could save about 550 of ~604 minutes. **ESTIMATE**, A2-F-09. The attested release behaves byte-identically (**SUPPORTED**, A2-F-08).
- What reuse would buy, on one F# fixture: a no-op build costs ~4% of a clean build's CPU, and an affected-project test run ~4% of the full suite. **SUPPORTED**, D-F-09, D-F-11. Selection safety is NOT TESTED.
- The billable-minutes figure is a compute proxy. Public repositories are not billed.

## 4. Merge friction is tool state

- 26 of 49 R8 PR merges conflicted, every one only in `.ros` state files. **VERIFIED+IV** at PR level, A-F-07 / V1.
- Replay shows 56 of 60 conflicted R8 merge commits were `.ros`-only. **VERIFIED**, B-F-09.
- **Correction:** at least 4 branch-side merges conflicted in application, test or CI code. **VERIFIED+IV**, B-F-09 / V1.
  - **[DO NOT STATE]** "no application-code conflicts" (matrix X-02).
- A semantic merge driver, on replay, removes every `.ros` conflict:
  - R8: 93% of conflicted merges become clean. R10: 85%.
  - 0 records lost, and `praxis validate` passes on 92/92.
  - It found a real team merge error that dropped a live work item.

  **VERIFIED** (replay only), A2-F-01..F-04. V3 pending. Disclose the v2 ordering amendment.
- **[DO NOT STATE]** "removes all merge conflicts". 9 application-code merges remain (A2-F-04).

## 5. Parallelism

- Task agents used about a third of 6 lanes: mean 1.6–2.2 concurrent depending on window and span source, with a peak of 4 distinct lanes. **VERIFIED+IV** with range, A-F-08 / V1 PARTIALLY VERIFIED.
- The effect of agent count on cost is **NOT TESTED** (A-F-17; FX-06).

## 6. Process instructions

- In controlled pilots (n=3 per arm), a construction protocol used 47–93% more tokens at equal acceptance. **SUPPORTED**, A-F-16.
- Earlier REL-001 results show +35.5% per correct requirement. **VERIFIED+IV**, G-F-08 / V1, with the output-lower-bound caveat.
- Both sit at a ceiling (every arm correct), so a quality benefit is **NOT TESTED** on harder tasks (FX-05).
- The sprint's own matched agent experiment: a governance block added +6.1% tokens and +55% wall time at 12/12 vs 12/12 acceptance (**SUPPORTED**, n=4 per arm, D2-F-02; Holm-adjusted p=0.086 for tokens).
  - Two harder fixtures could not make the ungoverned baseline fail (DECISION-LOG D-027, D-030).
  - **[DO NOT STATE]** "governance has no benefit". The benefit is untested beyond short tasks.

## 7. What we cannot measure yet

- Time waiting for approvals or CI. **NOT TESTED**, A-F-18: `blocked_ms` is 0 everywhere.
- Execution wall time is unreliable. **VERIFIED**, A-F-10.

## 8. Limits section (mandatory)

- A single rehearsal with per-request data.
- List prices only.
- Category assignments are judgement.
- Cross-rehearsal cost-per-unit is not comparable, because the units differ. **INCONCLUSIVE**, A-F-02; matrix X-13.
  - **[DO NOT STATE]** "cost per requirement rose from R3 to R8".

## Figures (candidates)

- Stacked bar: R8 tokens and cost by bucket.
- Line: coordinator vs median task-agent context over time.
- Bar: red or cancelled CI share per rehearsal, with R6 and R10 annotated by mechanism.
