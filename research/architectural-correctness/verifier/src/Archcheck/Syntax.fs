/// Facts read from the untyped parse tree: enclosing scopes, comments, record-construction
/// labels, try/with handlers, match arms, literals and infix operators.
///
/// Typed symbol uses come from `Symbols`; this module supplies the structure the typed
/// results do not expose directly (which module a use sits in, whether a field label is a
/// write, where comments are). It never decides a DET rule on its own except ARC-TRC-01,
/// which is defined over comments.
module Archcheck.Syntax

open System
open System.Globalization
open FSharp.Compiler.Syntax
open FSharp.Compiler.SyntaxTrivia
open FSharp.Compiler.Text
open Archcheck.Domain

let spanOf (r: range) : Span =
    { StartLine = r.StartLine
      StartCol = r.StartColumn
      EndLine = r.EndLine
      EndCol = r.EndColumn }

let private joinIds (ids: Ident list) = ids |> List.map _.idText |> String.concat "."

/// (span, dotted name) of every namespace and module, outermost first.
let scopeTable (input: ParsedInput) : (Span * string) list =
    let rec decls (parent: string) (ds: SynModuleDecl list) =
        ds
        |> List.collect (fun d ->
            match d with
            | SynModuleDecl.NestedModule(moduleInfo = SynComponentInfo(longId = ids); decls = inner; range = r) ->
                let name = if parent = "" then joinIds ids else parent + "." + joinIds ids
                (spanOf r, name) :: decls name inner
            | _ -> [])

    match input with
    | ParsedInput.ImplFile(ParsedImplFileInput(contents = modules)) ->
        modules
        |> List.collect (fun (SynModuleOrNamespace(longId = ids; kind = kind; decls = ds; range = r)) ->
            let name =
                match kind with
                | SynModuleOrNamespaceKind.GlobalNamespace -> ""
                | _ -> joinIds ids

            (spanOf r, name) :: decls name ds)
    | ParsedInput.SigFile _ -> []

/// Innermost scope containing `span`.
let scopeAt (table: (Span * string) list) (span: Span) : string =
    table
    |> List.filter (fun (s, _) -> Span.within s span)
    |> List.sortByDescending (fun (_, name) -> name.Length)
    |> List.tryHead
    |> Option.map snd
    |> Option.defaultValue ""

let private lastIdent (e: SynExpr) : string option =
    match e with
    | SynExpr.Ident id -> Some id.idText
    | SynExpr.LongIdent(longDotId = SynLongIdent(id = ids)) -> ids |> List.tryLast |> Option.map _.idText
    | SynExpr.DotGet(longDotId = SynLongIdent(id = ids)) -> ids |> List.tryLast |> Option.map _.idText
    | _ -> None

/// The function at the head of an application chain: `Error (f x)` → `Error`.
let rec private headName (e: SynExpr) : string option =
    match e with
    | SynExpr.App(funcExpr = f) -> headName f
    | SynExpr.Paren(expr = inner) -> headName inner
    | SynExpr.Typed(expr = inner) -> headName inner
    | other -> lastIdent other

let private isExnType (t: SynType) =
    match t with
    | SynType.LongIdent(SynLongIdent(id = ids)) ->
        match List.tryLast ids with
        | Some id -> id.idText = "exn" || id.idText = "Exception"
        | None -> false
    | _ -> false

/// `_`, `ex`, `:? exn`, `:? Exception as ex`, `(ex: exn)`: a handler that matches anything.
let rec private isCatchAll (p: SynPat) =
    match p with
    | SynPat.Wild _
    | SynPat.Named _ -> true
    | SynPat.Paren(pat = inner) -> isCatchAll inner
    | SynPat.Typed(pat = inner; targetType = t) -> isCatchAll inner && isExnType t
    | SynPat.IsInst(pat = t) -> isExnType t
    | SynPat.As(lhsPat = l; rhsPat = r) -> isCatchAll l && isCatchAll r
    | _ -> false

/// The union case a pattern names, if it is a (possibly applied) case pattern.
let rec private patternCase (p: SynPat) : string option =
    match p with
    | SynPat.LongIdent(longDotId = SynLongIdent(id = ids)) -> ids |> List.tryLast |> Option.map _.idText
    | SynPat.Named(ident = SynIdent(id, _)) when id.idText.Length > 0 && Char.IsUpper id.idText[0] -> Some id.idText
    | SynPat.Paren(pat = inner) -> patternCase inner
    | _ -> None

