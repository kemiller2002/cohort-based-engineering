# V5-001: verification of SPR-X-03

> Committed by RD-000 from V5-001's final hand-back text (D-010).
> - Worker final commit: `b31fb93` (16:22 EST).
> - Outputs: `verdicts.json` (9 entries), `CHECKPOINT.md`, `scripts/` (four test suites passing: V4's `test_oracle.py` re-run, plus `test_v5stats.py`, `test_prompts_check.py`, `test_helpers.py`), and `raw/` (v5-scores, agreement, v5-stats, confounds, prompts_check, descriptive, t5_across_experiments, sensitivity_extra, v4-oracle-provenance.sha256).

## Bottom line

The primary claim reproduces exactly, with an independent oracle and my own statistics code: C − K = **11/3 per run summed across the two fixtures**, exact two-sided **p = 1/2178 = 0.000459** (392 of 853,776 relabelings). All secondaries reproduce.

What I flag is wording only:
- "silent/undocumented" for C's T5 violations;
- X-F-08's "may look specified" explanation;
- the strength of the descriptive "K worse than M" claim.

## 1. Re-score (VERIFIED)

- V4's oracle was copied and hash-recorded, and its control validation was re-run first: 7/7 tests, covering 11 controls.
- Agreement with the committed scores is complete; there are no disagreements:

  | Comparison | Agreement |
  |---|---|
  | Per-run | 24/24 |
  | Trap cells | 96/96 |
  | Planted-value cells | 36/36 |

- Sensitivity probes never change a trap verdict.
- Per-run violations:

  | Fixture | C | K |
  |---|---|---|
  | D2-02 | 1 in every run (always T5) | a12 4, a07 5, a04 2, a10 1, a09 5, a06 4 |
  | D2-03 | 0 in every run | b09 2, b06 2, b03 2, b02 1, b10 0, b12 0 |

- Planted values:
  - K followed them in b02, b03, b06 and b09: T3 half-up in all four, and T4 active-only in b06 and b09.
  - C followed none.
  - b03 T4 returns 5, which counts cancelled lines. That is the opposite of the plant, so it is a violation but not a planted follow.

## 2. Statistics (VERIFIED)

Own exact enumeration with Fractions (fixture convolution, checked against brute force); x02.py, x03.py and V4's stats.py were not used.

| Outcome | Statistic | Exact p | Holm p |
|---|---|---|---|
| Primary | 11/3 (D2-02 5/2 + D2-03 7/6) | 1/2178 | — |
| followed_planted | 1 | 2/33 | 2/33 |
| Undocumented violations | −1 (K better) | 1/462 | 1/231 |
| Tokens | 6,386.8 per run | 1/426888 | 9.4e-6 |
| Wall-clock | 21.73 s per run | 1/426888 | 9.4e-6 |

- **Per fixture:** D2-03 alone is **not significant** (p = 2/33). D2-02 alone gives p = 1/66.
- **Sensitivity:**
  - stratifying by fixture × batch gives p = 2/729;
  - dropping the four SO-01 runs (a07, a10, b10, b04) gives p = 1/8820.

## 3. Arm assignment (VERIFIED)

- QUESTIONS.md and EVIDENCE.md appear only in the 12 K runs: 0 mismatches.
- Every batch has 3 C and 3 K runs.
- File times cluster by batch: 16:00:43–16:01:07, 16:02:59–16:03:31, 16:05:12–16:05:29 and 16:07:16–16:07:46.
- The preregistration commit 90f85c1 is at **15:59:50 EST**, before every run. PROTOCOL.md's "~16:05" is a mislabel.

## 4. Prompt derivation (VERIFIED, templates only)

- The frozen G.txt hash matches.
- C.txt and K.txt are each M.txt plus exactly one section, inserted before "Task:". G_as_delivered.txt has both sections there.
- The hashes match the PROTOCOL.
- The delivered prompts cannot be seen.
- **Design note:** K's section asks for two extra files. That explains part of K's cost overhead mechanically, and it means the "documented" measure exists only for K.

## 5. Descriptive comparison with X-02 (PARTIALLY VERIFIED; not randomized)

| Claim | Holds? | Detail |
|---|---|---|
| C ≈ G on violations | Yes | D2-02: 1.00 vs 0.83. D2-03: 0 vs 0.50. Unadjusted p = 13/22 |
| C ≈ M on cost | Partly | Tokens: yes (−0.6% / +1.6%). Wall-clock on D2-03: about 11% above M |
| K > M on D2-02 | Weakly | 3.50 vs 2.00, p = 0.10, descriptive only. Reverses on D2-03 (1.17 < 1.50), and K is better than M on the undocumented measure |

## 6. T5 and X-F-08 (PARTIALLY VERIFIED)

**T5 is a fair trap.** R-08 never says whose calendar decides "Saturday or Sunday". D2-03 needed signed decision D-002 to settle it, and Sonnet plus one G run flagged it.

**T5 barely discriminates.** The SPEC's wording and Python's `.weekday()` both point to a device-local default. **24 of 25 Haiku D2-02 runs chose device-local, in every arm**; only G s13 raised.

**Wording problems in X-F-08:**
- "Silently" is wrong. All 6 C runs state the reading in a code comment, and a02 flags it for confirmation.
- "May look specified" is only weakly supported. All 6 K runs called T5 unspecified and still implemented the default, which points to a strong natural default.

**Excluding T5 changes nothing in the primary result.** The statistic stays 11/3 and p stays 1/2178, because every D2-02 run violated T5. Without T5, C has **0 violations in all 12 runs**; descriptively, G is 0.00 and M is 1.00.

## 7. Confounds (VERIFIED: none found)

- Only allowed imports (AST-checked).
- No file, os, sys, subprocess or network use.
- Fixture files are byte-identical to the templates.
- C < K in every batch (C 2/1/2/1 vs K 6/7/4/11).
- Process-level behaviour (SO-01, /tmp files) is not visible from the workspaces.

## Verdicts

**SPR-X-03 overall: VERIFIED.**

| Component | Verdict |
|---|---|
| Re-score, primary, secondaries, arm assignment, confounds | VERIFIED |
| Prompt derivation | VERIFIED (templates only) |
| Descriptive claims vs X-02 | PARTIALLY VERIFIED |
| T5 / X-F-08 | PARTIALLY VERIFIED |
