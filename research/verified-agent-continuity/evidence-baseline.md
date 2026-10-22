# Verified agent continuity: evidence baseline

Status: **baseline**, 2026-10-21. Written before any VAC-001 trial ran.

**Question.** Can persistent, independently verified engineering state make agent reliability independent of
session length? This file records what existing Echelon evidence already says about that question, and how
strong that evidence is.

**Scope of the discovery pass.** Every repository named in the brief was inspected at the commit below. Owner
`kemiller2002` holds all of them.

| Repository | Commit | Agent-experiment evidence found |
|---|---|---|
| praxis | `986211c` (v3.19.0) | EX-ROS-2026-A020–A024, EV-A059…A076, `.ros/telemetry` (324 records) |
| cohort-based-engineering | `4bc4aee` | REL-001 run-01/02/03, token-efficiency index (TE-H01…H20), reliability readiness |
| research-documents | `f6778c2` | CONSTRUCT-007/008, time-entry-expanded-01, ordo-directed-ui experiments, ai-drift (designed only) |
| percepta | `1eb43a9` | EX-PERCEPTA-2026-0001…0004 (UI semantic contracts; not agent continuity) |
| ordo | `bb43c26` | see "Ordo, Dokimos, Percepta" below |
| dokimos | `04b5f85` | verification observations; completion-verification docs |
| summa, signal, forma | `8b0e93e`, `e19101f`, `b4d2ec2` | none. Copies of the four-tier doctrine only; the canonical copy is `ordo/doctrine/FOUR-TIER-ARCHITECTURE.md` (SDE-DOCTRINE-003 v0.2.1, theory TH-SDE-2026-0001) |
| decision-posture | `92d57d5` | none. The decision-posture model is conceptual |
| visual-engineering | `1bda5ff` | none on agents (EX-VE-TCG-319C and EX-VE-TYP-001 are human-subject UI studies) |

**Ownership correction.** The brief expected Percepta to own experiments and metrics. Percepta is the Echelon
**UI system** repository: its experiments test UI semantic contracts. Echelon's agent reliability, cost and
continuity experiments live in `cohort-based-engineering/research` (REL-001, token-efficiency). VAC-001 is
therefore placed there, beside REL-001, whose fixture it reuses.

## Classification key

| Class | Meaning |
|---|---|
| **Established** | Reproducible evidence supports the conclusion |
| **Promising** | Preliminary evidence exists; replication is insufficient |
| **Inconclusive** | Evidence is missing, conflicting or inadequately controlled |
| **Contradicted** | Evidence opposes the hypothesis |

## Experiments

Every figure below is quoted from the committed file named in its Evidence row. Any figure not recorded there is
marked *not recorded*. Unless a row says otherwise, the model is `claude-opus-5-5`.

### EX-ROS-2026-A021: grouped vs independent execution (R1)

| Field | Value |
|---|---|
| Hypothesis | HY-ROS-2026-A028: one shared context reduces repeated work, improves architectural consistency, or both |
| Method | **Grouped:** 1 session for PRAXIS-GROUP-01..05. **Control:** serial fresh sessions, 7 including 2 failed attempts at item 04. Both arms started at `8b4ffa3` |
| Model / configuration | Claude Code remote, `claude-opus-5-5`; reasoning effort *not recorded* |
| Trials | 1 cohort × 1 run per arm |
| Tokens | Grouped: input 234, output 112,377, cache read 24,507,715, cache write 290,847. Control: output 244,630, cache read 45.1M. Total 24,911,173 vs 46,270,704 (−46.2%) |
| Cost | $9.48 vs $21.51 (platform) |
| Wall-clock | 61 vs 112 min of session time |
| Correctness | Tests at head 811 vs 829. Tests added 19 vs 37. Grouped was more architecturally consistent (1 store vs 3); control met individual criteria more faithfully |
| Verification | Independent Claude evaluator with partial blinding. A second kit evaluation (EV-A067) had its blinding compromised |
| Limitations | One cohort, written by the designer. The treatment bundles shared context, a written group analysis and continuity. Control-05 started from the wrong commit. 0 compactions in either arm |
| Evidence | praxis `research/evidence/EV-ROS-2026-A064`, `research/experiments/EX-ROS-2026-A021-harness/sessions.json`, `-evaluation/` |

