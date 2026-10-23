# VAC-002-P3: minimal authority contract

**What it asks.** Do explicit, inexpensive authority instructions prevent unauthorized consequential decisions more
efficiently than a checklist, typed decision records or executable enforcement?

**Status: complete.**

- **Stage 1** qualified the baseline on its second, revised corpus.
- **Stage 2** ran the preregistered, powered-by-design confirmatory comparison: 90 executions, 18 paired blocks
  × 5 arms, blind-reviewed.
- **Primary result: inconclusive.** The contract's effect points the hypothesised way, but does not reach
  significance against a lower-than-planned baseline.
- **Spend:** $92.31 of $150.

**In one paragraph.**

- **The P2 confound, removed.** P2 gave every arm a README authority section. P3 removed it from every arm and gave a
  33-word contract to four of the five.
- **Announced temptations do not need it.** Without any authority instruction, the agent declined announced
  temptations itself: 1 unauthorized decision in 40 on P2's own families. P2's zero was not mainly the README
  section's doing.
- **Incidental temptations do.** What does produce unauthorized decisions is a rule embedded in code the work reuses,
  such as a superseded rate, an unrecorded exemption, or a silent 0% default.
  - **Discovery:** 11 / 15 without the contract, 1 / 15 with it.
  - **Confirmatory, six new scenarios:** 7 / 18 without it, 3 / 18 with it. Risk difference −0.22 (95% CI −0.56 to
    0), p = 0.125.
  - **Every one of P3's 36 confirmed unauthorized decisions** reused such a code-embedded rule.
- **The checklist and typed records added nothing** over the contract (identical in all 18 blocks).
- **Executable authorization added harm.** It prevented nothing, and rejected 10 authorized or harmless decisions,
  four of which turned into unauthorized defaults or a crash. It was worse than the contract alone in every discordant
  block, at +67% cost.
- **The contract was the cheapest arm per independently accepted requirement.**
- **One unrecorded exemption in reused code (C06) defeated every control.** Only the post-hoc blinded review caught it.

## The ten final questions

Evidence classes: **Demonstrated**, **Preliminary**, **Inconclusive**, **Contradicted** (`PREREGISTRATION.md` §9).

### 1. Does explicit authority guidance reduce unauthorized decisions?

**Probably, for the failure mode that remains, but not demonstrated.**

| Data | Without the contract | With it | Result |
|---|---|---|---|
| Confirmatory (paired, 18 blocks) | 7 / 18 | 3 / 18 | −0.22 [−0.56, 0], p = 0.125; all 4 discordant blocks favour the contract |
| Exploratory (incidental corpus) | 11 / 15 | 1 / 15 | Discovery data |
| Announced temptations, no instruction at all | 1 / 40 | — | The guidance has little to prevent there |

**Class.**

- **Inconclusive** at the preregistered threshold.
- **Preliminary** evidence of benefit for incidental, code-embedded rules.
- **Contradicted** that P2's README section explains P2's zero: preliminary, from a cross-experiment comparison.

### 2. Does a checklist add measurable value?

**No added value was observed.** The checklist matched the contract alone in all 18 blocks (3 / 18 each), at +2%
cost. P2 found the same. **Class: Inconclusive** (no difference observed; small sample).

### 3. Do typed decision records add measurable value?

**No added value for prevention was observed.** Records matched the contract alone in all 18 blocks, at +15% cost.
**Class: Inconclusive.**

### 4. Does executable authorization prevent errors that instructions cannot?

**No.**

- **Prevented, detected or corrected:** 0 unauthorized decisions.
- **Errors:** 7 / 18, against 3 / 18 with the contract alone, worse in all 4 discordant blocks (p = 0.125, Holm 0.5).
- **Why it cannot see the dominant failure:** it misses undeclared behaviour in reused code (C06).
- **Why it adds failures of its own:** it rejects the declared refusals and questions that would have prevented them
  (C03, C04).

**Class: Contradicted** in direction (not significant). The absence of any prevented error is **Demonstrated** for
this corpus.

### 5. Which mechanisms introduce false rejections?

**Executable authorization.**

- **Rejections.** Admission and the gate rejected 10 decisions in 10 of 18 executions, every one authorized or
  harmless:
  - a tie-break for output order;
  - keeping accepted behaviour unchanged;
  - recorded questions;
  - one correct refusal.
- **Harm.** Four led to harm: three unauthorized 0.00 defaults, and one correct refusal repaired into a crash.
- **Other arms.** The natural-language arms (B, C, D) had no false rejections, and no arm lost a hidden functional fact.

**Class.** **Demonstrated** as a mechanism, each rejection listed in `results/S2/e-rejections.json`. **Preliminary**
as a rate: the experimenter's unblinded application of the preregistered definition, which the frozen code
implemented only in part.

### 6. Which approach minimizes cost per independently accepted requirement?

**The contract alone (B).**

| Arm | Cost per accepted requirement |
|---|---|
| A, no instruction | $0.203 |
| **B, contract** | **$0.158** |
| C, checklist | $0.161 |
| D, typed records | $0.182 |
| E, executable authorization | $0.395 |

B / E = 0.40 (95% CI 0.15–0.63). **Class: Demonstrated (H5).**

### 7. Can the controls be simplified without compromising demonstrated reliability?

**Yes.**

- **Nothing beyond the contract showed any reliability benefit.**
  - The checklist and records: identical outcomes.
  - Executable authorization: worse outcomes.
- **The reliability that was demonstrated was all functional.**
  - Every arm passed every hidden functional fact.
  - The contract held B's error rate to the lowest observed, tied with C and D.
