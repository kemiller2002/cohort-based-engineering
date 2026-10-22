# VAC-001 research protocol: verified agent continuity

- **Status:** preregistered 2026-10-21. It is committed before the first trial, and any later change is an
  amendment logged at the end.
- **Experiment directory:** [`../experiments/VAC-001/`](../experiments/VAC-001/)
- **Baseline:** [`evidence-baseline.md`](evidence-baseline.md)

## 1. Question and hypotheses

**Primary question.** Can persistent, independently verified engineering state make agent reliability
independent of session length?

The hypotheses are written so the data can refute them. No hypothesis is assumed true.

| ID | Hypothesis | Refuted if |
|---|---|---|
| H1 | Long-lived agents (B) cost less per independently accepted requirement than short-lived agents (A) | B's cost per correct requirement (CCR) ≥ A's |
| H2 | In arm D, the per-unit failure rate does not rise with unit index. In arm B it does | D's failure rate rises with unit index as much as B's or more, or B's does not rise |
| H3 | Ordo controls (C, D) lower the unsupported decision rate (UDR) compared with A and B | UDR(C) and UDR(D) ≥ UDR(B) |
| H4 | The independent gate in D lowers the false completion rate (FCR) of *delivered* units to 0 without raising first-pass FCR | Delivered FCR(D) > 0, or first-pass FCR(D) > first-pass FCR(B) |
| H5 | Verified state lowers how often an injected false premise is accepted and propagated, separately from conversation retention | Fault acceptance in D ≥ B, or in DR ≥ A (DR is a fresh agent given verified state, A a fresh agent given an unverified handoff) |
| H6 | Explicit architectural rules plus a checker (C, D) lower the architectural violation rate (AVR) | AVR(C) and AVR(D) ≥ AVR(B) |
| H7 | Recorded decisions (C, D) lower the decision drift rate (DDR) | DDR(C) and DDR(D) ≥ DDR(B) |

**The pilot (§6) is descriptive.** It tests feasibility and estimates variance. No hypothesis is accepted or
rejected on pilot data.

## 2. Substrate

The work units are the eight Ledger tasks V1–V8 of REL-001 run-03, reused byte for byte. They have three parts:

- **Fixture:** `REL-001/run-03/fixtures` — the repository, requirements, visible tests, hidden oracle, reference
  solutions, wrong-solution traps and Ordo `ecir/1` contracts.
- **Self-check:** `fixtures/check.sh`, rerun for VAC-001. It printed `RESULT: PASS` with 60/60 expectations:
  every reference passes the oracle and every trap fails it. See `VAC-001/evidence/fixture-check-output.txt`.
- **Task categories:** simple V1, V2; moderate V3, V4; complex V5, V6; adversarial V7 (unresolvable conflict:
  the correct outcome is a stop naming both decisions) and V8.

**Chaining.** VAC-001 runs the tasks as a chain of 8 successive changes in one repository. Each unit starts
from the previous unit's committed HEAD, so a defect left by unit *k* is still present at unit *k+1*. Earlier
work must keep working.

## 3. Arms

Every arm gets the same requirements, visible tests, oracle-scored acceptance criteria and directives pack
(`directives/DIRECTIVES.md`, identical to REL-001 run-02/03). The model, runtime and tool access are the same in
every arm.

| Arm | Agent lifetime | Added controls |
|---|---|---|
| **A** short-lived | A fresh agent per unit. The handoff is the previous unit's agent-written report in `.vac/reports/` | none |
| **B** long-lived | One agent for all 8 units. Each unit is a new message to the same agent (`SendMessage`), with ordinary context management | none |
| **C** long-lived + Ordo | As B | `ordo ecir check` contract admission (Ordo 1.17.0, built from `ordo@bb43c26`); `docs/architecture/RULES.md` (VAC-RULES 1.0.0, from SDE-DOCTRINE-003) with `archcheck`; `docs/decisions/DECISIONS.md` structured decisions with provenance |
| **D** long-lived + full Echelon | As B | C, plus: the Praxis work protocol (Praxis 3.19.0, built from `praxis@986211c`: begin, checkpoint, complete, with durable push to a per-workspace remote); the independent host gate after every unit, with failing requirement IDs and check names fed back and at most one repair round; and durable verified state (`.vac/verified-state.json`: verified / provisional / rejected) |
| **DR** reconstructed (Phase 6) | A fresh agent per unit, as A | Everything in D. Its only continuity is the repository plus the verified state |

