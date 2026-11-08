# Track B3: Semantic pre-T0 package checks (SPR-B3-01)

> Committed by RD-000 from B3-001's final hand-back text. The harness refuses subagent report-file writes (D-010).
>
> - **Worker final commit:** `82f159b`.
> - **Preregistration:** `1af19bc`. The protocol and all check code were committed before any execution, including the unit tests.
> - **First run:** `f783da9`. **Post-hoc additions:** `73d3c3e`.
>
> Outputs:
> - `protocols/SPR-B3-01.md`, with a deviations addendum.
> - `checks/semcheck/`: Python stdlib, functional style.
> - `checks/tests/`: 24 unittest tests passing. `test_raw.py` re-runs every package from git and asserts that the raw records match exactly.
> - `raw/`, `results.csv`, `experiments.json`, `findings.json` (9 findings), `CHECKPOINT.md`.

## 1. Headline

| Blocker | Primary check | Outcome on the pre-T0 package |
|---|---|---|
| R8 INV-04 vs SM-SAVE | C1-loop | **CAUGHT** |
| R8 command body (CommandEnvelope) | C2 | **CAUGHT** |
| Causa T18↔T20 | C4 (lower priority) | **Detectable before T0.** This contradicts B2, but the detector is noisy |

- **Catch count:** 2 of R8's 2 semantic blockers.
- **False alarms from the primary checks (C1-loop, C2): 0 across three control packages.**
  - v4.1.2 at `bc3c381`: the corrected package, which is also R9's frozen package, so these two controls are one package.
  - v4.1.5 at `89f5840`: R10's frozen package.
  - v4.1.6 at `dae2347`: Causa's frozen package.
- **Secondary checks:** C2b and C3 also raise 0 alarms on all controls.
- **Cost:** 0.26–0.63 s in-process for all four packages (0.33–0.72 s process wall time) at load average 9–11. Each check takes ≤0.006 s per package. No build is needed.

**Caveat:** the checks were designed after the answer was known, and the corrected control text had been seen, so the control is not blind. See §4.

## 2. Artifacts located

All artifacts come from the read-only clone `/home/user/sprint-scratch/B2/indy-init-full`.

**R8 pre-T0 package** (`1cb27ec`, frozen v4.1.1):
- **INV-04** (`requirements-compiled/v4/invariants.json`):
  - per save request: at most 4 mutations and at most 3 automatic reconciliation reads, 2/4/8 s apart, plus one per offline-to-online change;
  - under total network failure: at most 4 mutations and 4 reconciliation reads in 60 s.
- **SM-SAVE** (`requirements-compiled/v4.1.1/state-machine-contracts.json`):
  - T-S31 CheckAgain: guard "automatic reads spent", effect "one reconciliation read";
  - T-S32 WentOnline: guard "true", effect "one reconciliation read";
  - T-S47 WentOffline: effect "one read on return".
- **Domain stubs** (`requirements-compiled/v4.1.1/contracts/00-DOMAIN-STUBS.fs`):
  - `CommandEnvelope = { CommandId: Guid; Investigation: InvestigationId; ExpectedVersion: AggregateVersion option }`;
  - `EventPayload of kind: string`.

**Correction, v4.1.2** (`AMENDMENT-4.1.2.md`, commits `f24b167`/`4d29296`, identical at `bc3c381`):
- **ODR-V412-01:** every reconciliation read is now windowed; T-S31, T-S32 and T-S47 are replaced, and T-S62, T-S63 and T-S65 are added.
- **ODR-V412-02:** `CommandEnvelope.Command : Command`, a union of 29 core cases plus an extension case.
- **ODR-V412-03:** adds T-S64 for DEV-R8-12.

## 3. Checks and results

### C1: state machine vs quantitative invariant (primary: C1-loop)

**How it works.** C1 parses each "at most N <noun>s [in W]" clause and links it to the machines the invariant names. A transition raises an alarm when all of these hold:
- an effect of the transition issues the bounded resource;
- its guard states no count and no window;
- its guard does not consult a remaining budget, so the transition stays enabled when repeated;
- it lies on a cycle whose stated delays fit inside the window.

Each alarm carries a witness: the shortest event path from the initial state, followed by N+1 cycle traversals.

**R8: 6 alarms.**
- **CAUGHT:** INV-04 "4 reads in 60 s" against T-S31 and T-S32. Witness: Edit, SaveRequested, AnswerLost, then the event ×5 at 0 s.
- **Related true positive:** T-S47, which v4.1.2 replaced for the same reason. This judgement was made post hoc.
- **3 misattributions:** these attach to the per-request bound "3 automatic reconciliation reads". The check matches only the head noun "reads" and ignores the qualifier "automatic".

**Controls:** 0 alarms each. The delegation variant, which also accepts an effect that names the window, gave identical results.

