# VAC-002-01: Verified state must bind to executed checks, not to text

Priority: P1
Owner system: Praxis (verified engineering state). Ordo for the requirement-to-check binding. Forward at triage;
the owning repositories were read-only in the session that wrote this.
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/` (`RESULTS.md` §4 I1, `RECOMMENDATIONS.md` R-VS-1). It
strengthens VAC-001 R-ORDO-1.

## Finding

The VAC-002 harness promoted a requirement to `verified` whenever an acceptance-test file in the repository mentioned
its id. In arm D at unit 4, the agent wrote a header comment saying "LEND-L04-R3 is not implemented (Ordo conflict)".
The harness then recorded LEND-L04-R3 as verified.

The agent noticed the false entry and rejected it at units 6 and 10, so no outcome was affected. But a
verified-state store that a comment can write to is not verified. This is one observed instance of an instrument
defect, not a measured error rate.

## Requirements (proposed)

- **VAC-002-01-R1.** A requirement may be promoted to `verified` only when a check that *executed and passed* in an
  independent gate is bound to it by structured metadata: a test trait or attribute naming the requirement id, or an
  Ordo contract node. Text occurrences of the id never promote it.
- **VAC-002-01-R2.** Verified state can represent `excluded` (for example, an unresolved conflict) and
  `not-implemented` explicitly. A promotion attempt on such a requirement is rejected and logged.
- **VAC-002-01-R3.** Each verified entry records the gate run, the check id and the commit it was verified at.

## Acceptance evidence

- A regression test in which a test file *mentions* a requirement id without a bound, executed check, and the
  requirement is not promoted.
- Re-running the VAC-002 P1 arm D promotion over `results/P1/D/gate-*.json` with the new rule leaves LEND-L04-R3
  unverified and changes no other entry.
