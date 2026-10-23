# Release gates

This document draws together the mandatory verification and release conditions for program work and states when
evidence may be reused. It builds on existing gates and does not replace them:

- Praxis completion refusals (`PRX.COMPLETION.*`);
- Dokimos policy gates and completion verification;
- the Registry's REG-RU-007 Conditor qualification;
- the rehearsal acceptance ledger (G0–G10, Indy-init `docs/REHEARSAL-ACCEPTANCE-LEDGER.md`).

**Statuses:** `NOT_RUN`, `PASS`, `FAIL`, `BLOCKED`. Missing evidence is never PASS.

## 1. Gate ladder

| Level | Applies to | Mandatory evidence | Reuse allowed? |
|---|---|---|---|
| L0 Checkpoint commit | Any intermediate commit | Builds or compiles where cheap; labelled UNVERIFIED unless more ran (R3-DV-003). Never called passing | n/a |
| L1 Increment complete | A work item in an owning repository | The repository's CI green on the exact commit; the increment's acceptance criteria evidenced; Praxis completion with evidence (`--evidence TYPE=PATH`, or verified completion where enabled) | Yes, per §4, except the never-deferred set |
| L2 Release | A component release | Full CI on the release commit, release workflow success, attestation, the Registry release manifest | No: full suite on the release commit |
| L3 Approved set | A Registry profile version | Every component's L2; Conditor qualification (REG-RU-007); the compatibility run; an explicit approval record (A6a) | Component L2 evidence is reused only if the release digests are unchanged |
| L4 Accepted application release | Rehearsal or product | G0–G9 PASS for one source identity; deployed SHA equal to the verified SHA; deployed acceptance PASS; no open critical defect class | No |

## 2. Never deferred

These run at the moment the risk appears, at every level. They are never satisfied by reused evidence, and never
traded for speed (R3-DV-005, mission §2):

1. **Credential and secret exposure.** Run a secret scan on every commit that adds files. Any finding stops the slice.
2. **Security failures:** authentication, authorization and boundary bypass.
3. **Authorization-boundary violations,** including persistence writes outside the authorized role. In wave B this is
   compile-enforced where feasible, and tested at runtime where not.
4. **Data integrity:** destructive or irreversible operations, corruption, loss, mutation of frozen fixtures.
5. **Producer/consumer contract mismatches** that block parallel work.
6. **Release acceptance** (L2–L4).

## 3. Real-provider ordering (A4)

- A slice that writes to a persistence or authorization boundary runs its **live-provider** test for that boundary at
  the slice's first checkpoint, not only at final integration. Mocks stay for speed; they never replace this test.
- Final integration still runs the full live-provider suite (G6, "BLOCKED if live provider untested").
- **Rationale:** in R002 the live GitHub provider found DC-004 and DC-005, which mocks could not reach.
- **Rehearsal 3:** this ordering applies only if the owner amends the approved plan (OD-4). Its G6 already requires
  live-provider evidence at acceptance.

## 4. Evidence reuse

A prior result may stand in for re-running a check only when **all** of the following hold:

| Condition | How it is checked | Invalidated by |
|---|---|---|
| Same subject | The `validity.sourceDigest` covers exactly the declared closure: the source files, plus generated files and fixtures the check reads | Any byte change in the closure |
| Same inputs | Handoff, trace and configuration digests | Any change |
| Same tools | Tool name and version, SDK version, and the dependency digest (lock files) | Upgrade, downgrade, or a different restore result |
| Same environment assumptions | The runner image and OS family, where the check is sensitive to them (declared per check) | A runner image change. EP-00 and EP-01 show this is real: git 2.55 and ubuntu-26.04 broke checks without a source change |
| Valid producer | A Dokimos or host receipt, not implementer-written; signed or attested where the repository requires it (REL-GATE-003/004) | An untrusted or unsigned receipt where attestation is required |
| Not a mandatory gate | §2 | Always re-run |
| Not a release level | L2–L4 | Always re-run |

**Mechanics.**
- Praxis already binds evidence to the exact revision and refuses stale evidence (`EVIDENCE_STALE`).
- A2a and A2b extend that binding to closure-scoped validity digests (CONTRACTS.md C3, C4).
- Until A2b is released, reuse across commits is **not** permitted: the existing exact-revision rule applies.

## 5. Completion gate (A3)

- One operation: `praxis work finish`, or `complete-verified` in released versions.
- It verifies evidence and either completes or refuses with structured `PRX.COMPLETION.*` reasons.
- **Repeating it is idempotent.** A completed item replays; a refused item refuses again with the same codes and no
  state change.
- **Missing evidence is always a refusal.**
- Where verified completion is not yet enabled, L1 requires the evidence paths to be listed in `work complete`. The
  coordinator does not report a capability complete without them.

## 6. Rehearsal 3 protection

Rehearsal 3 is a time-bounded application-delivery exercise. Its approved plan governs it
(`Indy-init/docs/REHEARSAL-003-DEFERRED-VERIFICATION-EXPERIMENT.md`). This program adds only these protections:

1. **No unverified engineering-system change enters its baseline.** Its stack is the newest **approved** compatible
   release set at kickoff (DEP-CURRENT-002/006). Today that is Registry echelon-current **1.25.0**, unless the owner
   approves a newer set first (OD-2).
   - Newer releases are not approved. Praxis 3.19.0 is newer and carries completion-gate fixes, but it is *not*
     approved.
   - None of the program's experimental work is in that set: the wave B slices, the A1 shadow, or the contracts.
2. **The 420-minute ceiling is a ceiling, not a target** (R3-DV-002). Phases exit on events (R3-DV-013), and the run
   stops on success (R3-DV-015).
3. **Commit frequently** (R3-DV-003). Noncritical routine verification may be deferred (R3-DV-004). The never-deferred
   set (§2) is not.
4. **Success requires every mandatory gate** G0–G9 PASS on one identity, with exact-SHA deployed acceptance and
   defect-class closure evidence (G7). R002 was not accepted precisely because G7 lacked closure evidence. A missing
   G7 is FAIL or BLOCKED, never PASS.
5. **Program experiments only observe Rehearsal 3** (EXP-2 phase 3); they do not modify it.
6. **Preflight BLOCKED items must clear before kickoff:** the Forma 0.9 compatibility gate, Folio/WASM startup, and
   the F# interface freeze (`NEXT-REHEARSAL-PREFLIGHT-STATUS.md`).

## 7. Program-specific gates for experimental work

| Gate | Condition |
|---|---|
| X1 Off default path | Not referenced by any default build, CI gate, release workflow or Registry profile |
| X2 Honest status | README states EXPERIMENTAL, and LIMITATIONS.md lists what is not shown |
| X3 Deterministic | Byte-identical output on rerun, tested |
| X4 Promotion | Only through EXPERIMENTS.md §6 |
