# SPR-B4-01: Does `percepta spec-preflight` do what Indy-init's docs say? (preregistration)

Worker B4-001, 2026-11-08. Parent RD-000. This file is committed **before any build or run** of percepta and before the
harness is executed. Later changes go in the Deviations addendum at the end.

## Question

Indy-init docs (`docs/engineering-improvement/R9-READINESS-HANDOFF.md` at `dae2347`; percepta
`docs/SPECIFICATION-PREFLIGHT.md`) claim that `percepta spec-preflight`, built for R9:
1. on frozen v4.1.1 (R8) runs in about 0.3 s, exits 3, and finds INV-04 x T-S31/T-S32, the `CommandEnvelope` body gap,
   and the (UnknownOutcome, ReconcileReadFailed) gap (DEV-R8-12), plus one non-blocking unstated pair, and nothing else;
2. exits 0 on v4.1.2.

Is that true when re-run, how does it compare per defect with B3's C1/C2/C3/C4, and does it flag Causa's T18<->T20?

## Hypotheses

- H1: on R8 (v4.1.1) spec-preflight exits 3 and catches R8-INV04 and R8-CMDBODY (criteria below).
- H2: it also reports DEV-R8-12.
- H3: it exits 0 with no blocking finding on v4.1.2, v4.1.5 and v4.1.6.
- H4: it does not flag T18<->T20 on v4.1.6 (expected from reading the rules: it takes no slice/plan input).
- H5: median wall time per run is under 1 s (claim: 0.3 s).

## Packages (read from git objects of `/home/user/sprint-scratch/B2/indy-init-full` with `git show`; never modified)

| Label | Commit | Machines | Interfaces | Invariants | Catalog |
|---|---|---|---|---|---|
| R8-frozen (target) | 1cb27ec | requirements-compiled/v4.1.1/state-machine-contracts.json | requirements-compiled/v4.1.1/analysis/interface-specifications.json | requirements-compiled/v4/invariants.json | docs/COMMAND-EVENT-CATALOG.md |
| R8-corrected = R9-frozen (control) | bc3c381 | v4.1.2/... | v4.1.2/analysis/... | v4/invariants.json | same |
| R10-frozen (control) | 89f5840 | v4.1.5/... | v4.1.5/analysis/... | v4/invariants.json | same |
| Causa-frozen (control; T18<->T20 check) | dae2347 | v4.1.6/... | v4.1.6/analysis/... | v4/invariants.json | same |

These are the same packages and the same machine/invariant inputs as B3. The files are extracted to
`/home/user/sprint-scratch/B4/inputs/<label>/` and their SHA-256 recorded in raw/.

## Tool version identification and build

- R9 pin: Indy-init `kickoff/rehearsal-009/toolchain.lock.json` at bc3c381 expects `percepta-semantic` 0.4.0;
  `docs/competition-readiness/dependency-lock.json` at dae2347 pins tag `percepta-semantic-v0.4.0`, commit
  `4a53688238f205fdde474cc340378a89ddea0c09`. In `/home/user/ext/percepta` that tag resolves to 4a53688, which is also
  the clone's HEAD. So **V-R9 = V-HEAD = 4a53688**: one build covers both preregistered versions.
- Secondary version V-FIRST = `0ad2bd3` (first spec-preflight commit, before `92527ed` changed the at-limit regex). Built
  only if time allows; used for the blindness assessment (what changed after first contact with the R8 answer).
- Build: `git worktree`-free copy: `git -C /home/user/ext/percepta archive <rev> | tar -x -C /home/user/sprint-scratch/B4/src-<rev>`.
  Preferred, matching `distribution/percepta-semantic/package.sh`:
  `dotnet publish src/Percepta.Cli/Percepta.Cli.fsproj -c Release -r linux-x64 --self-contained true -p:PublishSingleFile=false -p:Version=0.4.0 -o /home/user/sprint-scratch/B4/bin-<rev>`.
  Fallback if the self-contained runtime pack cannot be restored: framework-dependent `dotnet build -c Release`, run with
  `DOTNET_ROLL_FORWARD=Major` on the installed .NET 10 runtime (the project targets net8.0). Which path was used is
  recorded. One build at a time (`-m:1` not required; builds are sequential).

## Command lines

Condition **DOC** (the documented four-input form, as in R9-READINESS-HANDOFF and r9.fsx):
```
percepta spec-preflight --machines <in>/state-machine-contracts.json --invariants <in>/invariants.json \
  --interfaces <in>/interface-specifications.json --catalog <in>/COMMAND-EVENT-CATALOG.md --out raw/<ver>/<label>.DOC.json
```
Condition **CI** (secondary; exactly the inputs Indy-init's `preflight-tooling.yml` passes for v4.1.5 at dae2347, i.e. no
`--catalog`): same without `--catalog`.

