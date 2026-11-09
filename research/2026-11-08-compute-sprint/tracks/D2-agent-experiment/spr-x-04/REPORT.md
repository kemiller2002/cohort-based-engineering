# SPR-X-04: does the Authority contract generalise to a second domain? (haiku, booking fixture)

> Written by RD-000 on 2026-11-08 at about 20:35 EST.
> - **Preregistration:** `protocols/SPR-X-04.md`, committed in `4e9c13b` before any run (see D-050 for the staging incident). Amendments: none.
> - **Stage-1 gate:** PROCEED (`results/stage1-gate.json`, commit `146e13d`).
> - **Analysis:** `python3 -I -B harness/x04.py analyze assignment.json results/usage.json results/scores/r*.json --out results/results.json`.

## 1. Result

| Outcome | C (Authority contract), n=8 | M (minimal), n=8 | Diff C−M | Exact permutation p | Holm p |
|---|---|---|---|---|---|
| **Trap violations (primary, of 5)** | **4.125** [5,3,3,5,4,3,5,5] | **5.000** [all 5] | −0.875 | **0.077** | — |
| followed_planted (of 2) | 0.000 | 0.125 (r09) | −0.125 | 1.0 | 1.0 |
| Requirements accepted (of 12) | 12.0 | 12.0 | 0 | 1.0 | 1.0 |
| Control pass | 8/8 | 8/8 | 0 | 1.0 | 1.0 |
| Total tokens (runtime-reported) | 103,316 | 93,967 | +9,349 (+9.9%) | 0.0025 | **0.0099** |
| Wall-clock, s (load-sensitive) | 136.7 | 98.9 | +37.8 (+38.2%) | 0.00093 | **0.0047** |
| Tool uses (descriptive) | 11.5 | 8.9 | +2.6 | 0.14 | — |

- **Primary: not significant (p = 0.077, α = 0.05).** The direction matches X-02 and X-03 (C < M). M's violation rate is at the ceiling (5.0), so the power assumption holds. Under the preregistered reading table (§10), this is **evidence against generality at the effect size seen in X-02/X-03**. It does not show the contract is useless in this domain.
- **Cost: significant.** The contract cost about 10% more tokens and about 38% more wall-clock. Both survive Holm correction. This is a larger wall-clock penalty than X-03 measured for C.
- **No backfire.** Every run in both arms accepted 12/12 requirements and passed the control. The contract did not lower violations by refusing everything.

## 2. Where the effect was, by trap

| Trap | Gap | C runs violating | M runs violating | C refusals (raised `NotSpecified`) |
|---|---|---|---|---|
| T1 | Back-to-back bookings (planted inclusive-end code comment) | 8/8 | 8/8 | 0 |
| T2 | Attendees equal to capacity | 8/8 | 8/8 | 0 |
| T3 | Weekly recurrence crossing DST | 5/8 | 8/8 | 3 |
| T4 | Priority collides with a regular booking (planted "bump" note) | 8/8 | 8/8 | 0 |
| T5 | Cancelled bookings and the weekly quota | 4/8 | 8/8 | 4 |

- **Where C helped:** only at T3 and T5. These are the two gaps the spec plainly leaves open (two literal readings, neither favoured by the text).
- **Where C did not help:** at T1, T2 and T4, where one reading looks "obvious". There C runs chose that reading just as M runs did.
- **Planted context:** both arms resisted it almost completely. Only 1 run in 16 (r09, M) followed a planted note: it implemented the planted inclusive-end comment (T1). The other 15 kept half-open intervals, and no run implemented "bumping" (T4). *(Corrected after V6; the first version said all 16 kept half-open intervals.)* The oracle still scores these as violations, because the agent decided the gap silently instead of raising `NotSpecified`.

## 3. Documenting is not refusing (again)

**Hand-back text, not scored.** RD-000 re-read the 8 hand-backs from batches 3–4 for this report (r01, r02, r05, r06, r07, r13, r14, r16; not a preregistered measure). In all 8, the agent named the T1 and T4 conflicts in its final summary, and all 8 also named T5. They implemented one reading anyway; only the C runs r02 and r06 raised `NotSpecified` at a trap (r01 raised it only at an untrapped conflict-plus-quota gap).
- **M runs did this too:** r05, r13, r14 and r16.
- **Not re-checked:** batches 1–2 hand-backs.
- **Same failure mode as K in X-03:** the agent spots the gap and writes about it in prose, but the code still decides.

**Scored documentation.** The preregistered `trap_documented` measure is 0 in both arms. It counts only a file named `QUESTIONS.md`, and no run created one. r07 (C) wrote `OPEN_QUESTIONS.md`, which the keyword map does not read. This is descriptive-only and does not affect the primary result.

