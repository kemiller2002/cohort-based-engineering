# Incentive-Compatible Autonomous Engineering (ICAE)

Status: Research hypothesis, not established result. Date: 2026-10-30.

## Thesis

Autonomous engineering may become more efficient and reliable when its environment makes independently verifiable, architecturally valid work the lowest-friction path to task completion. This is inspired by mechanism design and coordination games, but no formal incentive-compatibility theorem has yet been demonstrated.

## Mechanism

- Praxis supplies bounded, dependency-coherent work and durable state.
- Ordo resolves supported decisions and patterns, reducing search and uncertainty.
- Shared components (Forma, Limen, Folio) make approved implementation paths convenient.
- Dokimos independently evaluates evidence tied to the exact source and requirements.
- Trusted CI and permissions prevent acceptance of invalid work, even if an agent disregards guidance.

Agents are not assumed to be malicious. Noncompliance can arise from ambiguity, context loss, shortcut optimization, specification gaming, or incomplete controls. Cooperation does not establish correctness.

## Formalization sketch

Let an agent choose action a from available actions A in state s. Let C(a,s) be expected execution cost (time, tokens, rework), P(a,s) the probability of verified acceptance, and R the value of completion. Its operational objective can be approximated by U(a,s)=R*P(a,s)-C(a,s). The engineering environment changes A, C and P. The desired property is that approved behavior has higher expected utility than prohibited shortcuts, while independent acceptance controls protect correctness. This is a modeling hypothesis; LLMs need not literally maximize this function.

Distinguish (1) guidance compliance, (2) mechanically prevented actions, and (3) independently verified acceptance. Formal incentive compatibility requires specifying players, information, strategies, payoffs, and equilibrium assumptions.

## Falsifiable hypotheses

H1: Pre-resolved decisions reduce decision latency and tokens versus equally detailed requirements alone.
H2: Approved reusable components reduce architecture violations and rework.
H3: Independent acceptance gates improve verified correctness, but add measurable cost.
H4: Extra supervisory agent handoffs may worsen total cost when deterministic checks suffice.
H5: Under deadline pressure, cooperative agents may take shortcuts that pass incomplete checks.

## Experimental design

Use identical task suites, model/version, starting commit, requirements, time/token budgets, and fixed evaluation criteria. Randomize run order, repeat runs, and report uncertainty.

Arms:
A. Baseline agent with task specification.
B. Agent plus compiled requirements and explicit architecture.
C. B plus Ordo decisions/patterns.
D. C plus Praxis scheduling and shared Echelon components.
E. D plus independent, protected acceptance enforcement.

To isolate Ordo's contribution, hold all other infrastructure fixed in a direct C-versus-B comparison. To isolate enforcement, compare E against D. Include a stress condition in which a shortcut is faster but invalid, and a condition in which the approved path has a missing component. Do not grant agents authority to change tests, protected policies, or acceptance gates in the enforcement arm.

Metrics: verified requirements per hour; tokens and dollars per verified requirement; wall-clock time; rework; architecture violations; bypass attempts; false acceptances and false rejections; provenance completeness; final independently evaluated functionality. Distinguish inherited code from new work.

## Evidence boundaries

Past Causa rehearsals show implementation progress, CI success, and unresolved evidence/provenance and time-limit issues. They do not isolate Ordo's causal effect, establish game-theoretic incentive compatibility, or prove general correctness improvement.

## Next steps

1. Inventory existing Ordo/Praxis/Dokimos contracts and identify which policies are executable versus advisory.
2. Define a small representative F# task suite and independent acceptance oracle.
3. Capture baseline cost, correctness, and provenance.
4. Run randomized paired comparisons with repeated trials.
5. Publish negative results and overhead as well as improvements.
6. Only then consider expanding Ordo pattern coverage or adding enforcement layers.

## Research questions

- When is an approved path genuinely cheaper than a shortcut?
- What kinds of decisions are reusable across applications?
- When does batching create integration conflicts?
- Which enforcement controls yield the best correctness-per-cost tradeoff?
- How do we avoid Goodhart effects where agents optimize passing checks rather than fulfilling requirements?
