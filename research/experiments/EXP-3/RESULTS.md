# EXP-3 phase 1: results

**Protocol.** `PREREGISTRATION.md`, committed and pushed as `8f68c6d` before the audit was run on any scenario.

**What was run.**
- The audit: Dokimos `experiments/rule-provenance` at commit `91fd1a2`, built with `run.sh build` on SDK 10.0.402.
- The harness: `harness/exp3.py`, run with `python3 -I`.
- The data: all 27 P3 scenarios, corpus revision `ea36618`.

**Cost.** $0: no LLM or provider call. A second full run produced byte-identical `results/`.

**Labels.** Available. `P3/CORPUS.md` §5 publishes the unsealed per-opportunity tables, so the sealed stores were not
opened.

## 1. Headline

| Metric (pooled, 27 scenarios) | Value | 95% CI (exact, descriptive) | H1 threshold |
|---|---|---|---|
| Recall (planted rules with ≥ 1 TP) | **5 / 13 = 38.5%** | 13.9%–68.4% | ≥ 90% |
| Precision, strict (TP / owner questions) | **6 / 63 = 9.5%** | 3.6%–19.6% | — |
| Precision, lenient ((TP + OTHER) / questions) | 6 / 63 = 9.5% (no OTHER findings) | — | — |
| False-question rate (FQ / owner questions) | **57 / 63 = 90.5%** | 80.4%–96.4% | ≤ 10% |

**H1 is Contradicted.** Both thresholds fail on the point estimates, and both CIs exclude their threshold.

- **H1a (recall ≥ 90%): Contradicted.**
- **H1b (false-question rate ≤ 10%): Contradicted.**

Under EXP-3-R2, phase 2 does not qualify.

**Breakdown of the 57 false questions:**
- 54 are on SUPPORTED code (an accepted decision or requirement in the same scenario states the rule);
- 3 are on TECHNICAL code;
- none are UNLABELLED, so no adjudication was needed.

All 63 findings are `uncertain-authority`; the audit raised no `proven` findings in legacy mode.

## 2. By mechanism, stage, domain and sensitivity sets

| Subset | Rules | Detected | Recall | Questions | TP | FQ | Precision | False-question rate |
|---|---|---|---|---|---|---|---|---|
| Superseded value (C01, C02, D03, D17, D20) | 5 | 2 | 40.0% | 13 | 3 | 10 | 23.1% | 76.9% |
| Exemption (C05, C06, D08, D18, D21) | 5 | 0 | **0.0%** | 9 | 0 | 9 | 0.0% | 100.0% |
| Silent default (C03, C04, D19) | 3 | 3 | **100.0%** | 9 | 3 | 6 | 33.3% | 66.7% |
| The 13 scenarios with a planted rule | 13 | 5 | 38.5% | 31 | 6 | 25 | 19.4% | 80.6% |
| Without D08 (12 rules, 26 scenarios) | 12 | 5 | 41.7% | 60 | 6 | 54 | 10.0% | 90.0% |
| Confirmatory C01–C06 | 6 | 2 | 33.3% | 11 | 2 | 9 | 18.2% | 81.8% |
| Discovery D01–D21 | 7 | 3 | 42.9% | 52 | 4 | 48 | 7.7% | 92.3% |
| Billing (13 scenarios) | 7 | 3 | 42.9% | 41 | 3 | 38 | 7.3% | 92.7% |
| Clinic (11 scenarios) | 5 | 1 | 20.0% | 1 | 1 | 0 | 100.0% | 0.0% |
| Lending (3 scenarios) | 1 | 1 | 100.0% | 21 | 2 | 19 | 9.5% | 90.5% |

**Mechanism correctness** (secondary): 5 of the 5 detected rules were reported with the right mechanism.
- D03 and D17 were classed `superseded-authority`, naming the superseded decision.
- C03, C04 and D19 carried the "wildcard default" hint.

The audit's wording was never wrong when it hit. Every miss is a failure to see the rule at all.

## 3. Per scenario

| Scen. | Mechanism | Questions | TP | FQ | Planted rule detected |
|---|---|---|---|---|---|
| C01 | superseded value | 0 | 0 | 0 | **missed** |
| C02 | superseded value | 3 | 0 | 3 | **missed** |
| C03 | silent default | 1 | 1 | 0 | yes (`visitFee`) |
| C04 | silent default | 4 | 1 | 3 | yes (`shippingCharge`) |
| C05 | exemption | 3 | 0 | 3 | **missed** |
| C06 | exemption | 0 | 0 | 0 | **missed** |
| D01 | — | 7 | 0 | 7 | — |
| D02 | — | 7 | 0 | 7 | — |
| D03 | superseded value | 7 | 2 | 5 | yes (`Policy.finePerDay`, `Policy.fineCap`; `Fines.fineFor` not flagged) |
| D04–D07 | — | 3 each | 0 | 3 each | — |
| D08 | exemption | 3 | 0 | 3 | **missed** |
| D09–D12 | — | 0 each | 0 | 0 | — |
| D13, D14 | — | 3 each | 0 | 3 each | — |
| D15, D16 | — | 0 each | 0 | 0 | — |
| D17 | superseded value | 3 | 1 | 2 | yes (`lateFeeRate`; `lateFee` not flagged) |
| D18 | exemption | 3 | 0 | 3 | **missed** |
| D19 | silent default | 4 | 1 | 3 | yes (`taxRate`) |
| D20 | superseded value | 0 | 0 | 0 | **missed** |
| D21 | exemption | 0 | 0 | 0 | **missed** |

