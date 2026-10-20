"""REL-001 run-03: regenerates reference/V<n> (reference solutions) and reference/V<n>-<variant> (plausible wrong
solutions, overlaid on the reference) as exact edits of the starting repository in repo/.
usage: python3 -I make-references.py FIXTURE_DIR   (each edit must match exactly once, or it fails)
"""
import pathlib, sys
FIX = pathlib.Path(sys.argv[1])
base = {n: (FIX / "repo/src/Ledger" / n).read_text() for n in ("Domain.fs", "Ledger.fs", "Ledger.fsproj")}

def edit(text, *pairs):
    for old, new in pairs:
        assert text.count(old) == 1, (old, text.count(old))
        text = text.replace(old, new)
    return text

def write(rel, files):
    d = FIX / "reference" / rel / "src/Ledger"
    d.mkdir(parents=True, exist_ok=True)
    for n, t in files.items():
        (d / n).write_text(t)

ERR_TAIL = "    | DateInPast of DateOnly\n"
def add_errors(*cases):
    return (ERR_TAIL, ERR_TAIL + "".join(f"    | {c}\n" for c in cases))

# ---------------- V1 closeAccount
v1_dom = edit(base["Domain.fs"], add_errors("NonZeroBalance of AccountId * decimal"),
              ("      Today: DateOnly }", "      Today: DateOnly\n      /// Accounts that were closed; a closed id is never reused.\n      Closed: Set<AccountId> }"))
V1_CLOSE = '''
/// Closes an open account with a zero balance. Its postings stay in the
/// journal; its id is never reused.
let closeAccount (id: AccountId) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    match balance id ledger with
    | Error e -> Error e
    | Ok current when current <> 0m -> Error(NonZeroBalance(id, current))
    | Ok _ -> Ok { ledger with Accounts = ledger.Accounts.Remove id; Closed = ledger.Closed.Add id }
'''
OPEN_OLD = "    if ledger.Accounts.Contains id then Error(DuplicateAccount id)"
v1_led = edit(base["Ledger.fs"], ("      Today = startDate }", "      Today = startDate\n      Closed = Set.empty }"),
              (OPEN_OLD, "    if ledger.Accounts.Contains id || ledger.Closed.Contains id then Error(DuplicateAccount id)")) + V1_CLOSE
write("V1", {"Domain.fs": v1_dom, "Ledger.fs": v1_led})
write("V1-reopen", {"Ledger.fs": edit(v1_led, ("    if ledger.Accounts.Contains id || ledger.Closed.Contains id then Error(DuplicateAccount id)", OPEN_OLD))})

# ---------------- V2 richest
v2_dom = edit(base["Domain.fs"], add_errors("InvalidCount of int"))
V2_SORT = '''        |> Seq.sortWith (fun (AccountId a, x) (AccountId b, y) ->
            match compare y x with
            | 0 -> String.CompareOrdinal(a, b)
            | c -> c)
'''
V2 = '''
/// The `count` open accounts with the largest balances, largest first;
/// equal balances are ordered by account id (ordinal, ascending).
let richest (count: int) (ledger: LedgerState) : Result<(AccountId * decimal) list, LedgerError> =
    if count < 0 then Error(InvalidCount count)
    else
        ledger.Accounts
        |> Seq.map (fun id -> id, balance id ledger |> Result.defaultValue 0m)
''' + V2_SORT + '''        |> Seq.truncate count
        |> List.ofSeq
        |> Ok
'''
v2_led = base["Ledger.fs"] + V2
write("V2", {"Domain.fs": v2_dom, "Ledger.fs": v2_led})
write("V2-tie-descending", {"Ledger.fs": edit(v2_led, (V2_SORT, "        |> Seq.sortByDescending (fun (id, amount) -> amount, id)\n"))})

# ---------------- V3 holds
v3_dom = edit(base["Domain.fs"], add_errors("DuplicateHold of string", "UnknownHold of string"),
              ("/// The ledger state.", "/// An active hold: part of an account's balance that cannot be spent.\ntype Hold = { HoldAccount: AccountId; HoldAmount: decimal }\n\n/// The ledger state."),
              ("      Today: DateOnly }", "      Today: DateOnly\n      /// Active holds by hold id.\n      Holds: Map<string, Hold> }"))
