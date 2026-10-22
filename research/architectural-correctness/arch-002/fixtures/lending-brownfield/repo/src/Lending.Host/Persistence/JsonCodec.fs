/// Hand-written JSON representation of the library state (format "lending/2").
module Lending.Host.Persistence.JsonCodec

open System
open System.Globalization
open System.Text.Json
open System.Text.Json.Nodes
open Lending.Semantic

let private text (value: string) : JsonNode = JsonValue.Create value
let private number (value: int) : JsonNode = JsonValue.Create value
let private amount (value: decimal) : JsonNode = JsonValue.Create value

let private date (value: DateOnly) : JsonNode =
    JsonValue.Create(value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture))

let private record (fields: (string * JsonNode) list) : JsonNode =
    let o = JsonObject()
    fields |> List.iter (fun (name, value) -> o[name] <- value)
    o

let private array (items: JsonNode seq) : JsonNode = JsonArray(Seq.toArray items)

let private memberType value =
    match value with
    | Standard -> "standard"
    | Student -> "student"
    | Staff -> "staff"

let private encodeMember (m: Member) =
    record [ "id", text (MemberId.value m.Id); "name", text m.Name; "type", text (memberType m.Type) ]

let private encodeBook (book: Book) =
    record
        [ "id", text (BookId.value book.Id)
          "title", text book.Title
          "author", text book.Author
          "isbn", text book.Isbn ]

let private encodeBranch (branch: Branch) =
    record [ "id", text (BranchId.value branch.Id); "name", text branch.Name ]

let private encodeCopy (copy: Copy) =
    record
        [ "id", text (CopyId.value copy.Id)
          "book", text (BookId.value copy.Book)
          "branch", text (BranchId.value copy.Branch) ]

let private encodeLoan (loan: Loan) =
    record
        [ "copy", text (CopyId.value loan.Copy)
          "member", text (MemberId.value loan.Member)
          "borrowedOn", date loan.BorrowedOn
          "dueDate", date loan.DueDate
          "renewals", number loan.Renewals ]

let private encodeHold (hold: Hold) =
    record
        [ "book", text (BookId.value hold.Book)
          "member", text (MemberId.value hold.Member)
          "placedOn", date hold.PlacedOn ]

let private encodeFine (fine: Fine) =
    record
        [ "member", text (MemberId.value fine.Member)
          "copy", text (CopyId.value fine.Copy)
          "amount", amount fine.Amount
          "assessedOn", date fine.AssessedOn ]

let private encodePayment (payment: Payment) =
    record
        [ "member", text (MemberId.value payment.Member)
          "amount", amount payment.Amount
          "paidOn", date payment.PaidOn ]

let private encodeOutcome (outcome: ReminderOutcome) =
    match outcome with
    | Sent -> record [ "kind", text "sent" ]
    | Bounced reason -> record [ "kind", text "bounced"; "reason", text reason ]
    | Unconfirmed -> record [ "kind", text "unconfirmed" ]

let private encodeReminder (reminder: Reminder) =
    record
        [ "copy", text (CopyId.value reminder.Copy)
          "member", text (MemberId.value reminder.Member)
          "dueDate", date reminder.DueDate
          "attemptedAt", text (reminder.AttemptedAt.ToString("o", CultureInfo.InvariantCulture))
          "outcome", encodeOutcome reminder.Outcome ]

let encode (library: Library) : string =
    let values (m: Map<_, _>) = m |> Map.toSeq |> Seq.map snd

    let root =
        record
            [ "format", text "lending/2"
              "members", array (values library.Members |> Seq.map encodeMember)
              "books", array (values library.Books |> Seq.map encodeBook)
              "branches", array (values library.Branches |> Seq.map encodeBranch)
              "copies", array (values library.Copies |> Seq.map encodeCopy)
              "loans", array (values library.Loans |> Seq.map encodeLoan)
              "holds", array (library.Holds |> Seq.map encodeHold)
              "fines", array (library.Fines |> Seq.map encodeFine)
              "payments", array (library.Payments |> Seq.map encodePayment)
              "reminders", array (library.Reminders |> Seq.map encodeReminder) ]

    root.ToJsonString(JsonSerializerOptions(WriteIndented = true))

