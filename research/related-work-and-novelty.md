# Related Work and Novelty Assessment

**Date:** 2026-10-14  
**Status:** Initial literature review. Claims of novelty are provisional; this is not a systematic review.

## Executive conclusion

Cohort-Based Engineering (CBE) is **not novel merely because it groups related agent tasks**. Cohesion-aware partitioning, context sharing, lightweight agents and Git-based coordination are active research areas. The most defensible potential contribution is a **requirements- and decisions-aware engineering operating model** that optimizes cumulative cost **subject to independent per-requirement quality and architecture constraints**. That differentiation must be validated, not asserted as unique.

## Closest work

### 1. Co-Coder: cohesion-aware task partitioning (Yang et al., 2026)

- Paper: https://arxiv.org/abs/2606.00953
- Code: https://github.com/Flitternie/CoCoder
- Approach: static-analysis dependency graph, structural hub isolation, community detection and dependency-aware scheduling; explicitly balances parallel critical path against cross-partition context transfer.
- Reported results: on 28 DevEval and CodeProjectEval tasks, up to 2.10x wall-clock speedup, 35% API-cost reduction and 14-point pass-rate improvement over specified baselines. These are **authors' results**, not reproduced by Echelon.
- **Substantial overlap:** cohesion-based decomposition, graph planning, context-transfer economics and scheduling.
- **Candidate CBE extension:** planning over requirement/decision/invariant graphs, immutable traceability and independently verified acceptance, rather than primarily static code dependency graphs.
- **Design consequence:** evaluate graph partitioning and hub-file isolation as baselines; do not reinvent a graph algorithm without comparison.

### 2. DeLM: decentralized multi-agent shared context (Mao et al., 2026)

- Paper: https://arxiv.org/abs/2606.10662
- Code: https://github.com/yuzhenmao/DeLM
- Approach: agents use a shared verified context and task queue, publishing reusable intermediate observations to reduce duplicate work and controller bottlenecks.
- The paper reports roughly 50% lower cost per SWE-bench Verified task versus its baselines; results are task- and protocol-specific.
- **Overlap:** verified context reuse, coordination overhead, bounded knowledge transfer.
- **Difference:** DeLM studies agent-level execution and shared context, not a complete requirements-to-delivery governance and acceptance model.
- **Design consequence:** compare continuity, typed handoffs and shared verified context; avoid presuming that a central orchestrator or separate handoff always wins.

### 3. Peer-aware Action-Space Coordination (PASC), ESEM 2026

- Conference: https://conf.researchr.org/details/eseiw-2026/eseiw-2026-esem---technical-track/18/Coordinating-Agents-on-a-Shared-Git-Workspace-An-Empirical-Study-of-Action-Space-Obs
- Approach: agents observe commits, lifecycle transitions and test/error output in a shared Git workspace rather than depending on natural-language coordination.
- **Overlap:** Praxis's commit-mediated progress and coordination, machine-observable state.
- **Difference:** focus on collaborative bug fixing and shared-workspace coordination, not semantic requirement cohort formation.
- **Design consequence:** benchmark structured shared state and commit signals against verbose natural-language handoffs. Preserve write isolation and collision safety.

### 4. Agentless (Xia et al., 2024)

- Paper: https://arxiv.org/abs/2407.01489
- Approach: constrained localization, repair and validation instead of a complex autonomous tool-using agent.
- Reported original SWE-bench Lite result: 32% (96 fixes), approximately $0.70 per issue under the authors' evaluation.
- **Overlap:** prefer a small deterministic/constrained workflow where it suffices.
- **Difference:** primarily software repair, not multi-requirement construction cohorts.
- **Design consequence:** always include simple, constrained or single-agent baselines, not only multi-agent variants.

## Comparison matrix

