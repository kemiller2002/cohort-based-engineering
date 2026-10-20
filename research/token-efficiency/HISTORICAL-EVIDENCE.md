# Historical token-efficiency evidence (Worker B audit)

Date: 2026-10-20. Scope: Praxis, Ordo, Dokimos, Visual Engineering and Cohort-Based Engineering history,
covering claims and experiments about agent token efficiency. Per-phase profiling of REL-001 run-01 and
run-02 belongs to Worker D and is not repeated here.

Machine-readable index: [`evidence-index.json`](evidence-index.json) (schema `cbe.token-evidence-index/1`, 20 entries).

## Method and conventions

- **Total tokens** = input + output + cache-read + cache-write, summed over the sessions named. The two
  cache buckets are kept separate from input and never folded in.
- **Sources.** Platform figures are `get_session external_metadata.usage` as committed in each
  experiment's `sessions.json` or run record. Transcript figures are self-measured by
  `session_metrics.py`, and their output tokens are a lower bound.
- **Deltas.** `deltaPct` = (treatment − baseline) / baseline. This audit recomputed it from the raw files,
  and only where the model, toolchain, cohort and measure match.
- **What is not evidence here.** Platform USD is quoted only as a cross-check. No saving is inferred from
  elapsed time, or from a prompt simply being smaller.
- **Cache reads dominate every total.** For example, they are 98.4% of the A021 grouped total. Raw token
  totals therefore overweight cheap cached prefix, so cost-weighted comparisons need a versioned price
  table (REL-001 F5, now `research/pricing/anthropic.price-table.json` on the run-02 branch).

## Counts by classification

| Classification | n | Entries |
|---|---|---|
| demonstrated-improvement | 3 | TE-H01, TE-H02, TE-H03 |
| demonstrated-regression | 2 | TE-H04, TE-H07 |
| inconclusive | 5 | TE-H05, TE-H06, TE-H08, TE-H09, TE-H10 |
| implemented-unmeasured | 6 | TE-H11, TE-H12, TE-H13, TE-H14, TE-H15, TE-H19 |
| proposed-unimplemented | 4 | TE-H16, TE-H17, TE-H18, TE-H20 |

## Comparable observations (same model: claude-opus-5-5)

| ID | Experiment | Baseline → Treatment | Metric | Baseline | Treatment | Δ | Confidence |
|---|---|---|---|---:|---:|---:|---|
| TE-H01 | A021 (praxis) | 5–7 fresh sessions → 1 grouped session | platform total tokens | 46,270,704 | 24,911,173 | **−46.2%** (−38.7% vs completed sessions only) | medium |
| TE-H02 | A021-R2 | 5 fresh workers → 1 grouped | platform total, workers only | 55,640,723 | 28,359,020 | **−49.0%** | medium |
| TE-H03 | A024 A vs B | 5 code-only resets → 1 continuous | platform total, completed | 34,061,674 | 20,260,436 | **−40.5%** | medium |
| TE-H04 | A024 C vs B | code-only resets → resets + structured handoff | platform total, completed | 34,061,674 | 37,629,623 | **+10.5%** | low |
| TE-H07 | REL-001 run-01 D | Praxis 3.12 → verified completion (3.16/Dokimos/Ordo) | tokens / verified requirement | 205,274 | 270,402 | **+31.7%** (exploratory) | medium |

Supporting raw observations:
- **Discovery (A024).** File reads plus searches: A 112, B 263, C 276. Paths re-read across sessions:
  A 0, B 18, C 20. Governance reads: A 6, B 16, C 21.
- **Repeated reads (A021).** AGENTS.md was read 1 time (grouped) against 5 times (control). Model
  requests: 114 against at least 237.
- **Tool and test overhead (REL-001).** Tool calls per run went from 7.3 to 10.0, and test runs per run
  from 1.0 to 2.17.

## Inconclusive, unmeasured and proposed

