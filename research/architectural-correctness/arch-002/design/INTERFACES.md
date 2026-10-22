# ARCH-002 shared interfaces (coordinator-owned, v0.1 draft)

ARCH-002 is the violation-prone replication that ARCH-001 called for (intake ARCH-001-04,
`.praxis/inbox/documents/2026-10-21-ARCH-001-04-violation-prone-replication.md`).

ARCH-001 is frozen published evidence. Its files are never modified. ARCH-002 copies its instruments and adapts
them under `research/architectural-correctness/arch-002/`, recording the source path and sha256 of each copy in
`arch-002/PROVENANCE.md`.

## 1. What changes from ARCH-001, and why

| ARCH-001 limit | ARCH-002 change |
|---|---|
| Clean, small fixture; ceiling at 0 violations in every arm | **Brownfield fixtures.** Existing violations and inconsistent layering near the code each task touches, so the local precedent is a bad pattern. |
| Tasks of about 3 minutes per phase | **Larger multi-feature tasks**, spanning several tiers |
| Synthetic code only | **Real-application snapshots.** Summa at `8b0e93e` (builds here) and, if feasible, Signal at `e19101f`. Read-only fixture copies; production repositories are never modified. |
| One model | **Two models:** `claude-opus-5-5` and `claude-sonnet-5-5`. Model is a blocking factor. |
| No calibration | **Arm-A-only calibration** before the pilot (§5) |

Out of scope, and deferred to a separate experiment: H7, grouped execution × enforcement. Running it here would make
grouping and enforcement impossible to attribute separately.

## 2. Arms (unchanged semantics)

| Arm | Material |
|---|---|
| A | Requirements only |
| B | + the doctrine (SDE-DOCTRINE-003 v0.2.1, byte for byte) and the fixture's instance document (tier map, placement rules) |
| C | + the `ecir/1` decision contract, `ordo ecir check`, and decision-id citation |
| D | + `archcheck` during development and in `submit` |

Completion stays identical across arms: the `submit` gate, at most 3 submits, and the final `ARCH002-DONE <head>` line.
Praxis is held out of every arm, as in ARCH-001.

## 3. Brownfield scoring: baseline-delta

A brownfield start commit already has violations. Architectural correctness of a trial is therefore defined
**relative to the start commit**:

- **New violation.** A DET finding at S1 or S2 whose key `(ruleId, file, symbol, enclosing module)` does not appear
  at the start commit, compared as multisets. Line numbers are ignored.
- **Fixed violation.** A start-commit finding that is absent at S1 or S2. Reported descriptively; never required.
- **Architectural acceptance.** Zero *new* DET findings of severity ≥ 2 (full policy plus sealed probes).
- **Arm D gate.** `submit` fails on new DET findings of severity ≥ 2 only. It never requires fixing pre-existing
  violations, because that would turn D's task into a different, larger task.

The verifier gains `--baseline REPORT.json`. A finding whose key matches the baseline's (multiset) is marked
`preexisting: true` and does not count toward the exit code. Exit 0 means no new DET finding of severity ≥ 2.

## 4. Fixtures and tasks

| Fixture | Description |
|---|---|
| F1 `lending-brownfield` | The ARCH-001 Lending app after plausible erosion: business rules leaked into the CLI, a Transition function reading the clock, duplicated limits, a use case calling a Persistence adapter's helper. Each seeded violation is recorded in sealed `seeded.json` with its rule id. The repository still builds and passes its own tests. |
| F2 `summa` | A snapshot of Summa at `8b0e93e`, as a fixture copy. Tier map proposed in `inventory/architecture-spec-inventory.md` §5.1, with Storage as Tier 2 (A6) and the composition-root exception for `*.Application/Runtime.fs` (A5). |
| F3 `signal` | Optional: a snapshot at `e19101f`, if it builds and a task is feasible. |

**Per fixture:**

