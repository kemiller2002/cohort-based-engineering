# Adoption roadmap

**Status:** Proposed. No cross-repository changes made by this document.

## Phase 0: method and evidence
- Publish principles, operating model, planner contract, evidence references and open questions in this repository.
- Inventory existing Praxis work grouping, Ordo recognition, Dokimos audits, Conditor decisions and Signal requirement ledgers.
- Avoid a parallel orchestration framework.

## Phase 1: deterministic planning prototype
- Ordo/Conditor: ensure complete source requirement and decision traceability.
- Praxis: build a read-only cohort-plan command over existing work and dependency models.
- Emit rationale, hard-constraint failures, stable cohort IDs and a full requirement disposition ledger.
- Test reproducibility and architectural boundaries before any automatic execution.

## Phase 2: execution policy
- Praxis: use coherent cohort continuity by default only when a safe plan exists.
- Reuse existing group execution, workspace isolation, handoff, cost telemetry and host-owned validation.
- Introduce adaptive compile checkpoints and bounded escalation; avoid extra agents without measured benefit.
- Dokimos: independently verify each requirement and the integrated cohort; never weaken quality gates.

## Phase 3: controlled experiments
- Freeze benchmark requirements and acceptance.
- Compare per-requirement, fixed-size and affinity-based execution with optional continuity ablation.
- Include at least one non-Praxis application and high/low affinity workloads.
- Report full provider cost, quality, rework and uncertainty.

## Phase 4: conditional rollout
- Adopt only rules meeting preregistered cost and quality thresholds.
- Record planner predictions against actuals for calibration.
- Preserve human approval for consequential decisions and cross-boundary risks.
- Keep calendar-based human planning optional; delivery is evidence-based.

## Suggested cross-repository ownership

| Repository | Ownership |
| --- | --- |
| cohort-based-engineering | Method, experimental hypotheses, decision records, adoption guidance |
| research-documents | Frozen research artifacts, raw evidence, reproducibility |
| ordo | Semantic model, recognition and requirements/decision graph |
| praxis | Cohort planning, scheduling, execution, telemetry and checkpoints |
| conditor | Approved decision and input provenance |
| signal | Requirement disposition and delivery tracking |
| dokimos | Independent behavioral, architectural and coverage verification |

## Open decisions

1. How should affinity be calibrated and which signals should be hard constraints?
2. When does context pressure justify splitting a cohort?
3. What minimum quality and cost thresholds authorize rollout?
4. Which source owns canonical cohort and requirement IDs?
5. Which approval boundaries must remain explicitly human?
6. What experiment design best separates grouping, continuity and agent model effects?

No fixed answers should be invented before the evidence is available.