let normalizeNumber (c: SynConst) : string option =
    let ofDecimal (d: decimal) =
        let n = d / 1.000000000000000000000000000000000m // strips trailing zeros
        Some(n.ToString(CultureInfo.InvariantCulture))

    match c with
    | SynConst.Int32 n -> Some(string n)
    | SynConst.Int64 n -> Some(string n)
    | SynConst.Int16 n -> Some(string n)
    | SynConst.UInt16 n -> Some(string n)
    | SynConst.UInt32 n -> Some(string n)
    | SynConst.UInt64 n -> Some(string n)
    | SynConst.Byte n -> Some(string n)
    | SynConst.SByte n -> Some(string n)
    | SynConst.Decimal d -> ofDecimal d
    | SynConst.Double d when Double.IsFinite d && abs d < 1e15 -> ofDecimal (decimal d)
    | SynConst.Single d when Single.IsFinite d && abs d < 1e15f -> ofDecimal (decimal d)
    | SynConst.Measure(constant = inner) ->
        match inner with
        | SynConst.Int32 n -> Some(string n)
        | SynConst.Double d when Double.IsFinite d -> ofDecimal (decimal d)
        | SynConst.Decimal d -> ofDecimal d
        | _ -> None
    | _ -> None

let private operatorSymbols =
    Map.ofList
        [ "op_LessThan", "<"
          "op_GreaterThan", ">"
          "op_LessThanOrEqual", "<="
          "op_GreaterThanOrEqual", ">="
          "op_Addition", "+"
          "op_Subtraction", "-"
          "op_Multiply", "*"
          "op_Division", "/"
          "op_Modulus", "%" ]

/// Identifiers that re-raise or raise from a handler.
let private raising =
    set [ "reraise"; "raise"; "rethrow"; "failwith"; "failwithf"; "invalidOp"; "invalidArg"; "nullArg" ]

type private Acc =
    { Labels: Span list
      Strings: (Span * string) list
      Bindings: string list
      Raises: Span list
      Tries: (Span * (SynMatchClause list)) list
      Arms: SynMatchClause list
      Literals: (Span * string) list
      Ops: (Span * string * SynExpr * SynExpr) list }

let private emptyAcc =
    { Labels = []
      Strings = []
      Bindings = []
      Raises = []
      Tries = []
      Arms = []
      Literals = []
      Ops = [] }

let private bindingName (p: SynPat) =
    match p with
    | SynPat.LongIdent(longDotId = SynLongIdent(id = ids)) -> ids |> List.tryLast |> Option.map _.idText
    | SynPat.Named(ident = SynIdent(id, _)) -> Some id.idText
    | _ -> None

let private collect (input: ParsedInput) : Acc =
    ParsedInput.fold
        (fun acc _path node ->
            match node with
            | SyntaxNode.SynBinding(SynBinding(headPat = pat)) ->
                match bindingName pat with
                | Some n -> { acc with Bindings = n :: acc.Bindings }
                | None -> acc
            | SyntaxNode.SynMatchClause clause -> { acc with Arms = clause :: acc.Arms }
            | SyntaxNode.SynPat(SynPat.Const(SynConst.String(text, _, r), _)) ->
                { acc with Strings = (spanOf r, text) :: acc.Strings }
            | SyntaxNode.SynExpr e ->
                match e with
                | SynExpr.Record(recordFields = fields) ->
                    let labels =
                        fields
                        |> List.choose (fun (SynExprRecordField(fieldName = (SynLongIdent(id = ids), _))) ->
                            ids |> List.tryLast |> Option.map (fun id -> spanOf id.idRange))

                    { acc with Labels = labels @ acc.Labels }
                | SynExpr.Const(SynConst.String(text, _, r), _) -> { acc with Strings = (spanOf r, text) :: acc.Strings }
                | SynExpr.InterpolatedString(contents = parts; range = r) ->
                    let text =
                        parts
                        |> List.choose (function
                            | SynInterpolatedStringPart.String(s, _) -> Some s
                            | _ -> None)
                        |> String.concat ""

                    { acc with Strings = (spanOf r, text) :: acc.Strings }
                | SynExpr.Const(c, r) ->
                    match normalizeNumber c with
                    | Some v -> { acc with Literals = (spanOf r, v) :: acc.Literals }
                    | None -> acc
                | SynExpr.Ident id when raising.Contains id.idText -> { acc with Raises = spanOf id.idRange :: acc.Raises }
                | SynExpr.TryWith(withCases = clauses; range = r) -> { acc with Tries = (spanOf r, clauses) :: acc.Tries }
                | SynExpr.App(isInfix = false; funcExpr = SynExpr.App(isInfix = true; funcExpr = op; argExpr = left); argExpr = right; range = r) ->
                    let opName =
                        match op with
                        | SynExpr.Ident id -> Some id.idText
                        | SynExpr.LongIdent(longDotId = SynLongIdent(id = [ id ])) -> Some id.idText
                        | _ -> None

                    match opName |> Option.bind (fun n -> operatorSymbols |> Map.tryFind n) with
                    | Some symbol -> { acc with Ops = (spanOf r, symbol, left, right) :: acc.Ops }
                    | None -> acc
                | _ -> acc
            | _ -> acc)
        emptyAcc
        input

let private constOf (e: SynExpr) =
    match e with
    | SynExpr.Const(c, _) -> normalizeNumber c
    | SynExpr.Paren(expr = SynExpr.Const(c, _)) -> normalizeNumber c
    | _ -> None

