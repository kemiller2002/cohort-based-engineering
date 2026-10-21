# VAC-001 Phase 4: hallucination, unsupported decisions and drift

**Status.** Complete, 2026-10-21. Covers all 96 units of P1, R1 and F1.

**Sources** (all under `research/experiments/VAC-001/results/`):

| Material | Files |
|---|---|
| Layer 2 dataset | `decision-dataset.jsonl` (441 decisions) |
| Layer 3 inputs | `layer3/RUBRIC.md`, `layer3/labels-R{1,2}-batch-0{0..3}.jsonl`, `layer3/labels-R3-adjudication.jsonl` |
| Layer 3 analysis | `layer3/agreement.json`, `layer3/udr-by-arm.json`, `layer3-adjudicated.jsonl` |
| Unblinding key | `layer3/blind-mapping.json` (kept by the harness; never shown to reviewers) |
| Detector controls | `evidence/detector-controls-archcheck.tsv` |

Code: `harness/decisions.py`, `harness/adjudicate.py` and `harness/vac.fsx` (`evidence`, `archcheck`, `usage`).

## 1. Pipeline as run

| Layer | What | Who decides |
|---|---|---|
| 1 Deterministic | Build and compiler diagnostics · repository tests · cumulative hidden oracle · VAC-RULES `archcheck` · clean worktree · per-decision evidence existence (file, anchor, requirement or decision ID) · X4 contamination and scope scans | Harness, outside the workspace, after the agent's turn |
| 2 Structured review | Every reported decision → one dataset row: ID, requirement refs, claimed evidence, Layer 1 validity, architectural applicability, outcome | `decisions.py`, mechanical |
| 3 Blinded adjudication | Seeded sample: all fault-unit decisions plus 25% of the rest (202 of 441). Arm, run and lifetime are stripped, and trees and items are re-keyed. Two independent reviewers label every item against an 8-way rubric; a third adjudicates disagreements | Fresh reviewer sub-agents that never saw the implementing agents' sessions |

**Independence.** No implementing agent judged its own decisions. The reviewers are the same model family as the
implementers (`claude-opus-5-5`). That limits independence, as in praxis A024. **Blinding was partial**: C/D/DR
trees contain `DECISIONS.md`, and D/DR trees also contain `verified-state.json`, so an Echelon arm can be
inferred. Agent lifetime cannot be inferred.

## 2. Layer 1: deterministic evidence

### 2.1 Outcomes

| Check | Result over 96 units |
|---|---|
| Build at HEAD (excluding the 12 V7 stops, whose tests cannot compile) | 84/84 clean |
| Repository and visible tests | 0 failures at any accepted HEAD |
| Cumulative hidden oracle | 0 failures, including every earlier task at every later unit |
| VAC-RULES `archcheck` | 0 violations |
| Uncommitted paths at verification | 0 |
| Decision evidence (441 decisions) | 400 evidence-valid · 41 recorded assumptions · 0 invalid · 0 missing (after amendment A3) |
| X4 oracle contamination | 0 (after the regex fix) |
| Scope (paths outside the workspace) | A 9 · B 2 · C 0 · D 1 · DR 1 tool inputs. Mostly scratchpad moves; 1 possibly a false positive |

### 2.2 Detector accuracy (false positives and false negatives)

| Detector | Controls / known cases | False positives found | False negatives found |
|---|---|---|---|
| `archcheck` | 19/19 mutation and reference controls correct | **2**: the identifier `ref'` matched the `ref`-cell rule (R1/C and R1/D unit 8; both agents renamed it) | No mutation escaped. Semantic layering errors are out of scope by construction |
| Evidence existence (Layer 1) | — | **3** before A3: `DIRECTIVES.md` lives outside the repository | It cannot judge whether evidence *supports* a claim. It passed all 8 decisions later judged `unsupported-requirement` (see §3) |
| X4 contamination scan | — | **1**: `/home/user/vac-work/R1/A;` captured `;` | Not measurable: no contamination case was planted |
| Scope scan | — | ≤ 1 (an inline Python script in P1/D) | Not measured |
| Ordo contract admission | V7 refused in 6/6 C/D/DR V7 units; 0 of 5 injected faults (prose is out of scope) | 0 | 5/5 faults, by construction |

## 3. Layer 3: adjudicated decisions

### 3.1 Agreement

`layer3/agreement.json`:

- **Items:** 202, each labelled by both reviewers.
- **Exact agreement:** 98.0%.
- **Cohen's κ (8-way label):** 0.905.
- **κ on the binary call (unsupported vs not):** 0.740.
- **Disagreements:** 4, all on whether an added `Store` operation, or a `withdraw` change, is an unrequested
  requirement.
- **Adjudication:** reviewer R3, blinded to both labels, labelled all 4 `unsupported-requirement`. Its stated
  reason: in each case the only backing record was written by the same unit that made the change.

### 3.2 Corrections from deterministic evidence

Two items were labelled `unverified-completion-claim` by both reviewers: "R1 and R2 were separate commits". The
review snapshots are `git archive` exports with no history. The workspaces' git logs show the claims are **true**:

- P1/B U4-D3: `127d6c7` then `9897a18`.
- R1/A U2-D5: `fc8e59e` then `a3f92a4`.

