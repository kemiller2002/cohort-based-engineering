# VAC-002: recommendations (Phase J)

**Rule.** Each recommendation cites the finding it rests on and that finding's class (`PREREGISTRATION.md` §4).
Changes are only recommended when the evidence supports them. An instrument defect observed directly counts as
evidence for its fix. A hypothesis that is still *Inconclusive* does not justify new infrastructure. Nothing here is
made mandatory production policy.

**Intake.** Requirements go to Praxis document ingestion in `.praxis/inbox/documents/` (`2026-10-22-VAC-002-*.md`).
The Ordo, Praxis, Dokimos and Percepta repositories were read-only in this session, so their requirements are placed
here, in cohort-based-engineering's inbox, with the owning system named. They are to be forwarded at triage. No
GitHub issues were opened.

## 1. Implement now

| ID | Change | Owner | Evidence | Class of evidence |
|---|---|---|---|---|
| **R-VS-1** | **Bind verified-state promotion to executed checks.** A requirement becomes `verified` only when a check that *executed* in the gate is bound to it by a structured id (a test attribute or trait, or an Ordo contract node), never because its id appears as text in a file. Entries that are excluded or not implemented must be representable as such | Praxis (verified state); Ordo (binding) | Instrument finding I1: D's verified state admitted LEND-L04-R3 from a test-file comment saying it was *not* implemented. VAC-001 R-ORDO-1 raised the same risk in the abstract | Observed defect (one instance); fix is small, and it removes a false-fact path. Supported but preliminary |
| **R-PERC-1** | **Session-aware cost telemetry.** For resumed CLI sessions, record cost as per-turn deltas of the cumulative `total_cost_usd`, and the session total as its last value. Never sum the cumulative value across turns | Percepta / Praxis telemetry (and every experiment harness) | Finding I2 (amendment A1): summing the cumulative value over-counted the pilot's spend 2.8× partway through, and would have stopped the pilot at a third of its budget | Observed defect; measured |

## 1a. Keep, with no change

| ID | Control | Evidence | Class |
|---|---|---|---|
| R-ORDO-K | Ordo contract admission with conflict records, at arm C's level, is already available | It cost nothing measurable over plain continuity (C vs B −0.7%). In every arm that had it (C–F), the L04 conflict, whose record names R2, was not silently resolved. The one arm without Ordo that was also long-lived (B) resolved it silently. Arm A, without Ordo, did not. One event, and an experimenter-authored conflict node | Supported but preliminary (cost); Inconclusive (benefit) |

## 2. Defer until a corpus produces failures

Every item below targets a reliability effect that VAC-002 could not observe: 0 failures in 72 units. Building any of
them now would add infrastructure on Inconclusive evidence.

| ID | Change | Owner | Evidence and why it is deferred | Class |
|---|---|---|---|---|
| R-AD-1 | Adaptive (risk-triggered) verification in Ordo | Ordo | E vs D: equal reliability (0 vs 0, noninferiority not established); +3.8% model cost, −10% host CPU. Gating is not where the cost is. If pursued, retarget it at the *protocol* (Praxis scaffold and commands, which are about +13% over B), not the gate, and only behind a flag (§4) | Inconclusive |
| R-AD-2 | Risk classification in Praxis (signals S1–S12) | Praxis | The classifier escalated exactly the three hardest units, hindsight-free. But S8 fired on every unit, and the low tier never occurred. Next version: remove S8 as an escalation signal, then re-validate on reference diffs before use | Supported but preliminary (escalation targeting); defect observed (S8) |
| R-DOK-2 | Incremental, AST-scoped and cached architecture verification | Dokimos | `archcheck` takes about 25 s and the gate about 110 s of host time per unit. That is host cost, not model cost, and its reliability value is unmeasured (0 findings in 121 runs) | Inconclusive |
| R-CR-1 | Context-reconstruction improvements (F) | Praxis | F cost +16% over D, about +$0.38 per restart, with no reliability gain observed. Compaction did no harm in B–E. Restarting only for reliability is not supported. Revisit if a longer chain shows degradation after compaction | H7(b) Supported but preliminary; H7(a) Inconclusive |
| R-DOK-3 | Blinded decision review of conflict-unit decisions as a Dokimos control: read each decision against the requirements and decision records it touches | Dokimos | The pilot's only consequential error (B, L04: staff silently exempted from R2) escaped the oracle and every automated check. Both Layer 3 reviewers caught it independently, at about $0.11 per reviewed decision ($19.80 for 186). One event; the review was an instrument here, not a tested control | Supported but preliminary (one event) |
| R-DOK-1 (VAC-001) | Chained re-verification of every earlier accepted requirement | Dokimos | Still untested. 0 regressions in 72 units, and in 96 units in VAC-001 | Inconclusive |

