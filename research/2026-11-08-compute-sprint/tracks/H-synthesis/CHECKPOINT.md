# Track H checkpoint log (H-001, Research Synthesis and Publications)

All outputs are EXPERIMENTAL synthesis, not public claims. Prose report is delivered as reply text (D-010).

## CP-H-01 (~14:01 EST): cross-track matrix, first pass
- `synthesis/cross-track-matrix.json`: 22 themes (15 corroborate, 5 contradict, 2 independent).
- Inputs: A, B, C, E, G complete; V1 partial (4 verdicts); A2 preregistration; D CLAIMS.md; F, V2, B2 not yet available.
- Key contradictions: A-F-07 'no app-code conflicts' vs B-F-09 and V1 (X-02); computed-verdict framing B-F-04 vs E-F-02 (X-05); units (X-13); coordinator cap vs VAC-001 continuity (X-12).

## CP-H-02 (~14:02 EST): claims ledger
- `synthesis/claims-ledger.json` built by `scripts/build_ledger.py` (joins track findings with V1/V2 verdicts.json at build time; re-run to refresh).
- 63 consequential claims (28 high). Independently checked so far: 6 (V1: A-F-01, A-F-03, G-F-07, G-F-08 VERIFIED; A-F-07, A-F-08 PARTIALLY VERIFIED). V2 has no verdicts yet; every B, C, E claim is unverified by an independent track.

## CP-H-03 (~14:03 EST): ADRs
- `synthesis/adr/ADR-S01..S05`: signed Registry sets; .ros out of merge path; trusted acceptance job; mandatory pre-T0 dry run; coordinator context cap (conditional, weakest, contradicted in part by VAC-001 per X-12).

## CP-H-04 (~14:04 EST): datasets
- `synthesis/datasets.json`: 8 candidate datasets (B events, B summary, Actions A+B, A tokens, A controlled, C graph, E bypass matrix, merge replays). Global caveats: private-source data inside a public repo branch; no LICENSE in source repos; model column in A data vs MANIFEST rule; E bypass matrix is security-sensitive.

## CP-H-05 (~14:05 EST): future experiments
- `synthesis/future-experiments.json`: 8 implementation items (IM-01..08, evidence sufficient) and 13 research items (FX-01..13, evidence gaps). All costs ESTIMATE.

## CP-H-06 (14:11 EST): outlines
- `synthesis/outlines/outline-1..3`: self-declared done (governance); where the compute went (economics); independent verification positioning (commercial, internal first). Each claim carries an evidence class; [DO NOT STATE] items list framings the evidence does not support.
- Timestamps in earlier CP headings corrected to actual wall clock (first pass completed well before 17:00).

## CP-H-07 (14:16 EST): V1/V2 verdicts integrated
- V2: B-F-01, B-F-02, B-F-07, C-F-01, C-F-04, C-F-05, C-F-08, E-F-01, E-F-02, E-F-03, E-F-07, R10-gate-deadlock VERIFIED; B-F-03 PARTIALLY VERIFIED (first blocker, not dominant blocker). V1: G-F-10 VERIFIED (G had INCONCLUSIVE).
- Matrix: new theme X-23 (governance failure masked product incompleteness; contradicts B-F-03's strong reading). Notes added to X-04/05/06/08/09/10/14/15.
- Ledger: 18 of 63 independently checked (15 clean, 3 partial). Builder now carries verifier notes, scope notes and out-of-ledger verifications.
- ADR-S01/S03/S04 and outlines 1 and 3 updated; ADR-S04 narrowed to 'removes the first point of failure'.

## CP-H-08 (14:39 EST): B2, D, V1 complete; new tracks noted
- B2-dryrun findings integrated: ADR-S04 now carries the measured catch rate (4/8 brief, robust 2/8; 7/11 extended) and cost (seconds); FX-01 marked DONE.
- D-experiments findings integrated: X-12/X-11/X-15 updates; new X-25 (incremental verification); IM-09 added.
- V1 final (A-F-11, A-F-12 VERIFIED; A-F-13 PARTIALLY VERIFIED: ~605 min not 688). Outline 2 corrected.
- New theme X-24: B2-F-07 contradicts B's 'cycle in the frozen slice plan'.
- Ledger extended to B2 and D: 77 claims, 21 independently checked.
- New tracks seen (not yet producing findings): B3-semantic, D2-agent-experiment, E2-hardening.

## CP-H-09 (15:09 EST): wave 3/4 integrated (A2, C2, B3, B4, D2, F)
- Matrix: 27 themes (17 corroborate, 8 contradict, 2 independent). New X-26 (built but not adopted, 6 tracks), X-27 (CR-01 vs C2 prototype). X-24 resolved in favour of B/B3 (B2-F-07 contradicted).
- ADR-S01 rewritten: host-tool range policy (CON-343) first; signed attestations second; set-integrity and expiry gaps. ADR-S02 carries A2 replay results; ADR-S04 adds B3/B4 semantic checks (spec-preflight with --catalog).
- Ledger: 105 claims across 11 tracks; V3 verdict loading wired (none yet); contradicted findings listed.
- Future experiments: FX-02/FX-11 done, FX-05 short-task arm concluded; FX-14 (blind semantic-check test), FX-15 (adoption barriers), IM-10..12 added.
- Datasets: 13 entries (added F defects, F perf, A2 replay, B2 dry-run, D/D2 benchmarks).

## CP-H-10 (15:39 EST): V3 verdicts; D3/D4 series end
- Ledger reads V3 (combined ids like A2-F-01/02 expanded; SPR-D2-01 aliased to D2-F-02/03): 29 of 105 independently checked.
- New X-28: rehearsal over-claiming/authority failures are not reproduced by 5 controlled fixtures (contradict, moderate). Outline 1 gains the counterpoint.

## CP-H-11 (16:06 EST): SPR-X-01/X-02 and E2
- X-11 agreement changed to contradict: cost corroborated everywhere; benefit appears for Haiku (SPR-X-02) but not for capable models. X-28 partly reconciled by model dependence (over-claiming still not reproduced in any model).
- E2 integrated into X-04/X-05/X-26 and ADR-S03; new X-29 (permission-layer containment, SO-01). IM-13 (per-model governance calibration).
- Ledger: 110 claims plus supplementary SPR-X-01/X-02 entries (V4 verifying).
