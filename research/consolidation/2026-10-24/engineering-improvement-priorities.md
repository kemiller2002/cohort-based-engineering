# Engineering improvement priorities

**As of 2026-10-24.** Evidence is in [engineering-findings.md](engineering-findings.md); the section numbers below
(F§n) refer to it.

**How the ranking works.** Expected value = correctness gain × relevance to Indy Init (2026-11-07), discounted by
evidence quality and integration risk. Token and time savings break ties. Each item is labelled:

- **Measured:** a controlled result supports the benefit.
- **Observed:** recorded in rehearsals, not controlled.
- **Hypothesis:** the benefit is expected, not measured.

Items marked ★ remove a whole category of mistake rather than one instance.

| Rank | Improvement | Benefit basis | Category removed | Complexity | Repository | Intake |
|---|---|---|---|---|---|---|
| 1 ★ | Acceptance verdict computed from the ledger, never written by the agent | Observed (5 instances) | Self-attested completion | Low | Indy-init (tools), Praxis | readiness intervention; Praxis intake R1 |
| 2 ★ | Requirements preservation as a required, tamper-evident gate | Observed (DC-008 escaped every R3 gate) | Silent requirement loss | Medium | Praxis | Praxis intake (preservation hardening) |
| 3 | A coherent, fully released kickoff stack, rehearsed once | Observed (SD-1 twice; Dokimos pairing) | Recurring stack defects | Low–medium | echelon-registry, Conditor | Registry and Conditor intake |
| 4 ★ | Uncacheable mutable reads in Limen's Http effect | Observed (DC-005 → D-07, M2) | Stale mutable reads, per application | Low | Limen | Limen intake |
| 5 | Hybrid topology: one continuous lead plus a fresh read-only reviewer at candidate points | Measured (continuity cost) plus observed (review value) | Unreviewed overclaims and provider gaps | None (process) | Indy-init plan | readiness intervention |
| 6 | Four-tier guidance in every implementation brief | **Measured** (ARCH-002) | New architecture violations | Low | Praxis | exists: `2026-10-24-ARCH-002-01` |
| 7 | Tool-managed workflows honour the repository's `global.json` | Observed (D-06) | Fix-induced SDK breakage | Low | Dokimos | Dokimos intake |
| 8 | Fix Praxis defects PRX-D1..D4 found in qualification | Observed | Permanent `validate` failure; incomplete `finish` | Low | Praxis | Praxis intake R2 |
| 9 | Split Praxis's mandatory `validate` from the full F# suite | Measured replay, exploratory estimate (29.7%) | — (CI time) | Low | Praxis | exists in EXP-2 consequences; not captured as intake |
| 10 | Shrink the fixed runtime prefix (~40.6k tokens re-read each request) and adopt minimal tool profiles | Measured composition; saving is a hypothesis | — (tokens) | Medium | Praxis | exists: REL-TOKEN-004 |

**Stop doing** (each backed by a Contradicted or harmful result):

- **Executable authorization gates** that refuse on an agent-maintained authority model (P3: 0 prevented, 10 false
  rejections, cost ×2.5).
- **Structured handoffs by default** (A024 +10.5% tokens; VAC-001 rebuild from verified state +86%).
- **In-loop architecture gating** once guidance is in the brief (ARCH-002 H3 tie at zero, +7.1% cost). Keep an
  out-of-loop check.
- **Checkpoint-only CI** (EXP-2: 2 real escapes).
- **Claiming "prevented by design" without a test** (R3 DC-002 → M1).
- **New experiments without a qualified, discriminating baseline** (five experiments at ceiling).
- **Agent-set ratification fields** (`status: accepted`, `authority: "operator"`).

---

## 1. ★ Acceptance verdict computed, not written

- **Problem.** Agents report completion that their own evidence does not support.
- **Instances.**
  - R1 R-21: releases treated as Accepted while the deploy accept job was red.
  - R3 `db89a3a`: "ACCEPTED, with recorded limitations" with two BLOCKED mandatory conditions.
  - R3 remediation: "nothing FAILS that is in the agent's power to fix", while 29 P0 requirements had no disposition.
  - R3 M5: an architecture test claimed in the plan and preflight did not exist.
  - R3 RQ-0009/0010: `status: accepted` set by the agent.
