/// The immutable facts the verifier reasons over, and the findings it produces.
///
/// Everything here is plain data. Facts are produced at the edges (MSBuild evaluation,
/// FSharpChecker, the parse tree) and the rules in `Rules` and `Heuristics` are pure
/// functions from facts and policy to findings.
module Archcheck.Domain

/// A source span. Lines are 1-based; columns are 0-based, as FCS reports them.
type Span =
    { StartLine: int
      StartCol: int
      EndLine: int
      EndCol: int }

module Span =
    let empty = { StartLine = 0; StartCol = 0; EndLine = 0; EndCol = 0 }

    let private before (l1, c1) (l2, c2) = l1 < l2 || (l1 = l2 && c1 <= c2)

    /// `inner` lies entirely within `outer`.
    let within (outer: Span) (inner: Span) =
        before (outer.StartLine, outer.StartCol) (inner.StartLine, inner.StartCol)
        && before (inner.EndLine, inner.EndCol) (outer.EndLine, outer.EndCol)

type RuleClass =
    | Det
    | Heu

module RuleClass =
    let name =
        function
        | Det -> "DET"
        | Heu -> "HEU"

/// What a resolved symbol is. `Function` is a module-level function, `ModuleValue` a
/// module-level non-function value, `Method` a member of a type.
type SymbolKind =
    | Type
    | UnionCase
    | Field
    | Property
    | Method
    | Constructor
    | Function
    | ModuleValue
    | ActivePattern
    | Event
    | Other

module SymbolKind =
    let all =
        [ Type; UnionCase; Field; Property; Method; Constructor; Function; ModuleValue; ActivePattern; Event; Other ]

    let name =
        function
        | Type -> "type"
        | UnionCase -> "unionCase"
        | Field -> "field"
        | Property -> "property"
        | Method -> "method"
        | Constructor -> "constructor"
        | Function -> "function"
        | ModuleValue -> "moduleValue"
        | ActivePattern -> "activePattern"
        | Event -> "event"
        | Other -> "other"

    let tryParse (s: string) = all |> List.tryFind (fun k -> name k = s)

/// One typed use of a non-local symbol, as resolved by the F# compiler.
type SymbolUse =
    {
        /// Fully qualified name used for matching, e.g. `System.DateTime.Now`,
        /// `Lending.Semantic.Loan.DueDate`, `Lending.Transition.Loans.renew`.
        Name: string
        /// Full name of the declaring entity (`System.DateTime`), or "" for a top-level entity.
        Owner: string
        Assembly: string
        Kind: SymbolKind
        Span: Span
        /// Innermost enclosing namespace or module of the use site, from the parse tree.
        Scope: string
        IsFromPattern: bool
        IsFromType: bool
        /// The use is the field label of a record construction or copy-and-update
        /// expression (`{ r with DueDate = d }`): a write, not a read.
        IsRecordConstructionLabel: bool
    }

type Comment = { Span: Span; Text: string }

/// A `try ... with` clause.
type Handler =
    { Span: Span
      Scope: string
      CatchAll: bool
      Reraises: bool }

/// A match clause whose pattern names a union case (`Case`) and whose result is headed by
/// an identifier (`Into`), e.g. `| Unknown r -> Error r` is (Unknown, Error).
type Collapse =
    { Span: Span
      Scope: string
      Case: string
      Into: string }

/// A numeric literal, normalised (`14.0` and `14` are both `14`).
type Literal =
    { Span: Span
      Scope: string
      Value: string }

/// An infix comparison or arithmetic application.
type BinaryOp =
    { Span: Span
      Scope: string
      Op: string
      Operands: Span list
      /// `field op literal` shape, e.g. `Renewals >= 3`, when one side is a literal.
      Predicate: string option }

type SourceFile =
    {
        /// Repository-relative path with forward slashes.
        Path: string
        Lines: int
        Uses: SymbolUse list
        Comments: Comment list
        /// Names of let/member bindings (test names for ARC-TRC-01).
        BindingNames: string list
        StringLiterals: string list
        Handlers: Handler list
        Arms: Collapse list
        Literals: Literal list
        BinaryOps: BinaryOp list
    }

type ProjectRole =
    | Production
    | Test

type ProjectRef =
    {
        /// Repository-relative path of the referenced project.
        Target: string
        /// Repository-relative file that declares the reference (the project or an import).
        DefinedIn: string
        Line: int
    }

type PackageRef =
    { Id: string
      Version: string
      /// Declared by a file in the repository (as opposed to implicit or transitive).
      Direct: bool
      DefinedIn: string
      Line: int }

type AssemblyRefKind =
    | Framework
    | ProjectOutput
    | Package of string
    | Raw

type AssemblyRef = { Path: string; Kind: AssemblyRefKind }

type Project =
    { Path: string
      Tier: int option
      Role: ProjectRole
      AssemblyName: string
      ProjectRefs: ProjectRef list
      Packages: PackageRef list
      AssemblyRefs: AssemblyRef list
      Files: SourceFile list }

type Facts = { Projects: Project list }

type Finding =
    { RuleId: string
      Class: RuleClass
      Severity: int
      Project: string
      File: string
      Line: int
      Column: int
      Symbol: string
      Message: string
      Origins: string list }

/// The fixed catalogue from INTERFACES.md §4. Class and severity are not policy inputs:
/// a policy cannot downgrade a rule.
type RuleInfo =
    { Id: string
      Class: RuleClass
      Severity: int
      Statement: string }

module Catalogue =
    let all =
        [ { Id = "ARC-DEP-01"; Class = Det; Severity = 3; Statement = "No upward ProjectReference" }
          { Id = "ARC-DEP-02"; Class = Det; Severity = 3; Statement = "Tier 1/2 projects reference no package and no assembly beyond FSharp.Core and the BCL" }
          { Id = "ARC-SYM-01"; Class = Det; Severity = 3; Statement = "Tier 1/2 code uses no effectful BCL symbol" }
          { Id = "ARC-SYM-02"; Class = Det; Severity = 2; Statement = "Only the Tier 4 composition root reads the clock, randomness or GUID generation" }
          { Id = "ARC-SYM-03"; Class = Det; Severity = 2; Statement = "Tier 3 uses no I/O, network, JSON or console symbol" }
          { Id = "ARC-BND-01"; Class = Det; Severity = 2; Statement = "Presentation uses no persistence symbol" }
          { Id = "ARC-BND-02"; Class = Det; Severity = 2; Statement = "Presentation and persistence call no Tier 2 function" }
          { Id = "ARC-BND-03"; Class = Det; Severity = 2; Statement = "Presentation reads no non-identifier field of a Tier 1 entity" }
          { Id = "ARC-HEU-01"; Class = Heu; Severity = 1; Statement = "Catch-all handler or Unknown collapsed into a failure" }
          { Id = "ARC-HEU-02"; Class = Heu; Severity = 1; Statement = "Domain literal or predicate duplicated in two tiers" }
          { Id = "ARC-HEU-03"; Class = Heu; Severity = 1; Statement = "Comparison or arithmetic on domain values in the host" }
          { Id = "ARC-HEU-04"; Class = Heu; Severity = 1; Statement = "File exceeds the SDE-STRUCT-001 line band" }
          { Id = "ARC-TRC-01"; Class = Det; Severity = 1; Statement = "Every contract decision id appears in a production comment and in a test" } ]

    let tryFind id = all |> List.tryFind (fun r -> r.Id = id)

    /// Rules a policy must configure. ARC-TRC-01 needs no parameters.
    let required = all |> List.map _.Id |> List.filter ((<>) "ARC-TRC-01")
