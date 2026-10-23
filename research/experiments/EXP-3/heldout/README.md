# EXP-3 phase 1b: held-out corpus

This corpus tests the Dokimos rule-provenance audit on F# rules code that the audit's author never saw. An
independent author wrote it after phase 1 had run. It was frozen (`FREEZE.sha256`) and committed before any audit ran
on it. Nothing here was run through the audit.

## Layout

| Path | Contents |
|---|---|
| `scenarios/<id>/tree/` | A complete starting tree: `requirements/`, `docs/decisions/`, `docs/approvals/`, `docs/*.md` tables, `docs/notes/` (not a source), `README.md`, `src/<Project>/` (`Domain.fs`, the rules module(s) and an `.fsproj`). There are no overlays, so the tree is the materialised scenario. |
| `scenarios/<id>/scenario.json` | Domain, work item, audited files, number of planted rules. |
| `labels.json` | Ground truth in the format of `harness/labels.json`. See "Label format" below. |
| `handoffs/<id>.handoff.json` | One `echelon.authority-handoff/0.1` per scenario, built by `build_handoffs.py`. |
| `build_handoffs.py` | Calls `harness/exp3.py`'s `build_handoff` unchanged (PREREGISTRATION.md §4) and validates each handoff against the schema. |
| `FREEZE.sha256` | sha256 of every other file under `heldout/`. |

## Domains

Five domains, none used in P3. P3 used billing, clinic and lending.

| Domain | Scenarios | Audited files (`auditScope`) |
|---|---|---|
| Insurance claims | H01, H02, H03, H16 | `src/Claims/Rules.fs`, `src/Claims/Coverage.fs` (H03 only) |
| Payroll | H04, H05, H06 | `src/Payroll/Rules.fs`, `src/Payroll/Calendar.fs` (H05 only) |
| Freight / delivery | H07, H08, H09, H17 | `src/Freight/Rules.fs` |
| Subscription billing | H10, H11, H12 | `src/Subscriptions/Rules.fs`, `src/Subscriptions/Plans.fs` (H10 only) |
| Procurement | H13, H14, H15 | `src/Procurement/Rules.fs`, `src/Procurement/Limits.fs` (H14 only) |

`Domain.fs` holds data types only and is not audited, which matches P3's treatment of `Domain.fs`. A helper module
listed in `auditScope` but missing from a scenario's tree is skipped, as `exp3.py`'s `audit_files` already does.

## Counts

- **Scenarios:** 17. Fifteen contain planted rules. Two are controls with none (H16, H17), and every rule in them is
  authorized.
- **Planted unauthorized rules:** 30.
  - Superseded value: 10.
  - Exemption: 11.
  - Silent default: 9.
- **Labelled top-level declarations in the audited files:** 136.
  - PLANTED: 49. These are the declarations that carry the 30 rules; a rule can span a constant, the function that
    uses it and an active pattern.
  - SUPPORTED: 80. These are the authorized rule-bearing declarations.
  - TECHNICAL: 7. These are neutral.
- **Additional labels:**
  - Record-constant fields: 2 PLANTED and 2 SUPPORTED.
  - Alias spellings of active patterns, which repeat their pattern's label.

