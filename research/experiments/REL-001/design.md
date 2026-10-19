# REL-001: Ownership, contracts and independent verification vs. baseline

**Status:** Proposed protocol, not preregistered or run. No observation in
`observations/` exists yet; nothing here is a measured outcome.
**Source requirements:** RES-REL-001..008 (`.praxis/inbox/documents/2026-10-16-ENGINEERING-RELIABILITY-001.md`); Praxis PRX-REL-009.
**Relation to the CBE plan:** complements `research/experiment-plan.md`.
Cohort strategy is held constant here; only the reliability controls vary.

## Question

Does end-to-end enforcement (Ordo contracts + Praxis atomic ownership +
Dokimos independent completion verification) change cost per independently
verified requirement, rework and coordination failures, without increasing
escaped defects, compared with the existing workflow?

## Arms

| Arm | Workflow |
| --- | --- |
| `baseline` | Existing Praxis workflow: `work begin`/`work complete`, no claim/lease/fencing, no Ordo admission, no Dokimos completion gate. Verification still runs **after** the run, by the same Dokimos authority, only to score it. |
| `treatment` | Ordo constructibility contract admitted; Praxis claim/lease/fencing; completion only through `dokimos completion verify` (packet/1, authority/1); events per Praxis interface I1. |

## Controls

| Factor | Control |
| --- | --- |
| Requirements | Same frozen task set per arm (`task.taskId`, `requirementIds`); comparable size, recorded `complexity.class` (low/medium/high) with its basis; stratify assignment by class. |
| Acceptance | Identical acceptance criteria per task; `acceptanceCriteriaDigest` (sha256) must match across arms. |
| Model | Same provider, model and configuration digest (effort, temperature, tool set, max turns). A served-model change invalidates the pair. |
| Cache | Report cache-read and cache-write separately from input. Each run declares `cache.state` cold (fresh container, no prior session) or warm; compare only like with like; alternate arm order so neither arm always runs warm. |
| Concurrency | Declared agent count per run, equal across arms; contention scenarios (RES-REL-004: duplicate claim, stale completion, expired lease) run as separate, labelled scenarios, never mixed into nominal runs. |
| Repository state | Every repository pinned by full commit SHA (`environment.repositories`); Praxis/Ordo/Dokimos versions recorded. Isolated workspace per run. |
| Verification | One Dokimos authority and acceptance oracle for scoring both arms. Treatment's in-loop verification is part of its cost; baseline's post-hoc scoring is not charged to it. |
| Retries | Same retry policy (`retryPolicy.maxAttempts`) in both arms; every retry, replay and rework is counted, none discarded. |

## Measurement

- Instrument with `praxis telemetry reliability-report` (Praxis
  `docs/development-telemetry.md`, schema `praxis.telemetry-reliability-report/1`);
  store each raw report in `reports/` and reference it by sha256 from the observation.
- Copy each run's provider transcripts before the container ends and pass
  them with `--transcripts`; never estimate tokens from elapsed time.
- **Primary:** cost per independently verified requirement = total
  attributable cost through verified completion (including failed attempts,
  rework, subagents, retries) / distinct verified requirement IDs. Cost is
  `estimated` from a named, versioned price table, or `billed` when the
  provider reports it; the two are never pooled.
- **Secondary (RES-REL-003):** input/output/cache-read/cache-write tokens,
  tool calls, wall and active time, CI/test runs, rework frequency,
  first-pass verification rate, completion rejections, duplicate ownership
  attempts, stale-write rejections, escaped defects (found after acceptance
  by the frozen post-run oracle).

## Rules

1. **Report every run.** Failed, aborted and excluded runs are observations
   with `status` and reason. Exclusions are decided by rule before scoring.
2. **Instrumentation incomplete.** A run whose token buckets or cost are
   `unavailable` or `partial` in its report is `instrumentation.status:
   incomplete`. It is reported and counted in run totals but excluded from
   cost and token comparisons; it is never imputed or zero-filled.
3. **Zero verified requirements** leaves the run's ratio undefined (null),
   never zero or infinite; such runs are reported as failures.
4. **Not conclusive alone.** One run per arm is a feasibility check, not
   evidence. Preregister replicates per arm, the effect threshold and the
   stopping rule with the lead researcher before scored runs; report
   uncertainty (per-run distribution, not only pooled ratios).

## Hypotheses (RES-REL-007: targets, not results)

- H1: treatment reduces total tokens per verified requirement by >= 20%.
- H2: treatment reduces rework frequency by >= 30%.
- H3: treatment does not increase escaped defects.

## Rollout gates (RES-REL-008)

Treatment is eligible for rollout only if, across all treatment runs
including contention scenarios: zero duplicate active claims, zero invalid
accepted decisions, zero unverified completions, and no increase in escaped
defects versus baseline. A cost or token gain never overrides a failed gate.

## Layout

| Path | Content |
| --- | --- |
| `schema/observation.schema.json` | One run (`cbe.rel-001.observation/1`) |
| `observations/<arm>/<runId>.json` | Observations, one file per run, append-only |
| `reports/<sha256>.json` | Raw Praxis reliability reports the observations cite |
| `analysis/analyze.fsx` | Deterministic summary: `dotnet fsi analysis/analyze.fsx [observations] [analysis/results.json]` |