/// All comments: `//` and `(* *)` from the parse trivia, plus `///` documentation lines
/// (which the trivia omits) that do not start inside a string or block comment.
let comments (input: ParsedInput) (source: string) (strings: Span list) : Comment list =
    let lines = source.Replace("\r\n", "\n").Split('\n')

    let textOf (s: Span) =
        if s.StartLine < 1 || s.EndLine > lines.Length then
            ""
        elif s.StartLine = s.EndLine then
            let l = lines[s.StartLine - 1]
            l.Substring(min s.StartCol l.Length, max 0 (min s.EndCol l.Length - min s.StartCol l.Length))
        else
            [ yield lines[s.StartLine - 1].Substring(min s.StartCol lines[s.StartLine - 1].Length)
              for i in s.StartLine + 1 .. s.EndLine - 1 do
                  yield lines[i - 1]
              let l = lines[s.EndLine - 1]
              yield l.Substring(0, min s.EndCol l.Length) ]
            |> String.concat "\n"

    let trivia =
        match input with
        | ParsedInput.ImplFile(ParsedImplFileInput(trivia = t)) -> t.CodeComments
        | ParsedInput.SigFile(ParsedSigFileInput(trivia = t)) -> t.CodeComments
        |> List.map (function
            | CommentTrivia.LineComment r
            | CommentTrivia.BlockComment r -> spanOf r)

    let blocked = strings @ trivia

    let docLines =
        lines
        |> Array.mapi (fun i l -> i + 1, l)
        |> Array.choose (fun (n, l) ->
            let col = l.Length - l.TrimStart().Length

            if l.TrimStart().StartsWith "///" then
                let s = { StartLine = n; StartCol = col; EndLine = n; EndCol = l.Length }

                let inside =
                    blocked
                    |> List.exists (fun b -> Span.within b { s with EndCol = col + 1 } && b <> s)

                if inside then None else Some s
            else
                None)
        |> List.ofArray
        |> List.filter (fun s -> not (trivia |> List.contains s))

    (trivia @ docLines)
    |> List.distinct
    |> List.map (fun s -> { Span = s; Text = textOf s })
    |> List.sortBy (fun c -> c.Span.StartLine, c.Span.StartCol)

/// Per-file syntax facts. `scope` resolves a span to its enclosing module.
type FileSyntax =
    { Scopes: (Span * string) list
      RecordLabels: Set<Span>
      Comments: Comment list
      BindingNames: string list
      StringLiterals: string list
      Handlers: Handler list
      Arms: Collapse list
      Literals: Literal list
      BinaryOps: BinaryOp list }

let analyse (input: ParsedInput) (source: string) : FileSyntax =
    let scopes = scopeTable input
    let scope = scopeAt scopes
    let acc = collect input

    let handlers =
        acc.Tries
        |> List.collect (fun (_, clauses) ->
            clauses
            |> List.map (fun (SynMatchClause(pat = pat; whenExpr = guard; resultExpr = body; range = r)) ->
                let bodySpan = spanOf body.Range

                { Span = spanOf r
                  Scope = scope (spanOf r)
                  CatchAll = guard.IsNone && isCatchAll pat
                  Reraises = acc.Raises |> List.exists (Span.within bodySpan) }))

    let arms =
        acc.Arms
        |> List.choose (fun (SynMatchClause(pat = pat; resultExpr = body; range = r)) ->
            match patternCase pat, headName body with
            | Some case, Some into ->
                Some
                    { Span = spanOf r
                      Scope = scope (spanOf r)
                      Case = case
                      Into = into }
            | _ -> None)

    let ops =
        acc.Ops
        |> List.map (fun (r, symbol, left, right) ->
            let predicate =
                match constOf left, constOf right with
                | None, Some lit -> lastIdent left |> Option.map (fun f -> $"{f} {symbol} {lit}")
                | Some lit, None -> lastIdent right |> Option.map (fun f -> $"{lit} {symbol} {f}")
                | _ -> None

            { Span = r
              Scope = scope r
              Op = symbol
              Operands = [ spanOf left.Range; spanOf right.Range ]
              Predicate = predicate })

    let stringSpans = acc.Strings |> List.map fst

    { Scopes = scopes
      RecordLabels = Set.ofList acc.Labels
      Comments = comments input source stringSpans
      BindingNames = acc.Bindings |> List.distinct |> List.sort
      StringLiterals = acc.Strings |> List.map snd |> List.distinct |> List.sort
      Handlers = handlers |> List.sortBy (fun h -> h.Span.StartLine, h.Span.StartCol)
      Arms = arms |> List.sortBy (fun a -> a.Span.StartLine, a.Span.StartCol)
      Literals =
        acc.Literals
        |> List.map (fun (s, v) -> { Span = s; Scope = scope s; Value = v })
        |> List.sortBy (fun l -> l.Span.StartLine, l.Span.StartCol)
      BinaryOps = ops |> List.sortBy (fun o -> o.Span.StartLine, o.Span.StartCol) }
