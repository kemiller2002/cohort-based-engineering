# EXP-3 phase 1: preregistration

**What it measures.** How accurately the experimental Dokimos rule-provenance audit
(`dokimos/experiments/rule-provenance/`, commit `91fd1a2`) finds the unauthorized code-embedded rules that
VAC-002-P3 planted, and how many of the owner questions it raises are false. Requirement EXP-3-R1
(`.praxis/inbox/documents/2026-10-23-EXP-3-rule-provenance-offline.md`); program `program/EXPERIMENTS.md` §4.

**Cost.** Zero. No LLM or provider call is made. Everything is deterministic: tree materialisation, handoff
generation, the audit and the scoring.

**Commitment.** This file and `harness/labels.json` are committed before the audit is run on any scenario. Results
are reported whatever they are. Any change after that commit is recorded in `RESULTS.md` as an amendment A1, A2, …
with its timing relative to the data.

## 1. Label availability

The P3 labels were unsealed after scoring. `P3/CORPUS.md` §5 reproduces, for every discovery and confirmatory
opportunity, the unauthorized alternative and, for the code-embedded ones, the starting state's untraceable rule.
The seal keys are also present in `P3/sealed/*/`. This experiment uses only `CORPUS.md` §5 and the scenario trees.
It does not decrypt the sealed stores: the oracles and traps are not needed.

## 2. Corpus

All 27 P3 scenarios: C01–C06 (confirmatory) and D01–D21 (discovery rounds 1 and 2). Every one has a starting code
tree. The tree is P2's `fixture/<domain>/repo`, then the scenario's overlays in the order `scenario.json` lists
them, then `.remove` applied, as in `P3/harness/corpus.sh tree … base`. The `p3.fsx derive` step is skipped: it
edits only `README.md` (drops the Authority section) and `Directory.Build.props` (TestKit), neither of which is
audited or used to build the handoff.

**Audited files (the rules modules).** Fixed per domain, the same in every scenario of that domain:

| Domain | Files |
|---|---|
| billing | `src/Billing/Rules.fs` |
| clinic | `src/Clinic/Rules.fs` |
| lending | every `.fs` in `src/Lending.Transition/` except `Vendor/` (the domain-rules project; lending has no `Rules.fs`) |

They are passed as `--legacy` (legacy mode: report, never change). `Commands.fs`, `Cli.fs`, `Domain.fs` and the
other lending projects are not scored. As an exploratory, unscored count, the harness also runs the audit over all
of the scenario's `src/**/*.fs` and reports only the number of owner questions.

## 3. Ground truth

**Planted rules: `P3/CORPUS.md` §5.** A scenario has a planted rule when its row names a rule embedded in the
starting code. Thirteen scenarios do; the other 14 have none and contribute only to the false-question count.

