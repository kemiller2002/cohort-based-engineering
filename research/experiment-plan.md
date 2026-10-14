# CBE experimental program

**Status:** Proposed protocol, not preregistered or run.

## Question

Does affinity-based cohort execution reduce cumulative cost per independently accepted requirement while preserving or improving correctness and architecture quality, compared with requirement-at-a-time execution and fixed-size batching?

## Existing evidence

- [A021 grouping experiment](https://github.com/kemiller2002/praxis/pull/132): $9.48 grouped vs $21.51 independent; 61 vs 112 minutes; quality tradeoff, one high-affinity cohort.
- [A021 R2 preservation](https://github.com/kemiller2002/praxis/pull/145): same-direction high-affinity replication; low confidence.
- [A024 context continuity](https://github.com/kemiller2002/praxis/pull/205): continuous $8.27, code-only resets $15.30, structured handoff $17.43; 36/36 criteria in each; architecture 5/10, 10/10, 8/10. Structured handoff advantage not supported.
- [Ordo recognition](https://github.com/kemiller2002/ordo/pull/77): cheap bounded classification; not an agent-cost result.

## Arms

A. **Requirement-at-a-time:** fresh execution context per requirement, same frozen inputs and verification.
B. **Fixed-size batches:** size chosen and frozen before scoring; do not tune using test outcomes.
C. **Affinity-based cohorts:** deterministic, pinned planner with explicit constraints and continuity policy.
D. **Optional ablation:** same cohorts as C, but fresh agents per requirement, to separate affinity from continuity.

## Design

Use at least two independent application domains and multiple high- and low-affinity cohorts. Freeze requirements, decisions, acceptance oracles, model/provider, environment, repository commit, tool versions and scoring rubric before runs. Randomize arm order, use isolated workspaces, blind architecture review, and preserve all failed runs. Treat experimental repeats as repeated observations, not independent projects.

Define eligible workload and number of replications before execution. The earlier A022 attempt failed its target eligibility gate; do not quietly weaken that gate or call A023 completed.

## Metrics

**Primary:** total provider-reported cost per independently accepted requirement or cohort, including discovery, handoffs, subagents, retries and repairs. If cost is missing, separately report a prespecified cumulative token proxy and its limitations.

**Quality guardrails:** per-requirement frozen acceptance, first-pass pass rate, escaped defects, adversarial checks, architecture rubric and unauthorized changes.

**Secondary:** wall time, host compile/verify time, cache read/write tokens, repeated context reads, tool calls, session count, handoff bytes, integration conflicts, human interventions, and context compaction.

Cost buckets must not double count parent/child requests; do not equate output tokens, handoff file size or GitHub Actions runs with full provider cost.

## Hypotheses

- H1: Affinity-based cohorts lower total cost per accepted requirement relative to A.
- H2: Cohort affinity predicts relative benefit better than raw batch size.
- H3: Independent verification prevents grouped execution from sacrificing acceptance and architecture.
- H4: Adaptive checkpoints reduce total compile-plus-repair overhead versus compile-after-every-item and compile-only-at-end.
- H5: Typed handoffs are valuable at genuine context/ownership boundaries, but not automatically cheaper than continuity.

Pre-register effect thresholds, stopping rules and falsification criteria with the lead researcher **before** collecting scored outcomes. Publish raw telemetry, failures, blind assessments and confidence limitations.

## Decision policy

Adopt a scheduling rule only if it passes quality guardrails and shows repeatable cost/time benefit across domains. If an optimization improves cost but degrades architecture, retain it only with an independently validated mitigation and report the combined cost.
