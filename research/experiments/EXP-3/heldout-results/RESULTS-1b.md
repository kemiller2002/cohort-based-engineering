# EXP-3 phase 1b: held-out results

**Protocol.** `../PREREGISTRATION-1b.md` and `../harness/score_heldout.py`, committed and pushed as `061eaa4` before
either analyzer was run on any held-out scenario.

**What was run.**

- **Analyzer.** Dokimos `experiments/rule-provenance` at `fc9b31fe7c1dc76020a78868fee316d897d681ca` (origin/main).
  It was built with `run.sh build` in a clean detached worktree on .NET SDK 10.0.402. The tool version is
  `0.2.0-experimental`.
  - v2 `--analyzer ast` is the confirmatory subject.
  - v1 `--analyzer lexical` is reported for reference only.
- **Corpus.** `heldout/`, frozen at `000e90a`: 17 scenarios with 30 planted rules (10 superseded value, 11 exemption,
  9 silent default). `sha256sum -c FREEZE.sha256` passed before and after the run. The audit read copies of the
  trees, never the frozen corpus itself.
- **Handoffs.** The frozen `heldout/handoffs/*.json`. All 17 are byte-identical to a fresh regeneration with
  `exp3.build_handoff`.
- **Cost.** $0. No LLM call was made.

**Determinism.** Every audit ran twice inside the scorer, and both reports were byte-identical for all 34
analyzer×scenario pairs. The whole scorer was then run a second time: `heldout-results/` (35 files) was identical
to the first run (`diff -r`). No audit failed: every exit code was 0, and every report validates against
`echelon-provenance-audit-0.1`.

**Files.**
- `raw/<analyzer>/<id>.audit.json`: the reports.
- `scores.json`: every finding with its label, basis and outcome, every rule's detection, and all aggregates.

Intervals are Wilson 95% intervals, as preregistered. Phase 1 used Clopper-Pearson.

## 1. Headline (pooled, 17 scenarios)

| Metric | v2 `ast` (confirmatory) | v1 `lexical` (reference) | H1 threshold |
|---|---|---|---|
| Recall (rules with ≥ 1 TP) | **24 / 30 = 80.00%** [62.69%, 90.49%] | 26 / 30 = 86.67% [70.32%, 94.69%] | ≥ 90% |
| Precision, strict (TP / questions) | **27 / 36 = 75.00%** [58.93%, 86.25%] | 30 / 76 = 39.47% [29.25%, 50.71%] | — |
| False-question rate (FQ / questions) | **9 / 36 = 25.00%** [13.75%, 41.07%] | 46 / 76 = 60.53% [49.29%, 70.75%] | ≤ 10% |
| False questions by label | 9 SUPPORTED | 42 SUPPORTED, 3 UNLABELLED, 1 TECHNICAL | — |
| Controls H16 + H17 (no planted rule): false-question rate | **3 / 3 = 100%** [43.85%, 100%] | 12 / 12 = 100% [75.75%, 100%] | — |
| H01–H15 only: false-question rate | 6 / 33 = 18.18% [8.61%, 34.39%] | 34 / 64 = 53.13% [41.07%, 64.82%] | — |
| Secondary (A1 style, distinct path/symbol/label/class): false-question rate | 9 / 36 = 25.00% (no repeats) | 45 / 75 = 60.00% | — |
| Mechanism correct (class or hint) / detected | 17 / 24 | 11 / 26 | — |
| Exploratory, unscored: questions over all `src/**/*.fs` | 36 | 76 | — |

Precision is lenient = strict, because no finding was labelled OTHER. The exploratory counts equal the scored counts
because `Domain.fs` produced no findings.

**H1 (v2): Contradicted.** Both thresholds fail on the point estimates.

- **H1a (recall ≥ 90%): Contradicted.** The estimate is 80.00%. The interval's upper bound, 90.49%, only just
  reaches the threshold.
- **H1b (false-question rate ≤ 10%): Contradicted.** The estimate is 25.00%, and the interval's lower bound (13.75%)
  excludes 10%.

v1 is also Contradicted on both. This is descriptive only.

## 2. By mechanism (recall)