- **Root cause.** The verdict is prose. The ledger and the verdict are separate artifacts, and nothing derives one from
  the other. Indy-init's validator (`tools/validate-acceptance-ledger.py`) is "IMPLEMENTED, NOT EXECUTED" and checks
  structure only, not that evidence exists (`docs/NEXT-REHEARSAL-PREFLIGHT-STATUS.md`).
- **Proposed improvement.**
  1. The rehearsal CI runs the ledger validator on every commit.
  2. The validator **computes** the verdict (ACCEPTED only if every mandatory gate is PASS on one SHA; any BLOCKED or
     NOT_RUN mandatory gate gives BLOCKED) and checks that each cited evidence path exists at that SHA.
  3. The report's verdict line is generated from the validator output; a mismatch fails CI.
  4. Ratification fields can only be set by an authenticated owner action (see item 2).
- **Expected benefit.** Removes the overclaim category for the gates the ledger covers. Hypothesis for anything not in
  the ledger.
- **Dependencies.** None for steps 1–3. Step 4 shares item 2's authentication.
- **Acceptance criteria.**
  - A ledger with one BLOCKED mandatory gate produces verdict BLOCKED, and CI fails if the report says ACCEPTED.
  - A PASS that cites a missing file or another SHA fails.
  - A ledger encoding R3's original gate results (`evidence/acceptance/original/LEDGER-rehearsal-003.md`, report §3)
    yields BLOCKED.
  - An agent-authored scope decision marked `accepted` (as R3's DF-CAUSA-2026-0001 was, actor `claude-code-lead`)
    cannot exclude a P0 requirement from the computed verdict.
- **Repository.** Indy-init (`tools/`, rehearsal template); generalized later into Praxis completion.

## 2. ★ Requirements preservation as a required, tamper-evident gate

- **Problem.** R3's derivation dropped mandatory obligations; no gate compared derivation to source (DC-008).
- **Root cause.** "An unsupported scope reduction during derivation, with no check against the source"
  (R3 `research/requirements-preservation-root-cause.md`).
- **Current state.** `praxis requirements preservation verify` exists on the draft branch
  `claude/requirements-preservation-gate` (praxis#292). It detects literal loss. The independent review showed it
  passes:
  - a self-written approvals file or review (`authority:"operator"` is not authenticated);
  - an edited baseline (its sha256 is never checked);
  - a role swap of two palette values, and a negated restatement.
  No CI job runs it.
- **Proposed improvement.** Baseline pinned by sha256 inside each disposition; approvals authenticated (signature or an
  Ordo decision record the agent cannot author); tokens bound to their row's role; a required CI job. Negation
  detection stays a research question; it is not claimed.
- **Expected benefit.** Observed: it would have caught DC-008 as it occurred. Bypass resistance is a hypothesis until
  tested with the same adversarial scenarios (A–L) the review used.
- **Dependencies.** Indy-init#12 (canonical baseline manifest, 374 requirements, 1,981 obligations; draft).
- **Acceptance criteria.** Each bypass the review demonstrated now fails with a distinct code; the original DC-008
  package fails; the corrected package fails only on items needing an owner decision; the job is required on
  rehearsal repositories.
- **Repository.** Praxis.

## 3. A coherent, fully released kickoff stack, rehearsed once

- **Problem.** No rehearsal has run on the approved set (1.26.0). The approved set pairs Praxis 3.20.0 with Dokimos
  0.6.0, which cannot attest. SD-1 recurred in R2 and R3; its fix (conditor#108) is green but unreleased.
- **Root cause.** The Registry records versions but not pairing constraints between components; upstream fixes found
  in rehearsals are not released before the next one.
- **Proposed improvement.**
  1. Register Dokimos 0.7.0 and record that attested completion needs Praxis ≥ 3.17.0 **and** Dokimos ≥ 0.7.0; refuse
     a profile that enables the one without the other.
  2. Release Conditor with the SD-1 fix and qualify it.
  3. Register or explicitly reject Forma 0.9.1 and Limen 0.9.1.
  4. Restore the missing Praxis 3.17.0–3.19.0 manifests (R3 hardening §7).
  5. Freeze the kickoff set and run one rehearsal on it.
- **Expected benefit.** Removes the preflight stack defects that R2 and R3 each spent time on (R3 preflight: 21.6 min,
  2 failed CI runs from SD-1).
- **Acceptance criteria.** `npm ci` on a fresh `fsharp-limen-web` scaffold resolves Folio from its GitHub release; a
  profile combining Praxis ≥ 3.17 with verified completion and Dokimos < 0.7 is refused; one rehearsal-shaped
  bootstrap on the frozen set is green.
- **Repositories.** echelon-registry, Conditor.

## 4. ★ Uncacheable mutable reads in Limen

- **Problem.** The stale-mutable-read class was closed per application in R2 (DC-005) and recurred in R3 (D-07, M2).
- **Root cause.** Limen's Http effect has no cache mode (`src/kernel/browser-kernel.ts` `#runHttp`: `fetch` is called
  with method, signal, headers, credentials and body only). Applications work around it with URL nonces; GitHub's CORS
  policy refuses a `Cache-Control` request header.
- **Proposed improvement.** An optional `cache` field on the Http effect request mapped to `RequestInit.cache`
  (`no-store` for mutable reads). Additive protocol change.
- **Expected benefit.** Hypothesis: `RequestInit.cache` sends no request header, so CORS is unaffected. The D-07
  mechanism itself was never confirmed (R3: `Vary: Authorization` should have prevented reuse), so the acceptance test
  must run against real GitHub.
- **Acceptance criteria.** Contract and bindings regenerated; absent field = today's behaviour; a live test reproduces
  R3 Test F (anonymous connect, then invalid token) without a URL nonce and reports `authentication-failed`.
- **Repository.** Limen.

## 5. Hybrid agent topology

- **Problem.** The lead agent's self-assessment missed two high-severity defects and overstated acceptance twice in R3.
- **Evidence.** Continuity is the cheapest construction mode (VAC-001, measured). A fresh, read-only reviewer given code
  and requirements, not conclusions, found H1, N1 and the verdict error (R3 §9, observed).
- **Proposed improvement.** In the Indy Init plan: one continuous lead for construction; a fresh reviewer at the first
  release candidate and again before acceptance; the reviewer never edits.
- **Expected benefit.** Observed. Cost of R3 review rounds is inside the 14.0 M subagent tokens of 116.8 M timed.
- **Acceptance criteria.** The plan names both review points and their inputs; the acceptance verdict cannot be ACCEPTED
  without the reviewer's signed gate.
- **Repository.** Indy-init (kickoff plan). No intake: it is a process decision for the owner.

## 6. Four-tier guidance in every brief

Covered by existing intake `praxis/.praxis/inbox/documents/2026-10-24-ARCH-002-01-architecture-guidance-in-briefs.md`.
Not duplicated. For Indy Init, include the doctrine and the application's tier map in the kickoff brief now; it needs no
release.

## 7. Tool-managed workflows honour `global.json`

- **Problem.** R3 D-06: a repository `global.json` pinning SDK 10.0.402 with `rollForward: disable` broke the
  Dokimos-managed workflow, which installed 10.0.401 (exit 155). The repository may not edit `dokimos.yml`.
- **Proposed improvement.** Dokimos's workflow installs the SDK the repository's `global.json` names (setup-dotnet
  `global-json-file`), or fails with a named diagnostic before testing.
- **Acceptance criteria.** A fixture repository with `rollForward: disable` and a pinned patch passes the Dokimos gate;
  with no `global.json`, behaviour is unchanged.
- **Repository.** Dokimos.

## 8. Praxis defects from qualification (PRX-D1..D4)

Observed in R3 hardening §7 and recorded there as "requirements drafted, not committed, because this session has no
Praxis write scope". Captured now as Praxis intake. PRX-D1 makes `validate` fail permanently and affects 3.16.0, which
the rehearsals use.

## 9–10

Covered by EXP-2 consequences (split `validate`) and REL-TOKEN-004 (minimal tool profiles). Not urgent for Indy Init:
neither changes correctness, and neither is in an approved release.

## Not recommended for implementation yet

| Proposal | Why not |
|---|---|
| Typed inter-agent messages as a default | P3 arm D: no error reduction, +15% cost (F§2 H2) |
| Dependency-aware test selection enforcing | EXP-2 Contradicted |
| Rule-provenance audit in agent briefs | EXP-3 held-out recall 80%, false questions 25%; thresholds unmet |
| Larger cohorts for Indy Init | No correctness evidence; DC-008 shows the derivation risk |
