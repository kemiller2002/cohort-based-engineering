# Transitioning Teams from Scrum to Cohort-Based Engineering

**Status:** Proposed organizational adoption framework, 2026-10-14.  
**Audience:** Engineering leaders, product owners, architects, developers, QA and delivery coaches.

## Positioning

CBE does **not** claim Scrum requires one requirement per engineer or prohibits continuous delivery. The target is a common fragmented implementation of Scrum: tickets distributed without regard to semantic cohesion, repeated discovery and handoffs, sprint-end integration, and reporting based on activity rather than accepted outcomes.

The organizational change is to preserve stable human teams and product accountability while replacing ticket-by-ticket execution with bounded, coherent engineering cohorts.

## Operating model changes

| Concern | Common sprint-oriented practice | CBE target |
| --- | --- | --- |
| Planning horizon | Next sprint's tickets | Outcome roadmap plus continuously refreshed requirement/decision graph |
| Execution unit | Story or task | Coherent cohort of related requirements |
| Accountability | Story status and sprint goal | Each requirement's independent acceptance and capability outcomes |
| Coordination | Daily status updates | Exception, decision and integration signals |
| Work allocation | Individuals pull discrete tickets | Team owns a domain cohort with explicit boundaries |
| Integration | Frequently concentrated near sprint end | Integrate verified cohorts when ready |
| Quality | Definition of Done | Versioned acceptance and architecture evidence |
| Metrics | Velocity/points | Accepted outcomes, cycle time, total cost, rework and escaped defects |

## Five-stage migration

### Stage 0: Baseline and consent (2–4 weeks illustrative)

Choose one willing product team and one coherent domain area. Explain the change as an experiment, not a productivity mandate. Collect a baseline on lead time, rework, context switches, waiting for decisions, integration conflicts, first-pass acceptance and defects. Preserve a control or historical comparison where possible. Record qualitative team experience and stakeholder satisfaction.

**Exit gate:** team and sponsor agree on a narrow pilot, baseline and safety/quality guardrails.

### Stage 1: Cohort planning within Scrum (2–3 sprints illustrative)

Keep existing ceremonies. At refinement, identify domain invariants, shared decisions, interfaces and dependency clusters. Group related stories into one bounded cohort while retaining individual requirement IDs and acceptance criteria. Make cross-team contracts and unresolved decisions visible before implementation.

**Exit gate:** teams can form cohorts reproducibly without losing requirement traceability; no increase in blocked work or defect escapes.

### Stage 2: Continuous cohort execution (4–6 weeks illustrative)

Keep human product reviews on a predictable cadence, but permit cohorts to start, checkpoint, integrate and ship independently of sprint boundaries. Use WIP limits at cohort level. Preserve continuity of domain understanding. Split only at justified seams, not because a calendar interval ended.

**Exit gate:** reduced context reacquisition and waiting time, with stable or improved acceptance and architecture quality.

### Stage 3: Evidence-based governance (4–8 weeks illustrative)

Replace status-only reporting with requirement acceptance ledgers, architecture verification, decision latency, repair cost and integration readiness. Keep human approval for policy, risk and business tradeoffs. Make independent verification and rollback capability mandatory.

**Exit gate:** stakeholders can inspect delivered evidence without relying on ticket counts or unverified agent claims.

### Stage 4: Scale by domain and interface

Retain stable domain teams. Coordinate cross-domain cohorts using named interface owners and integration contracts. Expand only where measured outcomes and team feedback justify it. Keep a reversible path to prior practice.

**Exit gate:** repeatable benefit across at least two teams/domains, without quality degradation or unsustainable coordination burden.

## Team roles