**C1-cycle (secondary):** 6 false alarms on each control, plus 2 extra on R8, so 18 control false alarms in total. They all come from the save-success loop T-S19/T-S58/T-S59 → T-S22 → T-S04. That loop cannot occur "under total network failure", but C1 does not evaluate invariant preconditions.

### C2: every command carrier needs a body that can tell commands apart (primary)

**R8: 5 alarms, CAUGHT.**
- `CommandEnvelope` itself. Its only fields are a Guid, an id wrapping a Guid, and a version option.
- Four carriers that inherit the gap:
  - `RefusedCommand`;
  - `RefusedCommand.Command`;
  - `SaveEffect.ExportCommands`;
  - `Msg.DomainCommand` (= CR-T17-01).

**C2b (secondary):** flags `EventPayload`, a bare kind string, on R8 only. This is the other half of DEV-R8-09.

**Controls:** 0 alarms.

### C3: missing move when a budget runs out (exploratory, not counted)

Flags (UnknownOutcome, ReconcileReadFailed) on R8 only. This is the stall recorded as DEV-R8-12.

### C4: Causa cycle

**How it works.** C4 adds an edge from slice S to the owner of each source requirement of every invariant test in S's acceptance tests.

**Pre-T0 evidence at `dae2347`:**
- SL-T18 owns `playwright:invariants/INV-21.spec.js`.
- INV-21's sources are EXT-DATA-004 and EXT-DATA-005, both owned by SL-T20 ("Connect flow and GitHub provider").
- SL-T20 declares a dependency on SL-T18.

Together these give exactly the T18↔T20 2-cycle in Causa's FINAL-REPORT. B2 inspected the test's obligation (PF-015-O4, owned by T18), not the invariant's sources. B2's claim that the dependency was "not in any pre-T0 artifact" is therefore **CONTRADICTED**.

**Noise:**
- On Causa, the same 6-slice cycle group also contains T16↔T22 and T19↔T22.
- On the R10 control, one 6-slice cycle group.
- The broader variant, which uses all invariant tests rather than only browser tests, gives cycle groups of 25–29 slices.
- None of these extra cycles can be checked against run records: Causa never got past T18, and R10 merged under owner rule B after its gate deadlock.

## 4. Generality

**C1 ablation (post hoc; `raw/ablation.json`).**
- The R8 INV-04 catch survives all five rule variants.
- Zero control alarms depends on two rules chosen after the control text was seen:
  - **Requiring an emission cue before the noun.** Without it, T-S47 "automatic reads pause" becomes a false alarm on every control.
  - **Treating a remaining-budget guard ("left", "fewer than") as blocking repetition.** Without it, T-S14 and T-S65 alarm on every control.
- **Classification:** the C1 catch is robust. The zero-false-alarm result is shaped by knowing the answer.

**C2 out of sample (post hoc; `raw/c2-probe.json`, six other Echelon F# source trees).**
- 12 alarms in 3 trees. None was judged a real defect:

  | Tree | What C2 flagged |
  |---|---|
  | time-entry | Per-command records, where the type itself names the command |
  | causa | A capability descriptor |
  | ordo | Command-name strings in CLI and receipt types |

- C2 selects candidates by type names containing "Command", so it is **not generic**. A generic version would restrict candidates to the parameter type of an operation that must accept several commands, such as `Decide`. That version was not tested.

**Shared ancestry.** The three control packages are successive amendments of one specification, so they are not independent specifications.

**Prior art.** Indy-init's docs record that `percepta spec-preflight`, built for R9 after R8, already finds all three R8 defects in 0.3 s and passes v4.1.2. This was not re-run here (NOT TESTED). Like B3's checks, it was built knowing the answer.

## 5. Deviations

- **D1:** synthetic unit tests showed C2 treating metadata-named fields such as `CommandId` as carriers, and counting a single-case wrapper twice. Both were fixed before any package was read.
- **D2:** `summarize.py`, `ablation.py` and `probe.py` were added after the preregistered run and are labelled post hoc. No preregistered result changed.

## 6. Implication

A semantic pre-T0 check on the frozen package is cheap: sub-second, with no build. It would have surfaced:
- both R8 semantic blockers;
- the DEV-R8-12 gap;
- the Causa T18↔T20 dependency.

What is supported is narrower than that:
- Cross-checking quantitative invariants against state machines, and checking that command carriers can tell commands apart, are feasible and discriminate on this specification family.
- These particular lexical rules are not shown to be generic.

**Recommendation:** route each alarm to an owner decision before T0, rather than blocking automatically, until the false-alarm rate has been measured on independent specifications.

## Reproduce

```
cd checks
python3 -m unittest discover -s tests -v
python3 -m semcheck.run
python3 -m semcheck.summarize
python3 -m semcheck.ablation
python3 -m semcheck.probe
```
