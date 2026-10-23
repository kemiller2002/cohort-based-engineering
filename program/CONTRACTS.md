# Proposed inter-component contracts

**Status:** PROPOSED. Draft schemas are in [contracts/schemas/](contracts/schemas/); the test fixture is in
[contracts/fixtures/invoice-slice/](contracts/fixtures/invoice-slice/). On promotion, each schema moves to its owning
repository's `schemas/` directory. This file then keeps only the cross-references, so there is never a second
authority.

All contracts are **experimental 0.x**. They are additive to existing released formats: none replaces
`ros.handoff-authority` v1, `ordo.construction-plan/1`, `dokimos.results` 1.0.0 or
`dokimos.completion-verification/1`.

## Versioning and compatibility rules (all contracts)

| Rule | Statement |
|---|---|
| V1 | Each document carries `schema` (a stable name) and `schemaVersion`. Readers decode strictly: unknown fields are refused in 0.x, so drift is detected rather than ignored |
| V2 | 0.x versions may change incompatibly between minors; consumers pin an exact version. 1.0 freezes the wire format; afterwards only additive optional fields arrive in minors, and removals need a major |
| V3 | A producer emits exactly one version per document; a consumer may accept several and must say which it read |
| V4 | Output is deterministic: stable ordering, LF line endings, no wall-clock timestamps (times are fixed inputs), so the same inputs give byte-identical output |
| V5 | Every reference to another artifact is `sha256:` plus a revision, so evidence can be invalidated mechanically (RELEASE-GATES.md §4) |
| V6 | A newer contract version never selects itself. A component adopts it only through a release recorded in the Registry and installed by Conditor (A6) |

## C1. `echelon.authority-handoff/0.1`: Praxis → Ordo, Dokimos

- **Owner:** Praxis. **Schema:** `contracts/schemas/echelon-authority-handoff-0.1.schema.json`.
- **Satisfies:** VC-003 R1–R5, VAC-002-01 R1, the B1 mission requirement, and the "never conflate" table in PROGRAM.md §2.

| Collection | Holds | Rule |
|---|---|---|
| `requirements[]` | Accepted or superseded requirements, each with source path, locator, revision and sha256 | `supersededBy` is required when status is superseded |
| `decisions[]` | Decision records | `accepted` **requires** `authorizedBy` (a human) and `authorizedAt`. An agent's proposal can only be `proposed` |
| `policyQuestions[]` | Unresolved policy | `status` is always `unresolved`. `permittedOutcome` is `refuse-and-record` or `defer-scope`, and that outcome is valid input: admission never rejects it (VAC-002-P3-02-R1, R-ADM-1) |
| `observations[]` | Behaviour seen in existing code, tests or data | `authority` is always `unverified`. An observation is never authority (VAC-002-P3-03, VC-003 R2) |
| `invariants[]` | Technical invariants derived from requirements and accepted decisions | Listing one is not verifying it. Verification is Dokimos evidence (C3) |
| `authorityContract` | sha256 of the frozen four-sentence contract the brief carried | Lets telemetry relate outcomes to the contract version (R-PRAX-1) |

**Compatibility.** Additive companion to `ros.handoff-authority` v1. Its string `unknowns` map to `policyQuestions` with
`permittedOutcome: refuse-and-record` and an owner of `unassigned`, and that mapping is lossy and flagged. Praxis
continues to emit v1 unchanged.

**Admission (Ordo side) refuses:**
- an accepted decision without a human authorizer;
- an observation claiming authority;
- citing a superseded record as current;
- supersession cycles.

**Admission never refuses:**
- a recorded question;
- a refusal that cites a question;
- presentation choices (R-ADM-1..3).

## C2. `echelon.construction-trace/0.1`: Ordo → Dokimos, Praxis

- **Owner:** Ordo. **Schema:** `contracts/schemas/echelon-construction-trace-0.1.schema.json`.
- **Satisfies:** VC-002 R1, R6; VAC-002-P3-03-R2.
- **Each construct** maps every rule-bearing symbol (state, command, transition, refusal, validated constructor, value
  type, constant, port, capability) to its authority, with one of three `disposition` values: `authorized`,
  `deferred-pending-question`, or `technical`.
- **`excluded[]`** lists observations deliberately not constructed, and who they were routed to. Exclusion leaves the
  legacy code untouched.
- **Source marker:** handwritten rule-bearing symbols carry `[<Authority("ID", ...)>]` on the line above them, so the
  trace can be checked against source without trusting either alone.
