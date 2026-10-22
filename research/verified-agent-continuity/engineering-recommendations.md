# VAC-001: engineering implications and recommendations (Phase 8)

**Rule.** A recommendation is made only where a measurement supports it. Otherwise the answer says
**not supported by evidence yet** and names the experiment that would settle it. Effect sizes are from
[`agent-longevity-analysis.md`](agent-longevity-analysis.md) and
[`error-propagation-results.md`](error-propagation-results.md). Decision quality is from
[`hallucination-evaluation.md`](hallucination-evaluation.md).

**Scope of the evidence.** 96 units in 11 chains of 8 on a single F# fixture (REL-001 Ledger V1–V8). The model was
`claude-opus-5-5` at effort medium, run as sub-agents in condition K0. Correctness was at ceiling in every arm.

## Answers

### 1. Should Echelon prefer long-lived agents by default?

**Yes, for a chain of related, independently verified work items in one repository, within the range measured.**

- **Cost.** Long-lived (B) vs fresh-per-unit (A) cost per independently accepted requirement was −40.9% (CI −48.1%
  to −33.0%, 16 blocks). It replicated at −38.1% in F1.
- **Correctness.** No loss: 0 failures in 72 long-lived units, against 0 in 24 fresh units.
- **Range measured.** Up to 8 units and 167k prompt tokens.

This extends DF-ROS-2026-A053 (grouped execution by default for high-affinity groups of 2–6 members). It does not
replace that decision's gates. It is evidence for its PRAXIS-PLAN-11 review. Beyond 8 units, or past the compaction
threshold, there is **no evidence**.

### 2. Under what conditions should an agent restart?

**Not supported by evidence yet.**

- No long-lived agent failed, and none was compacted, so no failure-based restart trigger could be measured.
- What was measured is that *restarting is expensive*. A fresh agent with a handoff (A) costs about +70% vs
  continuing (B). A fresh agent reconstructed from verified state under the full protocol (DR) costs +86% vs
  continuing under the same protocol (D).
- **Recommendation.** Keep restarts event-driven: a context-pressure signal, a change of repository or ownership,
  or a gate failure that repair does not fix. Do not restart on a timer.
- **Follow-up.** R-EXP-2 measures where the failure rate starts to rise.

### 3. Should context compaction happen at fixed intervals or based on measured risk?

**Not supported by evidence yet.** There were 0 compactions in 96 units. Keep the provider's default behaviour, and
instrument `context.compactions` per work item (R-PRAXIS-1) so the next experiment can see it.

### 4. Which decisions must be verified before entering persistent state?

**Supported (design finding).** A decision may be labelled `verified` only when an independent check covers it: an
oracle or acceptance case on its requirement ID, an architectural rule, or an accepted decision record. Existence of
the cited evidence plus a passing unit is not enough:

- The prototype's rule promoted R1/D's out-of-scope "`withdraw` respects holds" decision (U7-D3) to `verified`.
- No requirement asks for that decision, and no check exercises it.

Anything uncovered stays `provisional` or `corroborated-unchecked` (R-ORDO-1). Decisions recorded as assumptions
were correctly kept provisional: 41 of 441 in the dataset.

### 5. Which verification checks give the largest reduction in error propagation per token spent?

**Not measurable here.** No error propagated in any arm, so no check prevented one. What can be stated is where the
errors were caught:

| Check | Faults caught | Cost |
|---|---|---|
| Visible acceptance tests | F3 | — |
| Repository source and comments | F5 | — |
| Compiler and search | F1 | — |
| Explicit limit or rule | F4 (also AR-6 in C/D) | — |
| Accepted design note | F2 | — |
| Ordo contract admission | 0/5 faults. It does catch unresolvable decision conflicts: V7 refused, 6/6 C/D/DR V7 units. A and B also stopped on V7 by reading the requirement | One CLI call per unit |
| Host gate (D) | Fired 0 times (no failures) | ~20–60 s host CPU per unit; no model tokens unless it rejects |

The cheapest effective defence in this fixture was **evidence that sits in the repository**: tests, comments,
accepted notes.

### 6. Can architectural constraints prevent entire classes of hallucinations?

**Partially, for the classes they encode.**

- VAC-RULES caught F4's dependency change class mechanically: AR-6, with 19/19 detector controls correct.
- No agent in any arm violated a rule, including A and B, which never saw the rules. So prevention cannot be
  attributed to the rules.
- Lexical rules have measured false positives: the `ref'` identifier, 2 cases in R1/C and R1/D.
- Lexical rules cannot see semantic layering errors.

**Recommendation.** Keep executable rules for mechanical classes (toolchain pins, I/O in pure tiers, throwing).
Do not expect them to stop semantic premises.

### 7. Does the four-tier architecture materially improve correctness?

**Not supported by evidence.** It was not varied: every arm worked in the same tiered fixture. Correctness was 100%
everywhere, and no AVR difference was observable (0 violations in every arm). This stays *Inconclusive*, as in the
baseline.

### 8. Can verified engineering state replace repeated conversational reconstruction?

**For correctness and traceability, yes, in this fixture. For cost, no.**