### EX-ROS-2026-A021-R2: replication

| Field | Value |
|---|---|
| Method | 5 fresh worker sessions vs 1 grouped session; same cohort as A021 |
| Tokens | Workers 55,640,723 vs grouped 28,359,020 (−49.0%) |
| Cost / time | $26.05 vs $10.75 (control including the orchestrator). 2h23m35s vs 55m53s |
| Correctness | 2 confirmed acceptance defects in each arm. Grouped was stronger on cross-item cohesion |
| Verification | Blind evaluator from a different model family (GPT-5.6 Sol), committed before unblinding. The salt was lost, so the mapping was confirmed by blob identity |
| Limitations | Control items 02 and 03 started from a stale baseline. Same feature family as R1. The evaluator could not build locally |
| Evidence | praxis `EV-ROS-2026-A070`, `EX-ROS-2026-A021-R2-blind/output/` |

### EX-ROS-2026-A024: continuous session vs code-only resets vs structured handoff

This is the closest prior experiment to the present question.

| Field | Value |
|---|---|
| Hypothesis | HY-ROS-2026-A030: fresh agents with a structured durable handoff recover a substantial part of the continuous-context benefit |
| Method | **A:** 1 continuous session. **B:** 5 fresh sessions with code only. **C:** 5 fresh sessions with a schema-validated JSON handoff. All from sanitized start `ddda837` |
| Model / configuration | `claude-opus-5-5`, effort **medium**, auto permission mode, Claude Code 2.1.292→2.1.293 mid-run |
| Trials | 1 execution per arm |
| Tokens | Output A 102,006 / B 163,797 / C 204,253. Total A 20,260,436 vs B 34,061,674 (−40.5%) |
| Model requests | 94 / 231 / 236 |
| Discovery (reads + searches) | 112 / 263 / 276 |
| Cost | $8.27 / $15.30 / $17.43 |
| Wall-clock | 51.2 / 128.7 / 77.9 min (summed) |
| Acceptance | 36/36 in every arm (ceiling) |
| Confirmed defects | 2 / 1 / 1 |
| Architecture composite (blinded) | **A 5, B 10, C 8** |
| Recovery ratio | Recovery(C) = −13/151 ≈ −0.086, against a preregistered 0.50 threshold. HY-A030 **not supported** |
| Verification | Fresh blinded acceptance scorers per snapshot; a blinded rubric evaluator committed before unblinding. All are the same model family as the executor |
| Limitations | Correctness at ceiling. Arm B inherited `.ros/` checkpoint summaries, an informal handoff. A launcher defect caused stale-start sessions (0.87M tokens). Deviation D7: arm-3-04 saw branch names |
| Evidence | praxis `EV-ROS-2026-A074`, `EV-ROS-2026-A075`, `EX-ROS-2026-A024-run/` |

### EX-ROS-2026-A022 and A023

- **A022 (affinity 2×2):** status `blocked` at the target-repository gate since 2026-10-02 (EV-A072). The values
  are sealed, and a blinding leak is recorded. No usable result.
- **A023:** `proposed`. No data.

### REL-001 run-01: verified completion

| Field | Value |
|---|---|
| Method | Praxis 3.12.0 vs Praxis 3.16.0 + Dokimos 0.6.0 + Ordo 1.17.0 |
| Trials | 12 agent trials (3 tasks × 2 arms × 2 replicates), plus deterministic case tables A–C |
| Tokens per verified requirement | 205,274 → 270,402 (+31.7%, bootstrap 95% CI +14.3% to +55.9%). **Exploratory** |
| Correctness | 12/12 vs 12/12; 0 rework; 0 escaped defects |
| Deterministic cases | Duplicate active owners 15 → 0. Invalid contracts accepted 11/11 → 0/11. Unverified completions accepted 8 → 1 (C3b forgery) |
| Verification | Hidden oracle; deterministic case tables |
| Limitations | The preregistered analysis had 0 eligible runs, so it is inconclusive. Ceiling effect. A shared prompt cache, so no trial started cold |
| Evidence | cohort-based-engineering `research/experiments/REL-001/REPORT.md`, `analysis/` |

### REL-001 run-02: four arms, confirmatory

