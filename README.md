# Cohort-Based Engineering (CBE)

**Status:** Research and design proposal, 2026-10-14.

Cohort-Based Engineering is a proposed method for building software with AI-assisted teams. Its central rule is:

> Requirements are units of accountability. Coherent requirement cohorts are units of planning, context, construction, and verification.

CBE separates human governance cadence from machine execution cadence. Humans approve outcomes, constraints and consequential decisions; machines plan and implement cohesive work with bounded authority and independently verifiable evidence.

## Why

A requirement-at-a-time, fresh-agent workflow repeatedly incurs repository discovery, domain comprehension, decision interpretation, and integration costs. Yet large undifferentiated batches increase context pressure, conflict and quality risk. CBE optimizes **cohesion**, not merely batch size.

## Principles

1. **Plan globally, execute in cohorts, verify independently.** Analyze the full requirement and dependency graph before execution.
2. **No requirement disappears.** Every source requirement retains a stable identifier and explicit disposition through construction, delegation, verification and delivery.
3. **Decisions precede implementation.** Never invent unresolved business policy. Record decisions with ownership, authorization, rationale and affected requirements.
4. **Cohesion defines execution boundaries.** Group by domain invariants, shared interfaces, dependencies and decisions; separate unrelated work even if it fits a numerical batch limit.
5. **Preserve useful context.** Prefer continuity within a cohort. Handoffs are bounded, typed and used when ownership, safety, context pressure or parallelism justify them.
6. **Deterministic where proven, agents where necessary.** Ordo recognizes supported construction contracts quickly; Praxis delegates unsupported work without repeated failed generation.
7. **Quality is independent of authorship.** Dokimos checks contracts, behavior, architectural constraints and adversarial cases for both generated and agent-authored code.
8. **Adaptive checkpoints.** Compile when shared contracts stabilize, after dependency groups, and when risk warrants it; full acceptance at cohort completion.
9. **Integrate on evidence, not sprint dates.** Completion requires explicit requirement coverage, accepted tests, architectural checks and provenance.
10. **Optimize accepted outcomes.** Measure total provider cost, time, repairs, first-pass acceptance, architectural quality and human intervention. Reject apparent savings that degrade correctness.

## Evidence and uncertainty

- Praxis EX-ROS-2026-A021: grouped related work cost $9.48 versus $21.51 for independent execution, and took 61 versus 112 minutes. Grouping yielded more consistent architecture, while independent work better satisfied some individual criteria. One experiment; causal confidence limited.
- A021-R2 replication: same-direction result for high-affinity work, still low confidence and with deviations.
- Praxis EX-ROS-2026-A024: continuous context cost $8.27, code-only resets $15.30, structured handoffs $17.43; all achieved 36/36 frozen acceptance criteria, but blinded architecture scores were 5/10, 10/10 and 8/10 respectively. Structured handoffs did not demonstrate the expected efficiency gain.
- Ordo pattern recognition H0: deterministic classification on four frozen cohorts was under one second per cohort including startup; Dokimos audits found zero findings. This is **not** a demonstrated end-to-end cost reduction.
- The high- versus low-affinity A022 experiment was blocked by eligibility criteria; A023 was proposed as a successor.

- VAC-001 (verified agent continuity; `research/verified-agent-continuity/`):
  - **Design.** 96 chained units on the REL-001 Ledger fixture, scored by a hidden oracle.
  - **Cost.** One continuous agent cost 40.9% less per accepted requirement than a fresh agent per change (CI −48.1% to −33.0%), at equal correctness. Adding Ordo or full-Echelon controls on top of continuity cost +14% to +31%. Rebuilding context from verified state with fresh agents cost +86%.
  - **Reliability.** Correctness, drift and fault rejection were at ceiling in every arm, so no reliability benefit of verified state could be measured.

These observations motivate CBE but do not prove that every cohort size or workload benefits. In particular, cost savings must not be confused with architectural correctness.

## Repository map

- [Operating model](docs/operating-model.md): lifecycle, human roles, agent roles and boundaries.
- [Cohort planner](docs/cohort-planner.md): proposed typed inputs, constraints and scheduling.
- [Experiment plan](research/experiment-plan.md): falsifiable hypotheses, benchmark design and measurements.
- [Adoption roadmap](docs/roadmap.md): phased integration with Ordo, Praxis, Conditor, Signal and Dokimos.

## Related repositories

- [Praxis](https://github.com/kemiller2002/praxis): orchestration, execution, context and cost telemetry.
- [Ordo](https://github.com/kemiller2002/ordo): semantic construction and pattern recognition.
- [Dokimos](https://github.com/kemiller2002/dokimos): independent verification.
- [Research documents](https://github.com/kemiller2002/research-documents): frozen experiments and raw evidence.

This repository defines the proposed **method**. It does not claim to replace those systems or implement their functionality.
