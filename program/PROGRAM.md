# Echelon constraint-driven engineering program

**Status:** active program, opened 2026-10-23. **Owner:** kemiller2002. **Coordinator:** a long-running agent
session; state in [EXECUTION-STATE.md](EXECUTION-STATE.md).
**Scope:** Praxis, Ordo, Dokimos, Conditor, Echelon Registry, and cohort-based-engineering. Percepta, Forma, Limen and
Aegis are consumers whose contracts must not break.

This directory is the cross-system program record. It does not replace any repository's own records. Requirements
still enter each owning repository through that repository's Praxis intake, and canonical work items are derived
there. GitHub Issues are not used.

| Document | Purpose |
|---|---|
| [CURRENT-STATE.md](CURRENT-STATE.md) | Evidence-backed inventory: one status per capability, with sources |
| [DEPENDENCIES.md](DEPENDENCIES.md) | Prerequisites, parallel lanes, shared interfaces, critical path |
| [IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md) | Ordered increments, each with an owning repository and acceptance criteria |
| [CONTRACTS.md](CONTRACTS.md) | Proposed inter-component contracts, versioning, compatibility, unresolved decisions |
| [EXPERIMENTS.md](EXPERIMENTS.md) | Hypotheses, baselines, budgets, metrics, promotion criteria |
| [RELEASE-GATES.md](RELEASE-GATES.md) | Mandatory verification and the conditions for reusing evidence |
| [EXECUTION-STATE.md](EXECUTION-STATE.md) | Progress, commits, open decisions, blockers, next actions |
| [contracts/](contracts/) | Draft machine-readable schemas and the invoice-slice fixture |
| [evidence/](evidence/) | The 2026-10-23 inspection reports that CURRENT-STATE cites |

## 1. Objective

Minimize the **total cost of accepted, correct functionality**: provider cost, wall time, CI and human attention spent
per requirement that is independently accepted, *including* the cost of the defects that escape and of correcting
them.

The program does not optimize tokens, speed or CI frequency on their own. A saving that weakens correctness, or that
moves cost into later correction, does not count as a saving.

### Measurable outcomes

| ID | Outcome | Measure | Baseline (evidence) | Target to promote |
|---|---|---|---|---|
| O1 | Cheaper accepted requirements | Cost per independently accepted requirement | VAC-001: arm B (continuous agent) is the cheapest arm with full correctness; P3: contract arm $0.158 per accepted requirement | No regression in correctness while O2–O4 changes land; any promoted change shows a CI-bounded cost reduction |
| O2 | Fewer unauthorized consequential decisions | Unauthorized decisions per opportunity (sealed oracle and blinded review) | P3: 7/18 with no contract, 3/18 with it; all 36/36 confirmed errors came from rules embedded in reused code | The provenance audit finds ≥ 90% of seeded inherited rules with ≤ 10% false owner questions (EXP-3, offline phase) before any paid arm |
| O3 | Less CI per accepted change | CI executions and CI minutes per accepted requirement, escaped defects | Praxis CI runs about 23–29 min on every push; R002: four defect classes recurred | EXP-2 replay shows ≥ 30% fewer CI minutes with zero additional escaped defects on the replayed history |
| O4 | Deterministic completion | Completions without the required evidence | Praxis `work finish` refuses with about 45 stable codes but is unreleased and opt-in | 0 completions without evidence, in every repository that enables verified completion |
| O5 | Honest measurement | Share of executions with token and cost data; unavailable never recorded as 0 | 287 of 307 Praxis execution records lack tokens | ≥ 90% of agent executions in program work carry tokens or an explicit `unavailable` |

## 2. Architectural shift

From: agent instructions → implementation → repeated verification → correction.

Toward: **authorized requirements → constrained construction → mechanical verification → independent acceptance.**

The shift is incremental. It is made by **removing invalid construction paths**: types that cannot represent an
invalid state, ports that cannot be called without a capability, and refusals that carry an unresolved question rather
than a guessed policy. It is not made by adding instructions, checklists or blocking reviews. That ordering is evidence,
not preference:

- **P3 contradicted executable authorization.** In VAC-002-P3, admission and the gate prevented 0 unauthorized
  decisions. They rejected 10 authorized or harmless ones, and 4 of those rejections caused harm.
- **P2 and ARCH-001 showed controls cost more than they returned.** Controls added 1.76× to 3.25× cost (P2), and
  enforcement added 15–25% cost at ceiling correctness (ARCH-001).
- **Errors come from reused code.** Every confirmed unauthorized decision in P3 came from a rule embedded in code
  the agent reused. Removing invalid paths and auditing rule provenance target that mechanism directly; more guidance
  does not.

### States that must never be conflated

