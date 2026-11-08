# SPR-C2-01 preregistration: does CR-01 work as claimed, with no new infrastructure?

- Worker: C2-001 (parent RD-000), sprint 2026-11-08, Track C2.
- Registered: 2026-11-08, before any build, key generation or test run.
- Start revisions: conditor `528ef45` (v0.10.21), echelon-registry `5752402`.
- Status: EXPERIMENTAL, local only. Nothing is pushed, released or signed with a real key.

## Claim under test

CR-01 (Track C): "sign Registry sets and enable Conditor's existing range
qualification; that would end the lockstep Conditor releases" (C-F-03, C-F-04).

## Code reading done before registration (informs the cases, not the results)

- The signature is per component entry (per release), not per set:
  `ReleaseAttestation.verify` (src/Conditor.Core/ReleaseAttestation.fs:125-161)
  rebuilds `echelon.release-attestation/v1|systemId|version|releaseManifest.sha256|contracts`
  (:46-47) and checks ECDSA P-256 / SHA-256, IEEE P1363 r||s (:153-156).
- Range qualification applies only to entries with `role = "project-binding"`
  (:176-177) whose embedded descriptor declares `qualifiedRange`
  (Registry.fs:22-26) and whose attestation claims
  `echelon.web-package-binding/v1` (:185). Lifecycle descriptors may not declare
  a range (ComponentDescriptors.fs:595-597, CON-343).

## Hypotheses

- **H1 (positive).** With a throwaway public key in the scratch trust file, an
  unmodified Conditor build qualifies a project-binding version that appears in a
  signed resolved set derived from echelon-current 1.37.0 but is absent from the
  embedded `qualifiedVersions`, through the production trust path
  (`ReleaseAttestation.embedded`), in `attestedSelections`, `Compatibility.validateIn`
  (`conditor doctor`) and `CurrentUpgrade.preview`/`apply` (`conditor upgrade --current`).
- **H2 (negative).** Each of these is refused with a stated reason: one byte
  changed in a signed field, one byte changed in the signature, a signature by an
  untrusted key (same keyId; unknown keyId), a revoked key, an attestation replayed
  from another version, a version outside `qualifiedRange`.
- **H2b (scope, expected to hold by design).** One byte changed in an *unsigned*
  field of the entry (for example an artifact digest) is NOT detected by the
  attestation, because the statement covers only four fields.
- **H2c.** The format has no expiry/freshness field; an "expired" or replayed
  attestation cannot be refused by date. Expected: not supported.
- **H3 (regression).** With the trust file populated, the existing suite passes
  except for checks that assert the shipped trust set is empty. Prediction: exactly
  one failing check, "this build pins no Registry release key yet ..."
  (tests/Conditor.Tests/DeclaredWebBindingTests.fs:900-902).
- **H4 (coverage of the claim).** Range qualification cannot cover host-tool or
  repository-lifecycle components (Praxis, Ordo, ...). Prediction: fewer than half
  of the 13 Conditor releases v0.10.9..v0.10.21 would have been avoidable under
  CR-01, so "ends lockstep releases" is CONTRADICTED as stated.
- **H5 (infrastructure).** The Registry side (signing key custody, signing
  workflow, resolver copying `releaseAttestation`, REG-RU-007 conformance) is not
  implemented, so CR-01 needs new infrastructure beyond a trust-file edit.

## Cases

| Case | Input | Expected |
|---|---|---|
| T0 | scratch build, trust file with 1 TEST-ONLY key | `embedded` has that keyId |
| A1 | real 1.37.0 linux-x64 forma 0.13.0 entry + attestation; scratch catalog with 0.13.0 removed from forma `qualifiedVersions` | `verify` = Attested; `attestedSelections` contains (forma, 0.13.0) |
| A2 | repo manifest declaring forma 0.13.0, recorded authority = signed set | `Compatibility.validateIn` no forma error; unsigned set -> error |
| A3 | `conditor doctor --json` on the A2 repo (CLI binary) | no COND-DOC-COMPAT for forma when signed; present when unsigned |
| A4 | existing upgrade fixture (Forma 0.6.1 -> 0.7.0, 0.7.0 not in catalog) with production `CurrentUpgrade.preview`/`apply` (embedded trust) | no refusal; plan reports `attested:>=0.2.0 <1.0.0:<keyId>`; apply lands 0.7.0 |
| N1 | one hex char of `releaseManifest.sha256` changed | refused: "does not verify" |
| N2 | one byte of the signature changed | refused: "does not verify" |
| N3 | signed by second throwaway key, same keyId | refused: "does not verify" |
| N4 | signed by second throwaway key, unknown keyId | refused: "not pinned" |
| N5 | trust key with `revokedAt` | refused: "was revoked" |
| N6 | 0.12.0's valid attestation copied onto the 0.13.0 entry | refused: "does not verify" |
| N7 | forma 1.0.0 attested (outside range) | not selected |
| N8 | praxis entry (host-tool) attested | not selected |
| S1 | one byte changed in an artifact sha256 of the signed entry | H2b: still Attested |
| S2 | `expiresAt` in the past added to attestation | H2c: ignored, still Attested |
| R0 | full suite, unmodified clone | baseline PASS/FAIL counts |
| R1 | full suite, trust populated | H3 |
| H4 | catalog diffs v0.10.8..v0.10.21 classified by component distribution | count avoidable releases |

## Success criteria

- H1 VERIFIED iff A1, A2, A3 and A4 all pass through the embedded (production)
  trust path with no code change to `src/`.
- H2 VERIFIED iff N1-N8 are all refused/excluded and each gives a reason string.
- H3 VERIFIED iff R1 failures - R0 failures equals exactly the predicted check(s).
- H4/H5 classified from the release history and Registry tree; no build needed.
- Any deviation is reported as CONTRADICTED or INCONCLUSIVE, not re-run until it passes.

## Constraints

- Throwaway keys generated in /home/user/sprint-scratch/C2/keys; private keys never committed.
- One `dotnet` build at a time. No builds after 19:30 America/Indiana/Indianapolis.
- No change to /home/user/ext/*; the scratch copy is a `git clone` of it.
