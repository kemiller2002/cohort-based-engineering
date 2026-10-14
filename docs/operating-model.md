# Operating model

**Status:** Proposed, not deployed.

## Units and responsibilities

- **Outcome:** human-approved business capability and success measure.
- **Requirement:** smallest individually traceable obligation; never silently merged away.
- **Cohort:** coherent, bounded execution package with a shared domain model, interfaces, decisions and acceptance contracts.
- **Checkpoint:** evidence-bearing construction boundary, not a sprint ceremony.
- **Release:** integration of independently verified cohorts.

Human stakeholders own priorities, policy and risk acceptance. Agents may propose decisions, never silently authorize them.

## Lifecycle

1. **Ingest:** Conditor/Signal collect source requirements, provenance, decisions, constraints, acceptance criteria and dependency links.
2. **Normalize:** Ordo creates a versioned semantic representation, preserving an explicit source-to-derived requirement mapping.
3. **Plan globally:** identify domain boundaries, shared invariants, interfaces, risk, dependency edges and work suitable for deterministic construction.
4. **Form cohorts:** Praxis proposes cohesive groups with rationale, expected cost, estimated context load, allowed paths and cross-cohort contracts. A human approves consequential boundary or policy decisions.
5. **Prepare:** pin inputs and decisions; freeze acceptance obligations; recognize constructible/delegated/blocked work; publish a bounded execution contract.
6. **Execute:** keep one construction context for tightly coupled work where feasible. Delegate separately only when justified by cohesion, safety or capacity. Do not use one fresh agent per requirement by default.
7. **Check:** compile shared contracts early; compile after coherent dependency milestones; run focused tests during implementation. Failed checkpoints require bounded repairs and explicit disposition.
8. **Verify independently:** Dokimos evaluates behavior, architecture, requirement coverage, provenance, negative tests and adversarial properties. An implementation cannot approve its own evidence.
9. **Integrate:** verify cross-cohort contracts and changes against current target; reject stale or conflicting assumptions.
10. **Learn:** record provider tokens and cost, agent time, host time, context reads, first-pass acceptance, repair cycles, defect escapes and cohort-affinity predictions.

## Team topology

Roles are capabilities, not mandatory separate paid agents:

- **Planner:** produces graph, cohort boundaries and execution order.
- **Constructor:** implements within one coherent context; can use Ordo-generated components.
- **Verifier:** independently checks requirement-by-requirement acceptance and architecture.
- **Integrator:** validates shared interfaces and merge safety.
- **Researcher:** investigates uncertain or novel constraints; produces evidence, not unauthorized policy.

Prefer the fewest sessions consistent with independent verification. Avoid unnecessary serial handoffs.

## Human governance versus execution cadence

Humans can keep weekly planning and demonstrations without turning them into execution gates. A cohort is eligible for integration whenever its independently checked obligations pass. No requirement is considered complete merely because its cohort compiled.

## Failure policy

- Missing policy or contradictory requirements: **DecisionRequired**, not guessed implementation.
- Unsupported but decided behavior: **Delegate** with typed contract.
- Unsafe ownership or unresolved dependency: **Blocked** for affected scope.
- Verification failure: repair within bounded budget, then escalate.
- Context exhaustion: split at a semantic seam; hand over decisions, requirements, interfaces, acceptance and provenance, not an unstructured transcript.

## Initial non-goals

No fixed ideal cohort size, no requirement that all work use one agent, no replacement for human product prioritization, no automatic authorization of business decisions, and no claim that structured handoffs are inherently cheaper.
