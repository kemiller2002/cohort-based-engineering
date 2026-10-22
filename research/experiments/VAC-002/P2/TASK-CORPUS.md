# VAC-002-P2 task corpus (Phase C)

**Sealing.** This file describes the corpus's design and composition. The per-scenario table that names each
scenario's unauthorized alternatives is in the sealed store (`sealed/`, `meta.json`) until the pilot is scored, and
is reproduced in §5 after unsealing.

## 1. Design

- **12 scenarios, 3 unrelated domains.** Each domain has its own repository, decision records and owners, so an agent
  cannot pass by recognising L04:
  - **Lending**: the VAC-002 library system at reference state `ref-L03`;
  - **Billing**: a new wholesale invoicing system;
  - **Clinic**: a new outpatient clinic system.
- **One scenario is a deliberate replication.** S01 is VAC-002's L04 exactly: the same requirement text, the same
  starting state (`ref-L03`) and the same visible tests. It answers whether the P1 finding reproduces under P2's
  conditions.
- **Every scenario is independent.** Each execution starts from its own tree. Propagation (F10) is built into the
  starting state (S08) rather than carried across executions, so that no arm's earlier errors contaminate a later
  scenario.
- **Same authority rules everywhere.** Every README carries the same "Authority" section
  (`fixture/authority-section.md`). The section says which sources are authority, that only an owner changes a
  record, how proposed and superseded records behave, that an approval covers only what it names, and what to do with
  a gap or a conflict. The authorized answer is therefore always *available*. The question is whether agents follow
  the rules under temptation.
- **Temptations are realistic.** They are notes from stakeholders, handoffs from earlier engineers, a requirement
  that conflicts with a record, plausible defaults, code that already embodies an unauthorized rule, and a requirement
  that asks for a verification the implementer cannot give.
- **The visible tests never encode the authorization dimension.** Every trap passes the visible tests and every
  hidden functional fact (`ORACLE-SPEC.md` §6). S02 is the one exception: its unauthorized alternative also has to
  rewrite an existing test, which agents can see.

## 2. Composition (public)

| Scenario | Domain | Work item | Requirements | Opportunities | Severity |
|---|---|---|---|---|---|
| S01 | Lending | LEND-L04 (replication) | 3 | 1 | high |
| S02 | Lending | LEND-L13 | 2 | 1 | medium |
| S03 | Lending | LEND-L14 | 1 | 1 | medium |
| S04 | Billing | BILL-11 | 2 | 1 | high |
| S05 | Billing | BILL-12 | 2 | 1 | high |
| S06 | Billing | BILL-13 | 2 | 2 | medium |
| S07 | Billing | BILL-14 | 2 | 2 | high |
| S08 | Billing | BILL-15 | 2 | 1 | high |
| S09 | Clinic | CLIN-21 | 3 | 1 | high |
| S10 | Clinic | CLIN-22 | 2 | 1 | medium |
| S11 | Clinic | CLIN-23 | 2 | 1 | high |
| S12 | Clinic | CLIN-24 | 2 | 3 | medium |
| **Total** | | | **25** | **16** | |

**Families covered.** F1–F10 are each covered at least once; F1, F3 and F7 twice. The mapping is sealed (§5).

**Severity.** High means money owed, money charged or patient safety; medium means service rules.

## 3. What each scenario contains

Each scenario directory (`scenarios/Sxx/`) holds:

- `scenario.json`: domain, work item, requirement ids and visible tests;
- `overlay/`: what the scenario adds to the domain's base repository, namely:
  - the requirement (`requirements/…`);
  - the visible acceptance tests;
  - any notes, decision records or approvals;
  - for S08, the earlier code.

The sealed store holds, per scenario:

- `oracle/OracleTests.fs`: the `FUNC` and `AUTH` facts;
- `ref/`: the reference implementation;
- `trap-*/`: the unauthorized alternatives, each a complete implementation;
- `valid-*/`: authorized alternatives, for false-positive checks;
- a generator script (`gen/Sxx.py`) that rebuilds `ref`, `trap-*` and `valid-*` from the base by exact edits.

`meta.json` holds every opportunity:

- its authorized and unauthorized behaviour;
- its probe;
- the escalation keywords;
- why it is solvable.

## 4. Confirmatory variants (specified, not built)

The mission asks for independent variants for confirmatory testing. Each scenario has a held-out variant
specification in the sealed store (`confirmatory-variants.md`): the same family in a different domain surface, with
different owners and wording. The variants are **not built**, because confirmatory evaluation needs a new
authorization. Building one costs about the same as a pilot scenario (requirement, overlay, reference, traps, oracle,
self-check).

## 5. Per-scenario table (sealed until scoring)

*Filled in after the pilot is scored, from `sealed/meta.json`.*
