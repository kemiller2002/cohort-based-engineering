# CBE operating model

**Status:** proposed method, 2026-10-22. This document states how a cohort is planned, built and verified, who decides
what, and the rules agents follow. Each rule that rests on a measurement cites it, with that measurement's scope. A
rule that no measurement supports is marked **not supported by evidence yet**.

**Source.** Sections 4 and 5 implement VAC-CBE-001-R1 and R2. The input is claim `INPUT-29db4a38cf86a56b`, and the
canonical record is [`../requirements/VAC-CBE-001.md`](../requirements/VAC-CBE-001.md). They also implement the
recommendations in
[`../research/verified-agent-continuity/engineering-recommendations.md`](../research/verified-agent-continuity/engineering-recommendations.md)
that belong to this repository.

## 1. Lifecycle

1. **Intake.** Source material enters as an input document (`.praxis/inbox/documents/`). It is never canonical until
   it is derived into records with provenance.
2. **Plan globally.** The full requirement and dependency graph is analysed. Every requirement keeps a stable ID and
   an explicit disposition.
3. **Decide.** Unresolved business policy goes to its owner before implementation (§3). Agents do not invent it.
4. **Form cohorts.** Requirements are grouped by cohesion: domain invariants, shared interfaces, dependencies and
   decisions. Unrelated work is separated even if it would fit a batch limit.
5. **Construct.** Within a cohort, one agent works the successive work items (§4). Ordo constructs what it recognises
   deterministically. Praxis delegates the rest.
6. **Verify independently.** Each work item is accepted only by checks the implementing agent does not control:
   acceptance tests, architectural checks, Dokimos verification. An agent's or a tool's completion claim is never
   acceptance.
7. **Integrate on evidence.** A cohort completes when every requirement has a disposition and accepted evidence, not
   when a date arrives.

## 2. Roles and boundaries

| Role | Decides | Does not decide |
|---|---|---|
| **Human owner** | Outcomes, constraints, consequential business decisions, acceptance of decision records, spending ceilings for experiments | Implementation detail that a requirement or accepted decision already settles |
| **Planning agent** | Proposed cohorts, order, checkpoints | Business policy; its own plan's approval |
| **Implementing agent** | How to meet the named requirements within the accepted decisions and rules | Anything no requirement names (§5); acceptance of its own decision records; whether its own work is verified |
| **Verifier** (Dokimos, host gate, reviewers) | Whether evidence meets the checks | Requirements or policy |

The implementing agent never judges its own decisions. In VAC-001, independent review was what found the dominant
unsupported-decision type (§5).

## 3. Decisions

- **Before implementation.** A decision is recorded with its owner, authorization, rationale and affected
  requirements.
- **Agent-written records enter as `proposed`.** Only an authorizing actor or an independent check moves a record to
  `accepted`.
  - Evidence: in VAC-001, agents self-accepted DEC-V1-STORE-CLOSE and DEC-V3-STORE-HOLDS, and Layer 3 later judged
    both unsupported requirements.
  - Status: method rule here. Enforcement is Ordo's (VAC-001 R-ORDO-2).
- **"Verified" is computed, never asserted.** A decision or requirement is `verified` only when an independent check
  covers it:
  - an oracle or acceptance case on its requirement ID;
  - an architectural rule;
  - an accepted decision record;
  - for promotion, a check that actually executed and is bound to it by a structured ID.

  The existence of cited evidence plus a passing unit is not enough. Anything uncovered stays `provisional`.
  Evidence: VAC-001 R-ORDO-1; VAC-002 R-VS-1.

## 4. Agent continuity within a cohort (VAC-CBE-001-R1)

**Rule.** A cohort's agent **continues across its successive work items by default**. It is restarted only when an
event occurs:

| Restart event | Meaning |
|---|---|
| **Context pressure** | A context-pressure signal from the runtime or Praxis (for example, the prompt nearing the compaction threshold) |
| **Change of repository or ownership** | The next work item is in another repository, or belongs to another owner or team |
| **Gate failure that repair does not fix** | Independent verification rejects the work item, and the permitted repair round does not make it pass |

**Agents are not restarted on a timer or a fixed work-item count.** Compaction is left to the provider's default
behaviour. Fixed-interval compaction is not adopted.

**Evidence: VAC-001** ([`../research/verified-agent-continuity/`](../research/verified-agent-continuity/)).

- **Cost.** One continuous agent across a chain of related, independently verified changes cost **40.9% less per
  accepted requirement** than a fresh agent per change with a handoff (95% CI −48.1% to −33.0%, 16 paired blocks). It
  replicated at −38.1% in a fault-injection run.
- **Correctness.** Equal: 0 failures in 72 long-lived units and 0 in 24 fresh units.
- **Restarting is expensive.**
  - A fresh agent with a plain handoff cost about +70% vs continuing.
  - A fresh agent rebuilt from verified state cost **+86%** vs continuing under the same controls.

  So verified state is a **safety net for restarts, not a cost lever**.

**Scope of that evidence (read before generalising):**