| State | Holder of record | Who may create it | Never inferred from |
|---|---|---|---|
| Accepted requirement | Owning repository's Praxis requirement record | Intake derivation, owner approval | Code, tests, an agent's summary |
| Authorized decision | Decision record with a human `authorizedBy` and a source revision | The decision owner | An agent's proposal, existing code, a passing test |
| Unresolved policy question | `policyQuestions` in the handoff; Ordo refusal carrying the question id | Anyone may raise; only the owner resolves | Silence in the requirements |
| Observed implementation behaviour | `observations` in the handoff, authority `unverified` | Anyone | — (it is never authority) |
| Verified technical invariant | Dokimos audit result, invariant verdict bound to source digest | Dokimos | A passing implementer-written test |
| Passing test | CI/test evidence bound to an exact commit | The test runner | — |
| Accepted release | Release gate record (RELEASE-GATES.md) bound to exact source and deployed SHA | Independent acceptance | Any single passing gate |

A compiler can prove that code conforms to a type model. It cannot prove that the modelled policy was authorized; that
is the job of the handoff's provenance and of Dokimos's audit.

## 3. Ownership

These responsibilities were verified against each repository's README, charter and code on 2026-10-23
([CURRENT-STATE.md §1](CURRENT-STATE.md#1-component-responsibilities-verified)). The program introduces no new
authority.

| Component | Owns | Does not own |
|---|---|---|
| **Praxis** | Execution orchestration, work scheduling, checkpoints, durable handoffs, telemetry, evidence coordination, completion verdicts, requirement intake | Decision semantics (Ordo), quality judgments (Dokimos) |
| **Ordo** | Engineering decision models, construction constraints, valid states, authorized transitions, decision provenance, F# construction | Running work, verifying its own output |
| **Dokimos** | Code-quality evidence, invariant verification, rule-provenance audit, defect-class analysis, quality and completion-verification results | Repairing code, deciding policy |
| **Cohort-based engineering** | Cross-system experimental protocols, agent-execution research, comparative methodology, this program record | Production implementation |
| **Conditor** | Installation, environment construction, dependency setup, reproducible installation evidence | Approving releases |
| **Echelon Registry** | Approved component selections and compatibility authority (profiles, snapshots, channels) | Installation records |
| **Percepta** | UI semantic contracts and rendered-evidence verification | Experiment telemetry or research coordination. VAC-002-02's "Percepta" owner is a misrouting; see CURRENT-STATE §4 |
| **Forma / Limen / Aegis** | UI components and accessibility / browser and WASM boundary / operational error representation | — |

## 4. Waves

| Wave | Purpose | Increments | Gate to start |
|---|---|---|---|
| 0 | Make verification trustworthy again | EP-00 to EP-03: red CI from runner drift, intake hygiene, duplicate reconciliation | none |
| A | Operational efficiency | A1 dependency-aware verification, A2 evidence reuse, A3 deterministic completion, A4 real-provider ordering, A5 telemetry, A6 compatibility reuse | Wave 0 CI green for the touched repository |
| B | Verified construction, one vertical slice | B1 Praxis handoff, B2 Ordo construction, B3 Dokimos audit, B4 integration | The shared contract (CONTRACTS.md C1–C3) |
| C | Execution efficiency | Tool profiles, checkpoint CI, typed messages, parallel and critical-path scheduling | A1 and A5 deliver measurements |
| X | Experiments | EXP-1 to EXP-4 | Preregistration plus an owner-authorized budget for any paid run |

Waves A and B run in parallel; they share only the evidence-validity contract (C3). Promotion of anything
experimental follows [EXPERIMENTS.md §6](EXPERIMENTS.md#6-promotion-criteria).

## 5. Rules of the program

1. **Inspect before building.** Every increment cites the existing implementation it extends (CURRENT-STATE).
2. **No duplicate requirements.** A new intake document names the existing records it relates to, and states why it is
   not a duplicate.
3. **Status is evidence.** Only implemented, tested code counts as a capability. A plan, a requirement or a schema is
   never reported as one.
4. **Experimental stays off the default path** until its promotion criteria are met.
5. **Mandatory gates are never deferred:** security, data integrity, authorization boundaries, and release acceptance
   ([RELEASE-GATES.md §2](RELEASE-GATES.md#2-never-deferred)).
6. **Rehearsal 3 is protected.** No engineering-system change from this program enters its baseline unless it is
   released, registered and approved ([RELEASE-GATES.md §6](RELEASE-GATES.md#6-rehearsal-3-protection)).
7. **No paid experimental execution** without an explicit owner budget.
8. **Prefer existing components and F#.** No new orchestration service, Kubernetes, or dependency unless existing
   capabilities are shown not to satisfy the requirement.