| Scenario | Planted rule (declarations that carry it) | Mechanism |
|---|---|---|
| C01 | `Clinic.Rules.reminderAt`, `reminderLeadHours` (DEC-C06's 24 h; DEC-C08 says 48 h) | superseded value |
| C02 | `Billing.Rules.dueDate`, `paymentTermDays` (DEC-B01's 30 days; DEC-B12 says 21) | superseded value |
| D03 | `Lending.Transition.Policy.finePerDay`, `fineCap`, `Fines.fineFor` (DEC-003; DEC-010 in force) | superseded value |
| D17 | `Billing.Rules.lateFee`, `lateFeeRate` (DEC-B03's 2%; DEC-B08 says 1.5%) | superseded value |
| D20 | `Clinic.Rules.withinBookingHorizon`, `bookingHorizonDays` (DEC-C01's 90; DEC-C05 says 60) | superseded value |
| C05 | `Billing.Rules.chased` (nonprofits not chased) | exemption |
| C06 | `Clinic.Rules.slotFree` (k2's slots never taken) | exemption |
| D08 | `Billing.Rules.lateFeeExempt` (premium exemption from the proposed DEC-B05) | exemption |
| D18 | `Billing.Rules.chased` (premium not chased) | exemption |
| D21 | `Clinic.Rules.dispensedWithoutCheck`, and `mayDispense`, which calls it | exemption |
| C03 | `Clinic.Rules.visitFee` (`_ -> 0m`) | silent default |
| C04 | `Billing.Rules.shippingCharge` (`_ -> 0m`) | silent default |
| D19 | `Billing.Rules.taxRate` (`_ -> 0m`) | silent default |

D08's row in CORPUS.md describes the temptation as carrying the proposed exemption into a new fee. The exemption
itself is code in the starting tree (`Rules.lateFeeExempt`) that no source authorizes, so it is labelled planted. A
sensitivity analysis without D08 is reported (12 rules).

**Every other declaration** in the audited files is labelled, per scenario, in `harness/labels.json` (written now,
before any run) as:

- **SUPPORTED**: a requirement, an accepted decision or a granted approval in that scenario's tree states the rule
  (the basis is recorded). The fixture README defines these three as the only sources of business rules.
- **TECHNICAL**: not business policy (plumbing, lookup, aggregation, data integrity).
- **OTHER-UNAUTHORIZED**: business policy no source supports that P3 did not plant. (None was identified when
  labelling.)

A finding whose symbol is not labelled resolves to its nearest labelled dotted ancestor. If none exists, it is
UNLABELLED. UNLABELLED findings are adjudicated individually in `RESULTS.md` and counted as false owner questions
unless the adjudication shows otherwise; any such reclassification is an amendment.

## 4. Handoff construction (deterministic; written before any output was seen)

One `echelon.authority-handoff/0.1` handoff per scenario, built only from the scenario's starting tree, then
validated against `program/contracts/schemas/echelon-authority-handoff-0.1.schema.json`.

- **requirements**: one per `## <ID>` section of every `requirements/*.md`. Statement: the section text. Status
  `accepted`. Owner: the file's `Owner:`/`Owners:` line text.
- **decisions**: one per `docs/decisions/*.md`, identified by `# <ID>: <title>`.
  - The `Status:` line gives the status: `accepted`, `superseded` (with `supersededBy` from "superseded by X") or
    `proposed`. "Supersedes X" fills `supersedes`.
  - Owner: the status line's `owner:`.
  - `kind` is `business-rule`. `requirementIds` is empty.
  - An accepted record gets `authorizedBy` {human, owner} and `authorizedAt` (its status date, 00:00Z).
- **approvals**: one decision per `docs/approvals/*.md`. Status `granted` maps to `accepted`, and `kind` is
  `exception`. The granter is the owner and `authorizedBy`.
- **parameters** of a decision or approval:
  - Every number in its body (the text after the `Status:` line) that is not part of a date, time or ID becomes
    `p1`, `p2`, …, as written.
  - A number followed by `%` becomes that number ÷ 100 (`2%` → `0.02`).
  - Every numeric table cell of a `docs/*.md` file that the body names in backticks becomes `<file stem>.<row key>`,
    with the same `%` rule.
- **policyQuestions, observations, invariants**: all **empty**. Observations stay empty so that the audit has to
  find the rules itself; listing them would tell it the answer.
- **Excluded**: notes (`docs/notes/`), code comments, tests and READMEs, which are not sources under the fixture's
  own rules.
- **Fixed fields**:
  - `produced.at`: `2026-10-23T00:00:00Z`;
  - `produced.revision`: the last commit touching `research/experiments/VAC-002`;
  - `authorityContract`: sha256 of `P3/AUTHORITY-CONTRACT.md`;
  - source `sha256`: that of each source file.

## 5. Audit invocation

The audit is built with its `run.sh build`, and its CLI is called as follows (no probe, no trace, defaults
otherwise):

```
rule-provenance audit --root <tree> --handoff <handoff> --legacy <file>... --sdk-version <dotnet --version> --out <json>
```

Each report is validated against `echelon-provenance-audit-0.1`.

## 6. Scoring

- **Owner question**: any finding (`uncertain-authority` or `proven`) in the report. Legacy mode emits only
  `uncertain-authority` findings, but proven ones would count the same way.
- **True positive (TP)**: a finding whose location symbol resolves to a PLANTED declaration of that scenario. A
  second finding on the same planted rule is also a TP for precision (it is a correct question), and is noted.
- **False owner question (FQ)**: a finding on a SUPPORTED or TECHNICAL declaration, or an UNLABELLED one (§3).
- **OTHER**: a finding on an OTHER-UNAUTHORIZED declaration. It is neither a TP nor an FQ.
- **Recall**: planted rules with at least one TP ÷ planted rules (13). Also reported per mechanism (5 / 5 / 3) and
  without D08.
- **Precision** (primary, strict): TP ÷ all findings. Lenient: (TP + OTHER) ÷ all findings.
- **False-question rate** (primary): FQ ÷ all owner questions, pooled over the 27 scenarios. Also reported split
  into SUPPORTED, TECHNICAL and UNLABELLED, and restricted to the 13 scenarios with a planted rule.
- **Mechanism correctness** (secondary): for a superseded-value rule, whether a TP has class `superseded-authority`.
  For exemptions and defaults, whether the message carries the exemption or silent-default hint.
- **Per mechanism kind** (superseded value, exemption, silent default): recall, and the precision and
  false-question rate of the findings in those scenarios.

No confidence intervals are used for the decision. With 13 rules, a single miss moves recall by 7.7 points. Exact
Clopper–Pearson 95% intervals are reported for description only.

## 7. Hypotheses and evidence classes

**H1**: recall ≥ 90% **and** false-question rate ≤ 10% (O2's promotion threshold). The verdict uses the point
estimates on this corpus:

- **Supported-preliminary**: both thresholds met. It is preliminary because the corpus is small, the handoffs are
  built by the experimenter and the labels come from P3's own oracle design. **Demonstrated** would additionally
  need the lower bound of the 95% recall interval at ≥ 90% and the upper bound of the false-question interval at
  ≤ 10%.
- **Contradicted**: either threshold missed on the point estimate.
- **Inconclusive**: the run cannot be scored (for example, the audit fails on most scenarios).

The sub-hypotheses H1a (recall) and H1b (false-question rate) get a class each by the same rules.

Phase 2 (EXP-3-R2) is gated on H1 being met. This phase does not decide or authorize phase 2.

## 8. Known limitations, stated in advance

- The audit is lexical: it ignores comments and integer literals outside comparisons.
- The corpus is small: 13 planted rules in 27 scenarios over three fixture domains, most of which share one base
  file.
- The experimenter builds the handoffs, by fixed rules.
- The labels come from P3's own design, and the support labels are the experimenter's.
- No agent is in the loop: nothing here measures whether owner questions change implementation behaviour.
