/// SPR-C2-01 case runner (EXPERIMENTAL). Every case reads Conditor's production
/// trust (`ReleaseAttestation.embedded`, i.e. the trust file compiled into the
/// scratch build) unless the case says otherwise (N5 builds a revoked trust list
/// through the production parser `ReleaseAttestation.parseTrust`).
module C2Harness.Program

open System
open System.Diagnostics
open System.IO
open System.Text
open System.Text.Json
open System.Text.Json.Nodes
open Conditor.Core
open C2Harness.Fixtures

type Outcome =
    { Id: string
      Description: string
      Expected: string
      Observed: string
      Pass: bool }

let outcomeText =
    function
    | Attested(keyId, contracts) -> $"""Attested({keyId}; {String.concat "," contracts})"""
    | NotAttested reason -> $"NotAttested({reason})"

let isAttested = function Attested _ -> true | NotAttested _ -> false

let notAttestedWith (needle: string) =
    function
    | NotAttested reason -> reason.Contains(needle, StringComparison.Ordinal)
    | Attested _ -> false

let argValue (args: string list) (name: string) =
    args |> List.pairwise |> List.tryPick (fun (k, v) -> if k = name then Some v else None)

let required args name =
    argValue args name |> Option.defaultWith (fun () -> failwith $"missing {name}")

/// Writes a minimal repository whose recorded Registry authority is `setBytes`.
let writeRepo (root: string) (label: string) (formaVersion: string) (setBytes: byte array) (recordedSha: string) =
    let target = Path.Combine(root, label)
    Directory.CreateDirectory(Path.Combine(target, ".conditor", "authority")) |> ignore
    File.WriteAllBytes(Path.Combine(target, ".conditor", "authority", "resolved-release-set.json"), setBytes)

    let manifest =
        $$"""{
  "schemaVersion": 1,
  "name": "spr-c2-01-{{label}}",
  "registryAuthority": {
    "kind": "resolved-release-set",
    "path": ".conditor/authority/resolved-release-set.json",
    "sha256": "{{recordedSha}}"
  },
  "components": [
    { "id": "forma", "version": "{{formaVersion}}", "required": false }
  ],
  "requirements": [],
  "execution": { "enabled": false }
}
"""

    File.WriteAllText(Path.Combine(target, "conditor.json"), manifest)
    target

let validateIn (target: string) =
    match Manifest.load (Path.Combine(target, "conditor.json")) with
    | Error errors -> errors |> List.map (fun e -> "MANIFEST: " + e)
    | Ok manifest -> Compatibility.validateIn target manifest

let runCli (cliDll: string) (target: string) =
    let info = ProcessStartInfo("dotnet", [ cliDll; "doctor"; "--json"; "--target"; target ])
    info.RedirectStandardOutput <- true
    info.RedirectStandardError <- true
    use proc = Process.Start info |> nonNull
    let stdout = proc.StandardOutput.ReadToEnd()
    let stderr = proc.StandardError.ReadToEnd()
    proc.WaitForExit()
    proc.ExitCode, stdout, stderr

/// COND-DOC-COMPAT findings that mention forma, from `conditor doctor --json`.
let compatFindings (stdout: string) =
    try
        use doc = JsonDocument.Parse stdout
        let rec walk (e: JsonElement) : JsonElement seq =
            match e.ValueKind with
            | JsonValueKind.Object ->
                seq {
                    yield e
                    for p in e.EnumerateObject() do
                        yield! walk p.Value
                }
            | JsonValueKind.Array -> e.EnumerateArray() |> Seq.collect walk
            | _ -> Seq.empty

        walk doc.RootElement
        |> Seq.filter (fun o ->
            let mutable code = Unchecked.defaultof<JsonElement>
            o.TryGetProperty("code", &code) && code.ValueKind = JsonValueKind.String && code.GetString() = "COND-DOC-COMPAT")
        |> Seq.map (fun o -> o.GetRawText())
        |> Seq.filter (fun t -> t.Contains "forma")
        |> Seq.toList
        |> Ok
    with ex ->
        Error ex.Message