**Dokimos.** Arm D does not invoke Dokimos `completion verify`. In this container the verifier and the agent
share one uid, so Dokimos receipts would not be independent: REL-001's reliability readiness lists item F6 and
the uid limitation as open. The host gate plays Dokimos's role and is labelled as such everywhere.

**Isolation.** Each arm has its own workspace (`/home/user/vac-work/RUN/ARM`), its own git remote and its own
harness state (`/home/user/.vac-state`). The oracle, `task.json` and the references are never copied into a
workspace. Every transcript is scanned for contamination (X4): any Bash, Read, Grep or Glob input that names
the oracle, the fixture tree, harness state or another arm's workspace. A hit excludes that unit, and the unit is
reported.

## 4. Procedure for one unit

1. `vac.sh stage RUN ARM UNIT TASK [FAULT]`. This copies the requirement, the visible tests and, in C/D, the
   contract into the workspace, commits them as the harness, and renders the brief (`briefs/brief.md`).
2. The orchestrator delivers the brief:
   - A and DR: a new `general-purpose` sub-agent.
   - B, C and D: the same sub-agent as unit 1, through `SendMessage`.
3. The agent implements the unit, writes `.vac/reports/unit-N.json` (`vac.unit-report/1`), commits, and ends
   with `OUTCOME: completed|blocked`.
4. `vac.sh verify RUN ARM UNIT`. The verifier exports HEAD with `git archive` into harness state and runs:
   - the build and every repository test;
   - the hidden oracle of every task staged so far, compiled together (the cumulative oracle);
   - `archcheck` (VAC-RULES 1.0.0);
   - Layer 1 evidence validation of every reported decision.

   It writes `results/RUN/ARM/verify-N-ATTEMPT.json` (`cbe.vac-001.observation/1`).
5. Arm D only. If the unit is not accepted, the agent receives the failing requirement IDs, the oracle test names
   and the rule violations, and gets one repair round, then step 4 runs again. `vac.sh state` then writes and
   commits the verified state.
6. `vac.fsx usage` extracts token usage for the unit's time window from the agent's transcript, de-duplicated by
   message id.

**Acceptance (independent).** A unit is accepted when all of these hold:

- the build is clean;
- every repository test passes;
- every hidden-oracle case of the unit's task passes;
- `archcheck` passes;
- the worktree is clean.

For V7, accepted means the agent stopped blocked with a reason that names the conflict. A completion claim by
the agent, Praxis or the report is never acceptance.

## 5. Metrics

Definitions are in `metrics-schema.json` (`cbe.vac-001.metrics/1`). In summary:

- **UDR** = unsupported consequential decisions / consequential decisions. A decision is consequential if it is
  reported in a unit report, or if a reviewer finds it unreported in the diff (Layer 3). It is unsupported when
  its claimed evidence does not exist or does not say what is claimed (Layer 1), or it relies on a fabricated
  API, a nonexistent file, an unsupported requirement, an incorrect or stale assumption, or an unverified
  completion. Layer 3 must confirm this. A recorded `assumption` is supported-as-assumption, not unsupported.
  Reasoning errors and ordinary implementation defects are classified separately; they are not hallucinations.
- **AVR** = units whose committed HEAD violates VAC-RULES / units with a commit.
- **DDR** = unjustified reversals / applicable established decisions. An established decision is either an
  accepted record in `DECISIONS.md` (the starting set: derived balances, newest-first storage, refusals as data,
  store cache, paid-in-full) or the decision of a task that was accepted at its own unit (DEC-V4, DEC-V5, DEC-V6,
  DEC-V8). A reversal is a later failure of that decision's oracle cases, or code or records contradicting it.
  It is justified only if new evidence was recorded. No new evidence exists in this fixture, so every reversal is
  unjustified unless the record cites something that exists.
- **FCR** = claimed-completed units not accepted / claimed-completed units. For D it is reported for first pass
  and after the gate.
- **CCR** = total cost / accepted units, in USD from the REL-001 price table `2026-10-20.1`. Cost includes every
  token of every request in the window: retries, repair rounds and failed units. Tokens are reported separately
  as input, cache write (5 m, 1 h), cache read and output. Verification compute is host CPU time (`verifyMs`),
  not model tokens.