- **TE-H05 and TE-H06: A022 2×2 (sealed).** Values withheld by the coordinator. A022 is blinded and
  unsealed results do not exist yet. The audit found that condition labels can be inferred from cohort
  item IDs and the `g` versus `w1..w5` metrics file names, so condition-mapped totals are not published.
  That inferability is a **blinding-leak finding** for A022's owners. Condition D is also incomplete
  (4 of 5 workers measured).
    covers only 4 of 5 workers. No delta is computed.
  - The direction is consistent with HY-ROS-2026-A029 (cohesion moderates the benefit).
  - The results record is still sealed. This audit inferred which run belongs to which condition from the
    cohort item IDs and the `g` versus `w1..w5` metrics files.
- **TE-H08: CONSTRUCT-008, mechanical-first versus conventional.**
  - Ordo claims the effect changes sign with the structure ratio: −4%, −13.6%, +14% and +8%/+33% across
    four slices.
  - The 0.45 threshold is fitted in-sample.
  - The raw data is in `research-documents`, which is not attached, so these figures are unverified.
- **TE-H09 and TE-H10: Ordo boundary hardening.**
  - The preregistered n was never reached, the within-condition spread is about the size of the gap, and
    the last pair reversed.
  - Experiment 3's −68% token figure counts only the resumed portion of the run, and its own record says
    it must not be cited.
- **TE-H11: orchestration waste (measured, not yet fixed).**
  - A021 control spent 5.66M tokens (12.2% of the arm) in stalled or permission-blocked sessions.
  - A024 spent 0.87M tokens in stale-launcher sessions.
  - A022 hit repeated stale-checkout repairs and a 4-day usage-limit pause, after which sessions resumed
    and had to re-pay the cache.
