# Indy Init readiness

**As of 2026-10-24.** Event build window: 9:30 AM to 5:00 PM on 2026-11-07 (Indy-init `docs/HACKATHON-BOUNDARIES.md`),
with a 420-minute hard ceiling in the rehearsal design (R3-DV-002). Evidence: [engineering-findings.md](engineering-findings.md).

## Current readiness: NOT READY to promise an accepted release within seven hours

The read path is proven. The parts of the competition scope that took R2 past twelve hours have not been rehearsed since,
and the acceptance gate itself cannot pass on the stack and tooling as released.

**The headline numbers, and why they mislead:**

| Rehearsal | Scope | Candidate | Accepted |
|---|---|---|---|
| R1 | — | PASS at T+261.8 min, but releases were treated as Accepted while the deploy job was red | — |
| R2 | read **and write** to GitHub | verified deployment at 296.8 min | **721.2 min** (G0–G9 PASS) |
| R3 | **read-only** (DF-CAUSA-2026-0001) | deployed and verified at T+118.9 min | **never**: blocked, then remediation also blocked |

R3's 118.9 minutes is not evidence that the competition scope fits. The competition's P0 requirements include writes:
EXT-DATA-009 requires "successful create/read/write/reload" and EXT-DATA-006 requires authorized writes with optimistic
concurrency (Indy-init `docs/REQUIREMENTS.md`). R3 excluded them by a scope decision that its **lead agent authored and
marked `accepted`** (R3 `research/decisions/DF-CAUSA-2026-0001--read-only-historical-scope.md`, actor
`claude-code-lead`). The remediation lists ratifying that decision as operator decision 1 of 5.

## Status by area

Statuses: Proven working · Implemented, unverified · Known failing · Blocked · Not implemented · Unknown. Absence of a
reported failure is never read as success.

| Area | Status | Evidence |
|---|---|---|
| Requirements ingestion (Praxis inbox, RQ/DF records) | **Proven working** on Praxis 3.16.0 | R3 report §2 (8 RQ, 2 DF) |
| Requirements preservation (derivation vs source) | **Known failing** | Preservation gate exit 3 on the corrected package: 204 requirements without verifiable disposition, P0 38/42; gate bypassable; no CI job (R3 remediation §3, §6) |
| Requirements baseline for kickoff | **Unknown / moving** | Indy-init#12 baseline is a draft (374 requirements, 1,981 obligations). Six requirement commits landed on 2026-10-24 after R3 (`ffab0bd`..`39a3b1a`): fixture provider, workflow-layout diagrams, administration separation, investigation-centered UX. None has been rehearsed |
| Architecture decisions | **Proven working** for read path | R3 ArchitectureTests (8), after review M5; decision records |
| Agent execution (continuous lead + reviewer) | **Proven working** | R3 §9 |
| Compilation | **Proven working** | CI 40081709897; remediation 40126993034 |
| Testing: unit, browser, axe | **Proven working** | 65 .NET tests, 31 browser tests, axe on 7 views |
| Testing: live provider, read | **Proven working** | Test A on `CAUSA_GITHUB_TOKEN` PASS (remediation §2) |
| Testing: live provider, **write** | **Not implemented since R2** | R3 read-only |
| Persistence / write path (create, write, reload, conflict) | **Not implemented** in the current code line; R2 implemented it and needed 6 defect classes (DC-001..006) to close | R2 report |
| Deployment (GitHub Pages, exact-SHA acceptance) | **Proven working** | Deploy 40128155698, Test K |
| UI integration (Forma tokens, UI-016 palette) | **Proven working**, O13 untested | Remediation §7 |
| Forma compatibility | **Proven working at 0.9.0**; 0.9.1 unregistered | R3 stack |
| Limen integration | **Proven working at 0.9.0**; no cache mode (DC-005 workaround needed) | R3 D-07 |
| Folio | **Implemented, unverified** for report export; SD-1 (Folio installed from npm) is fixed locally only, upstream fix unreleased | R3 SD-1; R2 UI-009 export NOT_RUN |
| Runtime data loading (causa-data, external) | **Proven working** | three investigations reconstruct with fixed digests |
| Causa data contracts | **Proven working** for read; write-path fixtures out of scope in R3 | R3 gate 10 |
| Percepta semantic UI verification | **Blocked**: only `percepta-repo-v0.1.0` is released. The kickoff manifest marks Percepta `required: true` (Indy-init `kickoff/indy-init.kickoff.json`) | R3 §3; remediation REM-07 used an unreleased build |
| Assistive technology / iPad Safari on device | **Not implemented** (axe and emulated viewports only) | Remediation §3.3 |
| Deterministic completion (`work finish`) | **Implemented, unverified** in any rehearsal; tested only in isolation; leaves the item `active` (PRX-D3) | R3 hardening §7 |
| Attested verified completion | **Known failing on the approved set**: 1.26.0 has no Dokimos 0.7.0 | Registry catalog; hardening §7 |
| Echelon-current 1.26.0 stack under a rehearsal | **Unknown**: never rehearsed | R3 used 1.25.0 |
| Final acceptance verification | **Blocked**: operator decisions DF-CAUSA-2026-0003 (5), Percepta, AT session | Remediation §3 |

