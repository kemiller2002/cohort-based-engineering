# Research protocol: Team topology and cohort execution

**Status:** Draft research design, 2026-10-14. Not preregistered and no empirical study has started.

## Research question

Which combination of stable domain ownership, temporary cohort staffing and execution cadence delivers the lowest coordination and repair cost per independently accepted capability while preserving architecture, quality, team sustainability and stakeholder responsiveness?

**Do not conflate:** team topology (who owns what), work partitioning (what belongs together), execution policy (how work progresses), and delivery cadence (when stakeholders review outcomes).

## Competing models

| Arm | Organization | Work grouping | Cadence |
| --- | --- | --- | --- |
| A | Stable product teams | Individual tickets | Sprint-driven |
| B | Stable product teams | Semantic cohorts | Sprint-driven |
| C | Stable domain teams | Semantic cohorts | Continuous execution, periodic human review |
| D | Temporary cross-functional cohort teams | Semantic cohorts | Continuous execution |

**Working hypothesis:** C will outperform A on repair-inclusive lead time without sacrificing architecture or team well-being. B isolates the grouping effect; C versus B isolates cadence; D versus C isolates dynamic staffing. This is a hypothesis, not a conclusion.

## Literature review streams

1. **Conway's Law / mirroring hypothesis:** organizational communication and architecture coupling; examine original claims and empirical limits.
2. **Team Topologies:** stable stream-aligned teams, platform/enabling/complicated-subsystem teams and interaction modes; practitioner framework, not a controlled experiment.
3. **Socio-technical congruence:** alignment between coordination needs inferred from dependencies and actual communication.
4. **Cognitive load and expertise:** human learning, team familiarity, interruptions and onboarding; distinguish human from model context windows.
5. **Lean flow / queueing:** batch size, WIP, Little's Law assumptions, arrival variability and flow efficiency.
6. **Agile and Scrum empirical research:** sprint boundaries, stable teams, cross-functionality, delivery performance and threats to causal inference.
7. **Multi-agent software engineering:** task partitioning, shared verified context, context handoffs, integration conflict and independent verification.

For every source capture full citation, DOI/URL, study design, sample, domain, treatment, outcome measures, effect sizes, confounders, replication and applicability to human teams versus AI agents. Record negative and contradictory evidence. Do not infer causal effects from anecdotal case studies.

## Research sequence

### Phase 1: Scoping review

Search ACM DL, IEEE Xplore, Google Scholar, arXiv and relevant conference proceedings. Use explicit search strings such as:
- `("software engineering" AND "team stability" AND performance)`
- `("socio-technical congruence" AND software AND coordination)`
- `("Conway's law" OR "mirroring hypothesis") AND empirical`
- `("Scrum" OR sprint) AND (batch size OR lead time OR context switching)`
- `("team topology" OR "cross-functional team") AND software delivery`
- `("multi-agent" AND coding AND (task partitioning OR context sharing))`

Maintain inclusion/exclusion criteria and a PRISMA-style screening log if a systematic review is pursued. Separate peer-reviewed research, preprints and practitioner sources.

**Output:** evidence map, disagreements, gaps and falsifiable hypotheses.

### Phase 2: Retrospective Echelon analysis

Use existing Praxis/Ordo/Signal/Summa/Chrona data to estimate repeated discovery, decision waiting, handoff overhead, integration conflicts, repair cycles and quality outcomes. Validate telemetry coverage before comparing costs. Human-team outcomes cannot be inferred from agent-only runs.

**Output:** baseline distributions and candidate affinity/coordination indicators, with missing-data limitations.

### Phase 3: Controlled agent simulation

Use frozen requirements and independent acceptance oracles in at least two domains. Keep model/provider, tool versions, repository state, decisions and evaluator rubric fixed. Randomize arm order and isolate workspaces. Compare A/B/C for agent execution; treat D as a **simulation of dynamic staffing**, not evidence about human organizations. Include a Co-Coder-inspired partitioning baseline and a context-continuity ablation.

**Output:** repair-inclusive provider cost, wall time, first-pass acceptance, architecture score, handoffs, conflict and blocked time.

### Phase 4: Human-team pilot

Recruit a willing team with leadership support. Begin with B within existing Scrum; move to C only after quality gates pass. Compare with a matched team or staggered rollout when possible. Dynamic staffing D requires a separate, consent-based trial with attention to team familiarity and knowledge retention. Avoid individual productivity surveillance and performance ranking.

**Output:** 6–12-week pilot evaluation (illustrative duration), interviews and a quantitative trend analysis. Do not interpret a before/after comparison as definitive causation.

### Phase 5: Replication and decision

Replicate in another team/domain. Publish the null and negative results. Adopt only if quality, security, accessibility, architecture and team well-being are non-inferior, and cost/lead time improve beyond preregistered thresholds.

## Measures

**Primary:** elapsed time and total labor/provider/repair cost per independently accepted capability, with human and agent cost reported separately.

**Quality guardrails:** per-requirement acceptance, escaped defects, architectural rubric, security/accessibility checks, integration stability and rollback rate.

**Coordination measures:** WIP, wait states, blocked time, handoff count, repeated discovery, decision latency, context switching, cross-team dependencies, ownership conflicts and onboarding time.

**Human measures:** perceived cognitive load, autonomy, clarity of ownership, team psychological safety, satisfaction and stakeholder responsiveness. Collect aggregated or consent-based data and minimize personal data.

## Confounders

Team maturity, skill mix, application architecture, requirement size, incident load, release constraints, model versions, prompt drift, evaluator bias, changing scope, organization incentives and Hawthorne effects. Freeze what can be frozen; measure and report the rest.

## Preregistration checklist

Before experiments, record:
- exact hypotheses and contrasts (B–A, C–B, D–C);
- inclusion criteria and assignment/randomization;
- primary metric definitions and cost accounting;
- quality non-inferiority margins;
- minimum sample, stopping rule and analysis plan;
- evaluator blinding and adverse-event escalation;
- artifact retention and publication plan.

## Decision boundaries

This protocol does **not** assert Scrum is inherently inefficient, that dynamic human staffing is beneficial, or that the 56% Praxis agent grouping result transfers to human teams. The intended outcome is evidence for when stable teams and temporary cohorts should coexist.