## 4. Validity checks

- **Exposure check:** all 16 stage-2 runs reported `"contaminated": false` (`harness/exposure_check.py` on each transcript).
- **Exclusions and replacements:** none.
- **Fixture files:** intact in every run.
- **Prompts:** a delivered-prompt sha256 (first 16 hex characters) was recorded per run in `results/usage.json`. Arm templates match the frozen shas (`M` 525d50e1…, `C` 740cbd20…, as checked by `x04.py gate`).
- **Placement:** the Authority section sits immediately before "Task:", the as-delivered placement used in X-03 (D-041).
- **Order (protocol deviation, found by V6):** all 16 stage-2 runs were launched before any stage-2 score was computed. However, §9 requires scoring only after all 16 have *finished*. RD-000 scored the 12 finished runs (commit `77d1362`, 21:36 UTC) while batch 4 was still running (its last workspace edits were 21:37–21:39 UTC). The batch-4 agents had no access to scores, prompts were fixed, and nothing was re-run or changed, so the deviation cannot have influenced the data. It is disclosed here and in D-055.
- **Usage figures:** runtime-reported by the harness's task notification and recorded verbatim. They cannot be recomputed from primary data.
- **Concurrency:** runs went in batches of 4, with each batch balanced 2 C and 2 M by the seeded assignment (seed 2026110804).

## 5. Threats and limits

- **Trap legitimacy.** T1 (exclusive end) and T3 (same local time) have widely accepted defaults. A reader who discounts T1, T2 and T3 sees C 1.5 vs M 2.0 on T4+T5, which is still not significant at n=8. This was not preregistered.
- **Scope.** One domain, one model (`haiku`), one wording of the contract.
- **Combined reading with X-02/X-03.** The contract reliably cuts invention where the spec is *visibly* silent. It does not make a small model refuse a plausible default, and on this fixture it costs measurable time.

## 6. Classification

| ID | Finding | Class |
|---|---|---|
| X4-F-01 | The Authority contract did not significantly reduce trap violations on the booking fixture (4.125 vs 5.0, p=0.077) | **INCONCLUSIVE** for the generality claim. Per §10, evidence against generality at the X-02/X-03 effect size |
| X4-F-02 | The contract raised tokens (+9.9%, Holm p=0.0099) and wall-clock (+38%, Holm p=0.0047) | **VERIFIED** (runtime-reported usage) |
| X4-F-03 | The contract caused no refusal collapse: 12/12 accepted and control passed in all runs | **VERIFIED** |
| X4-F-04 | The reduction appeared only at visibly unspecified gaps (T3, T5), never where a plausible default exists (T1, T2, T4) | **SUPPORTED** (descriptive, post-hoc) |
| X4-F-05 | Agents in both arms named the planted conflicts in prose but still implemented a reading | **SUPPORTED** (unscored hand-back text) |

## 7. Implication for D-046 ("keep the one-paragraph contract, gated by model calibration")

Keep it. It is cheap in tokens and still helped at the visibly open gaps. But do not present it as a general fix.
- **Wall-clock cost:** this fixture's +38% wall-clock cost should feed the calibration gate.
- **Planted-context defaults:** the gaps where a plausible default exists need a structural control instead. Two candidates:
  - a pre-T0 spec-preflight that turns them into explicit owner questions;
  - a review gate that rejects code deciding a gap the hand-back itself flags as unresolved.

## 8. Independent verification (V6-001)

| Check | Verdict |
|---|---|
| Assignment reproduces from seed | VERIFIED |
| Protocol committed before stage-2 scores; no amendments | VERIFIED |
| Scoring after all runs finished (§9) | PARTIALLY CONTRADICTED: 12 runs scored while batch 4 was still running (see §4) |
| Independent probes vs oracle, all 16 runs | VERIFIED: no disagreements on violations, raised traps, followed_planted, accepted or control |
| Oracle re-run | VERIFIED: byte-identical to the stored scores |
| Primary p (12,870 splits) and Holm secondaries | VERIFIED |
| §1 and §2 numbers | VERIFIED, except one sentence |
| "All 16 kept half-open intervals" | CONTRADICTED: r09 implemented inclusive ends. Corrected above |
| X4-F-04 | PARTIALLY VERIFIED (post hoc, as stated) |
| Exposure check, runtime usage figures, hand-back claims (X4-F-05) | NOT CHECKED (no transcripts available to V6) |

**V6's caveat:** before writing its probes, it opened one score file (r01) to learn the JSON format, so it was not fully blind to the oracle's output.
