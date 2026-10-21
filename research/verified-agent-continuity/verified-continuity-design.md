# Verified agent continuity: prototype design and evaluation (Phase 6)

**Status.** A prototype was built and exercised in VAC-001 arms D (24 units) and DR (8 units), 2026-10-21.

**Recommendation.** Do not build a new platform. The prototype reuses existing Echelon pieces, and its measured
benefit does not justify promoting it beyond an experiment harness. See §5.

## 1. Architecture as built

```text
agent working context
   │  unit report  .vac/reports/unit-N.json  (vac.unit-report/1: requirements, decisions + evidence, rejected assumptions)
   ▼
structured decisions  docs/decisions/DECISIONS.md  (Ordo-style records: ID, status, requirement, evidence, provenance)
   │
   ▼
independent verification   host verifier, outside the workspace, after the agent's turn
   │  build + repository tests · cumulative hidden oracle (per-task projects) · VAC-RULES archcheck · Layer 1 evidence
   ▼
persistent verified state  .vac/verified-state.json  (vac.verified-state/1), committed by the harness
   │
   ▼
reconstructed agent context: DR gets only the repository + verified state; D also keeps its conversation
```

| Piece | Implementation | Existing Echelon abstraction reused |
|---|---|---|
| Requirement identity | `requirements/V*.md`, IDs `LEDGER-Vn-Rk` | Praxis requirement IDs; Ordo `ecir/1` requirement keys |
| Contract admission | `ordo ecir check --blueprint contracts/Vn.json` | Ordo 1.17.0 (`ordo@bb43c26`) |
| Work protocol and durability | `praxis work begin / checkpoint / complete`, with a push to the workspace remote | Praxis 3.19.0 durable checkpoints (DF-ROS-2026-A042) |
| Architectural constraints | VAC-RULES 1.0.0 + `archcheck` | SDE-DOCTRINE-003 four-tier rules |
| Independent verification | `vac.sh verify` plus the REL-001 hidden oracle | Plays Dokimos's role. Dokimos `completion verify` was not usable as an *independent* verifier here (shared uid, F6 open) |
| Persistent state | `vac.fsx state`, a git-committed JSON file | Repository-backed storage, no new service |

## 2. State model (`vac.verified-state/1`)

| Field | Content |
|---|---|
| `requirements[]` | ID, unit, `verified` / `provisional` / `rejected`, `demotedAtUnit` |
| `verified[]` | Decisions whose Layer 1 evidence is valid **and** whose unit was independently accepted |
| `provisional[]` | Decisions recorded as assumptions, or decisions from units not yet accepted |
| `rejected[]` | Decisions citing evidence that does not exist |
| `constraints[]` | The rule set version |
| `lastUnit` | Accepted flag, failing check names, architecture violations |
| Provenance | `head` commit, `updatedAfterUnit`, verifier identity |

**Promotion rules (implemented):**

- **Nothing is promoted silently.** An assumption stays `provisional` even when its unit passes.
- **Earlier verified requirements are demoted.** A requirement already marked `verified` is set to `rejected`,
  with `demotedAtUnit`, when its oracle fails at a later unit. The code exists but was never exercised, because no
  regression occurred.
- **The agent is told the precedence.** Verified overrides any handoff or note; provisional must be re-checked;
  rejected is known false.

**Observed final states.** R1/D after unit 8 held 15 requirements (all `verified`) and 31 verified decisions, in
13 KB. F1/DR after unit 8 held 15 requirements (all `verified`), 29 verified decisions and 1 provisional decision,
in 15 KB.

## 3. Measured effects

### 3.1 Reconstructed versus uninterrupted context (run F1)

D keeps its conversation and DR is a fresh agent each unit. Both have identical controls and verified state.

| Measure | D (uninterrupted) | DR (reconstructed) |
|---|---|---|
| Accepted, first pass | 8/8 | 8/8 |
| False premises accepted | 0/5 | 0/5 |
| Traceability | All 15 requirements verified, with IDs preserved | All 15 requirements verified, with IDs preserved |
| CCR, lower bound | $0.227 | $0.421 (**+86%**; D vs DR −46.2%, CI −56.6% to −32.4%) |
| Requests per unit | 7.2 | 13.1 |
| Cache-write tokens | 120,718 | 383,084 |

**Interpretation.** Reconstructing context from the repository plus verified state kept requirement traceability
and correctness intact across 8 context resets. It did so at almost twice the cost of keeping the conversation, and
at +51% over a fresh agent with a plain handoff (A).

In this fixture, verified state **preserved** knowledge but did not **substitute** for it cheaply. Every DR unit
re-read governance, contracts, decisions and state before acting. The protocol overhead that is amortized in D is
paid again on every unit in DR.

### 3.2 Did verified state prevent errors?

Not measurable here. No arm, with or without verified state, produced an error for it to catch. All five fault
types were refuted from ordinary repository evidence (`error-propagation-results.md`).

## 4. Weaknesses found

1. **"Verified" over-claims for decisions the oracle does not test.** The promotion rule needs only two things:
   the cited evidence exists, and the unit passes. A decision about behaviour no oracle case exercises is promoted
   to `verified` as long as it cites an existing file. The clearest case is "`withdraw` also respects holds"
   (decision dataset, task V3). It was taken in 10 of 12 V3 units; P1/A and F1/D declined it and escalated:
   - 6 recorded it as an assumption: P1/B, P1/D, R1/A, F1/A, F1/B and F1/DR.
   - 4 recorded it as evidence-based: P1/C, R1/B, R1/C and R1/D.
   - In R1/D, the state recorded it as `verified` (U7-D3), even though no requirement asks for it and no oracle
     case exercises it.
   - P1/D, F1/D and F1/DR held it as `provisional`.

   **Fix.** Promote a decision only if an independent check covers it: an oracle case on its requirement ID, a
   rule, or an accepted record. Otherwise label it `corroborated-unchecked`, never `verified`. Layer 3 results
   (`hallucination-evaluation.md`) size this problem.
2. **Evidence validity is existential, not semantic.** Layer 1 confirms that a cited file or anchor exists, not
   that it supports the claim. Layer 3 review is the only semantic check, and it is model-based and sampled.
3. **State grows monotonically.** About 2 KB per unit. A long chain needs compaction of the verified state itself,
   for example by collapsing superseded decisions. This was not exercised.
4. **Same trust boundary as the agent.** The state file is committed into the agent's repository. A malicious or
   confused agent could edit it. This is the same class of issue as REL-GATE-004 and needs the same remedy: store it
   outside the agent's write path, or sign it.

## 5. Should this become Echelon infrastructure?

**Not yet.** The measured benefit in VAC-001 is zero on correctness, because of the ceiling, and negative on cost
(DR +86% vs D). The demonstrated gap is narrow: the promotion rule and state custody (§4.1, §4.4). It does not
justify a new platform.

The smallest useful integration reuses existing Echelon state and is captured as Praxis requirements:

- Praxis already holds durable checkpoints, `work context`, and execution telemetry. A verified-state *view*
  could be derived from Praxis plus Dokimos receipts, so no new store is needed.
- Ordo decision records already carry provenance. The missing piece is a link from decision to independent check,
  so that "verified" can be computed rather than asserted.

Any build-out should wait for an experiment where verified state has room to help (`engineering-recommendations.md`
R-EXP-1).
