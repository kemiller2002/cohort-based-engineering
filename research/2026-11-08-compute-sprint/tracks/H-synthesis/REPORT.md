# Track H report: research synthesis (H-001)

> Committed by RD-000 from H-001's final hand-back text (D-010). Worker final commit: `fb56dbf`.
>
> All of this is EXPERIMENTAL synthesis. Each conclusion cites a track finding ID, and that finding is the evidence.

## Artifacts

All artifacts are under `synthesis/`:

| File | Contents |
|---|---|
| `cross-track-matrix.json` | 30 themes |
| `claims-ledger.json` | Built by `scripts/build_ledger.py` from track `findings.json` and V1–V5 `verdicts.json` |
| `adr/ADR-S01..S05*.md` | Proposed architecture decisions |
| `datasets.json` | 13 datasets |
| `future-experiments.json` | 14 implementation items (IM) and 17 research items (FX) |
| `outlines/outline-1..3*.md` | Candidate publication outlines |

Checkpoints CP-H-01 to CP-H-13 are in `CHECKPOINT.md`. The first full pass finished at about 14:12. Track H then updated through waves 2–4, V1–V5 and SPR-X-04, and stopped polling on RD-000's 20:30 instruction.

## 1. Theme matrix

The matrix has 30 themes:
- 18 corroborate, 10 contradict and 2 are independent.
- 14 are strong, 13 moderate and 3 weak.

### Strongest corroborations

| Theme | Pattern | Main evidence |
|---|---|---|
| X-04 / X-26 | **Built but not adopted** (6 tracks). Verified completion exists but no repository enables it. Conditor range qualification is dormant because its trust list is empty. Limen view contracts and Folio are unused. spec-preflight `--catalog` is unused, and B3 rebuilt what spec-preflight already does | E-F-01 (V2 VERIFIED); G-F-07 (V1 VERIFIED); C-F-04 (V2 VERIFIED); C2-F-03; F-F-13, F-F-14; B4-F-05 (V3 VERIFIED); D-029 |
| X-01 | `.ros` state files are the dominant merge-conflict surface; the merge driver removes these conflicts on replay | A-F-07, B-F-09, V1, A2-F-01/02 (V3 VERIFIED) |
| X-08 | CI red and cancelled minutes are driven by harness semantics: R6 starvation and R10 job caps | A-F-12 (V1: 65.6%, 54–76% by definition), B-F-08, F-F-09 |
| X-30 | **Artefact-producing procedures are not controls.** Documenting is not refusing, and citing evidence is not running it | X-03 checklist arm, X4-F-05, D2-F-03, E-F-01/02, B-F-04 |
| X-14 / X-15 | No run reached governed acceptance, and cross-run comparisons are confounded | B-F-01 (V2 VERIFIED, with caveat); B-F-07 (V2 VERIFIED) |

### Key contradictions

| Theme | Resolution |
|---|---|
| X-02 | A-F-07 said R8 had no application-code conflicts. B, V1 and A2 contradict this: at least 4 R8 merges conflicted in application, test or CI code |
| X-05 | The computed verdict changed agent behaviour but was never an independent control. E-F-02 (V2 VERIFIED): it accepts a fully fabricated bundle |
| X-23 | Governance machinery was the first refusal, not the dominant blocker. R8 still FAILED with valid approvals, and R9 implemented 0 of 541 obligations |
| X-24 | B3-F-06 contradicts B2-F-07: the Causa T18↔T20 cycle was derivable before T0 |
| X-27 | CR-01 is contradicted by C2 (V3 VERIFIED): 2–3 of 13 releases were avoidable, host-tool exact pins (CON-343) drive releases, and the Registry signing side is absent |
| X-11 | Governance prompting: the cost is consistent (+6–10% tokens, +38–55% wall-clock). A benefit appears only on Haiku (X-02, X-03; V4/V5 VERIFIED). X-04 found no significant benefit in a new domain (p=0.077; since verified by V6) |
| X-12 | VAC-001 found continuity about 41% cheaper, and a fresh restart cost +86% (D-F-03, D-F-05) |
| X-13 | Tracks use different units for cost and acceptance: criterion, P0 requirement, obligation, fixture requirement and run verdict. G's fixture cost is 5–35× below A's rehearsal costs. A glossary is needed before publication |
| X-28 | Rehearsals show over-claiming and invented authority; five lab fixtures do not reproduce them. Policy invention is partly model-dependent. Over-claiming was 0 in every model tested, and its cause is untested |
| X-03 | Per-run conflict counts for R3, R5 and R6 differ between B and A2. This is minor and unreconciled (FX-09) |

## 2. ADRs

All five are Proposed, on EXPERIMENTAL evidence.

- **ADR-S01 (rewritten after C2).**
  - Decide the host-tool range policy (CON-343) first; it sits behind 7 of 13 releases.
  - Build signed Registry attestations second.
  - Close the expiry and set-integrity gaps (C2-F-04/05).
- **ADR-S02.** Take `.ros` out of the Git merge path.
  - **Interim:** A2's semantic merge driver. It made 93% of R8 and 85% of R10 conflicted merges clean, with 0 records lost, and caught a real dropped work item.
  - **Target:** per-lane append-only records.
  - Application-code conflicts still need lane file ownership.