V3_AVAIL = '''
/// The balance minus the account's active holds.
let available (id: AccountId) (ledger: LedgerState) : Result<decimal, LedgerError> =
    balance id ledger
    |> Result.map (fun current ->
        current - (ledger.Holds |> Map.toSeq |> Seq.sumBy (fun (_, h) -> if h.HoldAccount = id then h.HoldAmount else 0m)))
'''
V3_HOLDS = '''
/// Places a hold of `amount` on the account. Records no posting.
let placeHold (holdId: string) (id: AccountId) (amount: decimal) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    elif not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    elif ledger.Holds.ContainsKey holdId then Error(DuplicateHold holdId)
    else
        match available id ledger with
        | Error e -> Error e
        | Ok free when free < amount -> Error(InsufficientFunds(id, amount))
        | Ok _ -> Ok { ledger with Holds = ledger.Holds.Add(holdId, { HoldAccount = id; HoldAmount = amount }) }

/// Releases an active hold. Records no posting.
let releaseHold (holdId: string) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if ledger.Holds.ContainsKey holdId then Ok { ledger with Holds = ledger.Holds.Remove holdId }
    else Error(UnknownHold holdId)
'''
BAL_END = "    else postingsOf id ledger |> List.sumBy (fun p -> p.Amount) |> Ok\n"
v3_led = edit(base["Ledger.fs"], ("      Today = startDate }", "      Today = startDate\n      Holds = Map.empty }"),
              (BAL_END, BAL_END + V3_AVAIL),
              ("        match balance id ledger with\n        | Error e -> Error e\n        | Ok current when current < amount -> Error(InsufficientFunds(id, amount))",
               "        match available id ledger with\n        | Error e -> Error e\n        | Ok current when current < amount -> Error(InsufficientFunds(id, amount))"),
              ("        match balance source ledger with", "        match available source ledger with")) + V3_HOLDS
write("V3", {"Domain.fs": v3_dom, "Ledger.fs": v3_led})
write("V3-debit-only", {"Ledger.fs": edit(v3_led, ("        match available source ledger with", "        match balance source ledger with"))})

# ---------------- V4 fee preview and new rule
V4_FEE = '''/// The fee a period close charges an account with this balance.
let periodFee (balance: decimal) : decimal =
    if balance >= 1m && balance < 1000m then 1m else 0m

'''
V4_PREVIEW = '''
/// The fee the next period close would charge the account.
let feeFor (id: AccountId) (ledger: LedgerState) : Result<decimal, LedgerError> =
    balance id ledger |> Result.map periodFee
'''
CLOSE_DOC = "/// Closes an accounting period:"
v4_led = edit(base["Ledger.fs"], (CLOSE_DOC, V4_FEE + CLOSE_DOC),
              ("""            let current = balance id l |> Result.defaultValue 0m
            if current >= 1m then post id -1m ("fee:" + periodId) l, fees.Add(id, 1m)
            else l, fees.Add(id, 0m)""", """            let fee = periodFee (balance id l |> Result.defaultValue 0m)
            if fee > 0m then post id (-fee) ("fee:" + periodId) l, fees.Add(id, fee)
            else l, fees.Add(id, 0m)""")) + V4_PREVIEW
write("V4", {"Ledger.fs": v4_led})
write("V4-stale-preview", {"Ledger.fs": edit(v4_led, ("    balance id ledger |> Result.map periodFee", "    balance id ledger |> Result.map (fun b -> if b >= 1m then 1m else 0m)"))})
write("V4-boundary", {"Ledger.fs": edit(v4_led, ("balance >= 1m && balance < 1000m", "balance >= 1m && balance <= 1000m"))})

# ---------------- V5 standing orders
V5_TYPES = '''
/// A recurring payment on a fixed day of the month.
type StandingOrder =
    { OrderId: string
      Payer: AccountId
      Payee: AccountId
      Value: decimal
      DayOfMonth: int }

type OrderOutcome =
    | Paid of orderId: string
    | Skipped of orderId: string * reason: LedgerError
    | AlreadyPaid of orderId: string
'''
v5_dom = edit(base["Domain.fs"], add_errors("InvalidOrder of string")) + V5_TYPES
def proj(extra):
    return edit(base["Ledger.fsproj"], ('    <Compile Include="Ledger.fs" />\n', f'    <Compile Include="Ledger.fs" />\n    <Compile Include="{extra}" />\n'))
