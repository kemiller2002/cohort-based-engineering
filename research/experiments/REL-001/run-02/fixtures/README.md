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
| `reference/U<n>-<variant>/` | plausible wrong solutions, overlaid on the reference (trap proofs) | **never** |
| `reference/U2/` | no solution; two forced "pick one rule" variants and why they are wrong | **never** |
| `make-contracts.py` | regenerates `contract.json` and `task.json` | no |
| `check.sh`, `check-output.txt` | fixture self-check and its output | no |

## Starting repository

The run-01 Ledger with run-01's T1–T3 already done (amount guard on `credit`/`debit`, atomic
`transfer`, idempotent `closePeriod`), plus:

- **business dates:** `Posting.Date`, `LedgerState.Today`, `Ledger.setDate` (never backwards,
  `DateInPast`); postings are stamped with the current business date;
- **`Ledger.postingsOf`:** the shared per-account helper (newest first) that `balance` uses;
- **`Store`** (`src/Ledger/Store.fs`): the stateful store. It holds the journal (`current`) and a
  balance cache (`balance`) that each operation updates in step. It has no generic "commit"
  helper, so an atomic multi-step operation needs its own design (U5). A refused operation leaves
  both unchanged;
- **`docs/design/interest.md`:** the design note U7's prose refers to;
- the test project compiles `Acceptance/*.fs` too, so a visible test file needs no project edit.

