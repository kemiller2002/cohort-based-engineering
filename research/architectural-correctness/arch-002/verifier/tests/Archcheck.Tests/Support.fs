/// Builders for synthetic facts, so rules can be tested without building anything.
module Archcheck.Tests.Support

open System.IO
open Archcheck.Domain
open Archcheck.Policy

let span line col =
    { StartLine = line
      StartCol = col
      EndLine = line
      EndCol = col + 5 }

let symbolUse (scope: string) (kind: SymbolKind) (name: string) (line: int) =
    let owner =
        match name.LastIndexOf '.' with
        | -1 -> ""
        | i -> name.Substring(0, i)

    { Name = name
      Owner = owner
      Assembly = ""
      Kind = kind
      Span = span line 4
      Scope = scope
      IsFromPattern = false
      IsFromType = false
      IsRecordConstructionLabel = false }

let file (path: string) (uses: SymbolUse list) : SourceFile =
    { Path = path
      Lines = 10
      Uses = uses
      Comments = []
      BindingNames = []
      StringLiterals = []
      Handlers = []
      Arms = []
      Literals = []
      BinaryOps = [] }

let project (path: string) (tier: int) (files: SourceFile list) : Project =
    { Path = path
      Tier = Some tier
      Role = Production
      AssemblyName = Path.GetFileNameWithoutExtension path
      ProjectRefs = []
      Packages = []
      AssemblyRefs = []
      Files = files }

let facts projects = { Projects = projects }

/// The real Lending policy shipped with the verifier.
let policyPath =
    let rec up (dir: DirectoryInfo) =
        let candidate = Path.Combine(dir.FullName, "policy", "lending.policy.json")
        if File.Exists candidate then candidate else up dir.Parent

    up (DirectoryInfo System.AppContext.BaseDirectory)

let samplesDir = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName policyPath), "tests", "samples")

let lendingPolicy =
    lazy
        (match decode (File.ReadAllText policyPath) with
         | Ok p -> p
         | Error e -> failwith e)

let instance (ruleId: string) =
    lendingPolicy.Value.Rules |> List.find (fun r -> r.Rule.Id = ruleId)

let ruleIds (findings: Finding list) =
    findings |> List.map _.RuleId |> List.distinct |> List.sort