V5_SORT = "                |> List.sortWith (fun a b -> String.CompareOrdinal(a.OrderId, b.OrderId))\n"
V5_DUE = "    order.DayOfMonth = date.Day || (order.DayOfMonth > days && date.Day = days)"
V5_PAY = '''let private pay (date: DateOnly) (outcomes: OrderOutcome list, ledger: LedgerState) (order: StandingOrder) =
    let reference = referenceFor order date
    if ledger.Postings |> List.exists (fun p -> p.Reference = reference) then AlreadyPaid order.OrderId :: outcomes, ledger
    else
        match Ledger.transfer order.Payer order.Payee order.Value reference ledger with
        | Ok next -> Paid order.OrderId :: outcomes, next
        | Error e -> Skipped(order.OrderId, e) :: outcomes, ledger
'''
V5_PAY_PARTIAL = '''let private pay (date: DateOnly) (outcomes: OrderOutcome list, ledger: LedgerState) (order: StandingOrder) =
    let reference = referenceFor order date
    if ledger.Postings |> List.exists (fun p -> p.Reference = reference) then AlreadyPaid order.OrderId :: outcomes, ledger
    else
        match Ledger.transfer order.Payer order.Payee order.Value reference ledger with
        | Ok next -> Paid order.OrderId :: outcomes, next
        | Error(InsufficientFunds _ as e) ->
            match Ledger.balance order.Payer ledger with
            | Ok part when part > 0m ->
                match Ledger.transfer order.Payer order.Payee part reference ledger with
                | Ok next -> Skipped(order.OrderId, e) :: outcomes, next
                | Error _ -> Skipped(order.OrderId, e) :: outcomes, ledger
            | _ -> Skipped(order.OrderId, e) :: outcomes, ledger
        | Error e -> Skipped(order.OrderId, e) :: outcomes, ledger
'''
V5_MOD = '''/// Standing orders: recurring payments on a fixed day of the month
/// (docs/design/standing-orders.md).
module Ledger.StandingOrders

open System
open System.Globalization

let private invalid (seen: Set<string>) (order: StandingOrder) =
    order.Value <= 0m || order.DayOfMonth < 1 || order.DayOfMonth > 31 || seen.Contains order.OrderId

/// The id of the first invalid order, in list order.
let private firstInvalid (orders: StandingOrder list) : string option =
    orders
    |> List.fold
        (fun (found: string option, seen: Set<string>) order ->
            match found with
            | Some _ -> found, seen
            | None when invalid seen order -> Some order.OrderId, seen
            | None -> None, seen.Add order.OrderId)
        (None, Set.empty)
    |> fst

let private isDue (date: DateOnly) (order: StandingOrder) =
    let days = DateTime.DaysInMonth(date.Year, date.Month)
''' + V5_DUE + '''

let private referenceFor (order: StandingOrder) (date: DateOnly) =
    "standing:" + order.OrderId + ":" + date.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)

''' + V5_PAY + '''
/// Pays the orders due on `date`, in ascending ordinal id order, each in full or not at all.
let run (date: DateOnly) (orders: StandingOrder list) (ledger: LedgerState) : Result<OrderOutcome list * LedgerState, LedgerError> =
    match firstInvalid orders with
    | Some id -> Error(InvalidOrder id)
    | None ->
        Ledger.setDate date ledger
        |> Result.map (fun dated ->
            let outcomes, paid =
                orders
                |> List.filter (isDue date)
''' + V5_SORT + '''                |> List.fold (pay date) ([], dated)
            List.rev outcomes, paid)
'''
write("V5", {"Domain.fs": v5_dom, "Ledger.fsproj": proj("StandingOrders.fs"), "StandingOrders.fs": V5_MOD})
write("V5-list-order", {"StandingOrders.fs": edit(V5_MOD, (V5_SORT, ""))})
write("V5-exact-day", {"StandingOrders.fs": edit(V5_MOD, (V5_DUE, "    ignore days\n    order.DayOfMonth = date.Day"))})
write("V5-partial", {"StandingOrders.fs": edit(V5_MOD, (V5_PAY, V5_PAY_PARTIAL))})

