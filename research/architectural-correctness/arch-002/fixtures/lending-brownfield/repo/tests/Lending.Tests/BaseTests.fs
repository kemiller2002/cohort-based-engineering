module BaseTests

open Xunit
open Lending.Semantic
open Lending.Transition
open Lending.Host.Persistence
open Lending.Host.Cli
open Support

[<Fact>]
let ``borrowing lends a copy for 21 days`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("c1 lent to m1, due 2026-03-23", run w "borrow m1 c1")
    Assert.Equal("loans for m1 (Ada Lovelace):\n  c1 \"Dune\" due 2026-03-23", run w "loans m1")

[<Fact>]
let ``a copy on loan cannot be lent again`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    Assert.Equal("error: copy c1 is already on loan", run w "borrow s1 c1")

[<Fact>]
let ``a student may have three loans at once`` () =
    let w = seeded "2026-03-02"
    [ "add-copy c4 b2"; "add-copy c5 b2"; "borrow s1 c1"; "borrow s1 c2"; "borrow s1 c3" ] |> List.iter (run w >> ignore)
    Assert.Equal("error: member s1 already has 3 loans", run w "borrow s1 c4")

[<Fact>]
let ``returning late assesses a fine of 0.25 per day`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-26"
    Assert.Equal("c1 returned 3 days late, fine 0.75", run w "return c1")
    Assert.Equal("no loans for m1 (Ada Lovelace)", run w "loans m1")

[<Fact>]
let ``returning on time costs nothing`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-23"
    Assert.Equal("c1 returned", run w "return c1")

[<Fact>]
let ``fines are capped at 10.00`` () =
    Assert.Equal(10.00m, Fines.fineFor (day "2026-01-01") (day "2026-12-31"))

[<Fact>]
let ``a held book is lent only to the head of its queue`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("s1 holds b1 at position 1", run w "hold s1 b1")
    Assert.Equal("m1 holds b1 at position 2", run w "hold m1 b1")
    Assert.Equal("error: copy c1 is reserved for another member", run w "borrow m1 c1")
    Assert.Equal("c1 lent to s1, due 2026-03-23", run w "borrow s1 c1")
    Assert.Equal("c2 lent to m1, due 2026-03-23", run w "borrow m1 c2")

[<Fact>]
let ``renewal extends the due date and is limited`` () =
    let library =
        Library.empty
        |> Catalog.addMember { Id = MemberId "m1"; Name = "Ada"; Type = Standard }
        |> Result.bind (Catalog.addBook { Id = BookId "b1"; Title = "Dune"; Author = "Herbert"; Isbn = "x" })
        |> Result.bind (Catalog.addCopy { Id = CopyId "c1"; Book = BookId "b1"; Branch = BranchId "main" })
        |> Result.bind (Loans.borrow (day "2026-03-02") (MemberId "m1") (CopyId "c1") >> Result.map fst)

    let renew l = l |> Result.bind (Loans.renew (day "2026-03-10") (CopyId "c1") >> Result.map fst)
    let twice = library |> renew |> renew
    let due = twice |> Result.map (fun l -> l.Loans[CopyId "c1"].DueDate)
    Assert.Equal(Ok(day "2026-05-04"), due)
    Assert.Equal(Error(RenewLimitReached(CopyId "c1", 2)), twice |> renew |> Result.map ignore)

[<Fact>]
let ``unknown commands and wrong arity are reported`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("error: unknown command 'lend' (try help)", run w "lend m1 c1")
    Assert.Equal("usage: borrow <member> <copy>", run w "borrow m1")
    Assert.Equal("error: unterminated quote", run w "add-member m9 standard \"Bob")
    Assert.Equal("error: unknown member type 'vip' (standard, student or staff)", run w "add-member m9 vip Bob")

[<Fact>]
let ``the json file store round-trips the library`` () =
    let path = System.IO.Path.GetTempFileName()

    try
        let w = seeded "2026-03-02"
        [ "borrow m1 c1"; "hold s1 b1" ] |> List.iter (run w >> ignore)
        w.SetToday "2026-04-01"
        run w "return c1" |> ignore
        let library = w.Ports.Store.Load()
        let store = JsonFileStore.create path
        store.Save library
        Assert.Equal(library, store.Load())
    finally
        System.IO.File.Delete path

[<Fact>]
let ``copies are shelved at a branch and can be transferred`` () =
    let w = seeded "2026-03-02"
    Assert.Equal("branch east added: East Branch", run w "add-branch east \"East Branch\"")
    Assert.Equal("copy c4 added for book b2 at east", run w "add-copy c4 b2 east")
    Assert.Equal("error: unknown branch west", run w "add-copy c5 b2 west")
    run w "borrow m1 c1" |> ignore
    Assert.Equal("error: copy c1 is already on loan", run w "transfer c1 east")
    Assert.Equal("c2 moved to east (East Branch)", run w "transfer c2 east")
    Assert.Equal("copies at east (East Branch):\n  c2 \"Dune\" on shelf\n  c4 \"Emma\" on shelf", run w "shelf east")
    Assert.Equal("copies at main (Main Library):\n  c1 \"Dune\" on loan, due 2026-03-23\n  c3 \"Emma\" on shelf", run w "shelf main")

