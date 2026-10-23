# EXP-3 phase 1b: preregistration (held-out, confirmatory)

**What it measures.** How accurately the Dokimos rule-provenance audit finds the unauthorized code-embedded rules
planted in the **held-out** corpus `heldout/` (17 scenarios, 30 planted rules, five domains P3 did not use), written by
an independent author after phase 1 and frozen at commit `000e90a` (`heldout/FREEZE.sha256`), and how many of the
owner questions it raises are false. Phase 1 (`PREREGISTRATION.md`, `RESULTS.md`) measured v1 on VAC-002-P3; v2 was
then developed on that same P3 corpus, so its P3 numbers (13/13 recall, 0/15 false questions) are development-set
numbers. This phase is the held-out confirmation those numbers require.

**Cost.** Zero. No LLM or provider call. Audit, handoffs and scoring are deterministic.

**Commitment.** This file and `harness/score_heldout.py` are committed and pushed **before** either analyzer is run on
any held-out scenario. Results are reported whatever they are, in `heldout-results/RESULTS-1b.md`. Any deviation from
this file after that commit is logged there as an amendment B1, B2, … with its timing relative to the data.

**What the scorer has seen before this commit.** Phase 1's protocol, results and harness; `heldout/README.md` and
`heldout/labels.json` (the ground truth); the scenario file listings and `scenario.json` files; the analyzer's
`README.md` and the finding-message strings in its source (to fix the mechanism-hint tests below). The scorer has not
run either analyzer on any held-out file and has not read the held-out `.fs` sources. The analyzer is frozen at the
revision below and is not modified; nothing in it can be tuned by this phase.

## 1. Subject

| Item | Value |
|---|---|
| Analyzer | Dokimos `experiments/rule-provenance`, commit **`fc9b31fe7c1dc76020a78868fee316d897d681ca`** (`origin/main`, merge of dokimos#54), built with `run.sh build` from a clean detached worktree; the scorer refuses any other revision or a dirty tree |
| Confirmatory subject | v2, `--analyzer ast` (FSharp.Compiler.Service 43.12.400 untyped parse trees) |
| Reference only | v1, `--analyzer lexical` (the phase-1 analyzer, unchanged); reported for comparison, no hypothesis is tested on it |
| SDK | .NET SDK 10.0.402 |
| Corpus | `heldout/` at `000e90a`; `sha256sum -c FREEZE.sha256` must pass before and after the run (the scorer checks both and stops otherwise) |

## 2. Inputs and invocation

- **Trees.** Each `heldout/scenarios/<id>/tree/` is copied unchanged to a scratch work directory (so the frozen
  corpus is never written to) and audited there. Reported paths are relative to `--root`, so they are unaffected.
- **Handoffs.** The **frozen** `heldout/handoffs/<id>.handoff.json`, validated against
  `echelon-authority-handoff-0.1`. As a consistency check only, the scorer regenerates each with
  `harness/exp3.py`'s `build_handoff` and records whether it is byte-identical; the frozen file is used either way.
- **Audit scope.** `heldout/labels.json` `auditScope[<domain>]`, files missing from a scenario's tree skipped (as
  `exp3.audit_files` does); passed as `--legacy`.
- **Command** (once per analyzer, no probe, no trace, defaults otherwise):
  `rule-provenance audit --analyzer <ast|lexical> --root <tree> --handoff <handoff> --legacy <file>... --sdk-version <dotnet --version> --out <json>`
- **Failures.** Exit 0 or 4 is a completed audit; the report is validated against `echelon-provenance-audit-0.1`. Any
  other exit (2 invalid input, e.g. a parse failure; 3; 1) means that scenario contributes **no findings** for that
  analyzer and all its planted rules count as **missed**. Failures are listed individually.
- **Determinism.** Every audit is run twice; the two reports (and exit codes) must be byte-identical. The result is
  recorded per scenario and per analyzer.
- **Exploratory, unscored.** As in phase 1, each analyzer is also run over all of the scenario's `src/**/*.fs`; only
  the number of owner questions is reported.

## 3. Ground truth

`heldout/labels.json`, unchanged: per-scenario labels PLANTED, SUPPORTED, TECHNICAL (OTHER-UNAUTHORIZED unused),
and `plantedRules.<id>` = a list of `{rule, mechanism, form, symbols}`. 30 planted rules: superseded value 10,
exemption 11, silent default 9. H16 and H17 are controls with no planted rule (every rule authorized).

