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
        |> Result.bind (Catalog.addCopy { Id = CopyId "c1"; Book = BookId "b1" })
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