## 3. Reject for now

| ID | Change | Why | Class |
|---|---|---|---|
| R-REJ-1 | Making the full Praxis protocol, gate and verified state mandatory on every unit *for reliability* | They cost +12.9% over B and +13.6% over C. They prevented or detected no error in this pilot that C, without them, did not also avoid; C had no adjudicated error either. VAC-001: +16.8%, 0 errors. Keep them available. Do not mandate them on reliability grounds until a corpus shows a benefit. Their non-reliability uses (traceability, audit) are outside this experiment and are unaffected | Inconclusive benefit, Supported but preliminary cost |
| R-REJ-2 | Shipping adaptive policy 1.0.0 as an Ordo or Praxis feature | No saving, a degenerate low tier, and the wrong cost lever (§2, R-AD-1) | Inconclusive, leaning contradicted on cost |

## 4. If adaptive enforcement is later shown to work

The policy (`harness/policy/adaptive-policy.json`) is data plus a deterministic evaluator (`vac2.fsx policy`). The
reversible path to production is:

1. **Off by default.** An Ordo or Praxis configuration flag `verification.policy = "full" | "adaptive:<version>"`.
2. **Versioned.** Each tier decision is recorded with its inputs, as `results/P1/E/policy-N.json` already does, so
   every skipped check is auditable.
3. **Fail closed.** Any signal that cannot be computed sets the high tier.
4. **Only on evidence.** Promote the flag only after a confirmatory noninferiority result (H4 accept).

## 5. Experiments needed next

| ID | Experiment | Why |
|---|---|---|
| **R-EXP-4** | **A second pilot on a harder corpus**, run *before* any confirmatory spend. It must show a failure rate of at least 10% in some arm (`PROTOCOL.md` §7). Candidates: <ul><li>remove the four-tier documents from the natural-language arms;</li><li>a brownfield fixture with existing boundary violations to imitate (ARCH-002);</li><li>make D1 silent: a semantic change with no compile or test break;</li><li>premises that only decision records or verified state can contradict (VAC-001 R-EXP-1, still open);</li><li>tasks where the working implementation within the turn budget crosses a boundary unless a port is added</li></ul> | The pilot hit the ceiling (I5 and `PILOT-RESULTS.md` §1). On this corpus, a confirmatory run of about $4,000–4,500 could establish no reliability claim |
| R-EXP-5 | Implement and test the preregistered IRLS logistic model and the cluster bootstrap on simulated chains with known effects. Write conflict-unit oracles that test every side of the conflict (I7: L04 tested the 5.00 limit only for a standard member). Replace the propagation tracer's lexical citation match with a link to the origin's file, symbol or decision id, adjudicated in Layer 3 | Needed before a confirmatory run (`STATISTICAL-ANALYSIS.md` §3; `RESULTS.md` I6) |
| R-EXP-6 | Layer 3 reviewers from another model family, and full blinding (remove the Echelon artefacts but keep them available as reviewer-side evidence) | Limitations 3 and 5 in `RESULTS.md` §7. VAC-001 R-EXP-2 is still open |
| R-EXP-7 | Confirmatory chains at 25, 50 and 100 units, only after R-EXP-4 passes, with an explicit spending ceiling | `BUDGET.md` §5 |

## 6. Plan for completion

The experiment is **not complete**. To complete it:

1. Build and seal a harder L01–L12 variant, following R-EXP-4. Run its self-check, freeze it, and run a second pilot
   at about $45 of model cost (the P1 cost).
2. If the discrimination check passes, recompute the sample size from that pilot's failure rates and ICC. Fix a
   spending ceiling.
3. Build L13–L25 and the 50- and 100-unit chains with sealed oracles (`TASK-CORPUS.md` §4). Implement R-EXP-5.
   Freeze the confirmatory protocol.
4. Run the confirmatory chains, then Layer 3 per R-EXP-6, then the preregistered tests. Classify H1–H7, and revisit
   §2 and §3 above.