| Field | Value |
|---|---|
| Method | **A** bare Claude; **B** + directives; **C** original Echelon (Praxis 3.16 / Ordo 1.17 / Dokimos 0.6); **D** optimized Echelon (Praxis 3.17 / Dokimos 0.7, attested). One agent per trial, one task per agent |
| Trials | 88 confirmatory (22 blocks × 4 arms, seed 20261020) plus 5 pilot; 0 exclusions |
| Cost per correct requirement | A $0.1147, B $0.1390, C $0.1520, D $0.1555 |
| Tokens per correct requirement | 221,834 / 264,538 / 305,190 / 304,458 |
| Key contrasts | D vs A **+35.5%** (CI +24.9% to +49.5%). D vs C +2.3% (CI −4.8% to +12.1%). B vs A +21.2% |
| Correctness | 39/39 in all arms; first pass 17/17 |
| U6 (two agents, one item) | Duplicate owners: A 2, B 2, C 1, D 0 |
| Verification | Hidden oracle, plus a post-hoc integrity check of all 47 C and D trials |
| Limitations | Single-task agents only, so the trials say nothing about agent lifetime. Time metrics are exploratory: arms ran concurrently from trial 13 (amendment A3). A shared prompt cache |
| Evidence | `REL-001/REPORT-run-02.md`, `run-02/analysis/results.json` |

### REL-001 run-03

Draft and not preregistered; no trial has run. Its fixture (8 F# Ledger tasks V1–V8, a hidden oracle, reference
solutions, wrong-solution traps and Ordo contracts) is the substrate VAC-001 reuses.

### Construction-by-design: CONSTRUCT-007, CONSTRUCT-008, time-entry-expanded-01

| Experiment | Arms | n per arm | Primary tokens (median) | Correctness | Decisions (agent-made unconstrained / system-fixed) |
|---|---|---|---|---|---|
| time-entry-timer-01 (CONSTRUCT-007) | A conventional, B agent plan | 3 | A ~76.9–81.2k; B ~90.0–95.8k | 6/6 at 21/21 | A 25; B 2–3 |
| CONSTRUCT-008 | A, B, C mechanical-first (Ordo plan, typed handoff) | 3 + 3 pilot | 80,468 / 97,862 / 77,168 | 9/9 at 21/21 (Dokimos frozen oracle) | A 25/0; B 2–4/6; C 2–3/19 |
| time-entry-expanded-01 | A, B, C | 3 | 140,654 / 210,383 / 152,370 | First pass 1/3, 3/3, 0/3; final 9/9 | — |
| CONSTRUCT-008 Phase 9 (Chrona) | A vs C | — | 108,747 vs 123,749 | 48/48 | — |
| CONSTRUCT-008 Phase 9 (Summa) | A vs C | — | 128,414 vs 110,930 | 46/46 after erratum E-5 | — |

- **Verification.** An independent Dokimos frozen oracle. Raw `transcript.jsonl` and `usage.json` files are
  committed per run.
- **Limitations.** Fresh single-task agents only. CONSTRUCT-008 arm C silently resolved the D7 rounding tie in
  3/3 runs.
- **Evidence.** research-documents `research/construction-by-design/…`, and
  `echelon-foundry-program/SYNTHESIS-AND-RECOMMENDATION.md`: "correctness preserved but not improved; consistent
  gain is decision control".

### Ordo-directed UI obligation experiments (01–04)

- **Results.** First-pass checks: 8/10 vs 10/10, 10/12 vs 11/12, and 12/12 vs 12/12; condition C 11/12. Tokens
  are *not recorded*.
- **Verification.** Not blind: the same model implemented both conditions and knew the research question.
- **Evidence.** research-documents `visual-engineering/ordo-directed-ui/experiments`.

### Designed, never run

- ordo-foundations EX-01…EX-09. EX-06 is a structured-handoff A/B; its validation note says it "did not perform an
  independent A/B successor-agent trial".
- ai-drift EX-AIDRIFT-001/002 (context dilution).
- REL-001 run-03.

### Ordo EX-SDE-2026-0001 / 0002: cost under boundary hardening (HelixNote)