- `repo/` (git-initialised by setup);
- `pack/` (the doctrine plus the instance document);
- `policy.json` (archcheck policy);
- `tasks/T<n>/`, with `requirement.md`, `acceptance/`, `contract.json`, `followup.md`, `followup-acceptance/`,
  `followup-contract.json` and public `task.json`.

**Sealed** (in `/home/user/arch002-sealed/<fixture>/`): `oracle/T<n>/{Initial,Followup}OracleTests.fs`, `oracle.json`
(decisionTests, conflictTests, regression), `probes.json`, `reference/T<n>/{good,trap,followup-good}`,
`task-private/T<n>.json` (trap, expected placement) and `seeded.json`.

**Task design rules:**

- Every task is solvable by every arm.
- At least two thirds of tasks have a trap that is functionally correct but architecturally invalid and *mirrors a
  nearby existing violation*.
- At least one control task has no architectural temptation.
- Follow-ups exercise the structure the initial task created.
- The follow-up's superseded initial tests are computed from `followup-good` (ARCH-001 A3 rule), not by hand.
- Target size: 15–30 minutes per phase for a strong model.

**Planned suite:** about 6 F1 tasks and 3–4 F2 tasks, plus up to 2 F3 tasks if feasible.

## 5. Calibration, pilot and confirmatory (to be frozen in PROTOCOL.md)

1. **Calibration (arm A only; excluded from all analysis).** Every task × both models × 1 run, arm A. Purpose: verify
   solvability and that the fixtures elicit violations.
   - Arm-blind revision is allowed up to 2 rounds, using only arm A data:
     - a task that no model solves functionally is fixed;
     - if the pooled new-violation rate is 0, the fixtures are made more violation-prone and re-calibrated.
   - Selecting or revising tasks on arm A's violations biases *against* the treatments: regression to the mean lowers
     arm A's confirmatory violation rate. This is conservative, and is disclosed.
2. **Pilot (excluded).** 2 tasks × 4 arms × 2 models × 1 replicate. Verifies instruments and gives pooled variance for
   the ARCH-001 §9-style rule (replicates = max(2, min(needed, cap, 4))). Cap: **USD 600** confirmatory model cost.
3. **Stop rule.** If calibration round 2 still shows a pooled new-violation rate of 0, stop. Report a second ceiling,
   with no confirmatory run.

## 6. Hypotheses: as ARCH-001, re-estimated

Primary, H1a/b, H2, H3, H4, H5a/b and H6 keep ARCH-001's definitions, using the baseline-delta violation measure.
Contrasts are estimated within model and pooled with model as a stratum. The bootstrap resamples tasks within
fixture, then replicates.

Added hypothesis **H8: the treatment effect on violations differs by model** (interaction D−A × model).

**Lifecycle cost model:**

- `lifecycle cost = cost(phase 1) + cost(phase 2) + remediation`;
- remediation = the measured cost per rework line (from phase-2 cost and rework, pooled across arms) × the
  rework lines needed to remove the *new* violations left at S2;
- the lines needed are estimated from the reference `good` vs `trap` diff size for the same rule.

This is labelled a model, and reported next to the raw costs.

## 7. Runs, isolation and integrity (as ARCH-001, with fixes built in)

- K1 headless sessions with fresh config, home and session id; tools Bash, Read, Edit and Write; the ARCH-001
  environment scrubbing.
- Prefix `ARCH002_`; run ids `ARCH-002-{CAL|PILOT|CONF|SMOKE}-<fixture>-T<n>-<model>-r<k>-<arm>`, where model is
  `opus` or `sonnet`.
- State in `/home/user/arch002-runs/`.
- Built in from the start:
  - every contract and probe file is outside the evaluated repository;
  - `submit` prints verifier errors verbatim;
  - no `--help | grep` feature detection (options pinned);
  - the scan run-id boundary fix;
  - narrowed own-state X4;
  - regression excludes superseded tests;
  - observations stay out of git until all trials end;
  - the sealed tree is encrypted in git at the freeze.
- Budget: 60 minutes per phase (larger tasks); timeouts are scored, not excluded.
