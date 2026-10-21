# REL-001 run-02: four-arm results and final report

Status: **complete** (2026-10-20). Run-01 is reported separately in [`REPORT.md`](REPORT.md) and is unchanged.

**Sources:**
- Protocol: [`protocol/run-02.md`](protocol/run-02.md), preregistered at a00eba0, with amendments A1–A3.
- Gate: [`gate/gate-report.json`](gate/gate-report.json).
- Preregistered analysis: [`run-02/analysis/analyze-run02.fsx`](run-02/analysis/analyze-run02.fsx). Its sha256 `19d4f0ea…` is unchanged since preregistration, and it produces [`run-02/analysis/results.json`](run-02/analysis/results.json).
- Exploratory aggregates: [`run-02/analysis/exploratory-run02.jq`](run-02/analysis/exploratory-run02.jq), which produces [`run-02/analysis/exploratory-results.json`](run-02/analysis/exploratory-results.json).

Every number below comes from one of those committed files. **Confirmatory** marks a preregistered hypothesis. **Exploratory** marks anything computed after the data were seen.

## What was compared
| Arm | What the agent received |
|---|---|
| **A**, bare Claude | the requirement, the repository and minimal safe-operation instructions |
| **B**, Claude + directives | A plus the Echelon directives pack (`run-02/directives/`, identical bytes in B, C and D) |
| **C**, original Echelon | Praxis 3.16.0, Ordo 1.17.0 and Dokimos 0.6.0, with the run-01 A2 protocol (claim, then `validate-run`, then `complete-verified`), plus the directives pack |
| **D**, optimized Echelon | Praxis 3.17.0 and Dokimos 0.7.0 in attested mode: host verifier daemon, claim, `work verify`, then `work complete-verified --id --token`. Plus the directives pack. |

**Held constant across arms:** model (`claude-opus-5-5`, confirmed from every transcript), agent configuration, tools, the 45-minute budget, visible acceptance tests, hidden oracle and wrapper prompt.

**Tasks:** 9 tasks in 4 builder-assigned categories:
- simple: U1, U8
- moderate: U4, U5
- complex: U7, U9
- adversarial: U2, U3, U6

**Design:**
- 22 (task, replicate) blocks × 4 arms = **88 confirmatory trials**, run in the preregistered randomized order (seed 20261020).
- A pilot of 5 trials ran first and is excluded from analysis.
- 0 exclusions: no X1 setup failures, no X2 model mismatch, no X4 oracle contamination and no X6 host-file tampering. No run came near the X5 budget; the longest was 166 s.

