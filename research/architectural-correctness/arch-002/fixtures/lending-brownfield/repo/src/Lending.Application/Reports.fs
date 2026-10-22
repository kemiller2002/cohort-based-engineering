/// Reports the desk exports for the branch managers.
module Lending.Application.Reports

open System.IO
open Lending.Semantic
open Lending.Transition

/// Writes the overdue loans as CSV (`copy,member,due,days overdue`), longest overdue first.
let exportOverdue (ports: Ports) (path: string) : Result<Views.ExportView, LendingError> =
    let today = ports.Clock()
    let library = ports.Store.Load()

    let rows =
        Loans.overdue today library
        |> List.map (fun loan ->
            $"{CopyId.value loan.Copy},{MemberId.value loan.Member},{Views.date loan.DueDate},{Loans.daysOverdue today loan}")

    File.WriteAllLines(path, "copy,member,due,days overdue" :: rows)
    Ok { Path = path; Rows = rows.Length }
