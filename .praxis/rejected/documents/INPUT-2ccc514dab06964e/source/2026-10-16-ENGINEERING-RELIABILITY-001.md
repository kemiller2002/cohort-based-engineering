# REL-RESEARCH-001: Measure coordination and preventive engineering

Priority: P1
Research scope: Praxis, Ordo, Dokimos and representative application repositories

## Requirements
- RES-REL-001: Define a reproducible baseline for agent execution, claim collisions, rework, invalid decisions, integration failures and verified requirements.
- RES-REL-002: Compare existing workflow with atomic claims, early Ordo validation, and independent Dokimos verification using equivalent task sets.
- RES-REL-003: Record total input/output tokens, tool calls, wall time, CI/test runs, rework time, escaped defects and cost per independently verified requirement.
- RES-REL-004: Run explicit contention and failure-injection scenarios, including multiple agents claiming the same item and stale agents attempting completion.
- RES-REL-005: Test cohesive batched slices against independently scheduled slices while holding requirements and acceptance criteria constant.
- RES-REL-006: Publish experiment design, fixture provenance, raw observations, exclusions, uncertainty, and reproducible analysis.
- RES-REL-007: Treat 20% token reduction and 30% rework reduction as hypotheses/targets, not measured outcomes.
- RES-REL-008: Record decision gates for rollout: zero duplicate active claims, zero invalid accepted decisions, zero unverified completions, and no increase in escaped defects.

## Acceptance
Results are independently reproducible; report both successful and unsuccessful experiments without cherry-picking.
