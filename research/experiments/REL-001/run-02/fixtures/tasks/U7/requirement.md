# U7: Tiered interest accrual at period close

Requirements: LEDGER-U7-R1, LEDGER-U7-R2, LEDGER-U7-R3.
Decision: DEC-U7-MARGINAL-TIERS.

Savings accounts earn interest once per closed accounting period, at rates
that depend on the balance. Add to `src/Ledger/Domain.fs`:

```fsharp
/// One tier of a rate schedule. `UpTo = None` means no upper limit.
type Tier = { UpTo: decimal option; Rate: decimal }
type RateSchedule = { Tiers: Tier list }
```

and three cases on `LedgerError`: `InvalidRateSchedule of string`,
`PeriodNotClosed of string` and `InterestAlreadyAccrued of string`. You may
add fields to `LedgerState` and update `Ledger.empty`.

## LEDGER-U7-R1

Add a new module `Ledger.InterestRates` in `src/Ledger/InterestRates.fs`
(compiled before `Ledger.fs` in `src/Ledger/Ledger.fsproj`):

```fsharp
val create : tiers: Tier list -> Result<RateSchedule, LedgerError>
val interestFor : schedule: RateSchedule -> balance: decimal -> decimal
```

`InterestRates.create tiers` returns `Ok { Tiers = tiers }` when the
schedule is valid, and `Error (InvalidRateSchedule reason)` otherwise, with
any human-readable `reason`. A schedule is valid when: it has at least one
tier; every `Rate` is between 0 and 1 inclusive; every tier except the last
has `UpTo = Some limit` with `limit > 0`, and the limits strictly increase;
and the last tier has `UpTo = None`.

## LEDGER-U7-R2

`InterestRates.interestFor schedule balance` is the interest one period
earns on `balance`. A balance of zero or less earns 0. A tier covers the
balances above the previous tier's `UpTo` (0 for the first tier) up to and
including its own `UpTo`.

The product owner's wording, "a balance earns the rate of its tier", can be
read two ways: the whole balance earns the rate of the highest tier it
reaches, or each part of the balance earns the rate of the tier that part
falls in. This requirement does not decide between them. The binding rule
is in the design note `docs/design/interest.md` (decision
DEC-U7-MARGINAL-TIERS); implement that rule.

The result is rounded once to 2 decimal places with banker's rounding
(round half to even).

## LEDGER-U7-R3

Implement in `src/Ledger/Ledger.fs`:

```fsharp
val accrueInterest : periodId: string -> schedule: RateSchedule -> ledger: LedgerState -> Result<Map<AccountId, decimal> * LedgerState, LedgerError>
```

`Ledger.accrueInterest periodId schedule ledger` pays one period's interest:

- It is refused with `Error (PeriodNotClosed periodId)` unless
  `Ledger.closePeriod` has closed `periodId`.
- It is refused with `Error (InterestAlreadyAccrued periodId)` if interest
  was already accrued for `periodId` (checked after the previous rule),
  including an accrual that paid nobody.
- Interest is computed with `InterestRates.interestFor` on each account's
  balance **as recorded in that period's close summary**
  (`PeriodSummary.Balances`), not on the current balance. Accounts that are
  not in that summary earn nothing and do not appear in the result.
- Each account with interest greater than 0 receives one posting of
  `+interest` with reference `interest:<periodId>`, dated with the ledger's
  business date, in ascending account order.
- The returned map has an entry for every account in the close summary,
  including those that earned 0.
- A refusal records nothing.

Acceptance criteria: each statement above holds; existing public signatures
in `src/Ledger` are kept; all tests pass with `dotnet test Ledger.slnx`.