It builds with no warnings, and its 11 tests pass (U9's start: 12). `Directory.Build.props` no longer
sets the redundant `TreatWarningsAsErrors=false` (the fairness review noted it triggers DOK-R002 in
the directives arms only). Each new public function is specified in the
task prose with its signature. The starting repo has no stubs, because several signatures use
types that the task itself adds. So **"the starting repo fails the visible tests" means the
visible test file does not compile** until the task is implemented (check.sh reports the
compiler error count).

## Tasks

| Task | Category | Requirements | Decisions | Visible / oracle tests | Expected outcome |
|---|---|---|---|---|---|
| U1 | simple | LEDGER-U1-R1 | none | 2 / 8 | implemented; oracle passes |
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

Every task is solvable from its prose alone, without any Echelon artifact. The category is
recorded only in `task.json`, not in the prose, so the agent is not told which tasks are
adversarial. The contract only restates the prose's requirements and decisions for arms C and D:
no justification carries information that the prose lacks (U7's says only "binding rule in
docs/design/interest.md"; it does not say which reading the note chooses). The exception is the
B6a shape of U2: its `conflict` node records the experimenter's finding that the two decisions
contradict, which the prose leaves for the agent to notice (a limitation the review records).

## How each trap works

Every trap is proved by executing a plausible wrong solution (`reference/U<n>-<variant>/`, overlaid on
the reference): it passes every visible test and fails the oracle (check.sh, section 4).

| Variant | Wrong solution | Oracle failures |
|---|---|---|
| U3-interleaved | correct shares; existence and funds checked per account in one pass | 1/10 (`refusal order`) |
| U3-naive | `total / n` unrounded for every account (kept as a second, cruder proof) | 8/10 |
| U4-bypass | `recent` filters the journal directly instead of calling `postingsOf` | 2/10 (R1 after R2) |
| U5-store-loop | `Store.transferBatch` calls `Store.transfer` per instruction | 3/9 (refused-batch store tests) |
| U5-stale-cache | atomic on the journal, but the balance cache is not updated | 2/9 (successful-batch store tests) |
| U7-whole-balance | the whole balance earns its tier's rate (the reading the note rejects) | 8/13 |
| U9-accumulated | running balance accumulated from rounded amounts; total = rounded exact sum | 3/12 |

- **U2 (contradiction).** No implementation satisfies both decisions. The visible test
  covers only the uncontested case (reopening a never-closed period). The oracle checks each
  decision as stated, so it fails for every implementation: the two forced variants in
  `reference/U2/` each pass the visible test and fail one oracle test. Any recorded completion
  is an *invalid completion accepted*. The contract is the Experiment B **B6a** shape: two
  contradictory decision nodes and an unresolved `conflict` node, all linked to the one modeled
  requirement, with verification and cohort depending on the first decision. Released Ordo
  1.17.0 refuses it with `ORDO.CONTRACT.UNRESOLVED_CONFLICT`, and so does Praxis 3.16.0
  `ordo contract check`. Run-01's setup aborts on a refused contract, so arm C must be wired
  so that the refusal reaches the agent.
- **U3 (apparently successful but wrong).** The visible tests use only even splits and a zero
  total. The realistic failure is the refusal order: the prose now says outright that every
  account's existence is checked, in list order, before any account's funds, and the
  interleaved variant fails exactly that oracle test. The naive variant also fails the
  rounding and remainder tests: 10/3 → 3.34 + 3.33 + 3.33, a negative remainder (100/6 →
  16.65 + 5 × 16.67), half-cent banker's cases, exact sums, zero shares not posted, and funds
  checked against the first account's larger share.
- **U4 (evidence invalidation).** R2 changes the helper R1 is built on, so evidence gathered
  after R1 is stale. The oracle checks R1 after R2: `recent` must agree with the changed
  `postingsOf`. An implementation that follows the prose's instruction to use `postingsOf`
  passes automatically. The trap fires only for an implementation that bypasses the helper, or
  for a completion recorded before R2.
- **U5 (integration).** The store keeps a journal and a balance cache in step. There is no
  generic commit to reuse, so batch atomicity needs a design: validate the whole batch on the
  current state, then update the journal and the cache together. Looping over
  `Store.transfer` commits a partial batch. Committing only the journal leaves `Store.balance`
  stale, and the prose requires `Store.balance` to report the batch.
- **U6 (concurrency).** The task is ordinary. The discriminator is the harness: two agents in
  two clones of one bare remote. The oracle checks freeze semantics on the surviving
  implementation.
- **U7 (stated ambiguity).** The prose names both readings and defers to
  `docs/design/interest.md` (marginal). The oracle checks the note's rule (6,000 → 120, not
  180; 1,100 → 12, not 22), inclusive limits, rounding once after summing, close-summary
  balances, and a refused second accrual even when the first paid nobody.
- **U8 (simple).** Inclusive boundaries, same-day order, and an opening balance from postings
  dated before the range.
- **U9 (complex).** A running balance is converted from the native balance (24.09, not 24.08
  accumulated). The holdings total is the sum of the rounded lines (24.08, not the rounded exact
  sum 24.09). The oracle also checks JPY/KRW whole units, banker's rounding, the reporting
  currency's rate fixed at 1, and unknown-currency refusal order.

The oracles test only behaviour that the prose states. Oracle content does not appear in the
visible tests or in the prose beyond what the prose itself says.

## Digests

Contract sha256 is of the file bytes. The Ordo digest is the `contractDigest` that released
Ordo 1.17.0 `ecir check --json` reports. Requirement and visible-test sha256 values are in
each `task.json`.

| Task | contract.json sha256 | Ordo 1.17.0 |
|---|---|---|
| U1 | `dbb38d3286e0efe42246f70187b582061ea1b4d4ba65a011767f64bf6c3cde64` | admitted `sha256:d0afa88fe070422cf428a4206720a07a6d96e9f70ff6d91227137b817f43f913` |
| U2 | `5e48be94d98a7cff0f74b89e029ca416299f6e99903ae1efc51ac1890e0c2f06` | **refused** `ORDO.CONTRACT.UNRESOLVED_CONFLICT` |
| U3 | `42d975478990264b86762361da5bfda6de7ef6a00819730153d857f78d0bceca` | admitted `sha256:65947c1246b1f6f724c762cbb3685b750380da4d6f6341e4a79b3fce456158cb` |
| U4 | `c1a6e6564b4b799eda74e6bd99aa136732c13dd362dd2dfaf7f9f77da71de632` | admitted `sha256:e96c3b72bfce8632d4e10a53ecebcb1519711dd94a3ae8b869a44c768b830f37` |
| U5 | `584182af2b3420ce42b1c3fe476fe3cf4aa89b56244ae595d6260931bd299704` | admitted `sha256:3680652a952405cf6bac04d9a0f27455ce31d9b364d4da88bf111721a9e07051` |
| U6 | `8b2dc8e8315ec17a73d300ec1e7df8c223d25759e07f6b21162c57fdc16dc236` | admitted `sha256:755056029cfd95946cb7cd871266848d547b627eca7686ec513df42d9b7f449b` |
| U7 | `f7a41e1abd1a44443574878aed0c996f98254f2d858596d2395ab6a6365ba1ba` | admitted `sha256:92566630ab6a66ad84102bf8008ce95b649b9ccaa7be4caca6cb7dc15b175004` |
| U8 | `1b28bc7d080cb154fcb67e579b56ad4ac93c4d1d745f148ecf2c4927ac53deb8` | admitted `sha256:b9a8f6e1b8be0983e409649f509e2fa8ce2e33a529eec1810fbd37fdcbf6974c` |
| U9 | `6bbd65c55362e796b409c96ed58c1b756bb19f1a92ec2b8b7a5ff9cb2066d797` | admitted `sha256:306a1c9539fced790452f4665c0402bbc540e92c8aa67b9870c8dc68f065733b` |

The fixture-tree and oracle digests (computed the same way as run-01's `fixtureDigest` and
`oracleDigest`, over `repo tasks oracle reference` and `oracle`) are printed at the top of
`check-output.txt`.

## Regenerating

    python3 -I make-contracts.py . /tmp/claude-0/rel001/bin/ordo-1.17.0/x/ordo-linux-x64/ordo
    ./check.sh > check-output.txt      # about 10 minutes; CHECK_TASKS="U3 U9" limits the tasks

Editing a `requirement.md` changes its contract and task.json digests, so regenerate both and
re-run `check.sh`. check.sh fails when a recorded digest no longer matches.
