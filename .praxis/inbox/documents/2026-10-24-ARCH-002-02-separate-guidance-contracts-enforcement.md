# ARCH-002-02: Separate guidance, contracts and enforcement on harder work; H7 grouping

Priority: P3
Owner system: Cohort-Based Engineering (research)
Intake: Praxis document ingestion
Evidence: kemiller2002/cohort-based-engineering `research/architectural-correctness/arch-002/REPORT.md`, `RESULTS.json` (PR #17); ARCH-001 `research/architectural-correctness/REPORT.md`.
Related: ARCH-001-04 (done as ARCH-002), A023 and A024 (grouping).

## Finding
In ARCH-002, four-tier guidance alone took new architecture violations to zero. Ordo contracts and mechanical enforcement therefore tied with it at zero (H3 D − C = 0), and the design could not rank B, C and D on violations.

The only separation was exploratory and small. On a conflicting decision, guidance-only agents implemented the conflict in 2 of 8 trials; agents with contracts refused it in 8 of 8.

## Requirement
1. A replication whose tasks still produce violations *with* guidance:
   - longer multi-feature changes;
   - deeper precedent;
   - rules not named in the instance document but implied by the doctrine;
   - several conflicting decisions per task.
   It reuses the ARCH-002 harness (`harness/recover.sh` and the A4 rule included) and its scoring.
2. A powered test of contracts against conflicting decisions: enough conflict tasks to estimate C − B on conflict refusal.
3. H7 (grouped vs independent execution) as a separate factor crossed with guidance, so grouping and guidance stay separately attributable.

## Acceptance criteria
- Calibration in arm **B** shows a non-zero new-violation rate before the confirmatory run.
- The same preregistration discipline: freeze, sealed oracle, sample size from pooled pilot variance.
- The report states which ARCH-002 conclusions it confirms or overturns.