Each (version, package, condition) is run n=5 times sequentially by `harness/run_preflight.py`; exit code, stdout,
stderr, report JSON and wall time (`time.perf_counter` around the subprocess) are recorded. The report of run 1 is kept
in raw/; all runs' reports must be byte-identical (checked and recorded).

## Matching criteria ("caught"), against B3's defect list

On the DOC report (findings = union of `blockingContradictions`, `missingInterfaces`, `missingDecisions`, `warnings`,
de-duplicated by (rule, subjects)):
- **R8-INV04** CAUGHT iff a finding with rule `rate-bound-vs-unbounded-loop`, `blocking=true`, whose subjects contain
  `INV-04`, `SM-SAVE` and `T-S31` or `T-S32`.
- **R8-CMDBODY** CAUGHT iff a finding with rule `carrier-cannot-discriminate`, `blocking=true`, whose first subject is
  `CommandEnvelope`.
- **DEV-R8-12** (B3 C3, exploratory there) CAUGHT iff a finding with rule `counter-guard-without-complement` whose detail
  names `(UnknownOutcome, ReconcileReadFailed)` and whose subjects include `SM-SAVE`.
- **Causa T18<->T20** DETECTED iff any finding's subjects or detail mention both `T18` and `T20`.
- Exit code must be 3 on R8 and 0 on controls for the gate claims; recorded regardless.
- B3 side: B3's committed `results.csv` / `raw/*.json` (worker commit 82f159b). B3's outcomes are taken as recorded;
  additionally B3's checks are re-run from a copy in scratch (`/home/user/sprint-scratch/B4/b3-copy`) to confirm they
  reproduce (secondary).

## False alarms

- Control packages: every **blocking** finding is a false alarm of the gate (counted per package). Every non-blocking
  finding is counted separately as an "owner-decision note" and adjudicated post hoc (labelled) against v4.1.2's
  AMENDMENT/ODR text: real gap vs intended fail-closed vs wrong.
- R8: findings beyond the three defects are "extra" and adjudicated post hoc against R8's DEVIATIONS and AMENDMENT-4.1.2.
- B3 false alarms are counted the same way from B3's records, for primary checks (C1-loop, C2) and secondary
  (C1-cycle, C2b, C3, C4) separately.

## Blindness and generality (desk analysis)

- Compare commit dates of percepta `0ad2bd3`/`92527ed` with the R8 run window (Indy-init-rehearsal-008 history,
  2026-11-01) and with the R8 deviation records (DEV-R8-09/-11/-12).
- Read `src/Percepta.Core/Specification.fs` at 4a53688 and list, per rule, what is generic and what is lexically tied
  to this specification family; compare with B3's rules.
- Optional generality probe (post hoc if done): synthetic variants of the R8 inputs (e.g. bound reworded, loop made a
  2-cycle) to show rule limits stated in percepta's own Limitations section.

## Classification

Each finding is classed VERIFIED / SUPPORTED / INCONCLUSIVE / CONTRADICTED / NOT TESTED.

## Deviations addendum

- **D0 (build path):** the preferred self-contained `dotnet publish -r linux-x64` (as `package.sh`) restored and built
  in 36 s; the fallback was not needed. `percepta --version` prints `percepta 0.4.0`. This is a local rebuild from the
  tagged source, not the downloaded GitHub release archive (no network fetch of the release was attempted).
- **D1 (V-FIRST runs):** the secondary version 0ad2bd3 was run n=3 per cell (not 5), as a secondary condition.
- **D2 (POST HOC probe):** `harness/probe.py` (eight rewrites of the R8 inputs, run through both tools) was added after
  the preregistered runs. Its results are post hoc and labelled so. For P7 (carrier renamed) the preregistered
  `R8-CMDBODY` criterion requires the literal name `CommandEnvelope`, so the probe also reports a name-agnostic variant.
  For B3 the probe reports B3's own criterion and a stricter one (alarm attributed to the 'four reconciliation reads'
  clause), because B3 also alarms T-S31/T-S32 against the per-request 'three automatic reads' clause.
- **D3 (adjudication, POST HOC):** non-blocking extras on R8 adjudicated against v4.1.2's state machine and
  AMENDMENT-4.1.2 after the runs.
- **D4:** B3's checks were re-run from a scratch copy (`/home/user/sprint-scratch/B4/b3-copy`); results are identical to
  B3's committed raw for all four packages.
