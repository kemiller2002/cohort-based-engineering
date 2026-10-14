# Cohort planner: proposed contract

**Status:** Design proposal. No production implementation is claimed.

## Input graph

Each requirement node must include stable ID, source provenance, acceptance contract, approved decisions, domain entities, invariants, interface and file hints, estimated effort, uncertainty, risk, dependencies and required verifier obligations. Preserve links to all original requirements.

Graph edges are typed: hard dependency, shared invariant, shared domain model, interface contract, shared decision, competing file ownership, mutually exclusive implementation, and independent work. A hard dependency is not automatically an affinity benefit.

## Constraints before scoring

A candidate cohort is invalid if it:
- mixes incompatible approved decisions;
- requires implementing an unresolved policy;
- cannot preserve independent acceptance per requirement;
- creates unbounded ownership or write conflicts;
- crosses a mandatory security/isolation boundary;
- exceeds the host's safe execution or verification capacity.

These are hard gates, not weighted penalties.

## Affinity signals

Evaluate reproducible, versioned evidence for:
1. shared domain model and invariants;
2. dependency and interface coupling;
3. approved decision reuse;
4. overlapping source and test surfaces;
5. common acceptance fixtures and verification setup;
6. context reuse opportunity;
7. likely integration conflict;
8. estimated context pressure and repair risk.

The illustrative weights from discussion (35% shared domain, 30% dependency, 20% decisions, 15% inverse conflict risk) are **not validated** and must not become production defaults without experiment. Calibrate with actual execution outcomes.

## Output: versioned cohort plan

Each cohort must state:
- cohort ID, immutable input pins and planner version;
- source requirement IDs and complete disposition ledger;
- explicit inclusion/exclusion rationale;
- shared decisions, assumptions, open questions and approval state;
- interface/ownership boundaries, permitted writes and integration dependencies;
- construction route per requirement: deterministic, delegated, decision-required or blocked;
- execution order, agent continuity policy and bounded context budget;
- checkpoint triggers, independent acceptance checks and stop conditions;
- predicted cost/time/quality risk with uncertainty and the evidence used;
- cross-cohort integration contracts.

Require a machine-readable canonical format and a human-readable explanation derived from it. No duplicate competing source of truth.

## Scheduling

Build a DAG of admitted cohorts. Execute independent cohorts concurrently only when expected speedup exceeds additional context and integration cost. Keep closely coupled work in one continuity window. Do not use arbitrary sprint dates as execution boundaries.

## Adaptive checkpoints

Trigger at contract stabilization, material changes to shared types, completion of dependency clusters, elevated risk, or impending context limits. Optimize expected verification cost plus expected rework, rather than minimizing test runs alone. Full independent acceptance remains mandatory.

## Planner acceptance tests

- every input requirement appears exactly once in the disposition ledger;
- input order does not alter canonical planning without a documented tie break;
- conflicting decisions fail closed;
- no cohort crosses forbidden write boundaries;
- all hard dependencies are satisfied or explicitly blocked;
- split/merge of cohorts preserves requirement provenance;
- changing an approved decision invalidates affected plan pins;
- no model-generated score bypasses a hard constraint;
- plan forecasts and actual outcomes can be joined without losing cost attribution.