## Critical risks

1. **The write path is the long pole and is unrehearsed.** In R2 it caused DC-001 (critical), DC-003 and DC-005 and the
   gap between a verified deployment at 296.8 minutes and acceptance at 721.2 minutes.
2. **Acceptance cannot pass as specified.** Percepta is required but unreleased; operator decisions are open; the
   preservation gate fails on the corrected package. A perfect build still ends BLOCKED.
3. **Scope is unbounded at kickoff.** The baseline is 374 requirements; R3 built 56 criteria in its window and silently
   dropped obligations. Requirements are still being added two weeks out.
4. **Stack drift between rehearsal and event.** R3 ran 1.25.0; the approved set is now 1.26.0 (Praxis 3.20.0), and it is
   internally inconsistent for attested completion.
5. **Self-attested decisions and verdicts.** R3's lead authored and accepted its own scope reduction and first verdict.
   Without a mechanical verdict and authenticated ratification, the event run can do the same under time pressure.
6. **Provider behaviour.** Every late R2/R3 defect lived where the fake GitHub differed from GitHub. The remediation
   built a sanitized real-GitHub conformance fixture; it does not yet cover writes, conflicts or rate limits on writes.

## Unresolved blockers (owner actions)

| Blocker | Who | Unblocks |
|---|---|---|
| Ratify or reverse read-only scope (DF-CAUSA-2026-0001) **for the competition**, not only R3 | Owner | Whether writes are in the event scope |
| DF-CAUSA-2026-0003 items 2–5 (Connect vs auto-load, GUID vs caseKey URLs, Percepta waiver, baseline scope) | Owner | Preservation P0 4/42 and acceptance |
| Percepta: release the semantic CLI, or set `required: false` / waive in the kickoff manifest | Owner / Percepta | Gate "UI completion" |
| Freeze the kickoff requirement baseline (commit SHA plus manifest sha256) | Owner | Preservation gate, scope |
| Choose the kickoff release set (1.25.0 proven vs 1.26.0 unrehearsed) | Owner (A6a) | Stack risk |

## Highest-value interventions before November 7

Ranked by expected effect on "accepted within seven hours". Items 1 and 2 are decisions, not engineering.

1. **Decide and freeze scope.** Decide whether writes are in the event P0 set. Freeze the baseline by SHA with an explicit
   P0 list sized to the evidence: R3 delivered 56 read-path criteria to a candidate in about 2 hours; R2 needed about 12
   hours with writes. If writes are in, cut P1 UI scope instead.
2. **Make acceptance passable.** Resolve Percepta (release or waive in the manifest) and the DF-CAUSA-2026-0003 items
   now, so the event's acceptance depends only on work done during the event.
3. **Rehearse the write path on the frozen kickoff stack** (Rehearsal 4), with R2's DC-001..006 invariants as tests from
   the start and live write tests at the first persistence checkpoint (R3-DV-017). This is the only way to learn whether
   the scope fits. Stop on success; do not repeat the read path.
4. **Mechanical verdict and preservation in CI** (priorities items 1–2). Run the ledger validator on every commit,
   computing the verdict; run the preservation gate against the frozen baseline; agents may not set ratification
   fields.
5. **Close stack defects upstream before the freeze.** Release the Conditor SD-1 fix; decide Dokimos 0.7.0 for 1.26.0 or
   stay on 1.25.0; add Limen's `cache` option only if it can be released, registered and rehearsed before the freeze,
   otherwise keep the proven nonce.

## Seven-hour execution implications

- **Budget by phase, from evidence:** preflight before the clock (R3: 21.6 min, untimed); first build ~17 min; first
  green CI ~80 min; read-path candidate ~120 min (R3). With writes, R2 reached a verified remote write at about 177 min,
  a verified deployment at 296.8 min and acceptance at 721.2 min. Without new evidence, a write-inclusive scope **does
  not fit** the 420-minute ceiling.
- **Reserve review time.** R3's review rounds found 15 defects, two of them high, and its final review came after the
  candidate was deployed. Plan the first review at the first candidate, not at the end.
- **Do not upgrade tooling inside the event.** Promotion never happens into an in-flight run (RELEASE-GATES §6).
- **Never-deferred checks stay on:** secret and artifact exposure (N1), live provider at the first boundary checkpoint,
  and every workflow consuming a changed shared configuration file (D-06).
- **Stop rule:** stop when the computed verdict is ACCEPTED; if any mandatory gate is BLOCKED on an owner decision, the
  run records BLOCKED, never ACCEPTED with limitations.
