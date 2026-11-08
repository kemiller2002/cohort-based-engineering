/// SPR-C2-01 fixture construction (EXPERIMENTAL). Pure transformations of a
/// resolved release set: every function takes a JSON tree and returns a new one.
module C2Harness.Fixtures

open System
open System.Security.Cryptography
open System.Text
open System.Text.Json
open System.Text.Json.Nodes
open Conditor.Core

let WebContract = ReleaseAttestation.WebPackageBindingContract

let sha256Hex (bytes: byte array) =
    SHA256.HashData bytes |> Convert.ToHexString |> fun s -> s.ToLowerInvariant()

let parse (text: string) = JsonNode.Parse text |> nonNull :?> JsonObject

let clone (node: JsonObject) = node.DeepClone() :?> JsonObject

let serialize (node: JsonObject) =
    node.ToJsonString(JsonSerializerOptions(WriteIndented = true)) + "\n"

/// The string value of a property, or "" when absent.
let str (name: string) (o: JsonObject) =
    match o[name] with
    | null -> ""
    | n -> n.ToString()

/// A JsonElement view of a node (what Conditor's verifier takes).
let toElement (node: JsonObject) =
    use doc = JsonDocument.Parse(node.ToJsonString())
    doc.RootElement.Clone()

let components (set: JsonObject) =
    set["components"] |> nonNull :?> JsonArray |> Seq.map (fun n -> n |> nonNull :?> JsonObject) |> Seq.toList

let entryOf (systemId: string) (set: JsonObject) =
    components set |> List.find (fun e -> str "systemId" e = systemId)

/// Returns a copy of `set` with `f` applied to the entry for `systemId`.
let mapEntry (systemId: string) (f: JsonObject -> unit) (set: JsonObject) =
    let copy = clone set
    entryOf systemId copy |> f
    copy

let manifestSha (entry: JsonObject) = entry["releaseManifest"] |> nonNull :?> JsonObject |> str "sha256"

let loadKey (pemPath: string) =
    let key = ECDsa.Create()
    key.ImportFromPem(IO.File.ReadAllText pemPath)
    key

/// The REG-SIG-002 statement signed in IEEE P1363 form, base64.
let signStatement (key: ECDsa) (systemId: string) (version: string) (manifestDigest: string) (contracts: string list) =
    let statement = ReleaseAttestation.statement systemId version manifestDigest contracts
    key.SignData(Encoding.UTF8.GetBytes statement, HashAlgorithmName.SHA256, DSASignatureFormat.IeeeP1363FixedFieldConcatenation)
    |> Convert.ToBase64String

let attestationNode (keyId: string) (signature: string) (contracts: string list) =
    let node = JsonObject()
    node["schema"] <- JsonValue.Create ReleaseAttestation.StatementSchema
    node["consumerContracts"] <- JsonArray(contracts |> List.map (fun c -> JsonValue.Create c :> JsonNode) |> List.toArray)
    node["keyId"] <- JsonValue.Create keyId
    node["algorithm"] <- JsonValue.Create ReleaseAttestation.Algorithm
    node["signature"] <- JsonValue.Create signature
    node

/// Signs the entry's own (systemId, version, releaseManifest.sha256) and attaches it.
let attest (key: ECDsa) (keyId: string) (contracts: string list) (systemId: string) (set: JsonObject) =
    set
    |> mapEntry systemId (fun e ->
        let signature = signStatement key systemId (str "version" e) (manifestSha e) contracts
        e["releaseAttestation"] <- attestationNode keyId signature contracts)

let setVersion (systemId: string) (version: string) (set: JsonObject) =
    set |> mapEntry systemId (fun e -> e["version"] <- JsonValue.Create version; e["tag"] <- JsonValue.Create $"v{version}")

let setManifestSha (systemId: string) (digest: string) (set: JsonObject) =
    set |> mapEntry systemId (fun e -> (e["releaseManifest"] |> nonNull :?> JsonObject)["sha256"] <- JsonValue.Create digest)

/// Changes exactly one character of a hex string (position 0, '0'<->'1' or to '0').
let flipHexChar (hex: string) =
    let c = if hex[0] = '0' then '1' else '0'
    $"{c}{hex.Substring 1}"

/// Flips the low bit of one byte of a base64 signature.
let flipSignatureByte (signature: string) =
    let bytes = Convert.FromBase64String signature |> Array.copy
    bytes[10] <- bytes[10] ^^^ 1uy
    Convert.ToBase64String bytes

let mapAttestation (systemId: string) (f: JsonObject -> unit) (set: JsonObject) =
    set |> mapEntry systemId (fun e -> e["releaseAttestation"] |> nonNull :?> JsonObject |> f)

let bytesOf (set: JsonObject) = serialize set |> Encoding.UTF8.GetBytes