- **Product owner / outcome steward:** sets business outcomes, priorities and acceptance intent; approves policy tradeoffs.
- **Engineering lead / cohort steward:** owns cohort boundaries, WIP, dependencies, technical decisions and safe integration.
- **Engineers / constructors:** build and evolve the coherent capability, not isolated ticket fragments.
- **Verifier:** independent review of acceptance, architecture, security and adversarial cases; can be an engineer outside the construction context or an automated verifier.
- **Delivery facilitator:** resolves organizational impediments, decision latency and cross-team dependencies. This may be a Scrum Master evolving the role, not necessarily a new position.

Do not prescribe mandatory headcount, permanent agent personas or simultaneous sessions.

## Ceremonies and communication

- **Outcome planning** (weekly or as needed): priorities, decisions and cohort admission.
- **Cohort kickoff** (per cohort): scope, interfaces, invariants, acceptance, ownership and stop conditions.
- **Exception sync** (short, event-driven): unresolved decisions, blocked dependencies, risks and integration conflicts.
- **Capability review** (regular stakeholder cadence): working behavior and independently verified acceptance evidence.
- **Improvement review** (every 2–4 weeks): measured throughput, quality, cost, team experience and experiments.

A daily meeting remains useful if it resolves coordination issues. It should not exist solely to recite ticket statuses.

## Metrics and safeguards

**Primary team-level measures:** elapsed time from ready to independently accepted capability; accepted requirement coverage; defect escape rate; rework hours; waiting/decision latency; integration conflicts; work in progress; and team-reported cognitive load.

**For agent-assisted teams:** total provider cost per accepted requirement including retries, repairs, handoffs and integration; context reads; agent/host time; and independent architectural rubric scores.

Do not compare story points across teams or use agent cost savings as a proxy for human headcount reductions. Pair any efficiency target with non-inferiority guardrails for correctness, security, accessibility, maintainability and team sustainability.

## Example: time-entry lifecycle

**Fragmented approach:** separate tickets for start, pause, resume, stop, persistence, audit and retry semantics are distributed independently, leading to repeated state-machine discovery and possible interface conflicts.

**CBE cohort:** one bounded 'time-entry lifecycle' package covers the shared state machine and invariants. Each original requirement retains its own acceptance oracle. Durable idempotency, authorization and reporting may be separate cohorts only if the interface and decision boundaries are explicit. Compile when shared types stabilize, test transitions incrementally, and independently verify every original requirement before integration.

## Organizational risks and responses

1. **Cohorts become mini-waterfalls:** require bounded WIP, intermediate checkpoints and continuous integration.
2. **Large batches conceal defects:** preserve per-requirement tests, incremental validation and independent review.
3. **One expert becomes a bottleneck:** document approved decisions, pair on critical interfaces and define continuity limits.
4. **Teams lose predictability:** forecast cohort completion probabilistically using historical cycle time; keep stakeholder review cadence.
5. **Management turns metrics into quotas:** use measures for system improvement, not individual performance rankings.
6. **Cross-team cohorts erase ownership:** stable domain teams own interfaces; temporary cohorts never bypass approval boundaries.
7. **Tooling drives the method:** pilot the operating model with existing tools before making Praxis/Ordo integration mandatory.

## Pilot evaluation design

Pre-register one team's baseline and at least one comparable control cohort or phased rollout. Track 6–12 weeks if feasible, accounting for team learning and workload differences. Use mixed quantitative and qualitative evidence. Compare accepted outcomes and repair-inclusive cost, not merely ticket throughput. Interview participants for hidden coordination burden. Publish null and adverse findings.

## Adoption decision

Scale only if acceptance quality and architecture remain non-inferior, cycle time or repair-inclusive cost improves materially, and the team reports manageable coordination and cognitive load. Otherwise revise cohort boundaries or return to the previous execution cadence.

## Relationship to research

See [Related Work and Novelty](../research/related-work-and-novelty.md), [Cohort Planner](cohort-planner.md) and [Experimental Program](../research/experiment-plan.md). The Praxis grouped-agent findings motivate this approach, but **do not prove human teams migrating from Scrum will achieve equivalent savings**.