[<EntryPoint>]
let main argv =
    let args = List.ofArray argv
    let setPath = required args "--set"
    let keyId = required args "--key-id"
    let version = required args "--target-version"
    let synthetic = args |> List.contains "--synthetic"
    let outDir = required args "--out"
    let cliDll = argValue args "--cli"
    use trusted = loadKey (required args "--trusted")
    use untrusted = loadKey (required args "--untrusted")
    let fixtureDir = Path.Combine(outDir, "fixtures")
    let repoRoot = Path.Combine(Path.GetTempPath(), $"spr-c2-01-{Guid.NewGuid():N}")
    Directory.CreateDirectory fixtureDir |> ignore

    let real = parse (File.ReadAllText setPath)
    let trust = ReleaseAttestation.embedded.Value
    let contract = [ WebContract ]

    // The unsigned base: the real set, or the real set with Forma moved to a
    // synthetic, in-range version not in this build's catalog.
    let syntheticDigest =
        sha256Hex (Encoding.UTF8.GetBytes $"SPR-C2-01 synthetic forma {version} release manifest (not a real release)")

    let unsigned =
        if synthetic then real |> setVersion "forma" version |> setManifestSha "forma" syntheticDigest else clone real

    let signed = unsigned |> attest trusted keyId contract "forma"
    let save name (set: JsonObject) =
        let bytes = bytesOf set
        File.WriteAllBytes(Path.Combine(fixtureDir, name), bytes)
        bytes

    let verifyForma (set: JsonObject) = ReleaseAttestation.verify trust (entryOf "forma" set |> toElement)
    let selects (set: JsonObject) (id, v) = ReleaseAttestation.attestedSelections trust (bytesOf set) |> Set.contains (id, v)

    let signedBytes = save "signed.json" signed
    let unsignedBytes = save "unsigned.json" unsigned

    let caseVerify id description expected (set: JsonObject) (predicate: AttestationOutcome -> bool) =
        save $"{id}.json" set |> ignore
        let outcome = verifyForma set
        { Id = id; Description = description; Expected = expected; Observed = outcomeText outcome; Pass = predicate outcome }

    let qualifiedNow = Registry.qualifiedVersions "forma" |> Option.defaultValue Set.empty

    let t0 =
        { Id = "T0"
          Description = "embedded (compiled) trust file pins the TEST-ONLY key"
          Expected = $"keys = [{keyId}]"
          Observed = trust |> List.map _.KeyId |> String.concat ","
          Pass = trust |> List.map _.KeyId = [ keyId ] }

    let a0 =
        { Id = "A0"
          Description = $"forma {version} is absent from this build's built-in catalog (qualifiedVersions)"
          Expected = "absent"
          Observed = qualifiedNow |> Seq.sort |> String.concat ","
          Pass = not (qualifiedNow.Contains version) }

    let a1 =
        { Id = "A1"
          Description = $"signed entry verifies and attestedSelections contains (forma, {version}); unsigned set does not"
          Expected = "Attested + selected; unsigned not selected"
          Observed =
            (let sel = selects signed ("forma", version)
             let unsel = selects unsigned ("forma", version)
             $"verify={outcomeText (verifyForma signed)}; selected={sel}; unsignedSelected={unsel}")
          Pass = isAttested (verifyForma signed) && selects signed ("forma", version) && not (selects unsigned ("forma", version)) }

    let signedRepo = writeRepo repoRoot "signed" version signedBytes (sha256Hex signedBytes)
    let unsignedRepo = writeRepo repoRoot "unsigned" version unsignedBytes (sha256Hex unsignedBytes)
    let formaErrors errors = errors |> List.filter (fun (e: string) -> e.Contains "'forma'")
    let a2Signed = validateIn signedRepo
    let a2Unsigned = validateIn unsignedRepo

    let a2 =
        { Id = "A2"
          Description = "Compatibility.validateIn (used by doctor) accepts forma via the signed recorded authority; refuses with the unsigned one"
          Expected = "signed: no forma error; unsigned: forma not qualified"
          Observed = $"""signed=[{String.concat " | " a2Signed}]; unsigned=[{String.concat " | " a2Unsigned}]"""
          Pass = (formaErrors a2Signed).IsEmpty && not (formaErrors a2Unsigned).IsEmpty }

    // Tampered recorded authority: one byte of an unsigned field changed after
    // the digest was recorded -> the authority is ignored entirely.
    let tamperedAuthority =
        signed
        |> mapEntry "forma" (fun e ->
            let artifact = (e["artifacts"] |> nonNull).AsArray()[0] |> nonNull
            artifact["sha256"] <- JsonValue.Create(flipHexChar (str "sha256" (artifact :?> JsonObject))))
    let tamperedRepo = writeRepo repoRoot "tampered-authority" version (bytesOf tamperedAuthority) (sha256Hex signedBytes)
    let a2t = validateIn tamperedRepo

    let s3 =
        { Id = "S3"
          Description = "recorded authority file altered by one byte after its digest was recorded (signature still valid)"
          Expected = "authority ignored -> forma not qualified"
          Observed = String.concat " | " a2t
          Pass = not (formaErrors a2t).IsEmpty }

    let a3 =
        match cliDll with
        | None -> { Id = "A3"; Description = "conditor doctor --json (CLI)"; Expected = "run"; Observed = "NOT RUN (no --cli)"; Pass = false }
        | Some dll ->
            let codeS, outS, _ = runCli dll signedRepo
            let codeU, outU, _ = runCli dll unsignedRepo
            File.WriteAllText(Path.Combine(outDir, "A3-doctor-signed.json"), outS)
            File.WriteAllText(Path.Combine(outDir, "A3-doctor-unsigned.json"), outU)

            match compatFindings outS, compatFindings outU with
            | Ok s, Ok u ->
                { Id = "A3"
                  Description = "CLI `conditor doctor --json`: COND-DOC-COMPAT findings about forma"
                  Expected = "signed: none; unsigned: >= 1"
                  Observed = $"""signed(exit {codeS})={s.Length} {String.concat " " s}; unsigned(exit {codeU})={u.Length} {String.concat " " u}"""
                  Pass = s.IsEmpty && not u.IsEmpty }
            | e1, e2 ->
                { Id = "A3"; Description = "CLI doctor"; Expected = "JSON output"; Observed = $"parse failure {e1} {e2}; stdout(signed)={outS}"; Pass = false }

    let signedAttestation = (entryOf "forma" signed)["releaseAttestation"] |> nonNull :?> JsonObject
    let sigText = str "signature" signedAttestation
    let digest = manifestSha (entryOf "forma" signed)

    let negatives =
        [ caseVerify "N1" "one hex character of the signed releaseManifest.sha256 changed" "NotAttested: does not verify"
              (signed |> setManifestSha "forma" (flipHexChar digest)) (notAttestedWith "does not verify")
          caseVerify "N2" "one byte of the signature changed (low bit flipped)" "NotAttested: does not verify"
              (signed |> mapAttestation "forma" (fun a -> a["signature"] <- JsonValue.Create(flipSignatureByte sigText))) (notAttestedWith "does not verify")
          caseVerify "N3" "signed by an untrusted throwaway key under the pinned keyId" "NotAttested: does not verify"
              (unsigned |> attest untrusted keyId contract "forma") (notAttestedWith "does not verify")
          caseVerify "N4" "signed by an untrusted throwaway key under an unknown keyId" "NotAttested: not pinned"
              (unsigned |> attest untrusted "test-only-untrusted-key" contract "forma") (notAttestedWith "is not pinned")
          caseVerify "N6" "replay: a valid attestation for forma 0.12.0 (its statement) copied onto this entry" "NotAttested: does not verify"
              (signed |> mapAttestation "forma" (fun a -> a["signature"] <- JsonValue.Create(signStatement trusted "forma" "0.12.0" (sha256Hex (Encoding.UTF8.GetBytes "forma 0.12.0 manifest stand-in")) contract)))
              (notAttestedWith "does not verify")
          caseVerify "N9" "attestation claims no web-package contract (claims echelon.other/v1)" "Attested but not selected"
              (unsigned |> attest trusted keyId [ "echelon.other/v1" ] "forma") isAttested
          caseVerify "S1" "one hex character of an UNSIGNED field (artifacts[0].sha256) changed" "H2b: still Attested (not covered by the statement)"
              tamperedAuthority isAttested
          caseVerify "S2" "attestation carries expiresAt in the past (field not in the format)" "H2c: ignored, still Attested"
              (signed |> mapAttestation "forma" (fun a -> a["expiresAt"] <- JsonValue.Create "2000-01-01T00:00:00Z")) isAttested ]

    // N9 must also not be selected.
    let n9Set = unsigned |> attest trusted keyId [ "echelon.other/v1" ] "forma"
    let negatives =
        negatives
        |> List.map (fun o ->
            if o.Id = "N9" then
                let sel = selects n9Set ("forma", version)
                { o with Observed = $"{o.Observed}; selected={sel}"; Pass = o.Pass && not sel }
            else o)

    // N5: revoked key, through the production trust parser.
    let revokedTrustJson =
        let pub = trust |> List.head |> fun k -> Convert.ToBase64String k.PublicKey
        $$"""{"schema":"conditor.registry-release-keys/v1","keys":[{"keyId":"{{keyId}}","algorithm":"ecdsa-p256-sha256","publicKey":"{{pub}}","revokedAt":"2026-11-01T00:00:00Z"}]}"""

    let n5 =
        match ReleaseAttestation.parseTrust revokedTrustJson with
        | Error e -> { Id = "N5"; Description = "revoked key"; Expected = "was revoked"; Observed = String.concat ";" e; Pass = false }
        | Ok revoked ->
            let o = ReleaseAttestation.verify revoked (entryOf "forma" signed |> toElement)
            let sel = ReleaseAttestation.attestedSelections revoked signedBytes |> Set.contains ("forma", version)
            { Id = "N5"; Description = "same signed set, trust list marks the key revokedAt (parsed by ReleaseAttestation.parseTrust)"; Expected = "NotAttested: was revoked; not selected"; Observed = $"{outcomeText o}; selected={sel}"; Pass = notAttestedWith "was revoked" o && not sel }

    // N7: out-of-range forma 1.0.0, properly signed.
    let n7Set = unsigned |> setVersion "forma" "1.0.0" |> attest trusted keyId contract "forma"
    save "N7.json" n7Set |> ignore

    let n7 =
        { Id = "N7"
          Description = "forma 1.0.0 (outside qualifiedRange >=0.2.0 <1.0.0), validly signed"
          Expected = "Attested but not selected"
          Observed = (let sel = selects n7Set ("forma", "1.0.0") in $"verify={outcomeText (verifyForma n7Set)}; selected={sel}")
          Pass = isAttested (verifyForma n7Set) && not (selects n7Set ("forma", "1.0.0")) }

    // N8: a host tool (praxis) at a version absent from the catalog, validly signed.
    let n8Set = unsigned |> setVersion "praxis" "3.26.0" |> attest trusted keyId contract "praxis"
    save "N8.json" n8Set |> ignore
    let praxisOutcome = ReleaseAttestation.verify trust (entryOf "praxis" n8Set |> toElement)

    let n8 =
        { Id = "N8"
          Description = "praxis 3.26.0 (role host-tool, not in catalog), validly signed with the web contract"
          Expected = "Attested but not selected (lifecycle tools keep exact qualification, CON-343)"
          Observed =
            (let sel = selects n8Set ("praxis", "3.26.0")
             let range = Registry.attestedQualification "praxis"
             $"verify={outcomeText praxisOutcome}; selected={sel}; praxisRange={range}")
          Pass = isAttested praxisOutcome && not (selects n8Set ("praxis", "3.26.0")) }

    // Which entries of the real 1.37.0 set could ever be range-qualified by this build?
    let eligibility =
        components real
        |> List.map (fun e ->
            let id = str "systemId" e
            let role = str "role" e
            let range = Registry.attestedQualification id |> Option.map fst
            {| systemId = id; version = str "version" e; role = role; qualifiedRange = (range |> Option.defaultValue "")
               rangeEligible = role = "project-binding" && range.IsSome |})

    let results = [ t0; a0; a1; a2; a3 ] @ negatives @ [ n5; n7; n8; s3 ]

    results
    |> List.iter (fun r -> Console.WriteLine $"""{(if r.Pass then "PASS" else "FAIL")} {r.Id} {r.Description} :: {r.Observed}""")

    let report =
        {| experiment = "SPR-C2-01"
           mode = (if synthetic then $"synthetic forma {version} on stock catalog" else $"real forma {version}, catalog rolled back")
           setSource = setPath
           setSourceSha256 = sha256Hex (File.ReadAllBytes setPath)
           keyId = keyId
           results = results
           eligibility = eligibility |}

    File.WriteAllText(Path.Combine(outDir, "results.json"), JsonSerializer.Serialize(report, JsonSerializerOptions(WriteIndented = true)))
    (try Directory.Delete(repoRoot, true) with _ -> ())
    let failed = results |> List.filter (fun r -> not r.Pass) |> List.length
    Console.WriteLine $"{results.Length - failed} passed, {failed} failed"
    if failed = 0 then 0 else 1
