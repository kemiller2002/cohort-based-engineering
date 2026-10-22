# ARCH-001 scoring

The machine-readable, versioned specification is [`scoring-spec.json`](scoring-spec.json) (`arch001.scoring-spec/1`,
version 1.0.0). This document explains it. The spec governs if the two disagree. The implementing code is
`harness/score.py` (per trial) and `analysis/analyze.py` (across trials).

## Principle: the treatment does not define correctness

Correctness is fixed before any trial by sources that every arm is scored against identically:

- SDE-DOCTRINE-003 and its Lending instance, `fixtures/pack/LENDING-ARCHITECTURE.md`;
- the Lending app's own decision records, `docs/decisions/DEC-*.md`, which every arm can read;
- the requirements;
- the sealed hidden oracle.

Arm D's development-time verifier runs the same *deterministic* rules that score every arm. That shared use is the
treatment H3 tests, not a scoring bias. Four things keep scoring broader than what D can see:

- the sealed per-task probes;
- the hidden functional oracle;
- the heuristic findings;
- the blinded review.

No rule scores anything that the pack's text does not state. Arm A is scored on the same rules without having seen
the pack. That contrast is H1, and the report says so wherever it presents arm A's architecture results.

## Five dimensions

| Dimension | What is measured | Gate or descriptive |
|---|---|---|
| Functional | R1: all initial-oracle tests at S1. R2: all follow-up-oracle tests plus the regression-labelled initial tests at S2. First-pass correctness. Escaped defects (submit PASS, oracle FAIL). | Gate (acceptance) |
| Architectural | `archcheck` with the full policy plus the sealed task probes. Zero DET findings of severity ≥ 2 counts as acceptance. Also the severity-weighted DET count, new violations in phase 2, HEU findings and the blinded ARC-REV rubric. | Gate (DET ≥ 2); the rest descriptive |
| Decision fidelity | Pass rate of the decision-labelled oracle tests in every arm. T5: conflict refused and DEC-006 preserved. Invalid decisions accepted. ARC-TRC-01 traceability (C and D only). | H2, descriptive |
| Change resilience | Phase-2 cost, files changed and rewritten, rework lines, broken visible tests, regression failures, new violations | H4, descriptive |
| Evidence integrity | Pristine scorer copies. Commit- and tree-bound verdicts. Sealed and encrypted oracle. X4 contamination scan. X-integrity hashes. Harness-side ledger of every submit. | Exclusions |

## Requirement acceptance (the denominator of the primary metric)

A requirement is **accepted** when it is both:

- functionally correct at its phase commit; and
- architecturally accepted at the same commit (`archcheck` exit 0 under the full policy plus probes).

A commit `archcheck` cannot evaluate (exit 2: build failure, or a project added outside the tier map) is not
accepted. Such a commit is removed only from metrics that count violations.

## Rule classes

The detail is in [ARCHITECTURE-RULES.md](ARCHITECTURE-RULES.md).

- **DET**: decided from compiler-resolved project and symbol structure. Only DET findings of severity ≥ 2 gate.
- **HEU**: heuristic signals, such as catch-alls, duplicated literals, domain arithmetic in Tier 4 and file-size bands.
  They are reported and never gate, because their false-positive rate is unknown.
- **REV**: semantic properties no static check decides. A blinded reviewer scores them on the rubric in
  `analysis/review-rubric.md`. Before review, the scrubber removes arm-identifying text: decision ids, tool names,
  `docs/architecture` and `docs/contracts`. Review scores are descriptive and check convergent validity against DET.

## Costs

- **Model cost** is `total_cost_usd` summed over both phases, background model calls included. It is cross-checked
  against token counts priced from the pinned price table.
- **Compute and orchestration** (harness setup, submit, scoring) are wall time only.
- **Reviewer cost** is evaluation cost, never charged to an arm.

For each phase the scorer reports input, output, cache-read and cache-write tokens, tool calls, test executions and
verification executions.

## Primary metric

**Total model cost per accepted requirement, per arm.**

- The numerator includes every phase of every non-excluded trial: failed attempts, retries and timed-out phases.
- The denominator counts accepted requirements, 2 possible per trial.
- The companion metric is cost per completed task (phase-2 submit PASS), so that a low denominator cannot hide
  expensive failures.

Contrasts, hypotheses, inference and classification rules are in PROTOCOL.md §7 and in the spec's `primary`,
`secondary` and `classification` blocks.