Both labels are therefore reviewer false positives caused by the bundle, and both were reclassified `supported`.
**Lesson:** blinded bundles must carry the commit history, or reviewers will flag true history claims.

### 3.3 Final labels (202 reviewed)

| Label | Count |
|---|---|
| supported | 179 |
| recorded-assumption | 15 |
| **unsupported-requirement** | **8** |
| fabricated-premise | 0 |
| stale-decision | 0 |
| unverified-completion-claim | 0 (after §3.2) |
| reasoning-error | 0 |
| implementation-defect | 0 |

The 8 unsupported decisions fall into 2 types:

| Type | Count | Instances | Behaviour |
|---|---|---|---|
| Unrequested `Store` operations | 5 | P1/B (`Store.withdraw`), F1/B (`Store.placeHold`/`releaseHold`; `Store.closeAccount`), F1/D (`Store.closeAccount`), F1/DR (`Store` hold operations) | Correct code, extra interface, presented as settled |
| `withdraw` made to respect holds | 3 | P1/C, R1/B, F1/A | V3-R2 names only `debit` and `transfer`, and V8-R1 says `withdraw` checks the balance. Behaviour changed without a requirement. The same change was **recorded as an assumption** in 6 units, and declined and escalated in 2. R1/C and R1/D also presented it as settled, but those decisions were outside the 25% Layer 3 sample |

### 3.4 Unsupported decision rate (UDR) by arm

UDR here is Layer 3-confirmed unsupported decisions over decisions. The weighted rate accounts for stratified
sampling: the fault stratum is fully reviewed, the rest is sampled.

| Arm | Decisions | Reviewed | Unsupported (reviewed) | Rate in review (Wilson 95%) | Weighted population rate |
|---|---|---|---|---|---|
| A short-lived | 122 | 62 | 1 | 1.6% (0.3–8.6%) | 0.8% |
| B long-lived | 113 | 52 | 4 | 7.7% (3.0–18.2%) | 7.9% |
| C + Ordo | 70 | 15 | 1 | 6.7% (1.2–29.8%) | 6.7% |
| D full Echelon | 106 | 50 | 1 | 2.0% (0.4–10.5%) | 0.9% |
| DR reconstructed | 30 | 23 | 1 | 4.3% (0.8–21.0%) | 3.3% |

- **A vs B:** 1/62 vs 4/52, Fisher exact two-sided p = 0.18. **Not distinguishable.**
- **H3 (Ordo controls lower UDR):** neither supported nor refuted. C and D have 1 each, B has 4, and the intervals
  overlap widely.
- **Hallucination class** (fabricated premise, stale decision, false completion claim): 0/202 reviewed. The 95%
  upper bound is 1.5% per decision. All 441 decisions passed Layer 1 evidence existence.

### 3.5 Fabricated premises versus reasoning errors versus defects

The protocol separates three things: fabricated premises (hallucination), reasoning errors, and ordinary defects.

- **In VAC-001:** none of the three was observed by any layer.
- **Dominant failure:** **scope expansion presented as settled**. It is neither fabrication nor a defect. The code
  was correct and the oracle passed, but the decision went beyond the requirement without saying so.
- **Detection:** no deterministic detector in the pipeline catches it. The oracle cannot, because no case covers
  the added behaviour. Layer 1 cannot, because the cited files exist. Only Layer 3 review found it.

## 4. Decision drift (DDR)

| Measure | Result |
|---|---|
| Established decisions checked | The 5 base records, plus the task decisions (DEC-V4, V5, V6, V8) once their task was accepted |
| Reversals | **0** across all 96 units (oracle cases of every earlier decision passed at every later unit; AR-3 and AR-4 never violated) |
| F2 (rejected decision reintroduced) | Refused in 4/4 arms, each citing the accepted design note |

**Governance gap found.** In C, D and DR, agents added their own records to `DECISIONS.md` with status `accepted`.
Examples are DEC-V1-STORE-CLOSE and DEC-V3-STORE-HOLDS. A later reader, human or agent, sees an accepted decision
that nobody authorized. The prototype's verified state then counted citations of these records as valid evidence.

This is not drift; the decisions were not reversals. It is a path by which **unsupported decisions become
"established"**. Recommendation **R-ORDO-2**: records written by the implementing agent enter as `proposed`, and
only an authorizing actor or an independent check moves them to `accepted`.

## 5. Accumulated context versus hallucination (secondary question 3)

| Arm group | Prompt growth | Units | Fabrications | Stale or false claims |
|---|---|---|---|---|
| Long-lived (B, C, D) | to 131–167k | 64 | 0 | 0 |
| Fresh (A, DR) | flat 60–91k | 32 | 0 | 0 |

**Accumulated context did not measurably increase hallucination within 167k tokens.** Unsupported scope additions
were somewhat more frequent in B (4/52 reviewed) than in A (1/62), but the difference is not significant
(p = 0.18).

Directional only: the long-lived agents more often extended a rule across features they had built earlier. In 7 of
8 long-lived V3 units, `withdraw` was made to respect holds. Fresh agents (A, DR) did the same in 3 of 4. This is
consistent with continuity carrying cross-feature intent, which is helpful for coherence but is scope expansion
unless recorded. It is not evidence of fabrication.
