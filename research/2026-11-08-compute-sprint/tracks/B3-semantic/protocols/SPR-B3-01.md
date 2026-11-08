# SPR-B3-01 — Semantic pre-T0 package checks (preregistration)

Worker B3-001, 2026-11-08. Parent RD-000. This file and the check code under `checks/` are committed **before any check
or unit test is executed**. Every later change to check code or rules is recorded in the Deviations addendum at the end.

## Question

Can a cheap, generic semantic check on a frozen requirements package catch Rehearsal 8's two semantic blockers before T0,
without false alarms on the corrected package and on another rehearsal's frozen package?

- R8-INV04 (Track B event B-E-094, DEV-R8-11): frozen INV-04 caps reconciliation reads at four per 60 s under total
  network failure, but SM-SAVE T-S31 (CheckAgain) and T-S32 (WentOnline) issue a read with no count or clock.
- R8-CMDBODY (B-E-093, DEV-R8-09, CR-T17-01): frozen IF41-DOMAIN `CommandEnvelope` carries no command body.

## Hypotheses

- H1: C1 (state machine × quantitative invariant) flags INV-04 against T-S31 or T-S32 on the R8 frozen package.
- H2: C2 (command carrier body) flags `CommandEnvelope` on the R8 frozen package.
- H3: neither primary check raises any alarm on the control packages.
- H4 (Causa, lower priority): no pre-T0 artifact implies the T18→T20 dependency (B2's claim). C4 tests it.

## Packages (all read from git objects of the read-only clone `/home/user/sprint-scratch/B2/indy-init-full`)

| Label | Role | Commit | Package | Notes |
|---|---|---|---|---|
| R8-frozen | target | 1cb27ec (last main commit before R8 T0 2026-11-01T17:31:24Z; B2's pre-T0 commit, contains plan f85081f) | v4.1.1 | the frozen package R8 ran on |
| R8-corrected=R9-frozen | control | bc3c381 (R9 pre-T0, B2) | v4.1.2 | v4.1.2 = AMENDMENT-4.1.2 (ODR-V412-01..03, 05) which resolved DEV-R8-09/-11/-12; identical to its compile commit 4d29296 (empty diff). It is also R9's frozen package, so "corrected" and "R9" are one control |
| R10-frozen | control | 89f5840 (R10 pre-T0, B2) | v4.1.5 | + R10 slice manifest for C4 |
| Causa-frozen | control; C4 target | dae2347 (Causa pre-T0, B2) | v4.1.6 | + Causa slice manifest for C4 |

Inputs per package: `<pkg>/state-machine-contracts.json` (compiled machine table, frozen + approved amendments),
`requirements-compiled/v4/invariants.json` (the frozen invariant set all four packages use), `<pkg>/contracts/*.fs`
excluding `negative/`, and the slice manifest where listed. SHA-256 of every input is written to raw.

## Check definitions (code: `checks/semcheck/`)

**C1 — state machine vs quantitative invariant (`rate.py`, `model.py`).**
1. Parse each invariant statement into clauses (split on `;`). A clause with "at most" yields one bound per item
   `<number> [≤3 modifiers] <plural noun>` after "at most"; a window `in|within|per|over|during <n> <time unit>` in the
   clause applies to all its items; no window → count bound. Scope: machines the invariant lists (all if none).
2. A transition *emits* resource R (the bound's head noun) when one effect phrase (effects split on `;`) contains R's
   stem, with an emission cue (send, schedule, issue, resend, retry, one, another, new, fresh, next, a, an, extra, …)
   among the four words before it and no negation (no, nothing, never, not, none, without, zero) before it.
3. A transition is *bounded* for R when its guard names R together with a number, or names a time span (strict);
   the *delegation* variant also accepts an effect that names the bound's own window (e.g. "60 s").
4. A transition is *repeatable* unless its guard depends on a remaining budget (fewer than, less than, not reached,
   left, remaining, below, under, at most, up to, within) or a time span. An exhausted-budget guard ("spent", "reached")
   stays true when repeated, so it does not block repetition.
5. Alarm: an emitting, unbounded, repeatable transition on a cycle (variant **loop**: a self-loop; variant **cycle**: the
   transition plus the shortest return path through repeatable transitions) whose stated delays (`after|at|in <n> s`)
   over N traversals stay below the window. Witness = shortest event path from the initial state + N+1 cycle traversals.
   Guards are otherwise assumed satisfiable (over-approximation), and invariant preconditions such as "under total
   network failure" are not evaluated.
- Four variants are run and reported: C1-loop, C1-loop-deleg, C1-cycle, C1-cycle-deleg.
  **Primary: C1-loop (strict).** The others are secondary.

**C2 — command carrier body (`carrier.py`).** Parse the F# contracts into records, unions, opaque types and
abbreviations. Candidates: every type whose name contains "Command", and every union case or non-function record field
whose name contains "Command". A candidate *has a body* when some value part can discriminate alternatives: a union of
≥2 cases, an opaque type, a type the package does not define, or a record/tuple/container with such a part. Scalars
(Guid, string, int, int64, bool, DateTime*, …), single-case wrappers of scalars and function fields do not.
Alarm: a candidate without a body. **Primary: C2.** Secondary **C2b**: the same with "Payload".

**C3 (secondary, exploratory; not part of the brief's catch count) — budget partition (`partition.py`).** A legal
(state, event) pair with a remaining-budget guard and no exhausted-budget transition is flagged (the DEV-R8-12 class:
no move when the budget runs out).

**C4 (Causa) — implied slice dependencies (`slices.py`).** Edge S→owner(req) for each invariant test in S's
acceptanceTests, req in that invariant's `sources`, owner = slice whose `requirements` hold req, owner ≠ S; SCCs over
declared `dependsOn` ∪ implied edges. Variants C4-all and C4-browser (only `playwright:` tests). Run on Causa (target)
and R10 (control).

## Matching criterion ("caught")

- R8-INV04 CAUGHT iff a primary C1 alarm on R8-frozen names INV-04 and machine SM-SAVE with transition T-S31 or T-S32.
- R8-CMDBODY CAUGHT iff a C2 alarm on R8-frozen has candidate `type CommandEnvelope` or a case/field whose type is
  `CommandEnvelope`.
- Causa cycle detectable iff a C4 cycle on Causa-frozen contains SL-T18 and SL-T20 with an implied edge SL-T18→SL-T20.
- Other alarms on R8-frozen are reported as *extra alarms* and adjudicated separately against the R8 evidence
  (DEVIATIONS.md, AMENDMENT-4.1.2.md); adjudication is post hoc and labelled so.

## False-positive control

The same code, unchanged, runs on R8-corrected (=R9-frozen), R10-frozen and Causa-frozen. **Every** alarm of every
variant on a control is reported. By default each control alarm counts as a false positive; any argument that a control
alarm is a real defect is reported separately and labelled post hoc. The C4 control is R10's slice manifest: every
cycle reported; cycles are false alarms unless a run record shows a matching blocker.

## Measures

CAUGHT / NOT CAUGHT per blocker and per variant; alarm counts per package and variant; runtime (load + per check, plus
total wall clock) on the shared, loaded host.

## Contamination disclosure (honest generality)

These checks were designed **after** reading the answer: DEV-R8-09/-11/-12, AMENDMENT-4.1.2.md, the v4.1.1 SM-SAVE
UnknownOutcome rows, and the corrected v4.1.2/v4.1.5/v4.1.6 UnknownOutcome rows (T-S31, T-S32, T-S47, T-S62–T-S65).
The emission-cue requirement (step 2) and the budget/exhausted distinction (step 4) were chosen with that vocabulary
in view; the delegation variant exists because v4.1.2 T-S65 delegates its bound to `ReconcileDue` "under the 60 s
window". I also know that a post-R8 tool, `percepta spec-preflight` (Echelon percepta, introduced for R9), was built
to find these three defects. The control is therefore **not blind**. Author predictions, stated before running:
C1-loop alarms on R8-frozen for T-S31, T-S32 and T-S47 and nothing on controls; C1-cycle raises extra alarms on all
packages through success paths; C2 alarms on CommandEnvelope (and `Msg.DomainCommand`) only on R8-frozen; C2b alarms on
`EventPayload` only on R8-frozen; C3 flags (UnknownOutcome, ReconcileReadFailed) only on R8-frozen; C4 finds an
INV-21 source edge SL-T18→SL-T20 on Causa (INV-21's sources EXT-DATA-004/005 are T20 requirements).
A check whose rule was shaped by the answer is classified as *post hoc / answer-informed* in findings, whatever it
scores.

## Reproduction

```
cd checks
python3 -m unittest discover -s tests -v
python3 -m semcheck.run            # writes ../raw/<label>.json
python3 -m semcheck.summarize      # writes ../results.csv  (added after the run if needed; see addendum)
```

## Deviations addendum

- **D1 (before any package run; found by the synthetic unit tests).** C2 candidate selection treated record fields
  and union cases whose *name* contains "Command" but which are metadata by name (`CommandId`) as carriers, so every
  command record alarmed on its own id field; and a single-case wrapper `EventPayload of ...` was counted twice (type
  and case). Fix in `carrier.candidates`: case/field names ending in Id/Ids/Key/Version/At/Count/Time/Kind are not
  candidates, and a single-case case named like its union is not a separate candidate. Committed with the first run.
  No package had been read by the checks at that point.
- **D2 (post-run, additive).** `summarize.py` (results.csv), `ablation.py` (post-hoc sensitivity of C1 to its
  answer-informed rules) and `probe.py` (post-hoc C2 out-of-sample probe on other Echelon F# code) were added after the
  preregistered run. They do not change any preregistered result; their outputs are labelled post hoc.
