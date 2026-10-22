# VAC-002-04: Adaptive verification and risk classification, deferred with a retarget

Priority: P3
Owner system: Ordo (verification policy) and Praxis (risk classification). Forward at triage. Deferred: do not
implement until VAC-002-03 produces a corpus with failures.
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/ADAPTIVE-ENFORCEMENT.md`, `RECOMMENDATIONS.md` R-AD-1, R-AD-2 and
R-REJ-2.

## Finding

A frozen, hindsight-free adaptive policy (arm E) was compared with always-on full verification (arm D):

| Measure | Result |
|---|---|
| Reliability | Equal: 0 vs 0 failures. Noninferiority not established |
| Model cost | E +3.8% |
| Gate host CPU | E −10% |
| Escalation | Exactly the two conflict units and the dependency-change unit went to the high tier |
| Low tier | Never used: signal S8 (an open question in the report) fired on every unit |

The cost of D over plain continuity (about +13%) sits in the Praxis protocol and scaffold, which policy 1.0.0 did
not vary, not in the gate.

## Requirements (proposed, deferred)

- **VAC-002-04-R1.** Do not ship policy 1.0.0 as a product feature.
- **VAC-002-04-R2.** If adaptive enforcement is pursued, vary the *protocol* (scaffold and commands) by risk tier, keep
  the independent gate fixed, and remove S8 as an escalation signal. Re-calibrate on reference diffs only.
- **VAC-002-04-R3.** Any implementation is behind a flag that is off by default (`verification.policy = "full"`),
  records every tier decision with its inputs, and fails closed to the high tier. It is promoted only after a
  confirmatory noninferiority result (VAC-002 H4, margin 5 points).

## Acceptance evidence

- A confirmatory H4 result on a discriminating corpus before R3's flag is enabled anywhere.