- **TE-H12 to TE-H15: implemented but not measured.**
  - TE-H12: compact typed construction handoff (praxis#263).
  - TE-H13: mechanical-first routing (DF-ROS-2026-A072). Its routing record reports reasoning tokens as
    `unavailable`.
  - TE-H14: cumulative usage attribution (EV-ROS-2026-A076), a validated measurement capability.
  - TE-H15: provider usage pacing, which spreads usage over the quota window rather than reducing it.
  - TE-H19: REL-001 F4 (one test run, derived completion arguments) shipped in Praxis 3.17.0
    (PRAXIS-REL-012). Its only measurement is REL-001 run-02 arm D, which is in progress.
- **TE-H16 to TE-H20: proposed or absent.**
  - TE-H16: A023 is proposed.
  - TE-H17: A022 on main failed its target-repository gate.
  - TE-H18: HY-ROS-2026-A024 (structural locality) has no experiment.
  - TE-H20: no experiment anywhere manipulates **batched compilation** or **prompt caching** directly.
    Build counts change only as a side effect of grouping.
- **Visual Engineering.** No token experiments. `experiments/` holds user-test machinery that has not run,
  and `.ros/telemetry` is routine execution telemetry with no baseline or treatment.

## Observed results versus claims

- **Observed (raw files present).** TE-H01 to TE-H04 and TE-H07, plus the waste figures in TE-H11.
- **Claimed only.** These have no raw data available to this audit:
  - the CONSTRUCT-008 slice percentages (TE-H08);
  - the "56% lower cost" (A021) and "58.7%" (R2) figures, which are platform USD and are consistent with
    the token deltas above;
  - the PGEI mechanism (EV-ROS-2026-A063), which is an interpretation, not a measurement.

## Cross-cutting confounders

1. **Treatment bundling.** The grouped arms in A021 and R2 combine shared context, an up-front written
   cohort analysis and single-session continuity. A024 arm A drops the written analysis but keeps the
   token benefit, which suggests continuity is the token driver and the analysis mainly affects
   architecture.
2. **One cohort family.** A021, R2 and A024 all implement PRAXIS-GROUP-01..05 in one repository. Only
   A022 (the PRAXIS-CTL cohort) is a different subsystem.
3. **Quality does not track tokens.**
   - A021 and R2: the grouped arm had the more coherent architecture.
   - A024: the reverse (continuous architecture score 5, code-only 10).
   - Correctness was at ceiling in A024 and REL-001.
4. **Orchestration defects inflate the baseline arms.** Stale checkouts, permission stalls and launcher
   pinning all count against the many-session arm.
5. **Shared prompt cache in REL-001.** Sub-agents share one orchestrator's cache, so no trial started cold.

## Ranked opportunities (expected value × confidence)

EV is the expected token reduction for routine Echelon agent work if the mechanism is adopted.
Confidence comes from the evidence above.

| Rank | Opportunity | Expected value | Confidence | Score | Evidence | Next action |
|---|---|---|---|---|---|---|
| 1 | **Execute high-affinity cohorts in one long-lived session** (continuity), still committing and checkpointing incrementally | High (−40% to −49% in 3 of 3 comparable runs, one cohort family) | Medium | **High** | TE-H01, TE-H02, TE-H03 | Make continuity the default for planner-rated `high` affinity groups. Keep the per-member criterion check (A021 lesson). Complete and unseal A022 to test other cohorts and quality. |
| 2 | **Cut verified-completion protocol overhead**: one test run, derived completion arguments, fewer tool calls | High (recovers part of +31.7%; test runs 2.17 → 1) | Medium | **High** | TE-H07, TE-H19 | F4 shipped in Praxis 3.17.0. Measure it via the REL-001 run-02 preregistered analysis (arm D vs C), then run-03. |
| 3 | **Eliminate orchestration waste** (stale checkouts, permission stalls, launcher pinning, resume after pause) | Medium (12% of A021 control arm; 0.9M in A024) | Medium | **Medium-high** | TE-H11 | Add a start-head guard and pre-granted permissions to every fan-out harness. Count failed-session tokens as a first-class metric. |
| 4 | **Do not split work at low affinity**, or bound cohort size by measured context pressure | Unknown until A022 is unsealed | Low | **Medium** | TE-H05, TE-H06 (sealed) | Complete A022 condition D, worker 5, and unseal. Until then treat affinity as the gate for grouping. |
| 5 | **Cheaper fresh-session bootstrap** (reduce repeated governance and repository discovery), but not via the A024 handoff format | Medium (B re-read 18 paths across sessions; governance reads 16 against 6) | Low | **Medium-low** | TE-H03, TE-H04, TE-H18 | Design and test a different context pack (retrieval-indexed or a precomputed governance digest) against code-only resets. The A024 structured handoff added +10.5%. |
| 6 | **Route by structure ratio** (mechanical-first when ratio ≥ 0.45) | Low-medium (±4–14% by slice) | Low | **Low** | TE-H08, TE-H13 | Attach `research-documents` and verify the CONSTRUCT-008 usage.json files. Add an out-of-sample slice. |
| 7 | **Cost-weighted, cache-aware metric** (versioned price table, cache-write TTL split) | Enabler (raw totals are about 98% cache reads) | High (measurement validated, TE-H14) | **Enabler** | TE-H14, TE-H07 | F5 price table exists (PRAXIS-REL-013). Report cache-write and output separately from cache-read in every comparison. |
| 8 | **Boundary hardening for agent cost** | Unknown | Low | **Low** | TE-H09, TE-H10 | No action until an adequately powered rerun. Do not cite Experiment 3. |
| 9 | Batched compilation, prompt-caching strategy, structured agent messaging beyond handoffs | Unknown | None | **Unscored** | TE-H20, TE-H12 | Design isolated manipulations. Today their effects show up only as side effects of grouping. |

## Follow-up repositories (not attached; not cloned)

- `kemiller2002/research-documents`: CONSTRUCT-008 and CONSTRUCT-010 harnesses, `usage.json` and
  `transcript.jsonl` for the A/B/C runs (TE-H08), and timer pilot 01.
- `construct-010-trials`, if separate: the CONSTRUCT-010 phase trials cited by EV-ROS-2026-A076.