| Dimension | Co-Coder | DeLM | PASC | Agentless | Proposed CBE |
| --- | --- | --- | --- | --- | --- |
| Cohesion/dependency partitioning | Central | Task queue, not primary contribution | Limited | No | Central |
| Context reuse / communication economics | Central | Central | Central | Simplification | Central |
| Git/action-state coordination | Not defining feature | Shared notes/queue | Central | No | Praxis option |
| Approved requirement/decision traceability | Not established by reviewed abstract | Not established | Not established | Not established | Required |
| Independently verified each source requirement | Not established | Benchmark evaluation | Bug-fix evaluation | Patch validation | Required |
| Human governance separate from agent cadence | Not established | Not primary focus | Not primary focus | Not primary focus | Proposed |
| Quality-constrained cumulative provider economics | Cost and pass rate measured | Cost and success measured | Coordination outcomes | Cost and fixes | Proposed primary objective |

**Interpretation:** 'Not established' means not demonstrated by the materials examined here, **not** that a project lacks the feature.

## Echelon internal evidence

- [Praxis A021](https://github.com/kemiller2002/praxis/pull/132): grouped high-affinity work $9.48 versus $21.51; 61 versus 112 minutes. Grouped architecture was more consistent, independent work more faithful to some individual criteria.
- [A021 R2 preservation](https://github.com/kemiller2002/praxis/pull/145): second same-direction high-affinity result, low confidence.
- [Praxis A024](https://github.com/kemiller2002/praxis/pull/205): continuous $8.27, fresh code-only $15.30, structured handoff $17.43; all 36/36 acceptance; blinded architecture 5/10, 10/10, 8/10. This contradicts a simplistic assumption that context continuity automatically improves quality or that handoffs automatically save money.
- [Ordo pattern recognition](https://github.com/kemiller2002/ordo/pull/77): deterministic recognition demonstrated; end-to-end agent-cost savings still unproven.

## Proposed contribution claims and required evidence

1. **Requirements-aware cohort planning:** show an explicit source-requirement/approved-decision graph improves cohort choices beyond code-dependency partitioning. Compare against Co-Coder-style static graph baselines.
2. **Quality-constrained economics:** demonstrate lower *total provider cost per independently accepted requirement*, including retries, repairs and integration, without reducing architecture quality. Measure and blind-score quality.
3. **Cohort execution as an operating model:** demonstrate a reproducible method connecting human outcome approvals, machine execution boundaries, and continuous evidence-based integration.
4. **Adaptive context and checkpoints:** demonstrate that continuity/split/checkpoint decisions improve cumulative economics versus fixed-size batching, fixed compile cadence and code-only fresh agents.

These are **testable hypotheses**, not proven firsts or patentability claims.

## Changes recommended to the CBE experiment

- Add a **Co-Coder-inspired static dependency partitioner** as a comparator, in addition to requirement-at-a-time and fixed-size batches.
- Add a **shared verified context** arm or ablation inspired by DeLM when resources allow.
- Compare **commit/action-state** communication against typed handoffs where multiple agents truly need coordination.
- Stratify high- and low-affinity workloads; freeze the cohort eligibility rules before executing.
- Pre-register quality non-inferiority thresholds. An arm that is cheaper but materially worse in architecture does not win.
- Separate **cohort selection** from **agent continuity** and **parallel scheduling** through factorial or ablation designs.
- Include at least two external-to-Praxis application domains, and publish failures, repairs, cumulative tokens/cost, human interventions and integration effort.

## Cautions and further review

This review uses public paper abstracts, conference descriptions and project documentation, not a comprehensive reproducibility audit of their source code and experimental data. Benchmark tasks, model choices and accounting methods differ; **do not compare their percentage gains directly with Praxis's 56% result**. Expand the review with detailed methodology, threats to validity, licensing, related surveys, and historical work on modularity, graph partitioning, team coordination and lean flow before any formal publication.

## Research decision

**Proceed with CBE as an integrative, empirically falsifiable methodology.** Do not claim invention of cohesion-aware agent task partitioning. Focus research investment on requirements/decision traceability, independent verification and measured end-to-end economics.
