# SPR-X-03 (CONFIRMATORY protocol, modest power): which part of the governance block helps Haiku?

**Preregistered by RD-000 at 2026-11-08 ~16:05 EST, before any run.**

## Question
SPR-X-02 showed that on `haiku` the combined block (Authority contract + Checklist) reduces policy invention compared with the minimal prompt. This experiment asks whether the effect comes from the **Authority** contract alone (arm C) or from the **Checklist** alone (arm K).

## Arms
Both arms use the `haiku` model, the general-purpose agent type and background runs. Each arm prompt is the frozen M.txt with one section of the frozen G block inserted, at the same position used in the X-02 runs (immediately before the "Task:" line; see the deviation note):

| Arm | Prompt file | sha256 (template) |
|---|---|---|
| C | `arm-prompts/C.txt` (M + Authority section) | 740cbd20…daf6 |
| K | `arm-prompts/K.txt` (M + Checklist section) | 30229d25…b4b7 |

- `arm-prompts/G_as_delivered.txt` (sha256 73fccb46…e371) records the exact G text pasted in the D2-01 and X-02 runs.
- `harness/test_x03.py` checks that the section text comes from the frozen G block (sha256 9e6b2256…e309).

## Fixtures
These are unchanged from X-02. All workspaces are freshly created and match the committed fixture templates byte for byte.

| Fixture | Traps | Workspaces | Scorer |
|---|---|---|---|
| D2-02 | 5 | `/home/user/sprint-scratch/D2b/ws/a01..a12` | `oracle-c41e/score.py` |
| D2-03 | 3, plus 2 controls | `/home/user/sprint-scratch/D2c/ws/b01..b12` | `oracle-9b27/score.py` |

## Design and analysis
- **Sample:** n = 6 per arm per fixture, 24 runs in total. Assignment is in `assignment.json`, generated with seed 2026110861 by `harness/x03.py assign`. Runs go in 4 batches of 6 (3 C + 3 K each), one batch at a time.
- **Primary outcome:** trap violations per run, using the raised measure.
- **Primary test (C vs K):** stratified exact two-sided permutation test, using the same tested function as X-02.
- **Secondary (descriptive only, not hypothesis tests):** comparison of C and K with X-02's G and M arms on the same model, fixtures and day. These are not randomized against X-03, so treat them as context only.
- **Other secondary outcomes:** followed_planted, undocumented violations, tokens and wall-clock. P-values are Holm-adjusted across the 4.

## Exclusions and caps
Same as X-02: contamination or infrastructure failure only. The time cap is 40 minutes.

## Interpretation (fixed now)
| Result | Reading |
|---|---|
| C ≈ G and K ≈ M | The contract carries the effect |
| K ≈ G and C ≈ M | The checklist carries it |
| Both partial | Both components contribute |

These readings compare against X-02 descriptively; only C vs K is tested.

## Deviation disclosed with this protocol
- **What happened:** the frozen G.txt places the block after the "Task:" line. In D2-01 and X-02, the Director pasted the block before the "Task:" line.
- **What was the same:** the block content was byte-identical, so only its position differed.
- **What check missed it:** `check_prompts.py` verified the files, not the delivered prompts.
- **Effect on these results:** X-02's conclusions apply to the as-delivered placement. X-03 keeps that placement so the two experiments compare cleanly.