| Rule | Mechanism | Declarations (symbols) | Syntactic form |
|---|---|---|---|
| H01-P1 | superseded value | `Claims.Rules.fastTrackCeiling`, `route` | decimal constant in an if/else (DEC-CL02 2500.00 → DEC-CL05 1800.00) |
| H01-P2 | silent default | `Claims.Rules.initialReserve` | `Map.tryFind \|> Option.defaultValue 2000.00m` (non-zero default) |
| H02-P1 | exemption | `Claims.Rules.(\|CatastropheEvent\|_\|)`, `referToSiu` | partial active pattern matched first; a *proposed* DEC-CL11 makes it look plausible |
| H02-P2 | superseded value | `Claims.Rules.acknowledgeWithin`, `acknowledgementDeadline` | `TimeSpan.FromHours 36.0` (DEC-CL06 → DEC-CL09 20 h) |
| H03-P1 | exemption | `Claims.Coverage.deductibleWaivedProducts`, `Coverage.deductibleWaived`, `Rules.deductibleFor` | `Set` membership in a helper module, used as a match guard beside an authorized branch (APR-CL01) |
| H03-P2 | silent default | `Claims.Rules.depreciationRate` | if/elif chain, final `else 0.0` (float) |
| H04-P1 | superseded value | `Payroll.Rules.overtimeRule`, `overtimeHours`, `hourlyGross` | decimal in a tuple `(44.0m, 1.5m)`, destructured (DEC-PY01 → DEC-PY06 40) |
| H05-P1 | silent default | `Payroll.Rules.duesRate` | `function` with a wildcard case |
| H05-P2 | exemption | `Payroll.Calendar.isProbationary`, `Rules.pensionContribution` | date-based helper predicate in another module |
| H06-P1 | superseded value | `Payroll.Rules.expensePolicy` (`.RatePerKm`), `mileageAmount` | float field of a record constant (DEC-PY07 0.58 → DEC-PY09 0.64) |
| H06-P2 | exemption | `Payroll.Rules.payableClaims` | condition inside a lambda in a `List.filter` pipeline (`c.Submitter.Grade >= 8`) |
| H07-P1 | superseded value | `Freight.Rules.dimensionalDivisor`, `dimensionalWeight` | float with a unit of measure, `5000.0<cm^3/kg>` (DEC-FR01 → DEC-FR04 6000) |
| H07-P2 | silent default | `Freight.Rules.zoneSurcharge` | `List.tryFind \|> Option.map snd \|> Option.defaultValue 0m` over an association list |
| H08-P1 | exemption | `Freight.Rules.needsSignature` | one case of a total multi-case active pattern mapped to `false` |
| H08-P2 | superseded value | `Freight.Rules.maxDeliveryAttempts`, `afterFailedAttempt` | int constant in a comparison (DEC-FR06 3 → DEC-FR08 2) |
| H09-P1 | silent default | `Freight.Rules.transitDays` | if/elif chain whose `else 8` merges the last listed case with every unlisted one |
| H09-P2 | exemption | `Freight.Rules.fuelSurcharge` | boolean record field flag (`s.Account.IsKeyAccount`); a note (not a source) hints at it |
| H10-P1 | silent default | `Subscriptions.Rules.monthlyPrice` | `Map.tryFind \|> Option.map \|> Option.defaultValue Plans.starter.Monthly` (another entry's price, across modules) |
| H10-P2 | superseded value | `Subscriptions.Rules.paymentGrace`, `suspendAt` | `TimeSpan.FromDays 7.0` (DEC-SB01 → DEC-SB05 3) |
| H11-P1 | exemption | `Subscriptions.Rules.isPartnerDomain`, `trialEligible` | string-suffix predicate OR-ed into an eligibility check |
| H11-P2 | superseded value | `Subscriptions.Rules.retryOffsetsDays`, `retrySchedule` | int list literal `[ 1; 3; 5 ]` (DEC-SB06 → DEC-SB07 2, 4, 6) |
| H12-P1 | exemption | `Subscriptions.Rules.refundOnCancel` | record pattern `{ Plan = "SCALE"; Seats = seats } when seats >= 150`, beside an authorized APR-SB01 branch |
| H12-P2 | silent default | `Subscriptions.Rules.seatLimit` | `defaultArg (Map.tryFind …) Int32.MaxValue` (sentinel) |
| H13-P1 | superseded value | `Procurement.Rules.approvalLimits` (`.ManagerMax`), `requiredApprover` | decimal field of a record constant; the other field (`DirectorMax`) is still authorized |
| H13-P2 | exemption | `Procurement.Rules.(\|ContractRenewal\|_\|)`, `bidsRequired` | partial active pattern next to an authorized one (`ApprovedSoleSource`, APR-PR01) |
| H14-P1 | silent default | `Procurement.Rules.paymentTermsDays` | `Dictionary.TryGetValue` tuple match `\| true, d -> d \| _ -> 35` (default equals a listed value) |
| H14-P2 | exemption | `Procurement.Limits.pettyCashCeiling`, `Limits.isPettyCash`, `Rules.needsPurchaseOrder` | threshold and predicate in another module, negated at the call site |
| H14-P3 | superseded value | `Procurement.Rules.priceTolerance`, `lineMatches` | float constant in arithmetic (DEC-PR05 4% → DEC-PR07 2.5%) |
| H15-P1 | exemption | `Procurement.Rules.mayIssuePo` | hard-coded id OR-ed after a `Set.Contains` test |
| H15-P2 | silent default | `Procurement.Rules.freightAllowanceRate` | match on `ToUpperInvariant()` with a non-zero wildcard copying a listed rate |

**Authorized code meant to test for false questions.** Each of the following resembles one of the three mechanisms,
but a source in the same tree authorizes it:

- **Exemptions with a source:**
  - APR-CL01: the `Glass -> 0m` branch.
  - PAY-14-R3: `vacationAccrued` on unpaid leave.
  - PAY-22-R1: the mileage receipt exemption.
  - DEC-CL17: no rental cover means no allowance.
  - DEC-FR11: free cover at or below 100.00.
  - APR-SB01: `refundException`.
  - APR-PR01: `(|ApprovedSoleSource|_|)`.
- **Authorized wildcard or else defaults:**
  - H06 `reimbursable`, where PAY-22-R2 says "any other claim at its receipted amount".
  - H17 `oversizeFee`, where DEC-FR13 says "in every other zone there is no oversize fee".
  - H05 `unionDues` returns `None -> 0m` for non-members, under PAY-14-R1.
  - H11 `prorate` returns 0 for a downgrade, under DEC-SB04.
- **Values that follow a supersession correctly:**
  - H16 `totalLossRatio` (DEC-CL16, not DEC-CL14). Its comment cites the old 75%.
  - H17 `coverRate` (DEC-FR11, not DEC-FR14).
  - H13 `DirectorMax`, which is unchanged across the supersession.
- **Constants in varied forms:**
  - `[<Literal>]` int.
  - `TimeSpan`.
  - A tuple (`earlyPayment`).
  - A unit-of-measure float.
  - A `Set`, a `Map`, a `dict` and records.

Comments cite the authorizing record on some authorized declarations and not on others. Some planted declarations
also carry a plausible comment. Two scenarios have a note in `docs/notes/` that hints at the planted exemption
(H09, H14). Two have a *proposed* decision that resembles it (H02, H03).

## Label format

`labels.json` has the same keys and categories as `harness/labels.json`: `schema`, `note`, `auditScope`, `base`,
`overrides` and `plantedRules`, with the categories PLANTED, SUPPORTED, TECHNICAL and OTHER-UNAUTHORIZED (the last
is unused). It differs in three ways:

1. Every scenario is a full tree, so all labels sit in `overrides.<id>` and `base.<domain>` is empty.
2. A scenario can hold more than one planted rule. `plantedRules.<id>` is therefore a list of
   `{rule, mechanism, form, symbols}` rather than a single mechanism string. A rule counts as detected when at least
   one finding resolves to one of its `symbols`, using the same nearest-dotted-ancestor resolution. Recall is computed
   per rule (denominator 30) and per mechanism (10 / 11 / 9).
3. Two kinds of symbol get extra labels:
   - An active pattern is labelled under both spellings, `Module.(|A|_|)` and `Module.|A|_|`.
   - A field of a record constant is labelled as `Module.binding.Field`, as well as the binding itself.

## Handoffs

Handoffs follow PREREGISTRATION.md §4 exactly, through `exp3.build_handoff`:

- Requirements come from `## <ID>` sections.
- Decisions and approvals come from the `Status:` lines.
- Parameters are the numbers in each body plus the backticked `docs/*.md` table cells.
- `observations`, `policyQuestions` and `invariants` are empty.
- The fixed fields are `produced.at = 2026-10-23T00:00:00Z` and `produced.revision` = the last commit touching
  `research/experiments/VAC-002` (`ea36618648f8a329021ed4c27dd5a6053d6bbb12`). The authority contract is the sha256
  of `P3/AUTHORITY-CONTRACT.md`.

All 17 handoffs validate against `program/contracts/schemas/echelon-authority-handoff-0.1.schema.json`.

## Compile check

Each scenario's tree was copied to a throwaway directory and its own `src/<Project>/<Project>.fsproj` was built with
`dotnet build` (.NET SDK 10.0.402, `net10.0`). The compile order is `Domain.fs`, then any helper, then `Rules.fs`.
All 17 build with 0 warnings and 0 errors.

## Independence statement

The corpus author was a separate agent session, working only from the files below. The author did not read, search or
open anything under `/home/user/dokimos/experiments/rule-provenance/`: not the analyzer, its tests, dev scripts,
README or LIMITATIONS. The author did not read `research/experiments/EXP-3/RESULTS.md`, `EXP-3/results/` or any
other audit output, and ran no audit.

**Files read:**

- `research/experiments/VAC-002/P3/CORPUS.md`.
- `research/experiments/VAC-002/P3/scenarios/`:
  - `C02`: requirement, both decision records and `scenario.json`.
  - `C04`: `docs/shipping.md`, the decision's status line and the overlay file list.
  - `C05`: `Rules.fs` and its decision record.
  - `D12`: the approval record.
  - `D19`: `Rules.fs`.
  - Directory and file listings of P3.
- `research/experiments/EXP-3/PREREGISTRATION.md`.
- `research/experiments/EXP-3/harness/exp3.py`.
- `research/experiments/EXP-3/harness/labels.json`.
- The first part of `program/contracts/schemas/echelon-authority-handoff-0.1.schema.json`.

The author did not open P3's `README.md`, `fixture/` or the P2 fixture. The identifiers, ids, owners and literal
values used here differ from the P3 scenarios'.
