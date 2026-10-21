# ARCH-001-04: Replicate architectural-correctness findings on violation-prone work

Priority: P2
Owner system: Cohort-Based Engineering (research)
Intake: Praxis document ingestion
Evidence: kemiller2002/cohort-based-engineering `research/architectural-correctness/REPORT.md`, `RESULTS.json`, `BASELINE.md`, `ARCHITECTURE-RULES.md` (branch `claude/echelon-architectural-correctness-m4glhq`, PR #16).
Related: A024 follow-on #1 (guidance ablation), A023 (grouping), REL-001.

## Finding
ARCH-001 hit a complete ceiling: 0 architecture violations and 128/128 accepted requirements in every arm. That limits every architecture conclusion to small, clean, consistently layered fixtures.

Measured costs are solid:
- guidance +15%;
- contracts and enforcement about +4% each;
- enforcement +48% wall time.

Exploratory signals favour guidance on review-judged quality (+0.59/6, p = 0.013) and on swallowed-failure heuristics. They do not favour contracts or enforcement beyond guidance. Mandates must not be made from a ceiling result.

## Requirement
1. A preregistered replication reusing the ARCH-001 harness, verifier and analysis, with fixtures that elicit violations:
   - brownfield code with existing boundary violations and inconsistent layering;
   - larger multi-feature tasks;
   - changes to real Summa and Signal snapshots, under read-only fixture copies.
2. At least two models, and n chosen by the ARCH-001 §9 rule from pooled pilot variance.
3. A separate factorial experiment for H7 (grouped execution × enforcement), so grouping and enforcement stay separately attributable.
4. A lifecycle cost model that prices follow-up rework, using ARCH-001's phase-2 metrics.

## Acceptance criteria
- The pilot shows a non-zero violation rate in at least one arm before the confirmatory trials. The task suite is not tuned on arm differences.
- The same scoring spec (`scoring-spec.json`) is used, with the A3 superseded-test rule and the A4 probe fix built in.
- The report states which ARCH-001 conclusions it confirms or overturns.