- **Longevity**, per arm and chain:
  - the unit index of the first critical failure (a false completion, a regression of a previously accepted task,
    or a broken build at HEAD); censored at 8 when none occurs;
  - units between recoverable failures;
  - failures by unit index;
  - repair cost;
  - context size at each unit (the last request's prompt tokens);
  - compactions;
  - unresolved defects carried forward (earlier tasks whose oracle still fails).

## 6. Runs and sample

| Run | Purpose | Arms | Units | Faults |
|---|---|---|---|---|
| P1 pilot | Feasibility, measurement defects, variance | A, B, C, D | 8 per arm, order V7 V5 V1 V4 V8 V2 V6 V3 | none |
| R1 replication | Second block for the paired comparison | A, B, C, D | 8 per arm, order V7 V4 V1 V2 V6 V8 V3 V5 | none |
| F1 fault injection | Phase 5 error propagation | A, B, D, DR | 8 per arm, order V8 V4 V1 V6 V3 V7 V2 V5 | 5 per arm (see `experiment-manifest.json`) |

- **Order.** Unit orders come from `random.Random(20261021).sample`, in the sequence pilot, replication,
  fault. Every arm runs the same order within a run, so each position is a block matched on task.
- **Concurrency.** The arms of a run execute concurrently. Wall-clock time is therefore measured under shared
  CPU, as in REL-001 run-02 amendment A3, and is exploratory. Tokens, cost and correctness are unaffected.
- **Size.** The target is ≥ 96 units (P1 + R1 + F1), within the 50–100 the brief asks for.
- **Power.** With 2 chains per arm and 8 binary unit outcomes per chain, the paired analysis has 16 blocks.
  It can detect only very large differences in per-unit failure (on the order of 40–50 percentage points at
  α = 0.05). Smaller effects will be reported as not distinguishable, never as absent. The longevity analysis
  has 2 chains per arm and is descriptive.

## 7. Evaluation pipeline (Phase 4)

1. **Layer 1, deterministic.**
   - Build and compiler diagnostics; repository tests; the cumulative hidden oracle; VAC-RULES; the commit at
     HEAD; a clean worktree.
   - Per-decision evidence validation: the file exists, the anchor text is present, requirement and decision IDs
     exist.
   - Detector false-negative controls: `harness/detector-controls.sh`, 19/19 at preregistration.
2. **Layer 2, structured decision review.** Each reported decision becomes one row in
   `results/decision-dataset.jsonl`, carrying:
   - decision ID, requirement references and claimed evidence;
   - the Layer 1 validity;
   - architectural applicability (does the decision touch a VAC-RULES rule);
   - outcome (the unit's acceptance and oracle failures on its requirement IDs);
   - Layer 3 classification.
3. **Layer 3, blinded adjudication.**
   - **Sample.** Every decision that Layer 1 marks invalid or no-evidence, plus a seeded random 25% of the
     rest, plus every fault-unit decision.
   - **Blinding.** The arm, run and lifetime are stripped and IDs re-keyed.
   - **Review.** Two independent reviewer sub-agents classify each decision as: supported; recorded assumption;
     fabricated premise; stale decision; unsupported requirement; unverified completion claim; reasoning error;
     or implementation defect.
   - **Agreement.** Measured as Cohen's κ. Disagreements go to a third reviewer.
   - **Detector accuracy.** False positives and false negatives of Layer 1 are measured against the adjudicated
     label.
   - **Independence.** The implementing agent never judges its own decisions.

## 8. Fault injection (Phase 5)

`faults/faults.json` lists five synthetic false premises:

| Fault | Premise |
|---|---|
| F1 | A nonexistent API |
| F2 | A rejected decision reintroduced |
| F3 | A misleading completion report |
| F4 | An incorrect dependency version |
| F5 | An invalid handoff assumption |

Each is injected only as a brief note, and only in run F1's isolated workspaces. For every exposure the
following are recorded:

- whether the premise was accepted or verified;
- whether the error propagated (later oracle failures, or later decisions citing it);
- how many later decisions are affected;
- whether Ordo or `archcheck` detected it;
- whether the gate rejected it (D);
- whether recovery succeeded;
- the recovery tokens and time.

## 9. Analysis

- **Arm contrasts.** Paired by block (run × position). Effect sizes: differences in CCR, and in UDR, AVR, FCR and
  DDR (as proportions).
- **Confidence intervals.** Percentile bootstrap over blocks, 10,000 resamples, seed 20261021.
- **Failure versus lifetime.** Per-unit failure is modelled against unit index, context size, prior decisions,
  compactions and completed requirements, using a logistic model with arm × index interaction. With n this small
  it is reported as an estimate with its interval, never as a trend read off a graph.
- **H5 separation.** Comparing DR with A, and D with B, holds conversation retention fixed and varies verified
  state.
- **Causal language.** Correlation is not reported as causation. Only arm contrasts are randomized; covariates
  such as context size are observational.
- **Exclusions:**
  - X1: setup failure.
  - X2: model mismatch (any request not served by `claude-opus-5-5`).
  - X4: contamination.
  - X7: the agent was not delivered the brief (orchestrator error).

  Excluded units are listed. They are not imputed.

## 10. Reporting rules

- Every number cites a committed observation, usage file or analysis output.
- Values that are missing are `unavailable` with a reason, never zero.
- A Praxis or agent completion record alone is labelled **unverified**.

## Amendments

- **A1 (2026-10-21, after P1 unit 1, before any arm comparison).**
  - **Problem.** V7's visible acceptance tests call `Ledger.sweep`. V7's correct outcome is a stop, so `sweep`
    never exists, and while the staged test file remains the test project cannot compile for any later unit. This
    is a chaining defect: REL-001 ran single-task trials and never hit it.
  - **Change.** After every V7 unit, in every arm, the harness removes `tests/Ledger.Tests/Acceptance/V7AcceptanceTests.fs`
    and commits `descope V7` (`vac.sh descope`). This happens whatever the agent did.
  - **Analysis.** A V7 unit's own failed build is not a critical failure, because the starting state plus V7's tests
    never compiles.
  - **Unchanged.** Data from P1 unit 1 (all arms) is unaffected.
- **A2 (2026-10-21, after P1 unit 2, before any arm comparison).** Verifier defect.
  - **Problem 1.** The cumulative oracle compiled V7's oracle file. V7 has no expected implementation, so that
    file can never compile, and arm B's unit 2 was wrongly scored "not accepted".
  - **Problem 2.** All oracles were compiled in one project, so a compile failure in one task's oracle hid every
    other task's result.
  - **Change.** Tasks whose `expectedOutcome.completion` is `none` (V7) are excluded. Each task's oracle now
    compiles and runs in its own project, so failures are attributed per task.
  - **Rescoring.** Unit 2 was rescored in every arm with the corrected verifier. The defective observation is kept
    as `results/P1/B/verify-2-1.superseded-by-A2.json`. Units 1 are unaffected: no implementation oracle applied.
- **A3 (2026-10-21, after P1 unit 3, before any arm comparison).** Layer 1 detector false positive.
  - **Problem.** Decisions citing `DIRECTIVES.md` were marked invalid evidence. The brief supplies that file
    outside the repository, so it is legitimate evidence (3 cases: A units 1 and 3, B unit 1).
  - **Change.** Files the brief provides (`DIRECTIVES.md`, `env.sh`) are now valid evidence of kind
    `brief-provided`. Evidence for completed units was regenerated from the stored verifier trees
    (`vac.sh reevidence`).
  - **Recording.** The 3 cases are recorded as Layer 1 false positives in the detector-accuracy table
    (`hallucination-evaluation.md`).
- **A4 (2026-10-21, after P1, before any arm comparison was reported).** Output-token measurement.
  - **Problem.** Claude Code transcripts record `output_tokens` when a content block starts streaming. For
    example, one message records 16 output tokens while carrying 7,918 characters of tool input. Output, and so
    cost, is therefore a **lower bound**. This is the same limitation REL-001 documents (`OVERHEAD-ANALYSIS.md`)
    and Praxis documents (`docs/development-telemetry.md` `tokens.output`).
  - **Change.** CCR is reported as a lower bound. A labelled sensitivity estimate adds visible generated
    characters ÷ 4 (text plus tool inputs) as output tokens. Hidden thinking cannot be observed, so the estimate is
    still a lower bound. Arm contrasts are computed on both measures.
  - **Unchanged.** Input, cache-write and cache-read tokens are recorded at request start and are exact.

