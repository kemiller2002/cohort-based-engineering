# ADR-S01: Reduce lockstep Conditor releases: a host-tool range policy first, signed Registry attestations second

- **Status:** Proposed — EXPERIMENTAL evidence.
  - **Revised 2026-11-08 ~15:10** after the C2 prototype contradicted the original framing, "signed Registry sets end lockstep releases" (Track C CR-01). See DECISION-LOG D-031.
- **Date:** 2026-11-08
- **Drafted by:** Track H (H-001), from Track C's CR-01 and Track C2's prototype. This is a candidate for owner decision. It is not a decision.
- **Paths:** relative to `research/2026-11-08-compute-sprint/tracks/`. C2 paths resolve in its worktree until merged.

## Context

**Two catalogs force releases in lockstep.**
- Conditor embeds its own component catalog. echelon-registry has another. REG-RU-007 requires a released Conditor to qualify each approved set (C-F-03, VERIFIED).
- Result: 13 Conditor releases went out alongside 12 approved sets in 14 days.
- echelon-current received 12 owner-approved sets in 13 days (C-F-18, VERIFIED).
- The catalogs disagree on forma-workflow (C-F-09). That matches a defect that recurred in R4, R5, R8 and R10 (B-F-13). Matrix theme X-07.

**Conditor's attested range qualification is live code, dormant only because no key is trusted.**
- The trust list is `keys: []` (C-F-04, VERIFIED by V2).
- C2 populated it with a throwaway key in scratch. Range qualification then worked end to end through the CLI (C2-F-02, C2-F-03, VERIFIED).
- Bad signatures, untrusted keys, revoked keys and replayed statements are all refused (C2-F-04).
- Only one existing test fails: the deliberate "inert" guard (C2-F-06).

**What signing would not do** (matrix X-27):
- **It would not end the lockstep releases.** Only 2 of the 13 recent Conditor releases were avoidable, at most 3 (C2-F-07, CONTRADICTED).
  - Range qualification applies only to project-binding web packages: forma, limen, folio and forma-workflow. That is 3 of the 17 entries in 1.37.0.
  - Seven releases were driven by exact pins of the Praxis and Ordo host tools. Descriptors may not declare a range for those (CON-343).
- **It needs new infrastructure.** The Registry has no signing keys, no signing workflow or protected environment, no resolver step and no REG-SIG checks. REG-RU-007 refuses range-only versions (C2-F-08). WI-0042 is waiting on a key-custody proposal.
- **It does not give set integrity.** The attestation covers the contract claim, not artifact digests or URLs (C2-F-05). It also has no expiry or freshness control (C2-F-04).

**Adjacent problem, not addressed here:** ecosystem pin staleness (C-F-01, VERIFIED by V2, 8 not 9 repositories on sets 1.3.0–1.24.0). That is CR-02.

## Decision (proposed)

1. **Owner decision first: a host-tool range policy (CON-343).** Decide whether the Praxis and Ordo host tools may be qualified by range or by signed attestation. Seven of the 13 releases trace to these exact pins. This is the lever with the largest measured effect (C2-F-07).
2. **Then, if the owner accepts range trust, build the Registry signing side** (C2-F-08):
   - key custody outside agent reach;
   - a protected signing workflow;
   - a resolver step that copies `releaseAttestation`;
   - REG-SIG conformance checks;
   - an REG-RU-007 change to accept range-qualified versions.
3. **Fix the formats before relying on them.**
   - Add expiry or freshness to the attestation statement (C2-F-04).
   - Either sign the set digest, or state plainly that attestation gives contract authenticity only (C2-F-05).
4. **Independently of 1–3, close the catalog gap.** Register forma-workflow in the Registry, or remove it from Conditor's built-ins (C-F-09). Update or remove Conditor's stale `defaultVersion` values (C-F-16).

## Consequences

**Expected:**
- Step 1 could remove most host-tool-driven Conditor releases. That is an ESTIMATE: up to 7 of 13 in the observed window, if the policy also covers future host-tool bumps.
- Step 2 alone removes about 2–3 of 13.
- Step 4 removes the forma-workflow class of rehearsal defect.

**Costs and risks:**
- Key ceremony and custody. The agent credential is reportedly admin (E-F-07; V2 verified that there is no branch protection or ruleset). A Registry key reachable by an agent would let it qualify anything.
- Key rotation and revocation each still require a Conditor release (C2-F-08).
- Owner approval churn (C-F-18) falls only if the owner accepts range trust. Otherwise every set remains an explicit approval.

## Evidence

| Finding | Class | Independent check |
|---|---|---|
| C-F-03, C-F-18 | VERIFIED (C) | not independently verified |
| C-F-04 | VERIFIED (C) | V2 VERIFIED |
| C2-F-02, C2-F-03, C2-F-04, C2-F-06 | VERIFIED (C2, scratch prototype) | V3 pending |
| C2-F-05, C2-F-08 | VERIFIED (C2) | V3 pending |
| C2-F-07 | CONTRADICTED (CR-01's claim) | V3 pending |
| C-F-09; B-F-13 | VERIFIED; SUPPORTED | — |
| E-F-07 | SUPPORTED with VERIFIED parts | V2 VERIFIED (protection parts) |

Files: `C-architecture/findings.json`, `C-architecture/complexity-reductions.json#CR-01`, `C2-signed-registry/findings.json`, `V2-verification/verdicts.json#C-F-04`. Matrix themes X-07, X-26, X-27.

## Open questions

1. Will the owner accept range or attested qualification for host tools (CON-343)? This decides most of the benefit.
2. Who holds the Registry key, and how is it isolated from agent sessions?
3. Should the attestation cover the whole set entry, including artifact digests, or should the set digest be signed separately (C2-F-05)?
4. Is owner time per approval material? Not measured (C-F-18).
5. Would a single catalog have prevented the forma-workflow rehearsal defects in practice? Not replayed.