The raw reports are in `results/raw/<S>.audit.json`, and the generated handoffs in `results/handoffs/`. Every
finding with its label, basis and outcome is in `results/scores.json`.

## 4. Every miss, with its reason

Each reason was checked against the scanner's rules (`RuleProvenance.Core/Scanner.fs`). Several are false-negative
risks that `LIMITATIONS.md` lists.

| Scen. | Planted code | Why the scan saw no rule-bearing construct |
|---|---|---|
| C01 | `let reminderLeadHours = 24`; `reminderAt` = `...AddHours(float -reminderLeadHours)` | Integer literal outside a comparison is not counted; arithmetic use is not a construct (documented limitation) |
| C02 | `let paymentTermDays = 30`; `dueDate` = `issued.AddDays paymentTermDays` | Same: integer constant used in arithmetic |
| D20 | `let bookingHorizonDays = 90`; `date <= today.AddDays bookingHorizonDays` | Integer constant; the comparison's neighbouring operands (`date`, `today`) are not constants, so it is not counted |
| C05 | `chased c = c.Kind <> Nonprofit` | Comparison against a union case: `Nonprofit` is neither a literal nor a `let`-constant |
| D18 | `chased c = c.Plan <> Premium` | Same (union case `Premium`) |
| D08 | `lateFeeExempt c = c.Plan = Premium` | `=` is counted only in a condition context (`if`/`when`/`&&`/`||` on the same line), and the operand is a union case |
| D21 | `dispensedWithoutCheck drug = drug = "paracetamol"`; `mayDispense` = `(... IsSome \|\| dispensedWithoutCheck ...) && ...` | `= "paracetamol"` has no condition token on its line. `mayDispense` has `\|\|`/`&&` but no comparison against a constant, and a call is not a construct |
| C06 | `clinician = "k2"` on one line, `\|\| state.Appointments ...` on the next | The condition context is computed per line, and the `\|\|` is on the following line, so `= "k2"` is not counted. The audit's own "C06 pattern" fixture (`fixtures/legacy-reuse/PaymentValidation.fs`) writes the exemption as `if customerId.StartsWith "PRT-"` next to a decimal limit, which the scan catches. The P3 original is shaped differently |

**Partial misses inside detected rules.** These do not change recall:
- D03's `Fines.fineFor` (`min Policy.fineCap (... * Policy.finePerDay)`) was not flagged. Its constants were, in
  `Policy`.
- D17's `lateFee` was not flagged; `lateFeeRate` was.

## 5. Every false owner question, with its reason

There are 57 false questions but only 10 distinct (file, symbol) findings, because the base fixture file repeats
across scenarios. Each distinct finding is listed below with the scenarios where it is false.

| Symbol (construct the audit saw) | Label and basis | False in | Count |
|---|---|---|---|
| `Billing.Rules.isOverdue` (`> 0m`) | SUPPORTED, DEC-B03 ("still unpaid after its due date"); DEC-B08 in D17 | all 13 billing scenarios | 13 |
| `Billing.Rules.owesLateFee` (`= 0m` under `&&`) | SUPPORTED, DEC-B03 ("charged once per invoice"); DEC-B08 in D17 | all 13 billing scenarios | 13 |
| `Billing.Rules.lateFeeRate` (decimal `0.02`) | SUPPORTED, DEC-B03 2%. The audit's own message says "Value 0.02 equals DEC-B03.p1 (accepted)" and still asks | 12 billing scenarios (not D17, where it is the TP) | 12 |
| `Lending.Transition.Fines.assess` (`if amount > 0m`) | SUPPORTED, DEC-003 / DEC-010 (no fine on or before the due date) | D01, D02, D03 | 3 |
| `Lending.Transition.Loans.borrow` (`match ... when head.Member <> memberId`) | SUPPORTED, DEC-005 (lent only to the head of the queue) | D01, D02, D03 | 3 |
| `Lending.Transition.Loans.overdue` (`days > 0`) | SUPPORTED, LEND-L02-R1 | D01, D02, D03 | 3 |
| `Lending.Transition.Policy.maxLoans` (`match` on member type) | SUPPORTED, DEC-002 (table 5/3/10) | D01, D02, D03 | 3 |
| `Lending.Transition.Policy.finePerDay` (decimal `0.25`; message: "equals DEC-003.p1 (accepted)") | SUPPORTED, DEC-003 | D01, D02 | 2 |
| `Lending.Transition.Policy.fineCap` (decimal `10.00`; message: "equals DEC-003.p2 (accepted)") | SUPPORTED, DEC-003 | D01, D02 | 2 |
| `Lending.Transition.Prelude` (`if` in `ensure`, `match` in `required`) | TECHNICAL, Result helpers | D01, D02, D03 | 3 |