- **ADR-S03.** Compute acceptance in a trusted job the candidate cannot write to, with verifier-signed evidence.
  - E2-F-05's prototype refuses the fabricated bundles, but only in a local simulation.
  - Prerequisites: branch protection and credential separation (E-F-07).
- **ADR-S04 (narrowed).** Make a pre-T0 dry run mandatory: mechanical checks, spec-preflight with `--catalog`, and a slice-cycle check.
  - In retrospect it catches 4 of the brief's 8 blockers (robustly 2 of 8) and both R8 semantic blockers, in seconds.
  - It removes the first point of failure. It does not make runs acceptable by itself, and its prospective generality is untested.
- **ADR-S05 (weakest).** Do not cap coordinator context yet. Use compact notifications and test the cap in a controlled run (FX-04).

## 3. Top 10 recommendations

### Implementation (evidence sufficient)

1. **IM-03 (E2 patches).** Repository-contained, digest-bound evidence, VERIFIED with no test impact. A queue/event cross-check found 0 false positives over 1,881 rows. The claim guard needs an owner decision on I8.
2. **IM-05 + IM-14.**
   - Branch protection and CODEOWNERS on the governance repositories.
   - A minimal tool allowlist for implementation subagents with no session-lifecycle tools (SO-01).
3. **IM-10.**
   - Ship the `.ros` history merge driver.
   - Make `praxis validate` detect duplicate event lines.
   - Decide the event-ordering policy.
4. **IM-02.** A hardened CI template: pipefail, `!cancelled()`, per-branch concurrency, sized job caps and explicit permissions.
5. **IM-01.** Cache the pinned Praxis verifier or use the attested release. Estimated saving: about 550 of roughly 605 minutes.
6. **IM-11.** Run spec-preflight with `--catalog` in Indy-init CI and fail on any blocking section.
7. **IM-13 (downgraded to Medium after X-04).** Use the Authority contract only for models that fail calibration, and count its wall-clock cost. It is not an authorization control.

### Research (gaps that block decisions)

8. **FX-03.** Does `requirements-compiler verify-plan` catch the fabricated bundle?
9. **FX-14 / FX-17.**
   - A blind test of the semantic pre-T0 checks.
   - A review gate that refuses code which decides a gap its own hand-back flags as unresolved.
10. **FX-04 / FX-16 / FX-09 / FX-15.**
    - FX-04: a coordinator-cap controlled run.
    - FX-16: long-horizon governance arms with capable models.
    - FX-09: reconcile the sprint's own conflicting counts.
    - FX-15: why existing capabilities go unadopted.

## 4. Roadmap

| Horizon | Actions |
|---|---|
| 24 h | Owner decisions: the I8 claim-marker policy, CON-343, and `.ros` event ordering. Apply IM-11 and IM-14. Turn on branch protection and CODEOWNERS (IM-05). **Decide the visibility of private-derived data, because the sprint lives in a public repository.** |
| 7 d | Review and merge the E2 patches (IM-03). Add the bypass matrix and REL-001 gate to Praxis release CI (IM-04). Verifier cache (IM-01). CI template (IM-02). Merge-driver package (IM-10). Telemetry fixes (IM-06). Run FX-03 and FX-09. Write a unit glossary (X-13). |
| 30 d | Trusted acceptance job (ADR-S03). Mandatory dry run, with the C4 cycle check contributed upstream (ADR-S04). Registry signing side, if range trust is accepted (ADR-S01). Research: FX-14, FX-17, FX-04, FX-16, FX-15, FX-10 (buyer interviews). Supply-chain baseline (IM-07). WASM fixes (IM-12). |

## 5. Ledger

- **Main ledger:** 110 consequential claims across 13 tracks, 42 of them high-consequence.
  - 29 independently checked: 24 VERIFIED, 5 PARTIALLY VERIFIED (A-F-07, A-F-08, A-F-13, B-F-03, A2-F-03).
  - 81 not yet independently verified.
- **Supplementary experiment claims:** X-01 to X-04. X-01 was verified by V4, X-02 by V4, X-03 by V5 and X-04 by V6 (recorded after this hand-back).
- **High-priority claims never verified:** A-F-16, B-F-04, B-F-09, B-F-16, C-F-02, C-F-03, C-F-13, E-F-06, E-F-14, G-F-01, G-F-02, G-F-06, B2-F-01, B2-F-08, D-F-03, C2-F-02, C2-F-08, B4-F-07, F-F-03, E2-F-03, E2-F-05.
- **Contradicted:** B3-F-06 (of B2-F-07), C2-F-07 (of CR-01), F-F-05, F-F-11, G-F-11.

## 6. Candidate publications

None of these is cleared for publication. Each outline marks its claims with an evidence class and lists **[DO NOT STATE]** items.

1. **"Done, according to whom?"**
   - It needs an owner decision on disclosing unfixed bypasses.
   - It must carry the X-28 counterpoint.
2. **"Where the compute went."**
   - Use V1's corrected figures.
   - Never write "no app-code conflicts" or "the contract is a general control".
3. **Independent-verification positioning paper.**
   - Internal only until Echelon enables its own verified completion and buyer evidence exists.
   - The G-F-10 site claims must be resolved first.

## 7. Unfinished

- F-F-16 (Playwright stability) is still pending in Track F.
- The FX-09 reconciliation was not done.
- Some artifact paths point to other tracks' worktrees; the `pathNote` fields say so.