| Configuration | Requirements verified | Accepted | CCR (lower bound) |
|---|---|---|---|
| DR (fresh agent + verified state) | 15/15, IDs preserved | 8/8 | $0.421 |
| D (continuous) | — | — | $0.227 |
| A (fresh + plain handoff) | — | — | $0.280 |

Continuity remains the cheaper way to carry context. Verified state is a **safety net for restarts**, not a cost
optimization. This agrees with praxis EX-ROS-2026-A024 (structured handoff +10.5%).

### 9. Does the system improve as more verified decisions accumulate?

**No improvement detected.**

- Cost per unit rose with index in every arm, confounded by task mix and codebase growth.
- D's slope was +$0.008 per unit, against B's +$0.009 and A's +$0.016.
- Correctness did not change (ceiling).

There is no evidence that accumulated verified state lowered cost or errors.

### 10. What evidence would justify publishing the findings?

See [`publication-readiness.md`](publication-readiness.md).

- **Publishable as a measured result with stated scope:** continuity lowers CCR by ~40%.
- **Publishable as negative or null results:**
  - Echelon controls cost +14% to +31% with no measured benefit at ceiling.
  - Verified-state reconstruction cost +86% vs continuity.
- **Not publishable:** any claim that verified state improves reliability.

## Recommendations with evidence status

| ID | Recommendation | Evidence | Status |
|---|---|---|---|
| R-OPS-1 | Default to continuing the same agent across successive related work items in one repository. Restart only on event-driven triggers | Q1, Q2 | **Supported** within 8 units / 167k tokens; route into the DF-ROS-2026-A053 review |
| R-OPS-2 | Do not add the full Echelon protocol to simple, well-specified chains purely for reliability. Measure it against a continuous baseline first | Q1, Q5: C/D +14% to +31% vs B at equal correctness; REL-001 run-02 D vs A +35.5% | **Supported** (cost); reliability benefit unmeasured |
| R-ORDO-1 | Decision records name the independent checks that cover them. "Verified" is computed, never asserted | Q4 | **Supported** (design defect observed) |
| R-ORDO-2 | Decision records written by the implementing agent enter as `proposed`, and only an authorizing actor or an independent check accepts them | Agents self-accepted DEC-V1-STORE-CLOSE and DEC-V3-STORE-HOLDS, which Layer 3 adjudicated as unsupported requirements (`hallucination-evaluation.md` §4) | **Supported** (governance gap observed) |
| R-OPS-3 | When a unit extends a rule to behaviour no requirement names, record it as an assumption or open question, never as settled | 8 Layer 3 unsupported-requirement decisions; the same change recorded as an assumption in 6 units | **Supported** (dominant unsupported-decision type) |
| R-PRAXIS-1 | Per-work-item usage windows, continuation index, prompt size and compactions, when one agent session spans successive work items outside a group | VAC-001 needed custom windowing (`vac.sh reusage`) | **Supported** (measurement gap) |
| R-DOK-1 | Chained verification: at each completion, re-verify every previously accepted requirement, with each requirement's checks isolated | Q5. Amendment A2: joint compilation masked results | **Measurement capability**. No propagation was observed, so the benefit is unproven |
| R-EXP-1 | Next experiment: premises the repository cannot contradict, such as rules or decisions that live only in verified state or decision records, and underspecified tasks with hidden expectations | Q5, Q8, H5 untested | **Needed** to test the primary hypothesis |
| R-EXP-2 | Next experiment: longer chains (≥ 24 units) past the compaction threshold, K1 isolated runs | Q2, Q3 | **Needed** |
| R-EXP-3 | Do not report token totals as a cost proxy. A vs B differed by ≤ 10% in tokens but ~40% in cost (cache writes, requests) | §2.3 of the longevity analysis | **Supported** (measurement practice) |

## Not recommended now

These changes are speculative, and the experiments do not justify them:

- New continuity infrastructure or a verified-state service.
- Mandatory verified state for every agent.
- Fixed-interval compaction.
- Treating the four-tier architecture as a correctness lever.

## Implementation status (2026-10-22)

The repository owner approved every recommendation above together with input VAC-CBE-001 (record
[`../../requirements/VAC-CBE-001.md`](../../requirements/VAC-CBE-001.md)). This section records where each one now
lives. The evidence status in the table above is unchanged.

| ID | Status |
|---|---|
| R-OPS-1, R-OPS-2, R-OPS-3, R-EXP-3 | In [`docs/operating-model.md`](../../docs/operating-model.md) §4, §6, §5 and §7 |
| R-ORDO-1, R-ORDO-2 | Method rules in the operating model §3. Enforcement is an Ordo follow-up |
| R-PRAXIS-1 | Praxis follow-up. The operating model §7 states the measurement need |
| R-DOK-1 | Dokimos follow-up |
| R-EXP-1 | Preregistered: [`r-exp-1-protocol.md`](r-exp-1-protocol.md). Not run |
| R-EXP-2 | Preregistered: [`r-exp-2-protocol.md`](r-exp-2-protocol.md). Not run |