let private str (node: JsonNode) (name: string) = node[name].GetValue<string>()
let private int (node: JsonNode) (name: string) = node[name].GetValue<int>()
let private dec (node: JsonNode) (name: string) = node[name].GetValue<decimal>()

let private day (node: JsonNode) (name: string) =
    DateOnly.ParseExact(str node name, "yyyy-MM-dd", CultureInfo.InvariantCulture)

let private items (node: JsonNode) (name: string) =
    match node[name] with
    | null -> []
    | list -> list.AsArray() |> Seq.toList

let private decodeMemberType value =
    match value with
    | "standard" -> Standard
    | "student" -> Student
    | "staff" -> Staff
    | other -> failwith $"unknown member type '{other}' in store"

let private decodeMember (n: JsonNode) : Member =
    { Id = MemberId(str n "id")
      Name = str n "name"
      Type = decodeMemberType (str n "type") }

let private decodeBook (n: JsonNode) : Book =
    { Id = BookId(str n "id")
      Title = str n "title"
      Author = str n "author"
      Isbn = str n "isbn" }

let private decodeBranch (n: JsonNode) : Branch =
    { Id = BranchId(str n "id")
      Name = str n "name" }

let private decodeCopy (n: JsonNode) : Copy =
    { Id = CopyId(str n "id")
      Book = BookId(str n "book")
      Branch = BranchId(str n "branch") }

let private decodeLoan (n: JsonNode) : Loan =
    { Copy = CopyId(str n "copy")
      Member = MemberId(str n "member")
      BorrowedOn = day n "borrowedOn"
      DueDate = day n "dueDate"
      Renewals = int n "renewals" }

let private decodeHold (n: JsonNode) : Hold =
    { Book = BookId(str n "book")
      Member = MemberId(str n "member")
      PlacedOn = day n "placedOn" }

let private decodeFine (n: JsonNode) : Fine =
    { Member = MemberId(str n "member")
      Copy = CopyId(str n "copy")
      Amount = dec n "amount"
      AssessedOn = day n "assessedOn" }

let private decodePayment (n: JsonNode) : Payment =
    { Member = MemberId(str n "member")
      Amount = dec n "amount"
      PaidOn = day n "paidOn" }

let private decodeOutcome (n: JsonNode) =
    match str n "kind" with
    | "sent" -> Sent
    | "bounced" -> Bounced(str n "reason")
    | "unconfirmed" -> Unconfirmed
    | other -> failwith $"unknown reminder outcome '{other}' in store"

let private decodeReminder (n: JsonNode) : Reminder =
    { Copy = CopyId(str n "copy")
      Member = MemberId(str n "member")
      DueDate = day n "dueDate"
      AttemptedAt = DateTime.Parse(str n "attemptedAt", CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)
      Outcome = decodeOutcome n["outcome"] }

let decode (json: string) : Library =
    let root = JsonNode.Parse json

    { Library.empty with
        Members = items root "members" |> List.map decodeMember |> List.map (fun m -> m.Id, m) |> Map.ofList
        Books = items root "books" |> List.map decodeBook |> List.map (fun b -> b.Id, b) |> Map.ofList
        Branches =
            match items root "branches" with
            | [] -> Library.empty.Branches
            | branches -> branches |> List.map decodeBranch |> List.map (fun b -> b.Id, b) |> Map.ofList
        Copies = items root "copies" |> List.map decodeCopy |> List.map (fun c -> c.Id, c) |> Map.ofList
        Loans = items root "loans" |> List.map decodeLoan |> List.map (fun l -> l.Copy, l) |> Map.ofList
        Holds = items root "holds" |> List.map decodeHold
        Fines = items root "fines" |> List.map decodeFine
        Payments = items root "payments" |> List.map decodePayment
        Reminders = items root "reminders" |> List.map decodeReminder }
