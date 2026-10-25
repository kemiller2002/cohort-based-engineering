# Next experiments

**Status: designs only.** No paid run is authorized (OD-1: zero-cost phases only). Each paid phase names a ceiling that
needs owner authorization. Conventions follow `program/EXPERIMENTS.md`: FREEZE commit before any run, sealed oracles,
a stop file at 80% of the ceiling, cost per independently accepted requirement priced from
`research/pricing/anthropic.price-table.json`, unavailable values reported as unavailable.

**Not redesigned here** (already preregistered; reuse them): R-EXP-1 / VAC-003 (failing baseline), R-EXP-2 / VAC-004
(compaction), EXP-1 (typed construction, VC-001), ARCH-002-02 (harder architecture tasks, H7 grouping).

**Selection.** The three designs below target the unresolved questions with the highest Indy Init relevance
(findings §5, questions 1–2) plus one zero-cost check on the top-ranked improvement. Every design starts with a
baseline qualification step, because five earlier experiments ended at ceiling.

---

## NX-1: computed verdicts against agent-written verdicts ($0, replay)

**Question.** How often does an agent-written completion or acceptance claim contradict the evidence that existed at
the same commit, and would a computed verdict have caught each one?

- **Baseline.** The verdict and status claims as written in R1, R2 and R3 (reports, ledgers, RQ/DF `status` fields,
  work-item completions).
- **Treatment.** The verdict computed from the same ledger at the same SHA by the priorities-item-1 rule (every
  mandatory gate PASS on one SHA, every cited evidence path present).
- **Workload.** Every commit in R1–R3 that changes a verdict, a ledger row or a ratification field.
- **Correctness measurement.** Two blinded labellers mark each claim supported / unsupported against the evidence at its
  SHA; disagreements adjudicated by a third. Known positives to recover: R1 R-21, R3 `db89a3a`, R3 remediation
  overstatement, R3 M5, R3 RQ-0009/0010, R3 DF-CAUSA-2026-0001.
- **Token and time measurement.** Not applicable (no agent runs); record labeller hours.
- **Failure classification.** Unsupported claim caught; unsupported claim missed (gate gap); supported claim wrongly
  refused (false refusal).
- **Hypotheses.** H1: the computed verdict catches ≥ 90% of unsupported acceptance claims. H2: false refusals = 0 on
  R2's accepted candidate `45644a7`.
- **Stopping criteria.** Complete when every in-scope commit is labelled; abandon if κ between labellers < 0.6 after
  adjudication rules are fixed once.
- **Why first.** It decides whether priority item 1 is sufficient before anyone builds it into Praxis.

## NX-2: fresh independent review at candidate points versus continuous self-review

**Question.** Does adding a fresh, read-only reviewer at candidate points reduce escaped defects enough to justify its
tokens, compared with the same continuous lead reviewing its own work?

- **Baseline (arm S).** One continuous lead implements and self-reviews, with an explicit "review your work against the
  requirements" step at each candidate.
- **Treatment (arm R).** The same lead implements; a fresh agent with no access to the lead's conclusions reviews at
  each candidate (R3 protocol: code, requirements, binding constraints; never edits).
- **Comparable workloads.** A fixed, frozen slice of the Causa read **and write** path, built from the same SHA of
  causa-data and the same frozen requirements, with a sealed list of planted provider divergences (422 for a missing
  branch, cacheable mutable reads, a stale branch head on write) and two planted requirement-preservation traps.
  Equal wall-time budget per arm.
- **Qualification.** Run arm S twice first. If arm S finds every planted defect in both runs, the slice is at ceiling:
  add traps before any arm R run.
- **Correctness.** Escaped planted defects (sealed oracle); escaped unplanted defects found by a post-hoc third review
  (blinded to arm); acceptance-claim accuracy (NX-1 rule).
- **Tokens.** Per-agent totals by bucket from Praxis ≥ 3.17 work-item attribution (records carry no timestamps:
  PRX-D4; price at the run date).
- **Execution time.** Wall time to candidate and to computed-ACCEPTED.
- **Failure classification.** Prevented, detected-by-CI, detected-by-review, repaired-with-regression, escaped.
- **Hypotheses.** H1: arm R escapes fewer planted defects than arm S. H2: arm R's cost per accepted requirement ≤ arm
  S + 25%.
- **Design.** 4 blocks × 2 arms, randomized order, same model and effort.
- **Budget.** Qualification **$30 hard** (stop $24); pilot **$90 hard** (stop $72).
- **Stopping criteria.** Stop at the ceiling; stop early if arm R's escapes ≥ arm S's in the first 3 blocks (futility).

## NX-3: requirements preservation under cohort derivation

**Question.** When a large requirement set is derived into one cohort's acceptance criteria, how many mandatory
obligations are lost, and does a required preservation gate reduce the loss without blocking legitimate derivations?

- **Baseline (arm N).** Agent derives the cohort's criteria from the frozen baseline with the current Praxis intake
  workflow and no preservation gate.
- **Treatment (arm G).** Same, with the hardened preservation gate (priorities item 2) required before derivation is
  accepted. The agent sees the gate's refusals and may repair.
- **Comparable workloads.** Three frozen baselines of increasing size: about 60, 150 and 374 requirements (the Indy-init#12
  manifest). This varies cohort size, which is H3's open risk.
- **Correctness.** Per P0 obligation: preserved verbatim, preserved in paraphrase (blinded labeller), weakened, dropped,
  or excluded with an authenticated owner approval. Seeded traps: one role swap, one negated restatement, one
  self-written approval.
- **Tokens and time.** Per derivation, by bucket; wall time; number of gate refusals and repair rounds.
- **Failure classification.** Dropped; weakened; bypass succeeded; false refusal of a faithful paraphrase.
- **Hypotheses.** H1: arm G drops fewer P0 obligations than arm N at every size. H2: in arm N, dropped P0 obligations
  rise with baseline size. H3: arm G's false-refusal rate ≤ 10% of faithful paraphrases.
- **Qualification.** Arm N at the 374 size must drop ≥ 1 P0 obligation in a qualification run, otherwise the traps are
  strengthened first.
- **Design.** 3 sizes × 2 arms × 3 replicates. Derivation only; no implementation, which keeps cost small.
- **Budget.** **$45 hard** (stop $36).
- **Stopping criteria.** The ceiling; or abandon H3 if the gate refuses > 50% of faithful paraphrases in the first
  replicate (the gate is then not usable and goes back to Praxis).

## Ordering and dependencies

| Order | Experiment | Cost | Depends on |
|---|---|---|---|
| 1 | NX-1 | $0 | nothing |
| 2 | NX-3 | $45 | hardened gate (Praxis intake `2026-10-24-REQ-PRES-001`) |
| 3 | NX-2 | $120 | a write-path slice; ideally after Rehearsal 4 |

None of these may modify Rehearsal 4 or the Indy Init event run. Rehearsals are observed only (RELEASE-GATES §6).
