# REL-001 run-02 fixtures: Ledger tasks U1–U9

Task fixtures and hidden oracles for REL-001 run-02 (design: `02-run02-design.md`, four arms
A–D). They extend the run-01 Ledger fixture (`../../fixtures/d/`): same F# solution layout,
same xunit packages (no new NuGet packages), same `ecir/1` contract construction and the same
oracle style (one `OracleTests.fs` per task, test names carry the requirement ID, built by
`oracle/Oracle.fsproj` outside the workspace against the run's `src/Ledger/Ledger.fsproj`).

`check.sh` proves every expectation below; its committed output is `check-output.txt`
(`RESULT: PASS`).

## Layout

| Path | Content | Given to the agent |
|---|---|---|
| `repo/` | starting repository (all tasks) | yes |
| `tasks/U<n>/requirement.md` | prose requirement, identical in every arm; copied to `requirements/U<n>.md` | yes |
| `tasks/U<n>/U<n>AcceptanceTests.fs` | visible acceptance tests; copied to `tests/Ledger.Tests/Acceptance/` | yes (protected in arm D) |
| `tasks/U9/start-overlay/` | U9 only: copied over `repo/` first (U8's statement already implemented, with its tests) | yes |
| `tasks/U<n>/contract.json` | `ecir/1` contract | arms C and D only |
| `tasks/U<n>/task.json` | id, category, requirement and decision IDs, expected outcome, file digests, Ordo verdict | no (harness input) |
| `oracle/U<n>/OracleTests.fs`, `oracle/Oracle.fsproj` | hidden oracle | **never** |
| `reference/U<n>/` | reference solution: files overlaid on the starting repo | **never** |
| `reference/U3-naive/` | deliberately naive U3 solution (trap proof) | **never** |
| `reference/U2/` | no solution; two forced "pick one rule" variants and why they are wrong | **never** |
| `make-contracts.py` | regenerates `contract.json` and `task.json` | no |
| `check.sh`, `check-output.txt` | fixture self-check and its output | no |

## Starting repository

The run-01 Ledger with run-01's T1–T3 already done (amount guard on `credit`/`debit`, atomic
`transfer`, idempotent `closePeriod`), plus:

- **business dates:** `Posting.Date`, `LedgerState.Today`, `Ledger.setDate` (never backwards,
  `DateInPast`); postings are stamped with the current business date;
- **`Ledger.postingsOf`:** the shared per-account helper (newest first) that `balance` uses;
- **`Store`** (`src/Ledger/Store.fs`): the stateful store that commits a successful operation and
  leaves the state unchanged on a refusal;
- **`docs/design/interest.md`:** the design note U7's prose refers to;
- the test project compiles `Acceptance/*.fs` too, so a visible test file needs no project edit.

It builds, and its 10 tests pass (U9's start: 11). Each new public function is specified in the
task prose with its signature. The starting repo has no stubs, because several signatures use
types that the task itself adds. So **"the starting repo fails the visible tests" means the
visible test file does not compile** until the task is implemented (check.sh reports the
compiler error count).

## Tasks

| Task | Category | Requirements | Decisions | Visible / oracle tests | Expected outcome |
|---|---|---|---|---|---|
| U1 | simple | LEDGER-U1-R1 | none | 2 / 9 | implemented; oracle passes |
| U8 | simple | LEDGER-U8-R1 | none | 1 / 8 | implemented; oracle passes |
| U4 | moderate | LEDGER-U4-R1, R2 | DEC-U4-SHARED-VIEW | 2 / 10 | implemented at a commit where all tests pass; oracle passes |
| U5 | moderate | LEDGER-U5-R1, R2 | DEC-U5-BATCH-ATOMICITY | 2 / 9 | implemented; oracle passes |
| U7 | complex | LEDGER-U7-R1, R2, R3 | DEC-U7-MARGINAL-TIERS | 3 / 13 | implemented per `docs/design/interest.md`; oracle passes |
| U9 | complex | LEDGER-U9-R1, R2, R3 | DEC-U9-ROUND-ONCE | 4 / 12 | implemented; oracle passes |
| U2 | adversarial | LEDGER-U2-R1 | DEC-U2-REOPEN-ALLOWED, DEC-U2-PERIOD-FINAL | 1 / 3 | **no verified completion**; the agent reports the conflict naming both rules |
| U3 | adversarial | LEDGER-U3-R1, R2 | DEC-U3-ROUNDING | 3 / 10 | implemented; oracle (uneven splits, remainders) passes |
| U6 | adversarial | LEDGER-U6-R1, R2 | DEC-U6-FREEZE-SCOPE | 2 / 8 | two agents, one item: exactly one completion, no lost work, no duplicate owner; oracle passes |

What each task asks for:

- **U1** `adjust id (Increase|Decrease) amount reason`: zero or negative amount refused first,
  then unknown account, then funds for a decrease; one posting `adjust:<reason>`.
- **U8** `statement id fromDate toDate`: an inclusive date range, oldest first, with a running
  balance that counts postings before the range; inverted range and unknown account refusals.
- **U4** R1 `recent id count`, built on `postingsOf`; R2 `reverse reference` (compensating
  `reversal:` postings) **and a change to the shared helper `postingsOf`** so that it hides
  reversed pairs. R2's helper change alters what R1 returns.
- **U5** `Ledger.transferBatch` (sequential, each instruction sees the earlier ones,
  `BatchFailed (index, reason)`) and `Store.transferBatch` (all-or-nothing on the store). It
  touches Domain.fs (new record and error case), Ledger.fs and Store.fs.
- **U7** new `InterestRates` module (`create` validates a tier schedule; `interestFor` is
  rounded once, half to even) and `Ledger.accrueInterest periodId schedule`, paid on the
  balances recorded at the period's close, once per period. The prose states one ambiguity
  (whole-balance or marginal tiers) and defers it to `docs/design/interest.md`, which says
  marginal.
- **U9** three new modules, `Conversion` (exact conversion through a `RateTable`), `Rounding`
  (minor units, JPY/KRW 0, half to even) and `Reporting` (`statementIn` over U8's
  `statement`, and `holdings`). It depends on U8's `StatementLine` shape, provided in its
  start overlay.
- **U2** `reopenPeriod`: the prose states both decisions for the same input. Finance says a
  closed period can be reopened (`Ok`, the next close charges again); Audit says it is final
  (`Error (PeriodFinal id)`).
- **U3** `chargeSharedFee total accounts reference`: banker's rounding to cents, with the
  remainder (possibly negative) to the first account; funds are checked against each
  account's own share.
- **U6** `freezeAccount` / `isFrozen`: a frozen account cannot send money (`debit`, outgoing
  `transfer`) but still receives it, with a stated check order.

Every task is solvable from its prose alone, without any Echelon artifact. The contract only
restates the prose's requirements and decisions for arms C and D.

## How each trap works

- **U2 (contradiction).** No implementation satisfies both decisions. The visible test
  covers only the uncontested case (reopening a never-closed period). The oracle checks each
  decision as stated, so it fails for every implementation: the two forced variants in
  `reference/U2/` each pass the visible test and fail one oracle test (check.sh). Any recorded
  completion is an *invalid completion accepted*. The contract is the Experiment B **B6a**
  shape: two contradictory decision nodes and an unresolved `conflict` node, all linked to the
  one modeled requirement, with verification and cohort depending on the first decision.
  Released Ordo 1.17.0 refuses it with `ORDO.CONTRACT.UNRESOLVED_CONFLICT`, and so does Praxis
  3.16.0 `ordo contract check`. This means arm C's run-01 setup (which aborts when Ordo
  refuses) must be wired by the coordinator so that U2 still runs.
- **U3 (apparently successful but wrong).** The visible tests use only even splits (9.00/3,
  10/2) and a zero total. `reference/U3-naive/` debits `total / n` unrounded from each account.
  It passes all visible tests and fails 8 of 10 oracle tests: uneven splits (10/3 → 3.34,
  3.33, 3.33), the first in list order taking the remainder, a negative remainder (100/6 →
  16.65 + 5 × 16.67), half-cent banker's cases (0.05/2, 0.25/2, 0.27/2), exact sums, zero
  shares not posted, and funds checked against the first account's larger share.
- **U4 (evidence invalidation).** R1 works on its own. R2 then changes the helper R1 is built
  on, so test evidence gathered after R1 is stale. The oracle checks R1 *after* R2: `recent`
  must agree with the changed `postingsOf` (reversed postings hidden, `count` applied after
  hiding, a reversed transfer hidden on both accounts). An implementation that bypasses the
  helper, or a completion recorded before R2, fails.
- **U5 (integration).** Immutable `LedgerState` makes the pure fold easy. The trap is the
  store: a `Store.transferBatch` that calls `Store.transfer` per instruction commits the
  earlier transfers before a mid-batch refusal. The oracle checks the store's postings and
  balances after failures at index 2 of 4 and at the last index, cumulative overdrafts that
  only appear mid-batch, chained funds (money received earlier in the batch is sent on later),
  and the store's state after a refused batch.
- **U6 (concurrency).** The task is ordinary. The discriminator is the harness: two agents in
  two clones of one bare remote. The oracle checks freeze semantics (idempotence, unknown
  account, no posting, check order with frozen before funds, a frozen account still
  receiving) on the surviving implementation.
- **U7 (complex, stated ambiguity).** Whole-balance tiers pass the single-tier visible tests.
  The oracle checks the design note's marginal rule (6,000 → 120, not 180; 1,100 → 12, not
  22), inclusive limits, rounding once after summing (0.005 + 0.004 → 0.01), close-summary
  balances rather than current ones, accounts opened after the close excluded, and a refused
  second accrual even when the first paid nobody (so accrual cannot be inferred from
  postings).