## Amendments (all before any arm comparison was computed)
- **A1** (pilot): in U6, a tool-recorded completion is credited only to its claimant. Before this fix, a clone that fetched the other agent's completion showed a false duplicate.
- **A2** (after trial 9): wall time now ends at the last agent transcript event, not at the orchestrator's `finish` call. Every trial was re-scored, and only wall time changed.
- **A3** (after trial 11, at the experimenter's request): from trial 13, the four arms of a non-U6 block ran **concurrently**.
  - Cost, tokens, correctness and reliability are unaffected.
  - Time metrics were measured under up to 4-way CPU contention, shared equally by every arm in a block. Their pooled absolute values are exploratory.
  - The record is in `run-02/observations/concurrency.json`.

## Primary outcome (confirmatory)
**Total estimated model cost (USD, F5 price table) per correctly completed requirement**, pooled. U6 is excluded (R8), and U2 counts as one unit when the agent correctly stopped and named both decisions (R6, R9).

| Arm | Correct units | Cost per correct requirement | Tokens per correct requirement | Tokens excluding cache reads, per correct requirement |
|---|---|---|---|---|
| A, bare | 39/39 | **$0.1147** | 221,834 | 14,360 |
| B, directives | 39/39 | $0.1390 | 264,538 | 17,643 |
| C, original Echelon | 39/39 | $0.1520 | 305,190 | 18,644 |
| D, optimized Echelon | 39/39 | $0.1555 | 304,458 | 19,373 |

Every arm completed every requirement correctly. First-pass correctness was also 17/17 in every arm; the 3 U2 runs per arm have no first pass. So the arms differ only in cost.

## Hypotheses (confirmatory; paired percentile bootstrap over blocks, 10,000 resamples)
| | Question | Comparison | Result (cost per correct requirement) | 95% interval | Decision |
|---|---|---|---|---|---|
| **H1** (RQ4) | Does protocol optimization lower cost? | D vs C | +2.3% | −4.8% to +12.1% | **not distinguishable** (tokens: −0.2%, −8.4% to +10.4%) |
| **H2** (RQ5) | Is optimized Echelon cheaper than bare Claude? | D vs A | **+35.5%** | +24.9% to +49.5% | **D higher** |
| H2, simple | | D vs A | +64.7% | +27.5% to +110.5% | D higher |
| H2, moderate | | D vs A | +24.2% | +15.6% to +34.4% | D higher |
| H2, complex | | D vs A | +25.8% | +17.2% to +36.9% | D higher |
| H2, adversarial | | D vs A | +39.1% | +21.1% to +68.9% | D higher |
| **H3** (RQ1) | On simple tasks, is bare Claude cheaper than original Echelon? | A vs C | **−26.2%** | −28.6% to −23.8% | **A lower** |
| **H4** (RQ2) | Do directives alone change outcomes? | B vs A | correct rate: 0 difference | 0 to 0 | not distinguishable |
| | | B vs A | cost: **+21.2%** | +14.5% to +28.4% | **B higher** |

- Every result keeps the same decision with U2 left out (`withoutU2` in `results.json`).
- Per-category intervals rest on 4–6 blocks each.

**H5 (RQ3), per-category ordering** (cost per correct requirement, lowest first; descriptive, with intervals in `results.json`):

| Category | Order | A | B | C | D |
|---|---|---|---|---|---|
| simple | A < B < C < D | $0.191 | $0.234 | $0.258 | $0.314 |
| moderate | A < B < D < C | $0.120 | $0.140 | $0.167 | $0.149 |
| complex | A < B < D < C | $0.088 | $0.100 | $0.112 | $0.111 |
| adversarial | A < C ≈ B < D | $0.130 | $0.174 | $0.172 | $0.181 |

**Reliability non-inferiority** (preregistered: D no more than C on each count): **met.**

| Arm | Invalid completions accepted | Escaped defects | Duplicate owners (U6) | Lost work |
|---|---|---|---|---|
| A | 0 | 0 | 2 | 0 |
| B | 0 | 0 | 2 | 0 |
| C | 0 | 0 | 1 | 0 |
| D | 0 | 0 | **0** | 0 |

## U6: two agents, one item (exploratory; reported separately per R8)
Two agents ran at once on the same item, in two clones of one bare remote. Each arm had 2 runs.

**Shared outcomes:**
- Every run in every arm ended with **exactly one implementation on main**.
- There was no lost work and no conflicting completions in any run.
- In A and B, agents coordinated through git: the agent that lost the push race discarded its own commit.

**The difference is in what the losing agent reported** (the R8 duplicate-owner definition):
- **A and B, 4/4 runs:** the losing agent still reported `OUTCOME: completed`.
- **C, 1/2 runs:** Praxis refused the second claim (`PRX.CLAIM.HELD`) in both runs. In one run the refused agent still reported completed.
- **D, 0/2 runs:** the refused agent stopped `blocked` both times.
- The D pilot behaved the same way as D.

**Cost for the two runs:** A $1.27, B $1.84, C $1.85, D $2.15.

**Interpretation:** claims change the *agents' account* of ownership, not the code that lands. With n=2 per arm this is suggestive only.

## Mechanism attribution (RQ6; exploratory arm contrasts)
| Mechanism | Measured value in run-02 | Status |
|---|---|---|
| **Directives** (B − A) | **+$0.024 per correct requirement (+21%, confirmatory H4)**, with no change in correctness. Directives agents also ran more full test suites: 2.09 vs 1.41 per run. | **Measured: a cost with no benefit on these tasks** |
| **Orchestration** (claims, in the C − B bundle) | The bundle C − B adds +$0.013 per correct requirement. Claims refused the second owner in 4/4 C and D U6 runs. Duplicate-owner reports were 1 of 4 runs with claims, against 4 of 4 without (exploratory, n=2 per arm). | **Unresolved** as a separate cost. The benefit is suggestive and exploratory. |
| **Constructibility validation** (Ordo admission, in the bundle) | In all 12 U2 runs, every arm (including bare Claude) caught the contradiction in the prose and stopped before admission was invoked. Admission never fired in an agent trial. Deterministic experiment B still shows 0/11 invalid contracts accepted. | **Unresolved** in agent trials. Its value is shown only against direct adversarial inputs. |
| **Independent verification** (in the bundle) | There were 0 escaped defects in every arm, including A with no verification. All U3 runs passed the uneven-split oracle in all arms. Verification commands averaged about 10.2 s (C) and 10.8 s (D) per run, mostly test execution. Its proven value is **forgery resistance** (gate cases C3b and GATE-A1–A4), not quality. | **No measured quality benefit.** The security benefit is shown deterministically. |
| **Protocol optimization** (D − C) | **+$0.0035 per correct requirement, not distinguishable (confirmatory H1).** It adds attested receipts and exact completion identity (19/19) at no measurable extra cost. It did **not** remove test runs: 1.955 per run in both C and D. | **Neutral on cost; positive on guarantees** |

The four arms bundle orchestration, constructibility and independent verification together in C − B. This design cannot isolate them, and the report does not credit them individually.

## The nine REL-001 questions
1. **Can agents still forge successful completion?**
   - **In attested mode, no.** On the released binaries (Praxis 3.17.0, Dokimos 0.7.0) the following are all refused:
     - the C3b forgery;
     - self-signed receipts;
     - wrong-key receipts;
     - stale and replayed receipts.
   - Evidence: gate P4, cases GATE-A1–A4, and experiment C attested (0/3 accepted).
   - **In non-attested mode, yes:** GATE-3 and C3b are accepted. This is REL-GATE-003, filed in Praxis intake (P1).
   - In run-02 no agent attempted it: 0 invalid completions were accepted and 0 X6 tampering was detected.
2. **Can two agents successfully own the same work item?**
   - **Not at the tool level.** Experiment A recorded 0 duplicate active owners on 3.16.0 and on 3.17.0.
   - In U6, Praxis refused the second claim in 4/4 C and D runs.
   - Without claims (A and B), both agents claimed ownership in their reports in 4/4 runs, though only one implementation landed.
3. **Are invalid decisions rejected before completion?**
   - **Yes, deterministically:** experiment B accepted 0 of 11 invalid cases on 3.16.0 and on 3.17.0.
   - In the U2 agent trials the question never arose: in all 12 runs (3 per arm), the agent stopped first and named both conflicting decisions.
4. **Does completion reference the exact verified commit?**
   - **In D, yes, 19/19.** Every D completion's HEAD differs from the verified commit only in `.ros/`, and every D worktree ended clean (F3).
   - C has no identity check. Its agents often added post-verification `.ros` commits, which is the run-01 F3 finding.
5. **How many redundant test runs were eliminated?**
   - **None measurably in run-02.** D and C both averaged 1.955 test runs per run.
     - D: 1.09 by the agent plus 0.86 by the verifier.
     - C: 1.09 by the agent plus 0.86 through `validate-run`.
   - F4 removed command arguments and duplicate validation paths, not test executions.
   - Run-01's 2.17 runs per treatment trial used different tasks and is not comparable.
6. **How much did token consumption change?**
   - D vs C: **−0.2%** tokens per correct requirement (95% CI −8.4% to +10.4%). Not distinguishable.
   - D vs bare Claude: **+37.2%** (+25.0% to +52.1%).
7. **Did verified completion rates improve?**
   - **No.** Every arm completed 39/39 requirement units correctly, with 17/17 first-pass correct.
   - The task set again hit a ceiling. No arm made an error for verification to catch.
8. **What is the measured cost of reliability?**
   - **+35.5%** model cost per correct requirement for optimized Echelon over bare Claude (95% CI +24.9% to +49.5%).
   - By category: simple +65%, moderate +24%, complex +26%, adversarial +39%.
   - Breakdown of the cost (exploratory): directives +$0.024, the orchestration and verification bundle +$0.013, optimization +$0.003 per correct requirement.
   - Verification also adds about 10–11 s of command time per run.
9. **Is the optimized workflow ready for wider adoption?**
   - **Not as a default.** It is ready as an **opt-in assurance mode** where its guarantees are needed:
     - concurrent agents on one backlog;
     - forgery-resistant, audited completion on protected branches.
   - For those uses the gate is in place, but REL-GATE-003 must be fixed first.

## Is Echelon more efficient than simply giving Claude a requirement?
**No.** In every category, bare Claude reached the same correctness for less. Each category's conclusion stands on its own:

- **Simple (U1, U8):** bare Claude was cheapest: −26% against original Echelon (confirmatory H3) and −39% against optimized Echelon. No arm made an error.
- **Moderate (U4, U5):** bare Claude was cheapest. D cost +24% more with no quality difference.
- **Complex (U7, U9):** bare Claude was cheapest. D cost +26% more.
  - In all 12 U7 runs, every arm found and followed the design note that resolves the stated ambiguity.
  - Every arm got all 3 U9 requirements right.
- **Adversarial (U2, U3):** bare Claude was cheapest. D cost +39% more.
  - Every arm handled the contradiction (U2) and the hidden uneven-split rounding (U3) correctly.
  - U6 coordination is the only place Echelon showed a behavioural difference. It is reported separately and is exploratory.

## Recommendation for the default engineering workflow
1. **Default: give Claude the requirement and the repository, and let it work and run its own tests.**
   - Leave out the directives pack. On these tasks it cost +21% with no measured benefit.
2. **Use optimized Echelon (D) as a policy-selected assurance mode, not a default.** Select it when any of these holds:
   - more than one agent may take the same work item;
   - completion must be forgery-resistant evidence, for example release gating, audited or protected branches, or compliance work;
   - the requirement carries decisions that must be machine-admitted.
3. **Do not enable `requireVerifiedCompletion` globally.** The F6 gate stays closed for a global default.
   - Gate item 6 (run-02 reviewed) is now satisfied, and its recommendation is this section.
   - Gate item 5 (representative applications) remains open.
   - REL-GATE-003 must be fixed before any repository enables non-attested verified completion.
4. **Adaptive routing: justified by what the work requires, not by task category.**
   - The preregistered condition was met: confirmatory differences exist in every category. But they all point the same way (A cheapest), so category-based routing to Echelon is **not** justified.
   - What the evidence supports is a deterministic rule keyed on declared properties of the work: concurrency risk and required assurance level. It should not be keyed on inferred difficulty.
   - Filed as Praxis intake `2026-10-20-REL-ROUTE-001-deterministic-workflow-routing.md`.

## Decision: **MODIFY**
- **Keep:**
  - claims (0 duplicate active owners; 4/4 second claims refused in U6);
  - attested verification (forgery refused in attested mode);
  - exact completion identity (19/19);
  - contract admission (0/11 invalid accepted).
  
  These remove failure classes that bare Claude does not protect against: forged evidence, concurrent ownership and inadmissible decisions.
- **Change:**
  - Make those mechanisms opt-in by declared need rather than the default path. On single-agent bounded tasks they cost +35% (CI +25% to +50%) with no measured quality gain.
  - Drop the directives pack from the default prompt.
  - Fix REL-GATE-003 so that verified completion implies attestation.
- **Not REJECT:** the reliability mechanisms work as designed, and their cost is moderate and predictable.
- **Not ADOPT:** the evidence shows no efficiency or quality benefit for the default single-agent workflow.

## Threats to validity
- **Ceiling effect.** No arm made an error on any task, so this experiment measures the cost of reliability mechanisms, not their benefit.
  - Categories are builder-assigned. The observed failure rate was 0 for every task, so "complex" and "adversarial" were not hard for this model.
  - A benefit could appear on harder tasks, longer horizons or weaker models. That remains untested.
- **One codebase, one model.** All tasks are in one small F# ledger repository, and every trial used one model.
- **U6 sample size.** U6 has n=2 per arm, so its coordination findings are exploratory.
- **Time metrics.** Under A3, trials 13–88 ran block-concurrently. From trial 22, a Praxis development agent also shared the host at `nice 19` (see `concurrency.json`). Time figures are exploratory, while cost and tokens are unaffected.
- **Tokens.**
  - Transcript output tokens are a lower bound (run-01 A4).
  - Sub-agents of one orchestrator share the prompt cache, equally across arms.
  - Cost is **estimated** from the F5 price table ($4 / $20 / $0.20 / $5 or $8 per MTok for input / output / cache read / cache write).
- **Directives agents stepping outside their workspace.** Two directives-arm agents moved the visible acceptance file outside their workspace to take a baseline (see `run-02/observations/protocol-notes.md`). This is not oracle contamination; the runs were scored as they were.

## Cost of this implementation (measured from this session's transcripts, deduplicated by message id)
| Component | Messages | Input | Output (lower bound) | Cache write | Cache read |
|---|---|---|---|---|---|
| Orchestrator | 964 | 2,135 | 527,923 | 3,245,796 | 378,713,009 |
| Trial agents (102, pilot + confirmatory) | — | 1,940 | 21,290 | 3,960,814 | 53,940,457 |
| Other sub-agents (29: implementation, review, harness, Praxis) | — | 3,428 | 22,485 | 21,567,104 | 319,786,451 |

- **Estimated cost at F5 prices:** about $305–$392. The range depends on whether cache writes were 5-minute or 1-hour; the transcripts do not say. About $29 of this is the 88 confirmatory trials (the numerators in `results.json`). The rest is building F1–F6, the harness and the experiment itself.
- **Not included:** this covers this session only. Run-01 and earlier sessions are not included.

## Follow-ups
- **Praxis intake REL-GATE-003 (P1):** verified completion must imply attestation, and every completion should be labelled attested or unattested. The fix is in progress.
- **Praxis intake REL-ROUTE-001:** deterministic workflow routing by declared concurrency and assurance needs.
- **Cohort-side, for any run-03:** use tasks with a non-zero bare-agent failure rate, so that the benefit of verification can be measured and not just its cost.