**Symbol resolution** (phase 1 rule): a finding's `location.symbol` resolves to itself if labelled, else to its
nearest labelled dotted ancestor; if none, it is UNLABELLED. The labelled spellings include those the README lists:
both active-pattern spellings (`Module.(|A|_|)` and `Module.|A|_|`) and record-constant fields
(`Module.binding.Field`). No other alias is added. An UNLABELLED finding is adjudicated individually in
`RESULTS-1b.md` and **counted as a false question** unless the adjudication shows otherwise; any such
reclassification is an amendment and both numbers are reported.

## 4. Scoring (adapted for multi-rule scenarios)

- **Owner question**: any finding in the report (`uncertain-authority` or `proven`, any class).
- **TP**: a finding whose symbol resolves to a PLANTED declaration of that scenario (any of its planted rules). A
  second finding on the same rule is also a TP for precision.
- **False question (FQ)**: a finding that resolves to a SUPPORTED declaration, a TECHNICAL declaration, or nothing
  (UNLABELLED, subject to §3).
- **Detection of a planted rule**: the rule is detected when **at least one** finding of its scenario resolves to
  **one of that rule's `symbols`** (label keys). A finding on a different planted rule's symbol does not detect it.
- **Counting (primary, as phase 1's primary rule).** Every finding in a report is one owner question, pooled over all
  17 scenarios (no deduplication). **Secondary (phase 1 amendment A1 style):** one count per distinct
  (path, symbol, label, class), pooled; reported, not used for the verdict.
- **Mechanism correctness** (secondary, phase 1 tests): superseded value: a TP of the rule has class
  `superseded-authority`; silent default: a TP's message contains `wildcard default`; exemption: a TP's message
  contains `exemption`.

## 5. Metrics

All proportions are reported with **Wilson score 95% intervals** (phase 1 reported exact Clopper-Pearson intervals;
the point estimates are directly comparable, the intervals differ slightly in method).

- **Recall** = detected rules / 30, overall and per mechanism (10 / 11 / 9).
- **Precision** (strict) = TP / owner questions; lenient = (TP + OTHER) / owner questions.
- **False-question rate** = FQ / owner questions, pooled over the 17 scenarios; split into SUPPORTED, TECHNICAL and
  UNLABELLED.
- **Controls**: the false-question rate (and the number of questions) on H16 + H17 alone, reported separately.
  Also reported over H01-H15 alone, and per domain.
- Per mechanism, recall and the number of TP findings attributed to that mechanism's rules. Precision and
  false-question rate are not split by mechanism, because FQs cannot be attributed to a mechanism in multi-rule
  scenarios.
- Reported for both analyzers; v2 is primary.

## 6. Hypotheses and evidence classes (unchanged from phase 1)

**H1** (v2, `ast`): recall ≥ 90% **and** false-question rate ≤ 10%, on the point estimates over this corpus.
**H1a**: recall ≥ 90%. **H1b**: false-question rate ≤ 10%.

- **Supported-preliminary**: threshold(s) met on the point estimate.
- **Demonstrated**: additionally the lower bound of the 95% recall interval ≥ 90% and the upper bound of the 95%
  false-question interval ≤ 10% (with 30 rules this needs essentially perfect recall; 30/30 gives a Wilson lower
  bound of 88.6%, so Demonstrated for H1a is not reachable on this corpus, and this is stated in advance).
- **Contradicted**: either threshold missed on the point estimate.
- **Inconclusive**: the run cannot be scored (for example, the audit fails on most scenarios).

H1 gets the weaker of its two sub-classes; any Contradicted sub-hypothesis makes H1 Contradicted. v1 receives the
same descriptive classification for reference only. This phase does not decide or authorize EXP-3 phase 2; it
reports whether the gate's condition is met on held-out data.

**Overfitting statement.** `RESULTS-1b.md` compares the held-out v2 numbers with the development-set numbers
(13/13 recall, 0/15 false questions on P3) and states explicitly whether, and by how much, the held-out numbers are
worse, as evidence of overfitting to P3.

## 7. Known limitations, stated in advance

- 30 rules in 17 scenarios: one miss moves recall by 3.3 points; the intervals are wide.
- One independent author wrote both the corpus and its labels; SUPPORTED/TECHNICAL judgements are that author's.
- The handoffs are built by the experimenter's fixed rules (phase 1 §4), with empty observations.
- The corpus author knew the categories of v1's phase-1 misses only through `PREREGISTRATION.md`/`exp3.py`/P3 files
  (not `RESULTS.md`), and wrote varied syntactic forms; the corpus is still synthetic F# in a P3-like style.
- No agent in the loop.
