# ADR-S01: Qualify components from signed Registry sets instead of lockstep Conditor releases

- **Status:** Proposed — EXPERIMENTAL evidence
- **Date:** 2026-11-08
- **Drafted by:** Track H (H-001), from Track C's CR-01. This is a candidate for owner decision. It is not a decision.
- **Paths:** relative to `research/2026-11-08-compute-sprint/tracks/`.

## Context

- Qualification is defined in two places. Conditor embeds its own component catalog: 11 descriptors in `components/*.component.json`, each with `qualifiedVersions` and `defaultVersion`. The echelon-registry catalog covers 17 systems. REG-RU-007 requires a released Conditor to qualify each approved set (C-F-03, VERIFIED).
- **Effect:** 13 Conditor releases (v0.10.9–v0.10.21) went out alongside 12 approved sets (1.26.0–1.37.0) in 14 days. Several were pure "RELEASE TRIGGER" commits (C-F-03). echelon-current received 12 owner-approved sets in 13 days (C-F-18, VERIFIED). So one component release currently costs four things: a component release, a Conditor release, a Registry set and an owner approval.
- **The two catalogs disagree.** forma-workflow is a Conditor built-in with no Registry entry (C-F-09). Dokimos, arca, fides and others are in the Registry with no Conditor descriptor (C-F-03).
  - The forma-workflow gap matches a recurring rehearsal defect: forma-workflow sat outside the approved set in R4, R5, R8 and R10 (B-F-13, SUPPORTED; cross-track theme X-07).
- **The escape hatch exists but is switched off.** Conditor already implements attested range qualification (`Registry.attestedQualification`), but `trust/registry-release-keys.json` lists no keys (C-F-04, VERIFIED).
- **Adjacent problem, not solved here:** the wider ecosystem lags the approved set by up to 35 set versions (C-F-01, VERIFIED). That is CR-02 and needs its own decision.

## Decision (proposed)

1. Publish a Registry release-attestation key and add it to `conditor/trust/registry-release-keys.json`. Let project bindings use attested range qualification against signed Registry sets.
2. Make the Registry set the single source of qualified versions. Conditor descriptors keep only install mechanics: package and commands.
3. Add the missing catalog entries (forma-workflow in the Registry), or remove forma-workflow from Conditor's built-ins.
4. Separately, update Conditor's stale `defaultVersion` values (C-F-16), or remove them in favour of the bound set.

## Consequences

**Expected, all ESTIMATES:**
- No more Conditor release purely to qualify a set.
- Fewer owner approvals per component bump.
- A single catalog, which removes the forma-workflow class of rehearsal defects.

**New risks:**
- **Key ceremony and custody.** Track E found that the agent's credential is reportedly admin, and that the agent held the R7 signing key (E-F-07, SUPPORTED). A Registry key reachable by an agent would let it qualify anything. The key must sit outside agent reach, and E-F-09's caveat applies: attestations that bind only the repository are weak.
- **Policy.** The owner must accept range trust for signed sets (C-F-04 limitation).

**Not addressed:** ecosystem pin staleness (C-F-01, C-F-02). That needs CR-02.

## Evidence

| Finding | Class | Independent check |
|---|---|---|
| C-F-03 (dual catalogs, 13 releases in 14 days) | VERIFIED (C) | V2 pending |
| C-F-04 (range qualification built, keys empty) | VERIFIED (C, code reading) | V2 pending; not executed |
| C-F-18 (12 sets in 13 days) | VERIFIED (C) | V2 pending |
| C-F-09 (forma-workflow outside Registry) | VERIFIED (C) | V2 pending |
| B-F-13 (forma-workflow defect in R4, R5, R8, R10) | SUPPORTED (B) | none |
| E-F-07, E-F-09 (key custody and attestation scope risks) | SUPPORTED (E) | V2 pending |

Files: `C-architecture/findings.json`, `C-architecture/complexity-reductions.json#CR-01`, `B-forensics/findings.json#B-F-13`, `E-security/findings.json`. Theme: `H-synthesis/synthesis/cross-track-matrix.json#X-07`.

## Open questions

1. Has anyone run `attestedQualification` end to end with a trusted key? C read the code; nobody executed it (NOT TESTED).
2. Who holds the Registry key, and how is it isolated from agent sessions (E-F-07)?
3. Does the owner accept range qualification, for example "any signed set ≥ X"? Or must every set remain an explicit approval, in which case the approval-churn saving shrinks?
4. Is the owner's time per approval material? It was not measured (C-F-18 limitation).
5. Would the forma-workflow defect have been prevented in practice? Only a replay of R8/R10 bootstrap with a single catalog would show that.