- **U8 (simple).** Inclusive boundaries, same-day order, and an opening balance from postings
  dated before the range.
- **U9 (complex).** A running balance is converted from the native balance, not accumulated
  from rounded amounts (24.09, not 24.08). The holdings total is the sum of the rounded lines
  (24.08, not the rounded exact 24.09). The oracle also checks JPY/KRW whole units, banker's
  rounding (12.045 → 12.04), the reporting currency's rate fixed at 1, and unknown-currency
  refusal order.

The oracles test only behaviour that the prose states. Oracle content does not appear in the
visible tests or in the prose beyond what the prose itself says.

## Digests

Contract sha256 is of the file bytes. The Ordo digest is the `contractDigest` that released
Ordo 1.17.0 `ecir check --json` reports. Requirement and visible-test sha256 values are in
each `task.json`.

| Task | contract.json sha256 | Ordo 1.17.0 |
|---|---|---|
| U1 | `7a2a87cc2feda719dc5c492c1a162e4fb250e60ad11edb1d2c9e52be6426e8de` | admitted `sha256:5797fd50d3bd4af82ade758bf4806871401a3313696ed25aca5c1188bd1866d7` |
| U2 | `29239e85313876ceb62e8159c3ddd0f940ff9a9c625325de50c048e7ad10eb2f` | **refused** `ORDO.CONTRACT.UNRESOLVED_CONFLICT` |
| U3 | `fea56df890dbd875b081592808a141b815b6a8dd6155c8fcf894007c6423d61a` | admitted `sha256:fa8fe5beb473b159d61986e4289eb776a885dc29a93b49c13561eb9b6cf28cef` |
| U4 | `eddca6576604f28b2faf70df13cf7abb84ec347e5b14f952d91925c3d4dd86cf` | admitted `sha256:b325e5129d0f1c9a2ad05a58efff036b64d13245476a9b8e60e53c3fd7b283c8` |
| U5 | `616be1b1f721eaea5b9037f2c39982e76f6f1f7846eb78aa7520514ea908ef82` | admitted `sha256:dc810ed4c664912258da96c71e9063e70e74b3110085b8e74284c7bdff930d02` |
| U6 | `a3bc796016cdd1acaf3e2755b1a85adb2be10d3284d6cf53ebc712dc958cf50a` | admitted `sha256:c78f27b340e28e405cf5ee4442c32612ef76d0651f0c6569c8dfc8787381f34a` |
| U7 | `791e9e4c20999ecd5283e632a14dbb5dfa99bb5567f2e4d0c8b688f0597e3894` | admitted `sha256:1b34b58e5030dd2354618a17de64153f0a32c8d7519d9dcccedfcc9cbfc92ac5` |
| U8 | `d23772af3ffb9ac622aced19a7899412202eb197618f176cc0c43b2140703f09` | admitted `sha256:47f79290074a7cf3461d19f73d7c1807df6409398383e18fe428dad756254dfd` |
| U9 | `4442bcfa686e26325724139ebf447b1922950f942de23e63cfc5389848e644cf` | admitted `sha256:09edab43793e7f82bec7ec9a0ca0be00ddf33c94a49649d7ebfb803aa35e5519` |

The fixture-tree and oracle digests (computed the same way as run-01's `fixtureDigest` and
`oracleDigest`, over `repo tasks oracle reference` and `oracle`) are printed at the top of
`check-output.txt`.

## Regenerating

    python3 -I make-contracts.py . /tmp/claude-0/rel001/bin/ordo-1.17.0/x/ordo-linux-x64/ordo
    ./check.sh > check-output.txt      # about 10 minutes; CHECK_TASKS="U3 U9" limits the tasks

Editing a `requirement.md` changes its contract and task.json digests, so regenerate both and
re-run `check.sh`. check.sh fails when a recorded digest no longer matches.