# ---------------- V6 reconciliation
V6_TYPES = '''
/// One line of a bank statement.
type BankLine =
    { BookedOn: DateOnly
      Value: decimal
      Memo: string }

/// The result of reconciling an account against a bank statement.
type ReconciliationReport =
    { Matched: (Posting * BankLine) list
      LedgerOnly: Posting list
      BankOnly: BankLine list }
'''
v6_dom = base["Domain.fs"] + V6_TYPES
V6_PICK = "                let i, p = candidates |> List.minBy (fun (i, p) -> gap p line, i)\n"
V6_WINDOW = "gap posting line <= 2"
V6_MOD = '''/// Bank reconciliation: matches an account's postings against the lines of
/// a bank statement.
module Ledger.Reconciliation

let private gap (posting: Posting) (line: BankLine) = abs (posting.Date.DayNumber - line.BookedOn.DayNumber)

let private canMatch (line: BankLine) (posting: Posting) =
    posting.Amount = line.Value && posting.Reference = line.Memo && ''' + V6_WINDOW + '''

/// Matches the lines one at a time, in order; each line takes the closest
/// unmatched posting (the earlier one in journal order when equally close).
let reconcile (id: AccountId) (lines: BankLine list) (ledger: LedgerState) : Result<ReconciliationReport, LedgerError> =
    if not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else
        let postings = Ledger.postings ledger |> List.filter (fun p -> p.Account = id) |> List.indexed
        let takenOf (matched: (int * Posting * BankLine) list) = matched |> List.map (fun (i, _, _) -> i) |> Set.ofList
        let step (matched: (int * Posting * BankLine) list, unmatched: BankLine list) (line: BankLine) =
            let taken = takenOf matched
            let candidates = postings |> List.filter (fun (i, p) -> not (taken.Contains i) && canMatch line p)
            match candidates with
            | [] -> matched, line :: unmatched
            | _ ->
''' + V6_PICK + '''                (i, p, line) :: matched, unmatched
        let matched, unmatched = lines |> List.fold step ([], [])
        let taken = takenOf matched
        Ok
            { Matched = matched |> List.rev |> List.map (fun (_, p, l) -> p, l)
              LedgerOnly = postings |> List.filter (fun (i, _) -> not (taken.Contains i)) |> List.map snd
              BankOnly = List.rev unmatched }
'''
write("V6", {"Domain.fs": v6_dom, "Ledger.fsproj": proj("Reconciliation.fs"), "Reconciliation.fs": V6_MOD})
write("V6-first-candidate", {"Reconciliation.fs": edit(V6_MOD, (V6_PICK, "                let i, p = List.head candidates\n"))})
write("V6-exclusive-window", {"Reconciliation.fs": edit(V6_MOD, (V6_WINDOW, "gap posting line < 2"))})

# ---------------- V7 sweep (no reference: two forced "pick one rule" variants)
V7 = '''
/// Moves the source's whole balance to the target (reference "sweep").
let sweep (source: AccountId) (target: AccountId) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if not (ledger.Accounts.Contains source) then Error(UnknownAccount source)
    elif not (ledger.Accounts.Contains target) then Error(UnknownAccount target)
    elif source = target then Error(SameAccount source)
    else
        match balance source ledger with
        | Error e -> Error e
        | Ok amount when amount > 0m -> transfer source target amount "sweep" ledger
        | Ok _ -> EMPTY
'''
write("V7/forced-noop", {"Ledger.fs": base["Ledger.fs"] + V7.replace("EMPTY", "Ok ledger")})
write("V7/forced-refuse", {"Ledger.fs": base["Ledger.fs"] + V7.replace("EMPTY", "Error(InvalidAmount 0m)")})

# ---------------- V8 daily withdrawal limit
v8_dom = edit(base["Domain.fs"], add_errors("DailyLimitExceeded of AccountId * decimal"))
V8_COUNT = 'p.Reference = "withdraw" && p.Date = ledger.Today'
V8_LIMIT = "        | Ok _, Ok today when today + amount > dailyWithdrawalLimit -> Error(DailyLimitExceeded(id, dailyWithdrawalLimit - today))\n"
V8 = '''
let private dailyWithdrawalLimit = 500m

/// Total withdrawn (reference "withdraw") on the current business date, as a positive amount.
let withdrawnToday (id: AccountId) (ledger: LedgerState) : Result<decimal, LedgerError> =
    if not (ledger.Accounts.Contains id) then Error(UnknownAccount id)
    else
        postingsOf id ledger
        |> List.filter (fun p -> ''' + V8_COUNT + ''')
        |> List.sumBy (fun p -> -p.Amount)
        |> Ok

/// A cash withdrawal, limited to 500.00 per account per business date (inclusive).
let withdraw (id: AccountId) (amount: decimal) (ledger: LedgerState) : Result<LedgerState, LedgerError> =
    if amount <= 0m then Error(InvalidAmount amount)
    else
        match balance id ledger, withdrawnToday id ledger with
        | Error e, _
        | _, Error e -> Error e
        | Ok current, _ when current < amount -> Error(InsufficientFunds(id, amount))
''' + V8_LIMIT + '''        | Ok _, Ok _ -> Ok(post id (-amount) "withdraw" ledger)
'''
v8_led = base["Ledger.fs"] + V8
write("V8", {"Domain.fs": v8_dom, "Ledger.fs": v8_led})
write("V8-per-call", {"Ledger.fs": edit(v8_led, (V8_LIMIT, "        | Ok _, Ok _ when amount > dailyWithdrawalLimit -> Error(DailyLimitExceeded(id, dailyWithdrawalLimit))\n"))})
write("V8-all-debits", {"Ledger.fs": edit(v8_led, (V8_COUNT, "p.Amount < 0m && p.Date = ledger.Today"))})
write("V8-exclusive", {"Ledger.fs": edit(v8_led, ("today + amount > dailyWithdrawalLimit", "today + amount >= dailyWithdrawalLimit"))})
print("ok")