- **What the data do not support.** A claim that the contract alone is as reliable as some untested better control.
  That would need the noninferiority design P3 did not power.

**Class: Preliminary.**

### 8. Which mechanisms deserve further long-horizon testing?

- **The contract.** A powered confirmation (28–39 blocks of A and B, about $35–45), and a long-lived agent across a
  chain in which earlier work leaves untraceable rules that later work reuses.
- **Rule provenance auditing (R-PROV-1)** and **targeted, non-blocking independent review (R-REV-1).** These address
  the one failure mode that defeated every control, embedded rules in reused code. The post-hoc review caught all
  15 C06 errors.

**Class: Preliminary.**

### 9. Which engineering changes should be adopted immediately?

- **R-PRAX-1: the four-sentence contract in the Praxis implementation brief.**
  - Adopted on an independent justification: CBE principle 3 already requires it.
  - Measured cost +6%, and the lowest cost per accepted requirement.
  - Adopted as a statement of policy, not as a demonstrated reliability control.
- **R-ADM-1..3: fixes to the contract v0.2 checker**, before any further test of executable authorization.
  - Recorded questions and refusals of uncovered cases need no authority.
  - Self-citation does not reject a deferral.
  - A6 does not apply to presentation choices or to keeping accepted behaviour.
  - These are established defects.
- **R-EXP-3: corpus design.** Embed authority questions in reused code; announced temptations no longer discriminate.

**Class.** **Demonstrated** for the defects and the cost. **Preliminary** for the contract's benefit.

### 10. Which controls should be deferred or removed?

- **Remove** executable authorization from any default path. Reconsider only after R-ADM-1..3 and a test that shows
  prevented errors.
- **Do not adopt** the decision checklist.
- **Defer** typed decision records as a prevention control.
- **Defer** blocking independent review. P3 measured only post-hoc review, which earned its cost as a detector.

**Class: Demonstrated (cost, harm mechanism) / Preliminary (relative benefit).**

## Publication

- This record: kemiller2002/cohort-based-engineering#21. It also brings P2 onto `main`.
- Summary: kemiller2002/research-documents#25, `research/agent-reliability/VAC-002-P3-minimal-authority-contract.md`.

## Documents

| Document | Contents |
|---|---|
| [`BASELINE.md`](BASELINE.md) | P2's recovered findings; P3's discovery baselines |
| [`PROTOCOL.md`](PROTOCOL.md) | Provenance, reuse, arms, isolation, deviations D1–D6, exposure check, freeze records, amendments A1–A5 and CR-1 |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | H1–H6, outcomes, both stages, analysis, evidence classes |
| [`AUTHORITY-CONTRACT.md`](AUTHORITY-CONTRACT.md) | The frozen contract and what it replaces |
| [`ARM-EXPOSURE-MANIFEST.json`](ARM-EXPOSURE-MANIFEST.json) | Per scenario and arm: tree hash, brief headings, authority-marker hits (27 / 27 pass) |
| [`CORPUS.md`](CORPUS.md) | Discovery rounds 1 and 2, confirmatory corpus, the basis of each answer, unsealed tables |
| [`ORACLE-VALIDATION.md`](ORACLE-VALIDATION.md) | Self-checks: 43/43, 17/17, 18/18, 22/22; coverage and limits |
| [`BUDGET.md`](BUDGET.md) | Estimates and actual spend |
| [`DISCOVERY-RESULTS.md`](DISCOVERY-RESULTS.md) | Stage 1 rounds 1 and 2; the sizing run |
| [`CONFIRMATORY-RESULTS.md`](CONFIRMATORY-RESULTS.md) | Stage 2 per arm, per scenario, hypotheses; arm E's rejections |
| [`BLINDED-REVIEW.md`](BLINDED-REVIEW.md) | Method, agreement, review against oracle, categories |
| [`STATISTICAL-ANALYSIS.md`](STATISTICAL-ANALYSIS.md) | Methods, counts, effects, CIs, costs, domains, sensitivity, threats |
| [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) | Candidates A–E; requirements; Praxis intake |
| [`REPRODUCTION.md`](REPRODUCTION.md) | Every command, from tools to analysis |
| [`DERIVATION.md`](DERIVATION.md) | How the harness derives from P2's |

## Praxis intake

These documents are in `cohort-based-engineering/.praxis/inbox/documents/`; each states its target repository:

- `2026-10-23-VAC-002-P3-01-authority-contract-results.md` (Praxis, CBE);
- `2026-10-23-VAC-002-P3-02-executable-authorization-harms.md` (Ordo, CBE);
- `2026-10-23-VAC-002-P3-03-rule-provenance.md` (Dokimos, Ordo).

No GitHub issues were created.

## Layout

| Path | Contents |
|---|---|
| `harness/` | `p3.sh`, `p3.fsx`, `corpus.sh`, `analyze.fsx`, `sizing.fsx`, `briefs/`, `review/`, `smoke/`, `derivation/` (diffs from P2), `FROZEN*.sha256` |
| `fixture/testkit/` | The NuGet-free xUnit stand-in (D1) |
| `scenarios/Dxx`, `scenarios/Cxx` | Scenario files and overlays (P2 overlays are referenced in place) |
| `sealed/{discovery,discovery-r2,confirmatory}/` | Encrypted stores, manifests, seal records and (after scoring) keys |
| `results/S1A1`, `S1R2`, `S1B`, `S2` | Observations, scores, analyses, blinded reviews, workspace bundles; `S1-void` is amendment A1's void run |
| `budget-ledger.jsonl` | The orchestrator's measured model calls |
