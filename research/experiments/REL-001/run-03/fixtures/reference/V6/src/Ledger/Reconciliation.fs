/// Bank reconciliation: matches an account's postings against the lines of
/// a bank statement.
module Ledger.Reconciliation

let private gap (posting: Posting) (line: BankLine) = abs (posting.Date.DayNumber - line.BookedOn.DayNumber)

let private canMatch (line: BankLine) (posting: Posting) =
    posting.Amount = line.Value && posting.Reference = line.Memo && gap posting line <= 2

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
                let i, p = candidates |> List.minBy (fun (i, p) -> gap p line, i)
                (i, p, line) :: matched, unmatched
        let matched, unmatched = lines |> List.fold step ([], [])
        let taken = takenOf matched
        Ok
            { Matched = matched |> List.rev |> List.map (fun (_, p, l) -> p, l)
              LedgerOnly = postings |> List.filter (fun (i, _) -> not (taken.Contains i)) |> List.map snd
              BankOnly = List.rev unmatched }