**Why the false-question rate is high.** In legacy mode with no observations, every rule-bearing declaration that
carries no `[<Authority>]` marker becomes an owner question:
- The fixtures cite their decisions in doc comments (`/// DEC-B03: …`). The lexer drops comments by design.
- When a literal equals an **accepted** decision's parameter, the audit adds a note but does not withhold the
  question (`Provenance.legacy`, unmatched branch).

So in this corpus every recognised rule is a question, whether or not it is authorized. Precision is then bounded
by how often the recognised rule happens to be the planted one.

## 6. Amendments

- **A1 (after the data; exploratory only; does not change any preregistered number).**
  - **Deduplicated view.** Counted once per distinct (file, symbol, label, class), there are 16 findings: 6 TP and 10
    FQ, a false-question rate of 62.5%. This still fails H1b.
  - **Exploratory all-`src` run (§2 of the preregistration).** It raised 406 owner questions across the 27
    scenarios (13–23 per scenario). These are unscored.
- **No other deviation.** The handoff rules were applied as written. Body numbers include list ordinals (DEC-004's
  "1.", "2.", "3."), as the rule "every number in its body" says. They affected no finding. DEC-B05 (D08) has no
  owner in its status line, so its owner is `unknown`, per the rule.

## 7. Evidence classes

| Hypothesis | Class | Basis |
|---|---|---|
| H1: recall ≥ 90% and false-question rate ≤ 10% | **Contradicted** | 38.5% and 90.5% on the point estimates. Both 95% CIs exclude the thresholds |
| H1a: recall ≥ 90% | **Contradicted** | 5 / 13; upper CI 68.4% |
| H1b: false-question rate ≤ 10% | **Contradicted** | 57 / 63; lower CI 80.4%. Deduplicated (A1): 10 / 16 |
| Per mechanism (descriptive only, not preregistered as hypotheses) | — | Silent default 3 / 3 detected. Superseded value 2 / 5, caught only when the value is a decimal literal. Exemption 0 / 5 |

## 8. What this means for EXP-3

- **Phase 2 (EXP-3-R2) does not qualify.** Its gate is this phase's H1.
- **Do not show this audit's owner questions to agents in a paid arm.** Nine in ten would be false, and they would
  bury the one-in-ten that is real. That is the control-induced harm P3 warned about.
- **The exemption mechanism is the one that matters most**: C06 defeated every P3 control, and the audit has 0 / 5
  recall on it.
- **Fixes this data points to.** These are hypotheses for a later, separately preregistered run, not results:
  - count integer `let`-constants and their arithmetic uses;
  - treat comparisons against union cases and string literals in any boolean expression as rule-bearing;
  - compute the condition context per expression rather than per line;
  - withhold or downgrade a question when a literal equals an accepted parameter, or read the doc-comment
    citation as a candidate authority to verify against the handoff.

  Any re-measurement must use a corpus the fixes were not tuned on, because these 27 scenarios have now been seen.

## 9. Limitations

- **The audit is lexical.** It drops comments and has no types or name resolution. The results measure this
  implementation (`91fd1a2`), not provenance auditing in general.
- **The corpus is small and repetitive.** There are 13 planted rules over 27 scenarios and three fixture domains. One
  billing base file recurs 13 times, so the pooled false-question rate is dominated by three repeated findings
  (A1 gives the deduplicated view). One miss moves recall by 7.7 points.
- **The experimenter built the handoffs**, by preregistered rules. Observations were deliberately empty: the audit's
  observation path, which would be told the rule's location, was not tested. With observations, recall would be
  trivial and uninformative.
- **The labels come from P3's own oracle design** (`CORPUS.md` §5). The SUPPORTED and TECHNICAL labels are the
  experimenter's, written before the run. D08's inclusion is a judgement; the without-D08 row shows it does not
  change the verdict.
- **The scope is the rules modules only.** Code in `Commands.fs` (for example C05's and D18's late-fee runs) was not
  scored.
- **No agent was in the loop.** Nothing here measures whether owner questions would change implementation behaviour.
