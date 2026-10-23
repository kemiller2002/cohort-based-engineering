# Experimental program

**Status:** designs only. **No paid execution is authorized.** Every paid phase names a ceiling that needs explicit
owner authorization (OD-1) before it can start. Zero-cost phases (offline replay, deterministic audits) may run without
authorization because they spend no provider budget, but they still preregister before looking at outcomes.

Conventions are reused from VAC-001/VAC-002 rather than reinvented:
- a FREEZE commit before any run, with amendments logged against the data;
- sealed oracles, with keys published after scoring;
- evidence classes: Demonstrated, Preliminary, Inconclusive, Contradicted;
- a hard ceiling per phase and a stop file at 80%;
- cost per independently accepted requirement, priced from `research/pricing/anthropic.price-table.json`.

## 1. What is already settled and will not be repeated

| Question | Settled by | Why not repeated |
|---|---|---|
| Does a continuous agent beat a fresh agent per change on cost at equal correctness? | VAC-001 (−40.9%, CI −48.1% to −33.0%) | Demonstrated on its fixture. EXP-4 reuses it |
| Does executable authorization (contract v0.2) prevent unauthorized decisions? | VAC-002-P3 (0 prevented, 10 false rejections) | Contradicted. Re-testing needs R-ADM-1..3 fixed first **and** a test of prevented errors (P3-02-R4) |
| Do announced temptations discriminate on the current model? | VAC-002-P3 discovery (1/40) | They do not. New corpora must embed rules in reused code (P3-01-R4) |
| Does architectural guidance or enforcement change correctness on the four-tier fixture? | ARCH-001 (128/128, ceiling) | Ceiling. ARCH-002 (CBE#17) is the violation-prone replication |

## 2. EXP-1: typed construction

- **Source:** VC-001 (CBE inbox, merged via CBE#22). This is the existing requirement; EXP-1 is its preregistration
  plan, not a new requirement.
- **Question:** does provenance-backed constrained construction reduce unauthorized consequential decisions and total
  cost per accepted requirement, compared with conventional and strictly typed implementations?

| Arm | Treatment |
|---|---|
| A | Conventional TypeScript |
| B | Strict TypeScript with explicit domain types (discriminated unions, branded types, `strict` on) |
| C | Conventional F# domain modelling |
| D | F# with provenance-backed constrained construction: the C1 handoff, the Ordo-constructed model (B2), and a Dokimos audit (B3) available to the agent |

**Preregistered hypotheses:**
- **H1 (construction model):** D has fewer unauthorized consequential decisions than C. Primary comparison: D vs C.
- **H2 (language):** C has fewer compile-detectable invalid states reaching tests than B.
  - Caveat: language and ecosystem differ; it is reported as descriptive, not causal.
- **H3 (cost):** D's cost per independently accepted requirement is no more than C's +10%. Non-inferiority margin
  fixed in advance.
- **H4 (harm):** D has no more false rejections of authorized decisions than C. This guards against repeating P3's
  control-induced harm.

**Workload.**
- Two bounded fixtures with equivalent requirements across arms:
  1. the invoice slice, extended to about 12 requirements;
  2. a second domain (scheduling or lending) reusing P3's C01–C06 mechanisms.
- Each contains:
  - an inherited unauthorized exemption;
  - a superseded rate still in code;
  - a silent default for an unlisted case;
  - an unresolved policy question;
  - a persistence authorization boundary.
- **Baseline qualification first:** arm A must show ≥ 20% unauthorized decisions on the qualification run, or the
  corpus is redesigned before any treatment run. This avoids another ceiling (P1, P2, ARCH-001).

**Frozen acceptance:**
- functional oracle (sealed);
- authority oracle (sealed; P3 standard: a consequential behaviour is authorized only if a requirement, an accepted
  decision or a granted approval supports it);
- blinded review.

**Metrics:**
- correctness (oracle pass), unauthorized decisions, false rejections;
- compile failures, repair cycles;
- tokens (input, output, cache read, cache write), cost, elapsed time.
- Unavailable values stay unavailable.

**Budget:**
- Qualification: **$40 hard** (stop at $32).
- Pilot: about 4 blocks × 4 arms on two fixtures, **$120 hard** (stop at $96).
- Confirmatory: sized from the pilot. Requires a new authorization.

**Prerequisite:** B4 passes all five frozen slice outcomes. Without a working D arm, EXP-1 would test an unbuilt tool.

**Limitations to state in advance:**
- one model family;
- small n;
- B4 is a prototype;
- TypeScript arms use no Echelon tooling, so D vs A mixes language and tooling.

## 3. EXP-2: verification scheduling

**Question:** does dependency-aware, checkpoint-driven verification reduce CI executions and time to accepted release
without increasing escaped defects?

**Phase 1: offline replay, $0 provider cost (no authorization needed).**
- Take ≥ 50 consecutive historical commits from Praxis and Dokimos main, with their CI outcomes from GitHub Actions
  history.
- For each commit compute two things:
  - the A1 selection in shadow mode (with the C5 map preregistered **before** the replay);
  - the checkpoint-CI schedule (full CI only at PR-ready or checkpoint commits).
- Counterfactual metrics:
  - CI executions and CI minutes avoided;
  - failures that the selected or scheduled CI would have missed, or caught later (escaped or delayed), and by how
    many commits.
- **H1:** ≥ 30% fewer CI minutes with 0 escaped failures on the replay set.
- **H2:** median detection delay ≤ 1 checkpoint.
- Escaped failures are listed individually, never summarized away.

**Phase 2: prospective shadow.**
- A1 runs in shadow on real program work for two weeks. Its predicted selection is recorded next to the full CI
  actually run.

**Phase 3: Rehearsal comparison (observational).**
- Rehearsal 3 already tests deferred verification at the application level (R3-DV-*).
- EXP-2 does **not** alter Rehearsal 3. It reads R3's CI execution and defect ledger as an observational comparison
  with R001 and R002, using R3-DV-011's denominators.

**Limitations:**
- Replay cannot see defects that historical CI also missed.
- Replay does not cover flaky failures. These are classified, not discarded.

## 4. EXP-3: rule provenance before implementation

- **Source:** VAC-002-P3-03-R3 and VC-004 R6 (existing), plus P3-01-R2's powered-confirmation design.
- **Question:** does identifying unverified inherited rules *before* implementation reduce unauthorized consequential
  decisions?

**Phase 1: offline audit accuracy, $0 (no authorization needed).**
- Run the B3 audit over the P3 corpus: C01–C06 plus the discovery scenarios, with their **sealed** labels of which
  code-embedded rules are unauthorized.
- Metrics: precision and recall of `uncertain-authority` findings against those labels, and the false owner-question
  rate.
- **H1:** recall ≥ 90%, false-question rate ≤ 10%. These figures are O2's promotion threshold.
- Preregister the label mapping before running.

**Phase 1 result (2026-10-23, $0): H1 Contradicted.**
- Preregistered at `8f68c6d`; results at `cd41e5f`, in `research/experiments/EXP-3/RESULTS.md`.
- Across 27 P3 scenarios with 13 planted rules: recall **5/13 = 38.5%** (CI 13.9–68.4%), false-question rate
  **57/63 = 90.5%**.
- By mechanism:
  - silent defaults: 3/3 found;
  - superseded values: 2/5 found;
  - **exemptions: 0/5 found, including C06**, the case that beat every control in P3.
- Causes, all in the lexical method:
  - whole-number date constants are ignored;
  - comparisons against named-type values are not treated as constants;
  - a condition split across lines is missed;
  - decision citations in comments are dropped, so every unmarked rule becomes a question.
- **Consequences:**
  - Phase 2 does not qualify.
  - The B3 audit stays experimental and off every default path.
  - O2's promotion threshold is unmet.
  - The P3 corpus is now a **development set**. The next audit version (typed analysis: FSharp.Compiler.Service
    symbols, constants of any numeric type, union-case comparisons, and accepted-decision citations matched to
    values) must be confirmed on a **held-out** corpus that was not used to tune it, such as new VC-001 fixtures, to
    avoid overfitting.

**Phase 2: paid, needs authorization.** Paired arms on P3-style scenarios:
- A: no contract;
- B: four-sentence contract;
- C: contract plus the audit's owner questions shown in the brief before implementation (non-blocking).

- **H2:** C has fewer unauthorized decisions than B.
- **H3:** C's cost per accepted requirement is ≤ B's +15%.
- Include the known P3 failure mechanisms:
  - superseded rate (C01, C02);
  - unrecorded exemption (C05, and C06's "operational fact" framing);
  - silent 0.00 default (C03, C04, D19);
  - implementer tests that lock errors in (D19, D21).
- **Budget:** 28–39 blocks per the frozen P3 simulation. **$60 hard** (stop at $48).

## 5. EXP-4: agent continuity

- **Reuse VAC-001** as the evidence base for continuity by default. That rule is already adopted in CBE as
  VAC-CBE-001-R1.
- **No new run** unless a question remains that VAC-001 could not answer. Two do:
  - reliability under a failing baseline (R-EXP-1 / VAC-003);
  - behaviour past compaction (R-EXP-2 / VAC-004).
- Both are preregistered and remain **unfunded**: pilot ceilings $80 and $110, needing OD-1.
- This program does not re-preregister them.

## 6. Promotion criteria

A change moves from experimental to an approved default only when all of the following hold:

1. **Evidence:** the experiment's primary hypothesis is Demonstrated or Supported, not Inconclusive. Or, for a policy
   adopted on grounds other than effect (such as R-PRAX-1), the record says so explicitly.
2. **Correctness:** no regression in correctness or escaped defects on the evidence set. Any false rejection of an
   authorized decision is reported, and the rate is under the experiment's preregistered bound.
3. **Cost:** cost per accepted requirement is within the preregistered non-inferiority margin, or better.
4. **Engineering:** the implementation is merged on main with CI green, released, recorded in the Registry, and
   approved by the owner (A6a).
5. **Reversibility:** a documented way to turn it off.
6. **Rehearsal 3:** promotion never happens *into* an in-flight Rehearsal 3 baseline (RELEASE-GATES §6).

## 7. Experiment ingestion

| Experiment | Repository | Intake |
|---|---|---|
| EXP-1 | cohort-based-engineering | VC-001 (merged; pending claim) |
| EXP-2 | cohort-based-engineering | `.praxis/inbox/documents/2026-10-23-EXP-2-verification-scheduling-replay.md` |
| EXP-3 | cohort-based-engineering | `.praxis/inbox/documents/2026-10-23-EXP-3-rule-provenance-offline.md` |
| EXP-4 | — | none (reuse) |