- **`outputs[]`** pins generated files by sha256.

## C3. `echelon.provenance-audit/0.1`: Dokimos → Praxis

- **Owner:** Dokimos. **Schema:** `contracts/schemas/echelon-provenance-audit-0.1.schema.json`.
- **Satisfies:** VAC-002-P3-03-R1, VC-004 R1–R5, A2.

**Findings:**
- `certainty: proven` is a mechanical fact: a counterexample, or a citation of a missing or superseded record.
- `certainty: uncertain-authority` means no record supports the rule; whether the rule is wanted is the owner's call.
- **Blocking:** only `proven` findings from a formally specified, validated check may block. Uncertain authority never
  blocks; it becomes an owner question. While precision and recall are unmeasured, proven *provenance* findings
  default to non-blocking, and only validated invariant violations block (VC-004 R4/R5).

**`invariants[]`:** verdicts are `holds-within-bound`, `violated` (with a counterexample) or `not-checked`. A bounded
verdict states its bound; it is never reported as a proof.

**`validity`:** the digests of source, handoff, trace, tool name and version, configuration and SDK, plus an optional
dependency digest. A consumer may reuse the result only while every digest matches.

**Mapping into existing Dokimos results:**
- the summary verdict maps to the `dokimos.results` disposition;
- proven blocking findings map to policy failure (exit 4);
- validity maps to the Provenance block.

A future `dokimos.completion-verification` minor can carry the audit's digest as additional evidence; that is a Dokimos
release decision.

## C4. Completion evidence binding: Dokimos → Praxis (existing, extended)

- **Existing:** `praxis work complete --evidence TYPE=PATH`, `work complete-verified` and `work finish` consume
  `dokimos.completion-verification/1` receipts, bound to the exact revision (`PRX.COMPLETION.EVIDENCE_*`).
- **Proposed extension (A2/A3):** the evidence entry may cite a C3 audit, or any result carrying a `validity` block.
  Praxis then reuses it across commits only when every validity digest recomputed at the current HEAD matches.
- **Any mismatch** gives the existing refusal `PRX.COMPLETION.EVIDENCE_STALE`, with the mismatched digest named.
- **Missing evidence** never yields completion; that is unchanged.

## C5. Verification selection map (A1, Praxis-owned, proposed)

- **File:** `praxis.verification-map/0.1` in each repository. It lists path globs and interface identifiers, each with
  the checks it requires and a risk class. It also lists a `mandatory` set that is never deselected: security, data
  integrity, authorization boundary and release acceptance, per RELEASE-GATES.md §2.
- **Rollout:** Praxis computes the selection from changed paths, the resolved dependency closure, risk and prior valid
  evidence (C4). It runs in **shadow** first: it records what it would have selected next to what actually ran, so
  EXP-2 can measure escaped-defect risk before anything is skipped.
- **Ownership:** Dokimos remains the definer of what a check result means. The map only names which checks are
  required.

## C6. Compatibility evidence (A6, Registry and Conditor)

- **Existing:** Registry profiles, snapshots and channels; Conditor lock v4 and authority pinning.
- **Proposed:**
  - **Registry:**
    - Record each echelon-current profile version as an immutable set, with an explicit
      `approval: {by, at, evidence}` field.
    - Record assessed-but-unapproved releases as `assessed: rejected|pending`, rather than leaving them unregistered.
  - **Conditor:** reuse a prior environment receipt only while the resolved-set digest, the per-component descriptor
    digests and the host fingerprint match (completing CON-INDY-050..054).
  - **Selection:** never move to a newer release unless an approved set names it.

## Unresolved decisions (owner)

These are tracked with options in [EXECUTION-STATE.md](EXECUTION-STATE.md#open-decisions).

| ID | Question | Why it matters |
|---|---|---|
| OD-3 | Accept VAC-002-P3-02-R1 ("refuse the uncovered case and record the question is an authorized outcome") as policy? | C1 and the B2 slice assume it. Today it is a proposed requirement, not an accepted one |
| OD-7 | Where should the authority handoff schema live at 1.0: Praxis `schemas/`, or a shared Echelon contracts package? | Avoids a second authority. The proposal is Praxis `schemas/`, beside `ros-handoff-authority` |
| OD-8 | Should the `[<Authority(...)>]` source marker become part of Ordo's emitter output (generated code), or stay limited to handwritten code? | Decides whether Dokimos audits markers or only the trace for generated code |