- **One fixture.** The REL-001 Ledger repository (F#), with tasks V1–V8.
- **8-change chains.** Up to 167k prompt tokens, and **0 compactions**. Nothing is known beyond 8 changes or past the
  compaction threshold.
- **Ceiling correctness.** Every arm was accepted on every unit, so no reliability benefit or harm of continuity could
  be measured. The evidence says continuity is **cheaper at equal correctness**. It does not say continuity is safer.
- **K0 cache condition.** The agents were sub-agents sharing a prompt-cache prefix with the orchestrator. Isolated CLI
  processes (K1) may change the size of the gap.
  - Corroboration: the VAC-002 pilot (K1, Lending fixture, 12 units, one chain per arm) found continuity 32% cheaper,
    and one automatic compaction per long-lived chain with no observed harm. That is descriptive only.

**What is not supported by evidence yet:**

- Which restart trigger actually prevents failures: no long-lived agent failed.
- Where the failure rate starts to rise with agent lifetime.
- Whether to compact or restart under context pressure.

R-EXP-2 ([`../research/verified-agent-continuity/r-exp-2-protocol.md`](../research/verified-agent-continuity/r-exp-2-protocol.md))
is designed to answer these. Until then, the restart events above are a cost-preserving default, not a
reliability-proven policy.

## 5. Scope: extensions of a rule are assumptions, never settled (VAC-CBE-001-R2)

**Rule.** When an agent extends a rule, decision or requirement to behaviour **that no requirement names**, it must
record the extension as an **assumption** or an **open question**, with the requirement it extends and why. It must not
implement or report the extension as settled.

- **What counts.** Applying an existing rule to another operation or feature, adding an interface or operation nobody
  asked for, or changing behaviour of a feature the requirement does not mention.
- **Where it is recorded.** Recorded where the work item's decisions are recorded (the unit report, or a decision
  record with status `proposed`), and surfaced to the owner at the cohort's next human checkpoint.
- **An open question blocks only what depends on it.** If the work item can meet its named requirements without the
  extension, the agent leaves the extension out and asks.

**Evidence: VAC-001** (`hallucination-evaluation.md` §3).

- **The dominant type.** The commonest unsupported decision was a scope addition presented as settled: 8 of 202
  adjudicated decisions. Examples are unrequested `Store` operations, and `withdraw` made to respect holds when the
  requirement named only `debit` and `transfer`.
- **The same change, recorded correctly.** The same `withdraw` change was recorded as an assumption in 6 units, and
  declined and escalated in 2.
- **No deterministic check caught it.** The oracle had no case for the added behaviour, and the cited files existed.
  Only blinded independent review found it.

So the rule must be followed by the agent, and checked by review (§2).

### Refusing the uncovered case is an authorized outcome (VAC-002-P3-02-R1)

**Rule.** When no requirement or accepted decision covers a case, an agent may refuse that case with a recorded open
question that names the owner. This outcome needs no further authority source. No admission check, gate or reviewer
may reject it, or reject it for citing the agent's own question.

**What it is not.** It is not a business rule. The question stays open until its owner answers it, and the refusal is
replaced when they do.

**Status.** Accepted by the owner, kemiller2002, on 2026-10-24.

**Evidence.**
- In VAC-002-P3, executable authorization rejected recorded questions and correct refusals 5 times.
- Those rejections led to three unauthorized defaults and one crash (`research/experiments/VAC-002/P3/CONFIRMATORY-RESULTS.md` §5).
- Where this is implemented: `program/CONTRACTS.md` C1 (`permittedOutcome: refuse-and-record`) and the Ordo slice's
  handoff admission.

## 6. Controls in proportion to evidence

- **Do not add the full Echelon protocol to simple, well-specified chains purely for reliability.** Measure it
  against a continuous baseline first.
  - VAC-001: Ordo or full-Echelon controls on top of continuity cost **+14% to +31%**, with no measured correctness
    benefit at ceiling.
  - VAC-002 pilot: +13%.
  - The controls stay available for traceability and audit. Those uses are outside these measurements.
- **Executable architectural rules for mechanical classes.** These are toolchain pins, I/O in pure tiers and
  throwing. Do not expect lexical rules to stop semantic premises (VAC-001 Q6).
- **Evidence in the repository is the cheapest defence measured.** Every injected false premise in VAC-001 was
  rejected using tests, comments, compiler output or accepted notes that were already in the repository. Put
  decisions where the next agent will read them.

## 7. Measurement

- **Report cost per accepted requirement, never token totals as a cost proxy.** In VAC-001, fresh and continuous
  agents differed by ≤ 10% in tokens but by ~40% in cost: cache writes and request counts (VAC-001 R-EXP-3).
- **Record, per work item:**
  - the usage window;
  - the continuation index (how many work items this agent session has done);
  - prompt size at the last request;
  - compactions;
  - restarts with their trigger.

  This is required wherever one agent session spans successive work items. Praxis provides it natively (VAC-001
  R-PRAXIS-1). Until then, experiments derive it from transcripts.
- **Missing measurements are `unavailable` with a reason, never zero.**

## 8. Not adopted

The evidence does not justify these:

- New continuity infrastructure or a verified-state service.
- Mandatory verified state for every agent.
- Fixed-interval compaction, or restarts on a timer.
- Treating the four-tier architecture as a correctness lever: it was not varied.
- Any claim that verified state improves reliability: it was unmeasured at ceiling.

## 9. Open experiments

| ID | Question | Protocol |
|---|---|---|
| R-EXP-1 | Do Ordo controls, verified state and executable rules lower unsupported decisions, premise acceptance and architecture violations on a fixture where the uncontrolled baseline fails? (H3, H5, H6) | [`r-exp-1-protocol.md`](../research/verified-agent-continuity/r-exp-1-protocol.md) |
| R-EXP-2 | Does failure rise with agent lifetime past the compaction threshold, under K1 isolation, with reviewers from another model family? Is restarting on context pressure better than compaction? (H2) | [`r-exp-2-protocol.md`](../research/verified-agent-continuity/r-exp-2-protocol.md) |

Both are preregistered designs. Neither has run, and neither is authorized to spend beyond its pilot or qualification
ceiling without an explicit owner ceiling. When they report, §4 and §6 are revisited.
