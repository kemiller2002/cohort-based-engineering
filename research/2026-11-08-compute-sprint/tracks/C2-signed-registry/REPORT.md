# SPR-C2-01: does CR-01 work as claimed, with no new infrastructure? (C2-001)

> Committed by RD-000 from C2-001's final hand-back text (D-010). Worker final commit: `6b5d6c3`. Preregistration `6f564d8` was committed before any build or key generation. EXPERIMENTAL: everything was done in scratch copies with throwaway TEST-ONLY keys. Nothing was pushed, released or signed with a real key.

## Bottom line

| Part of CR-01 | Verdict | Why |
|---|---|---|
| Conditor side | **VERIFIED** | Changing only the trust file turns on Conditor's existing range qualification. In-range project-binding versions missing from the built-in catalog are then accepted through `doctor` and through `upgrade --current` (preview and apply). Every negative case is refused with a clear reason. |
| "Ends the lockstep Conditor releases" | **CONTRADICTED** | Only 2 of the 13 releases from v0.10.9 to v0.10.21 were avoidable. |
| "No new infrastructure" | **CONTRADICTED** | None of the Registry side exists. |
| "Sign Registry sets" | **Mis-stated** | Conditor verifies per-release attestations, not set signatures. |

## Code reading (conditor 528ef45)

1. **What a signed entry must contain.**
   - Each component entry in the resolved set needs `systemId`, `version`, `role:"project-binding"` and `releaseManifest.sha256`.
   - It also needs a `releaseAttestation` object with these fields:

     | Field | Required value |
     |---|---|
     | `schema` | `"echelon.release-attestation/v1"` |
     | `algorithm` | `"ecdsa-p256-sha256"` |
     | `keyId` | present |
     | `signature` | base64 |
     | `consumerContracts` | must include `echelon.web-package-binding/v1` |

   - Code locations in ReleaseAttestation.fs: `verify` at :125-161; `attestedSelections` at :168-192, with the role check at :176-177 and the contract check at :185.
   - No set-level signature exists.
2. **Signature format.**
   - ECDSA P-256 over SHA-256, in IEEE P1363 r||s form, base64-encoded. It is verified by the .NET base library against a DER SubjectPublicKeyInfo key (:153-156).
   - The signed payload is `echelon.release-attestation/v1|systemId|version|manifestSha256|sorted,contracts` (:46-47).
   - Trusted keys come from the embedded resource `trust/registry-release-keys.json` (Conditor.Core.fsproj:62; ReleaseAttestation.fs:108-121). A key may carry `revokedAt`.
3. **Does the built-in catalog still have to list the version?**
   - No. But the catalog must declare a `qualifiedRange` for that component, and the version must not be in `deniedVersions` (Registry.fs:22-26; WebPackageBinding.fs:538-575).
   - Host-tool and lifecycle descriptors cannot declare a range (ComponentDescriptors.fs:595-597, rule CON-343). Praxis, Ordo and other lifecycle tools therefore always need exact versions.
4. **Is the code reachable?** Yes. It is not dead; it only appears dormant because the key list is empty. The embedded trust is read by:
   - `Planner.create` (Program.fs:90 for init, verify and doctor; Planner.fs:594-595);
   - `Compatibility.validateIn` (Doctor.fs:63);
   - `CurrentUpgrade.preview` and `apply` (Program.fs:706 and 734, through CurrentUpgrade.fs:379-384 and 442-444 into WebPackageBinding).

## Prototype

- **Scratch copies** under `/home/user/sprint-scratch/C2/`. `/home/user/ext/*` was not changed.
  - `conditor-base`: unmodified.
  - `conditor-c2`: trust file plus one added test scenario.
  - `conditor-c2-rb`: the same, plus forma 0.13.0 removed from the catalog.
- **Keys.** Two throwaway P-256 keys, generated with openssl in scratch. Only the public keys and fingerprints are committed, labelled TEST-ONLY. The trusted key's SHA-256 is b5447954…f858 and its keyId is `test-only-c2-001-2026-11-08`. No real key was used or sought.
- **Data.** Taken from the real echelon-current 1.37.0 resolved set (`channels/echelon-current/linux-x64.json`, sha256 bba3594a…).

## Results

### (a) Positive: VERIFIED

The F# harness (`harness/C2Harness`) passed 17/17 cases in each of two modes:
- real forma 0.13.0, with 0.13.0 removed from the catalog;
- a synthetic forma 0.14.0 on the stock v0.10.21 catalog.

In both modes:
- the signed entry verifies against the embedded trust;
- `attestedSelections` includes it;
- `Compatibility.validateIn` reports no forma error;
- CLI `conditor doctor --json` reports no COND-DOC-COMPAT finding;
- the same set without a signature is refused ("not qualified by this Conditor compatibility graph").

Doctor exited 12 in both the signed and unsigned runs because of unrelated lifecycle findings, so only the compatibility findings were compared.

Separately, production `CurrentUpgrade.preview` and `apply` qualified Forma 0.7.0, which is not in the catalog, as `attested:>=0.2.0 <1.0.0:test-only-c2-001-2026-11-08`, and applied it with no drift. This used the existing upgrade test fixture, not the 1.37.0 data.

### (b) Negative: VERIFIED

Each case was refused, with a reason:

| Case | Result |
|---|---|
| One hex character changed in the signed manifest digest | "signature does not verify" |
| One signature byte flipped | "signature does not verify" |
| Untrusted key under the pinned keyId | "signature does not verify" (production preview also refused) |
| Untrusted key with an unknown keyId | "is not pinned" |
| Revoked key | "was revoked at …" |
| Replayed signature for a different version | "does not verify" |
| Wrong contract | Verifies, but not qualified |
| Version 1.0.0, out of range | Not qualified |
| Praxis (host tool) with a valid signature | Not qualified |

Gaps found:
- **Expiry is not supported by the format.** A past `expiresAt` is ignored, so attestations never expire. Revocation takes effect only through a new Conditor release.
- **The signature does not cover every field.** It covers only systemId, version, manifest digest and contracts. Changing a byte in an unsigned field, such as an artifact sha256, leaves the attestation valid. Such tampering is caught only by the recorded-set digest check, and that check ignores an authority file altered after its digest was recorded.

### (c) Regression: VERIFIED

Full suite results:

| Run | Configuration | PASS | FAIL |
|---|---|---|---|
| R0 | Baseline | 1552 | 0 |
| R1 | Test key in trust file | 1552 | 1 |
| R1k | R1 plus the added embedded-trust scenario | 1557 | 1 |

The single failure is the deliberate guard "this build pins no Registry release key yet…" (DeclaredWebBindingTests.fs:900-902), as predicted in the preregistration.

## Findings

| ID | Class | Finding |
|---|---|---|
| C2-F-01 | VERIFIED | Signatures are per release, over a 4-field statement, not per set |
| C2-F-02 | VERIFIED | The catalog need not list the version, but needs a `qualifiedRange` |
| C2-F-03 | VERIFIED | The code is reachable from the normal CLI flows |
| C2-F-04 | VERIFIED | Negatives are refused; there is no expiry or freshness control |
| C2-F-05 | VERIFIED | Unsigned fields of the set entry are not covered by the signature |
| C2-F-06 | VERIFIED | Only the "inert" guard test breaks |
| C2-F-07 | CONTRADICTED (of CR-01's claim) | CR-01 does not end lockstep releases |
| C2-F-08 | VERIFIED | The Registry side needs new infrastructure and process |

### C2-F-07 in detail

- Only 3 of the 17 entries in 1.37.0 can be range-qualified: forma, limen and folio.
- Of the 13 releases from v0.10.9 to v0.10.21:
  - **2 avoidable:** v0.10.15 and v0.10.17, both Forma-only;
  - **9 still required:** 7 add Praxis or Ordo versions, v0.10.10 changes folio `releaseArtifacts`, and v0.10.21 adds a new descriptor;
  - **2 changed no catalog.**
- At most 3 of 13 would be avoidable, even counting v0.10.10.
- **Praxis and Ordo drive the lockstep releases.**
- Source: `harness/release_history.py` (9 unittest tests passing).

### C2-F-08 in detail

The Registry currently has none of the following:
- a `trust/release-signing-keys.json`;
- a signing workflow or protected environment;
- a resolver that copies `releaseAttestation` into sets;
- REG-SIG conformance checks.

In addition:
- WI-0042 is marked "proposal-required".
- Its REG-RU-007 gate reads exact versions only, from `conditor compatibility --json`, which carries no range data. Run in a scratch copy of the Registry, it refused a range-only forma 0.14.0 on all 5 platforms.

## Owner decisions and process changes CR-01 still needs

1. **Key custody.** A dedicated P-256 signing key in a protected GitHub environment with required reviewers, or in a KMS/HSM reached through OIDC. It must be out of reach of agents, PR workflows and forks (REG-SIG-001/003; consistent with Track E's E-F-07).
2. **Who signs.** Only a protected Registry workflow on the default branch, after review of the registration PR. The owner must also decide:
   - who reviews each `consumerContracts` claim;
   - whether to backfill attestations for active releases.
3. **Rotation and revocation.** Both require a Conditor release (REG-SIG-006/007). With no expiry, revocation is the only withdrawal mechanism, and it becomes urgent on any compromise.
4. **The Registry's REG-RU-007 gate** must learn to accept versions that are attested and in range. Otherwise the Registry still demands a Conditor release.
5. **Policy.**
   - Accept range trust for project bindings.
   - Decide whether to extend a range mechanism to host tools. That means revisiting CON-343, which is where the real release savings would be.
6. **The "inert" guard test** must be inverted or removed in the release that enables this.

## Limitations

- The synthetic 0.14.0 case uses a stand-in manifest digest.
- The real 0.13.0 case depends on rolling back the catalog.
- The full `apply` ran on the existing test fixture, not on 1.37.0.
- The replay case uses a stand-in digest, because no real attestations exist yet.
- Only the linux-x64 set was used.
- Key custody and rotation were analysed from the spec, not exercised.

## Files

- `protocols/SPR-C2-01.md`
- `patches/`:
  - `01-trust-file-TEST-ONLY-key.diff`
  - `02-scratch-test-embedded-trust-scenario.diff`
  - `03-rollback-catalog-forma-0.13.0.diff`
- `harness/C2Harness/` (F#)
- `harness/release_history.py`, `harness/test_release_history.py`
- `raw/`
- `experiments.json`, `findings.json`, `CHECKPOINT.md`