| Field | Value |
|---|---|
| Method | Paired A/B, one fresh session per run. Cost is read from outside the session (`get_session().external_metadata.usage`, close minus start); the run's self-report is not used |
| Model / configuration | Described as "pinned", but *not recorded* |
| Results | Verified runs: baseline $19.94, $15.92, $20.42 (mean $18.76); hardened $12.66, $14.73 (mean $13.70). Preregistered n=4 not reached. Sensitivity over all complete runs: baseline n=6, mean $20.05; hardened n=5, mean $17.43. Wave 6 reversed (A6 $25.70, B6 $27.15). HY-SDE-2026-0009 stays `proposed` at `very-low` |
| **Self-report accuracy** | Independent re-verification found agent self-reports **wrong**: B1 claimed "96/99", A1 claimed "27/62". A4's void was retracted because its self-report was false |
| Evidence | ordo `research/runs/EX-SDE-2026-0001/run-manifest.json`, `research/evidence/EV-SDE-2026-0007`, `EV-SDE-2026-0009` |

Ordo's HelixNote experiments 1–3 (EV-HN-2026-0003…0005) found a silent-omission probe that the compiler, tests
and runtime all missed. Their token counts are "NOT OBSERVABLE", and Experiment 3's 59/68/59% figures must not be
cited.

### Ordo, Dokimos, Percepta

- **Percepta EX-PERCEPTA-2026-0001…0004** test deterministic UI contract verification and held-out semantic
  generalization. They are not agent-continuity experiments, and they are excluded from the classification
  below. One result is directly relevant to deterministic detectors: EX-0001 detected 13/13 machine-addressable
  mutants, but 2/2 **semantic-substitution mutants escaped and reported complete** (EV-PERCEPTA-2026-0001). A
  deterministic layer has known false negatives on meaning-level errors. No tokens, wall-clock or model versions
  are recorded for any Percepta lane.
- **Dokimos** `research/experiments/` is empty. Its `observations/` are CI self-measurements only.
- **Ordo** is the contract-admission authority used by REL-001 and CONSTRUCT-008: `ordo ecir check --blueprint`,
  and Praxis `ordo contract check`. In REL-001 it refused unresolved-conflict contracts (11/11 invalid → 0/11
  accepted).
- **Dokimos** is the independent oracle and completion verifier: frozen oracles, attested receipts.

## Verification infrastructure: status of the critical gate

The brief forbids treating Praxis or Dokimos completion evidence as trustworthy until the known verification
failures are resolved, or until an independent verifier is available.

| Known failure | Status at praxis `986211c` / CBE `4bc4aee` | Source |
|---|---|---|
| C3b: forged result plus a forged validation event verifies (non-attested) | Fixed only in attested mode; **open** whenever `allowUnattestedEvidence: true` | praxis `docs/verified-completion-rollout.md`; CBE `research/reliability/README.md` |
| REL-GATE-003: `requireVerifiedCompletion` alone accepted forged store evidence | **Resolved** in Praxis 3.19.0 (GATE-A5) | CBE `reliability/README.md`, status update 2026-10-21 |
| REL-GATE-004 / PROBE-3, -4: agent-weakened policy; self-signed trusted receipt | **Resolved** in Praxis 3.19.0 (`POLICY_CHANGED`, `UNTRUSTED_AUTHORITY`) | same |
| Remaining limit: an agent that can rewrite `origin/HEAD`, `origin/main` or history defeats the check | **Open** | same |
| F6 / PRAXIS-REL-006: rollout gate | **Open**; mandatory verified completion is not enabled in any Echelon repository | same |
| Verifier runs under the agent's uid in the harness | **Open** in this container: one uid | `reliability/README.md` (run-02 harness item 4) |

**Decision for VAC-001.** Praxis and Dokimos completion records are captured as **claims**, never as acceptance.
Acceptance comes only from the harness-held hidden oracle and deterministic checks. These run in a directory the
agent is never pointed at, after the agent's turn has ended, on a copy of its committed tree. That independent
verifier makes the experiment possible while the gate stays open. Any measurement that relies on a Praxis or
Dokimos record alone is labelled **unverified**.

## Evidence classification for the VAC research questions