| Mechanism | v2 detected | v2 TP findings | v2 mechanism correct | v1 detected | v1 mechanism correct |
|---|---|---|---|---|---|
| Superseded value | **10 / 10 = 100%** [72.25%, 100%] | 10 | 10 / 10 | 9 / 10 = 90.00% [59.58%, 98.21%] | 8 / 9 |
| Exemption | **10 / 11 = 90.91%** [62.26%, 98.38%] | 13 | 6 / 10 | 11 / 11 = 100% [74.12%, 100%] | 0 / 11 |
| Silent default | **4 / 9 = 44.44%** [18.88%, 73.33%] | 4 | 1 / 4 | 6 / 9 = 66.67% [35.42%, 87.94%] | 3 / 6 |

## 3. By domain

| Domain (scenarios) | v2 recall | v2 questions (TP / FQ) | v1 recall | v1 questions (TP / FQ) |
|---|---|---|---|---|
| Claims (H01–H03, H16) | 5 / 6 | 7 (6 / 1) | 6 / 6 | 19 (7 / 12) |
| Payroll (H04–H06) | 5 / 5 | 9 (6 / 3) | 5 / 5 | 14 (6 / 8) |
| Freight (H07–H09, H17) | 5 / 6 | 7 (5 / 2) | 5 / 6 | 19 (5 / 14) |
| Subscriptions (H10–H12) | 4 / 6 | 7 (5 / 2) | 3 / 6 | 10 (3 / 7) |
| Procurement (H13–H15) | 5 / 7 | 6 (5 / 1) | 7 / 7 | 14 (9 / 5) |

## 4. Every v2 miss (6), with its cause

Each cause comes from the scenario source and the analyzer's documented rules (README "Rule-bearing constructs" and
"Authority matching"). The analyzer was not modified.

| Rule | Mechanism | Planted code | Why v2 raised no finding on any of the rule's symbols |
|---|---|---|---|
| H03-P1 | exemption | `Coverage.deductibleWaivedProducts = set [ "HOME-PLUS"; "LANDLORD-PRO" ]`; `deductibleWaived p = deductibleWaivedProducts.Contains p.Product`; `deductibleFor`: `\| _ when Coverage.deductibleWaived claim.Policy -> 0m`, beside `\| Glass -> 0m // APR-CL01` | String literals inside a `Set` constructor are not rule-bearing. `Contains` counts only against a string literal, and here its argument is a variable. So `deductibleWaived` is not a category predicate, and the guard calling it is not an exemption shape. The only remaining construct, the `0m` branch result, is excused by rule (c): the declaration's `// APR-CL01` comment cites an accepted approval that declares no parameters. The unauthorized branch rides on the authorized branch's citation |
| H07-P2 | silent default | `zoneSurcharges \|> List.tryFind … \|> Option.map snd \|> Option.defaultValue 0m` | A silent default is recognised only as a catch-all match clause. `Option.defaultValue` is a call, and `0m` as a call argument is not in a value position. Even if counted, 0 equals DEC-FR03's `URBAN` 0.00 parameter |
| H10-P1 | silent default | `Map.tryFind plan \|> Option.map … \|> Option.defaultValue Plans.starter.Monthly` | There is no literal and no catch-all clause. The default is another entry's value, by reference |
| H12-P2 | silent default | `defaultArg (Map.tryFind plan seatLimits) Int32.MaxValue` | There is no literal or clause, and `MaxValue` is explicitly excluded as a BCL sentinel |
| H14-P1 | silent default | `match termsByTier.TryGetValue tier with \| true, days -> days \| _ -> 35` | The wildcard default is a recognised construct, but its value 35 equals the accepted DEC-PR03 parameter `vendor-terms.STANDARD` = 35. Rule (b) therefore marks it supported and no question is raised. An authorized value used as an unauthorized default is invisible to value matching |
| H15-P2 | silent default | `match incoterm.ToUpperInvariant() with … \| _ -> 0.045m` | Same as H14-P1: 0.045 equals the accepted DEC-PR09 `incoterm-allowances.FOB` parameter |

H14-P1 and H15-P2 are inferred from the documented precedence: no finding exists to quote.

**v1 misses (4).**
- H07-P2, H10-P1 and H12-P2 are missed for the same reasons as v2.
- H11-P2 (`retryOffsetsDays = [ 1; 3; 5 ]`) is missed because v1 does not count integer literals outside
  comparisons.