[<Fact>]
let ``holds can be listed and cancelled`` () =
    let w = seeded "2026-03-02"
    [ "hold s1 b1"; "hold m1 b1" ] |> List.iter (run w >> ignore)
    Assert.Equal("holds for b1 (Dune):\n  1. s1 (Sam Student) since 2026-03-02\n  2. m1 (Ada Lovelace) since 2026-03-02", run w "holds b1")
    Assert.Equal("s1 no longer holds b1", run w "cancel-hold s1 b1")
    Assert.Equal("error: member s1 does not hold book b1", run w "cancel-hold s1 b1")
    Assert.Equal("c1 lent to m1, due 2026-03-23", run w "borrow m1 c1")
    Assert.Equal("no holds for b1 (Dune)", run w "holds b1")

[<Fact>]
let ``renewing moves the due date by 21 days`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-10"
    Assert.Equal("c1 renewed, due 2026-04-13", run w "renew c1")
    Assert.Equal("error: copy c3 is not on loan", run w "renew c3")

[<Fact>]
let ``fines and payments show on the account`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-03-26"
    run w "return c1" |> ignore
    Assert.Equal("error: member m1 owes only 0.75", run w "pay m1 1.00")
    Assert.Equal("error: invalid amount '0.123'", run w "pay m1 0.123")
    Assert.Equal("m1 paid 0.50, owes 0.25", run w "pay m1 0.50")
    run w "borrow m1 c1" |> ignore
    Assert.Equal("account for m1 (Ada Lovelace):\n  fine c1 0.75 assessed 2026-03-26\n  paid 0.50\nowed: 0.25\nloans: 1 of 5", run w "account m1")
    Assert.Equal("error: member s1 owes nothing", run w "pay s1 1.00")

[<Fact>]
let ``a member who owes 5.00 or more cannot borrow`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    w.SetToday "2026-04-13"
    Assert.Equal("c1 returned 21 days late, fine 5.25", run w "return c1")
    Assert.Equal("error: member m1 owes too much to borrow", run w "borrow m1 c2")
    run w "pay m1 0.25" |> ignore
    Assert.Equal("error: member m1 owes too much to borrow", run w "borrow m1 c2")
    run w "pay m1 0.01" |> ignore
    Assert.Equal("c2 lent to m1, due 2026-05-04", run w "borrow m1 c2")

[<Fact>]
let ``overdue loans are listed and exported`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow s1 c3" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-10"
    run w "borrow s1 c2" |> ignore
    w.SetToday "2026-03-30"
    Assert.Equal("overdue loans on 2026-03-30:\n  c1 \"Dune\" lent to m1, due 2026-03-23, 7 days overdue\n  c3 \"Emma\" lent to s1, due 2026-03-23, 7 days overdue", run w "overdue")
    let path = tempPath "overdue.csv"
    Assert.Equal($"exported 2 overdue loans to {path}", run w $"export-overdue {path}")
    Assert.Equal<string list>([ "copy,member,due,days overdue"; "c1,m1,2026-03-23,7"; "c3,s1,2026-03-23,7" ], System.IO.File.ReadAllLines path |> List.ofArray)

[<Fact>]
let ``reminders are sent once per loan and due date`` () =
    let w = seeded "2026-03-02"
    [ "borrow m1 c1"; "borrow s1 c3" ] |> List.iter (run w >> ignore)
    w.SetToday "2026-03-24"
    Assert.Equal("reminders: 2 sent, 0 bounced, 0 unconfirmed", run w "remind")
    Assert.Equal("reminders: 0 sent, 0 bounced, 0 unconfirmed", run w "remind")
    Assert.Equal(2, w.Sent().Length)

[<Fact>]
let ``members are imported from a csv file`` () =
    let w = seeded "2026-03-02"
    let path = tempPath "members.csv"
    System.IO.File.WriteAllLines(path, [| "member,type,name"; "m2,student,Bea Student"; "m3,staff,Carl Staff" |])
    Assert.Equal("imported 2 members", run w $"import-members {path}")
    Assert.Equal("no loans for m3 (Carl Staff)", run w "loans m3")
    Assert.Equal("error: line 2: member m2 already exists", run w $"import-members {path}")

[<Fact>]
let ``a backup holds the whole library`` () =
    let w = seeded "2026-03-02"
    run w "borrow m1 c1" |> ignore
    let path = tempPath "backup.json"
    Assert.Equal($"backed up to {path}", run w $"backup {path}")
    Assert.Equal(Some(w.Ports.Store.Load()), JsonFileStore.archive.Load path)

[<Fact>]
let ``an unconfirmed reminder waits for staff and a missing one is sent again`` () =
    let w = worldWith "2026-03-02" (fun _ -> NoAnswer)
    [ "add-member m1 standard \"Ada Lovelace\""; "add-book b1 9780441013593 Dune \"Frank Herbert\""; "add-copy c1 b1"; "borrow m1 c1" ]
    |> List.iter (run w >> ignore)
    w.SetToday "2026-03-24"
    Assert.Equal("reminders: 0 sent, 0 bounced, 1 unconfirmed", run w "remind")
    Assert.Equal("reminders: 0 sent, 0 bounced, 0 unconfirmed", run w "remind")
    Assert.Equal("reminder for c1 marked missing; it will be sent again", run w "reconcile c1 missing")
    Assert.Equal("reminders: 0 sent, 0 bounced, 1 unconfirmed", run w "remind")
    Assert.Equal("error: no unconfirmed reminder for c3", run w "reconcile c3 arrived")
    Assert.Equal("1 members:\n  m1 Ada Lovelace (standard), 1 loans", run w "members")