| # | Claim | Class | Basis |
|---|---|---|---|
| P | Persistent verified state makes reliability independent of session length | **Inconclusive** | No experiment has varied session length together with verified state. A024 varied continuity only, over 5 items |
| 1 | Long-lived agents are cheaper per correctly completed requirement | **Promising** | A021 (−46% tokens), R2 (−49%), A024 A vs B (−40.5% tokens, $8.27 vs $15.30), all with equal correctness. But n=1 per arm, with one feature family in R1/R2 and one in A024 |
| 1a | Structured handoffs recover the continuity benefit | **Contradicted** (low confidence) | A024 C vs B: +10.5% tokens; recovery −0.086 against a 0.50 threshold |
| 2 | Continuity reduces unsupported decisions | **Inconclusive** | Never measured. CONSTRUCT-008 shows *decision control* (25 → 2–3 unconstrained decisions) comes from Ordo contracts, not from continuity |
| 3 | Accumulated context increases or decreases hallucination | **Inconclusive** | No hallucination metric in any experiment. Compactions were 0 in every recorded session (A021, A024, praxis telemetry) |
| 4 | Ordo prevents architectural and decision drift | **Promising** for decision and contract admission; **Inconclusive** for drift over time | REL-001 run-01 B: 11/11 → 0/11 invalid contracts accepted. CONSTRUCT-008: unconstrained decisions 25 → 2–3. No longitudinal drift measurement. Silent tie resolution in CONSTRUCT-008 C (3/3) shows Ordo does not catch unmodelled decisions |
| 5 | Praxis and Dokimos prevent error propagation across successive changes | **Inconclusive** | No multi-change propagation experiment. REL-001 shows single-change gating (8 → 1 unverified completions accepted) |
| 6 | Agents recover from incorrect assumptions without discarding valid knowledge | **Inconclusive** | No fault-injection experiment on agents. Percepta EX-0001 injected faults into UI contracts, not into agent context |
| 7 | Optimal balance of lifetime, compaction, verification and cost | **Inconclusive** | REL-001 run-02: verification adds +35.5% cost per correct requirement on single tasks with no correctness gain at ceiling. Its effect on multi-change chains is unmeasured |
| — | Continuity improves architecture | **Contradicted / conflicting** | A021 and R2 favour grouped; A024 reverses it (A 5 vs B 10) |
| — | Agent self-reports of completion are reliable | **Contradicted** | Ordo EX-SDE-2026-0001/0002: self-reported test counts were false in at least 3 runs (B1, A1, A4). Percepta EX-0001: 2/2 semantic mutants reported complete. REL-001 run-01: 8/17 unverified completions accepted at baseline |
| — | Four-tier architecture improves correctness | **Inconclusive** | SDE-DOCTRINE-003 cites HelixNote structure only. No controlled comparison |

## Gaps that VAC-001 must fill

1. **Lifetime variation.** All prior trials are single-task (REL, CONSTRUCT) or 5-item chains with n=1 (A021,
   A024). Nothing yet shows error rate as a function of change index.
2. **Ceiling correctness.** Every prior agent experiment that reached completion scored at or near 100%. A
   continuity effect on correctness needs harder or adversarial units, or cumulative regression checking, which
   no prior experiment ran.
3. **Fault injection into agent context.** Never done.
4. **Decision-level evaluation (UDR, DDR).** Never done. Decision counts exist only as "unconstrained decisions"
   in CONSTRUCT.
5. **Separating verified state from conversation retention.** A024 arm C tested an *unverified*, agent-written
   handoff and found no recovery. No experiment has tested a handoff that an independent verifier gated.
6. **Compaction.** No observed compaction in any record, so compaction effects cannot be estimated from
   existing data.

## Reusable infrastructure (not rebuilt)

| Asset | Reused as |
|---|---|
| REL-001 run-03 fixture: Ledger repo, V1–V8 requirements, visible tests, hidden oracle, references, traps, Ordo `ecir/1` contracts | VAC-001 work units and independent verifier |
| `research/pricing/anthropic.price-table.json` (`2026-10-20.1`) | Cost computation |
| REL-001 run-02 directives pack | Common-baseline instructions in every arm |
| Sub-agent transcript JSONL with per-request `usage` (input, cache write 5m/1h, cache read, output, model, effort) | Token and cost measurement; method as in REL-001 K0 and praxis EV-A076 |
| SDE-DOCTRINE-003 four-tier architecture | Architectural rule set for AVR |