- v1 caught H03-P1 (on `deductibleFor`'s `when` branch), H14-P1 and H15-P2, because it flags every `if`, `match` and
  `when` branch whether or not it is authorized. That is also why its false-question rate is 60.53%.

**Detections that hit only incidentally (v2).** A rule counts as detected under the preregistered rule even when the
finding did not see its mechanism. Seven of v2's 24 detections lack the right mechanism hint:

- **Exemptions flagged only through a numeric literal:**
  - H05-P2: the 90-day literal and a `0`.
  - H09-P2: `0` on the `IsKeyAccount` branch; the boolean-field exemption itself was not recognised.
  - H12-P1: the literal 150 and a wildcard default.
  - H14-P2: the 250.00 ceiling.
- **Silent defaults flagged by a literal or exemption hint rather than the wildcard hint:**
  - H01-P2: 2000.00 as a literal.
  - H03-P2: the `else 0.0` chain was read as an `if` exemption shape.
  - H09-P1: also read as an exemption shape.

The pure-mechanism view is therefore weaker than 24/30. In particular, v2 recognised the silent-default mechanism
itself in only 1 of 9 rules (H05-P1).

## 5. Every v2 false question (9), with its cause

All 9 are on SUPPORTED declarations. None is UNLABELLED or TECHNICAL, so no adjudication was needed.

| Scen. | Symbol | Construct v2 objected to (finding text) | Label basis | Why it is false |
|---|---|---|---|---|
| H05 | `Payroll.Rules.unionDues` | "numeric literal 0 (line 21): value 0 equals no declared parameter" | PAY-14-R1 (non-members pay no dues) | The authorization is prose in a requirement ("pays no dues"). Requirements carry no parameters, so a prose zero never matches |
| H05 | `Payroll.Rules.vacationAccrued` | "numeric literal 0 (line 32) …" | PAY-14-R3 (unpaid leave accrues nothing) | Same cause: prose zero in a requirement |
| H11 | `Subscriptions.Rules.prorate` | "numeric literal 0 (line 27) …" | DEC-SB04 (a downgrade returns 0) | DEC-SB04 is accepted but has no numeric parameters, and the declaration does not cite it |
| H16 (control) | `Claims.Rules.rentalAllowance` | "numeric literal 0 (line 29) …" | DEC-CL17 (no rental cover, no allowance) | Prose zero ("no allowance"); DEC-CL17's parameters are 45.00 and 28 |
| H17 (control) | `Freight.Rules.coverPremium` | "numeric literal 0 (line 15) …" | DEC-FR11 ("covered free of charge" at or below 100.00) | "Free of charge" is not a number; DEC-FR11's parameters are 0.009, 3.20 and 100.00 |
| H17 (control) | `Freight.Rules.oversizeFee` | "wildcard default returning 0m … cited DEC-FR13 declares oversize-fees.REMOTE=42.00, … p1=150, not 0" | DEC-FR13 ("in every other zone there is no oversize fee") | The wildcard is authorized in prose, but the cited record's numeric parameters veto the zero under rule (c) |
| H10 | `Subscriptions.Rules.isSuspended` | "wildcard default returning false for unlisted cases (line 27): no value to match" | SUB-04-R2 | A boolean `\| _ -> false` fall-through in a status test is flagged as a silent default, and no record can match `false` |
| H06 | `Payroll.Rules.reimbursable` | "case keyed on "Meals" (line 20): no accepted record names "Meals"" | PAY-22-R2 ("Meal claims are paid up to the daily meal cap") | Whole-word, case-sensitive naming: "Meals" ≠ "Meal" |
| H13 | `Procurement.Rules.\|ApprovedSoleSource\|_\|` | "category test '= "LabReagents"' (line 22): no accepted record names "LabReagents"" | APR-PR01 ("Lab reagent requisitions from … V-3302") | The identifier spelling "LabReagents" ≠ the prose "Lab reagent". The vendor `V-3302` in the same test was matched through the comment citation |

**The pattern.** Six of the nine are a zero or a fall-through that the source states in words ("no", "free",
"nothing", "every other"), not as a parameter. Two are a category identifier written differently from the source's
prose. One is a boolean default. Every control-scenario question (3 / 3) belongs to the first group.

## 6. v1 UNLABELLED findings: adjudication and amendment B1

v1 emitted 3 findings whose symbol was absent ("module-level code"). They fall inside active-pattern bodies that v1
does not name.

- **H02, lines 14–16:** the body of the PLANTED `(|CatastropheEvent|_|)` (H02-P1). By content, this is a true
  question.
- **H08, lines 8–10:** the body of the SUPPORTED `(|DangerousGoods|ColdChain|General|)`. It stays false.
- **H13, line 22:** the body of the SUPPORTED `(|ApprovedSoleSource|_|)`. It stays false.

**B1 (after the data; v1 reference only; changes no preregistered number).** The primary figures above count all
three UNLABELLED findings as false, as preregistered. If the H02 finding is reclassified as true, v1 has 31 TP, and
its false-question rate becomes 45 / 76 = 59.21% [47.98%, 69.56%]. Its recall is unchanged, because H02-P1 is
detected through `referToSiu` anyway. v2 had no UNLABELLED findings.

There were no other deviations from the preregistration.

## 7. Comparison with the development set, and overfitting

| | Development set (VAC-002-P3; v2 tuned on it) | Held-out (this phase) | Change |
|---|---|---|---|
| v2 recall | 13 / 13 = 100% | 24 / 30 = 80.00% | −20.0 points |
| v2 false-question rate | 0 / 15 = 0% | 9 / 36 = 25.00% | +25.0 points |
| v2 silent-default recall | 3 / 3 | 4 / 9 | |
| v1 recall | 5 / 13 = 38.5% | 26 / 30 = 86.67% | +48.2 points |
| v1 false-question rate | 57 / 63 = 90.5% | 46 / 76 = 60.53% | −30.0 points |

**Statement on overfitting.** v2's held-out numbers are worse than its development-set numbers on both metrics: 20.0
points lower recall and 25.0 points higher false-question rate. The perfect P3 figures did not carry over. This is
consistent with overfitting to P3.

- **The misses** are in forms that P3 did not contain:
  - `Option.defaultValue` and `defaultArg` defaults;
  - `Set` membership in a helper;
  - a default equal to a listed value.
- **The false questions** come from authorization written in prose rather than parameters, which P3's fixtures
  rarely needed.

The two explanations, overfitting and a harder corpus, cannot be fully separated, because the held-out corpus is
not a replica of P3. v1 moved in the opposite direction (much higher recall, lower false-question rate). That shows
the held-out corpus differs from P3 in difficulty and style, not only in being unseen. v1's higher held-out recall
comes from its indiscriminate branch flagging, not from precision.

**Where v2 stands against v1.** On held-out data, v2 roughly halves the precision problem: 75.00% against 39.47%
precision, and 25.00% against 60.53% false questions. It does so at a recall cost of 2 rules: 24 against 26 of 30.

## 8. Evidence classes

| Hypothesis (v2 `ast`) | Class | Basis |
|---|---|---|
| H1: recall ≥ 90% and false-question rate ≤ 10% | **Contradicted** | 80.00% and 25.00% on the point estimates |
| H1a: recall ≥ 90% | **Contradicted** | 24 / 30; Wilson 95% interval [62.69%, 90.49%] |
| H1b: false-question rate ≤ 10% | **Contradicted** | 9 / 36; Wilson 95% interval [13.75%, 41.07%], which excludes 10% |

The gate condition for EXP-3 phase 2 is **not met** on held-out data. This phase does not decide phase 2.

## 9. Limitations

- **The corpus is small.** One rule is 3.3 points of recall. The intervals are wide; the recall interval only just
  touches 90%.
- **One author wrote both the corpus and its labels.** The SUPPORTED judgements on prose authorizations ("no
  dues", "free of charge") are that author's. An analyzer that reads requirement and decision prose for zeros would
  score differently. These are still correct false questions under the preregistered labels.
- **The handoffs follow the phase-1 rules.**
  - Requirements carry no parameters, so prose zeros cannot match by construction.
  - Observations are empty, so the analyzer's observation path is untested.
- **Detection is symbol-level.** A rule counts as detected when a finding lands on one of its symbols for any
  reason. Section 4 lists the 7 v2 detections that did not recognise the mechanism.
- **The corpus is synthetic F# in a P3-like style**, compiled but not drawn from a production codebase. No agent was
  in the loop.
- **The corpus author saw phase 1's preregistration and harness but not its results.** The author chose varied
  syntactic forms, which may over-represent forms that are hard for v2 relative to real code. This is also why the
  held-out set is informative.
