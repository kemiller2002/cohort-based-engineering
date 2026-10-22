# ARCH-002 protocol: violation-prone replication of ARCH-001

**Status:** PREREGISTRATION DRAFT (stage 1). It fixes the calibration, stop and sample-size rules **before** any
calibration trial. Stage 2, the freeze, follows calibration and the pilot. It records pins and the sealed-archive
digest. After stage 2, every change is a dated amendment in §11.

**Owner:** coordinator session `session_01E9jW5aZuFTf7HzifRjcs7y`, on the same branch as ARCH-001.

**Design detail:** [`design/INTERFACES.md`](design/INTERFACES.md). **Reuse of ARCH-001:** [`PROVENANCE.md`](PROVENANCE.md).

## 1. Question

ARCH-001 found no architectural benefit from four-tier guidance, Ordo contracts or mechanical enforcement, because
every arm made zero violations on a clean, small fixture.

ARCH-002 asks: **when the code base and its local precedent invite violations, do guidance, contracts and enforcement
reduce new architectural violations, and at what lifecycle cost?** It also asks whether the answer differs between a
frontier model and a cheaper one.

## 2. Hypotheses

All violation measures are **new** DET findings relative to the trial's start commit (`archcheck --baseline`).

| Id | Contrast (metric) | Predicted |
|---|---|---|
| Primary | D vs A, total model cost per accepted requirement (ratio − 1). Accepted = functional AND zero new DET sev≥2. | < 0 |
| H1a | B − A, severity-weighted new DET violations per trial at S2 | < 0 |
| H1b | B − A, architectural acceptance rate | > 0 |
| H2 | C − B, decision-test pass rate | > 0 |
| H3 | D − C, new DET violations at S2 | < 0 |
| H4 | D − C, phase-2 rework lines in pre-existing files | < 0 |
| H5a / H5b | D / C − 1 and D / A − 1, primary metric | < 0 |
| H6 | slope of the mean (D − A) new-violation difference on `crossTierCount` | < 0 |
| H8 | (D − A new-violation contrast in sonnet) − (same in opus) | two-sided |
| Lifecycle | D vs A lifecycle cost (phase 1 + phase 2 + modelled remediation of the new violations left at S2) | descriptive model |

H7 (grouped execution) is out of scope.

## 3. Design

- **Arms:** cumulative A–D, defined exactly as in ARCH-001. Completion orchestration is identical in every arm.
  Arm D's gate uses the baseline.
- **Fixtures:**
  - F1 `lending-brownfield`: 6 tasks. Brownfield, with 8 seeded violations giving 14 DET findings at start.
  - F2 `summa`: 3 tasks. A real-application snapshot at `8b0e93ea`, with 347 DET findings at start.
  - Each fixture's `check.sh` passes (109 and 53 checks).
  - F3 `signal` is deferred (PROVENANCE).
- **Models:** `claude-opus-5-5` and `claude-sonnet-5-5` (Claude Code 2.1.306, K1 isolation).
- **Budget:** 60 minutes per phase, 3 submits per phase.
- **Blocks:** one block is (fixture, task, model, replicate) and carries all four arms. Arm order is randomised within
  each block, and blocks are shuffled (seed 20261023).

## 4. Stage 0: calibration (arm A only; excluded from all analysis)

1. Run every task × both models × 1 trial in arm A: 18 trials (`harness/calibration-order.json`).
2. **Solvability:** a task that no model passes functionally in either phase is revised for clarity or scope. The
   revision is arm-blind, and the task is re-calibrated.
3. **Elicitation:** if the pooled new-violation rate (trials with ≥ 1 new DET sev≥2 finding / trials) is **0**, the
   fixtures are revised to be more violation-prone and re-calibrated. At most 2 revision rounds.
4. **Stop rule:** if the rate is still 0 after round 2, stop. Publish a second-ceiling report with no pilot or
   confirmatory trials.
5. Revisions use only arm A data. Using arm A's violations biases *against* the treatments (regression to the mean
   lowers arm A's later rate). This is conservative, and is disclosed. No arm B–D trial runs before the freeze.

## 5. Stage 1: pilot (excluded from all analysis)

- **Scope:** F1 T1 and F2 T1 × 4 arms × 2 models × 1 trial: 16 trials.
- **Purpose:** check the instruments in every arm, and get the pooled-across-arms variance inputs.

## 6. Sample size (never from an arm difference)

- `analysis/power.py` uses the pilot's acceptance rate and log-ratio variance, both **pooled over all arms**, for:
  - a D − A acceptance difference of 0.20;
  - a D/A cost ratio of 0.70.
- Rule: `replicates = max(2, min(needed, maxReplicatesUnderCap, 4))`.
- Cap: **USD 600** of confirmatory model cost.
- The confirmatory order is generated with that replicate count and committed before the first confirmatory trial.

## 7. Analysis (`analysis/analyze.py`)

- **Inference:** two-stage stratified cluster bootstrap. Tasks are resampled within fixture, then replicates within
  task; a block carries all its arms. 10,000 resamples. Contrasts are estimated within model and pooled as the
  unweighted mean of the per-model estimates.
- **Correction:** Holm across H1a–H8.
- **Classification:** as ARCH-001.
  - Supported: Holm p < 0.05 in the predicted direction (primary: the 95% interval excludes 0).
  - Not supported: the opposite direction, or the 95% interval inside the margin.
  - Otherwise: Inconclusive.
  - Margins as ARCH-001, plus H8 at 0.5.
- **Descriptive:** results by fixture and by model; fixed (pre-existing) violations; HEU findings; blinded review; the
  T6 and Summa T3 controls; cache share; a sensitivity analysis without timeouts.

## 8. Exclusions

As ARCH-001:

- **X1:** harness failure before the agent starts; re-run under the same id.
- **X4:** contamination; excluded. Patterns also cover `arch002-sealed`, ARCH-001/002 run directories, the source
  clones `/home/user/kemiller2002/*` and the other Echelon repositories.
- **X-integrity:** tamper; excluded.
- **X5:** timeout; scored as is.

**Coordinator rule (from ARCH-001's A3/A4 experience):** no harness or scorer file is edited while any trial is
running.

## 9. Integrity

As ARCH-001 §6:

- Sealed material is kept outside every repository and encrypted in git at the freeze. The key and manifest are
  published with the results.
- Scoring uses pristine copies, and verdicts are bound to commits.
- Observations stay out of git until all trials end.

## 10. Threats (known in advance)

- Seeded brownfield violations are synthetic. The Summa baseline is real but large (347 findings), and most of it
  comes from two rules.
- Both Summa traps exercise ARC-SYM-01 (JSON in Tier 1/2); F1's traps cover BND-01/02/03 and SYM-03.
- One language and two models from one family.

## 11. Amendments

| Date | Change | Reason |
|---|---|---|
| | | |
