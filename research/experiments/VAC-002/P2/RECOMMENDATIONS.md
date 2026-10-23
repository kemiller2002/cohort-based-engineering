# VAC-002-P2 recommendations (Phase J)

**Rule.** Only changes backed by sufficient evidence, or needed to correct an established defect, are classed
*Implement now*. Everything else is *Additional experiment required*, *Defer* or *Reject*. Requirements go to the
owning repository's Praxis intake (`.praxis/inbox/documents/`). No GitHub issues are created.

**What the evidence supports.** P2 established no prevention benefit, because no uncontrolled agent made an
unauthorized decision (0 / 48). It did establish three things:

1. the *defects* of the proposed authorization contract, which made the controls reject correct work (5 false plan
   rejections, 13 first-gate rejections of which none concerned an unauthorized decision, 3 functional or consistency
   harms);
2. the *costs* of each mechanism;
3. a consistent agent habit: citing its own tests as verification.

## 1. Classification

| ID | System | Recommendation | Evidence | Class |
|---|---|---|---|---|
| R-CON-1 | Contract (this repo) | **Status is computed, never written by the agent.** Remove `status` from the agent-written record; the checker's verdict lives in the host's admission record. A1's "self-asserted status" fired only on agents echoing the host's own verdict (6 / 24) | PILOT-RESULTS §5.4; STAT §5 | **Implement now** (in `DECISION-AUTHORITY.md` v0.2; an established defect) |
| R-CON-2 | Contract | **Separate evidence from verification.** Tests the implementer wrote are `evidenceRefs`; `verificationRefs` are host receipts only, and the brief must say so. A8 rejected agents' own tests in 22 of 36 record-keeping executions and caused 8 gate rejections plus the S05-D block | PILOT-RESULTS §5.1, §5.4 | **Implement now** (contract v0.2) |
| R-CON-3 | Contract | **A same-owner requirement revision is not an override needing a decision record.** A6 should require a record or approval only when the overridden source has a *different* owner, or is a decision record or approval | S02-D (§5.2) | **Implement now** (contract v0.2) |
| R-CON-4 | Contract | **Authorship at section granularity.** Editing a README's command list must not make its Authority section "implementer-written" | S10-D | **Implement now** (contract v0.2) |
| R-CON-5 | Contract | **A rejection must never leave the implementer with nothing to do.** The admission result must say which *behaviour* is not authorized and what is (as the arm-E reviewer did), not only which rule failed | S05-D: the agent implemented nothing after three A8 rejections | **Implement now** (contract v0.2) |
| R-EXP-1 | CBE research | **P3: vary the guidance.** Run a 2 × 2 design: README authority section (present / absent) × executable authorization (off / D with contract v0.2), plus arm B's checklist without the section. Add scenarios where the authority section does not settle the case (sources silent on precedence, as in VAC-002 L04) and a long-lived arm for S01 | P2 base rate 0 / 48 with the section; P1 1 / 2 without a requirement-conflict rule (confounded) | **Additional experiment required** (highest priority; about $35–45 at P2 rates) |
| R-EXP-2 | CBE research | Fix the S12 corpus defect (APR-C01's unrepresentable qualifier) before any reuse; review approval text for representability | S12-E | **Implement now** (an established corpus defect; recorded in `TASK-CORPUS.md` §5) |
| R-ORDO-1 | Ordo | Computed decision-authorization status, with independent authority references and rejection of self-authorization (A1–A9 as amended by R-CON-1..4) | Mechanism properties shown by unit cases (21 / 21); 0 prevented errors; 5 false plan rejections | **Additional experiment required** (P3 with v0.2) |
| R-ORDO-2 | Ordo | Scope-extension warnings for approvals: a machine-readable approval scope | F7 is a blind spot of mechanical admission (G1); no agent extended scope in P2 | **Defer** |
| R-ORDO-3 | Ordo | Supersession validation for decision records | Ordo already has `Disposition.Superseded` and `InvalidSupersession` for requirements; agents never relied on a superseded record (S03: 5 / 5 correct) | **Defer** |
| R-ORDO-4 | Ordo | Decision-to-verification traceability | No false verification claims in 60 executions | **Defer** |
| R-PRX-1 | Praxis | A standard "Authority" section in the agent contract (sources of business rules; proposed and superseded records; approval scope; gaps and conflicts) | P2: 0 / 48 unauthorized decisions with it; not varied, so causality is unknown | **Additional experiment required** (R-EXP-1 measures it). It is cheap and reversible, so it is the first candidate to adopt if P3 supports it |
| R-PRX-2 | Praxis | Decision provenance and authorization dependencies in work-item state | No observed need | **Defer** |
| R-PRX-3 | Praxis | Prevention of false completion claims | 0 false implemented claims on unauthorized requirements (0 / 15); S11: no agent claimed Pharmacy's verification | **Defer** |
| R-PRX-4 | Praxis | Session-aware cost telemetry | Already filed as VAC-002-02; P2 used the per-session rule throughout | **No change** (already filed) |
| R-DOK-1 | Dokimos | Authority-record checks (RC1–RC3: no implementer-written approvals, verification records, or accepted decisions) as a gate check | 0 false positives on 4 valid alternatives, 0 events in 60 executions, cheap (host only) | **Additional experiment required** (no event to justify a gate yet; candidate for P3's D arm) |
| R-DOK-2 | Dokimos | Independent semantic review of decisions against authority (arm E's reviewer) | It found the one real authority ambiguity in the corpus (S12), which no other arm surfaced. But its blocking finding stopped required behaviour, and it cost +84% over D. Blocking on ambiguity is the wrong action | **Additional experiment required.** Route review findings about *ambiguity* to the owners as questions (non-blocking), and block only on behaviour with no authority |
| R-DOK-3 | Dokimos | Mechanical checks for unauthorized architectural changes; incremental checks for changed boundaries | Not exercised in P2 (an authority pilot) | **Defer** |
| R-PER-1 | Percepta | Decision-authorization scoring, oracle coverage validation, reviewer reconciliation, error-propagation measurement | Percepta holds UI-contract verification (`Percepta.Core.Contracts`, `Percepta.Adapter.Playwright`); it has no scoring or reconciliation code. The P2 harness (`p2.fsx score`, `review/agreement.fsx`) is the working implementation | **Reject** (wrong home). Keep it in the CBE research harness |
| R-REJ-1 | Ordo, Dokimos | Make executable authorization (D) or adaptive review (E) mandatory on reliability grounds | No error prevented; D costs 1.76× A and E 3.25× A; both caused harm (§5) | **Reject (for now)** |

## 2. Praxis intake created

| Repository | Document |
|---|---|
| cohort-based-engineering | `.praxis/inbox/documents/2026-10-22-VAC-002-P2-01-authority-guidance-experiment.md` (R-EXP-1, R-EXP-2) |
| cohort-based-engineering | `.praxis/inbox/documents/2026-10-22-VAC-002-P2-02-decision-authority-contract-v0-2.md` (R-CON-1..5) |
| ordo | `.praxis/inbox/documents/2026-10-22-VAC-002-P2-03-computed-decision-authorization-design-input.md` (R-ORDO-1, design constraints from R-CON-1..5; additional experiment required) |
| dokimos | `.praxis/inbox/documents/2026-10-22-VAC-002-P2-04-authority-review-routing.md` (R-DOK-1, R-DOK-2; additional experiment required) |
| praxis | `.praxis/inbox/documents/2026-10-22-VAC-002-P2-05-agent-contract-authority-section.md` (R-PRX-1; additional experiment required) |

Nothing is filed in Percepta (R-PER-1 is rejected).

## 3. Implemented now

- `DECISION-AUTHORITY.md` §5 records contract v0.2 (R-CON-1..5). It is a specification change only; the P1 checker
  stays frozen as run.
- `TASK-CORPUS.md` §5 records the S12 defect and the fix any reuse needs (R-EXP-2). The sealed store is not
  re-sealed after the pilot.

No production code in Ordo, Praxis, Dokimos or Percepta is changed. Nothing in the evidence supports a production
change yet.
