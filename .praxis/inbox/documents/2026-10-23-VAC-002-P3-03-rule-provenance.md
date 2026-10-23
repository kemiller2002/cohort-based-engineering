# VAC-002-P3-03: Unauthorized decisions now come from rules embedded in reused code; audit rule provenance

Priority: P1
Owner system: Dokimos (independent verification); Ordo (construction traceability)
Target repositories: dokimos, ordo
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/P3/` (`DISCOVERY-RESULTS.md`, `CONFIRMATORY-RESULTS.md` §3,
`BLINDED-REVIEW.md` §3, `RECOMMENDATIONS.md` R-PROV-1, R-REV-1).

## Finding

- **Every confirmed error came from reused code.** All 36 confirmed unauthorized decisions in P3, across every stage
  and arm, reused a rule embedded in existing code that no accepted decision or requirement supports:
  - a superseded rate or horizon still in code;
  - an exemption with no record;
  - a 0% or 0.00 default for an unlisted case.
- **The same temptation announced in a note was declined.** D05 (note): 0 / 2. D19 (the same default embedded in a
  helper): 3 / 3.
- **One unrecorded exemption beat every control.** C06's exemption, framed as an operational fact inside the function
  that carries the accepted rule, was reused by every arm: no controls, the contract, the checklist, typed records
  and executable authorization (15 / 15).
- **Post-hoc blinded review flagged all 15**, and found two consequential changes no oracle probe tested.
- **Implementer-written tests lock these errors in.** In D19 and D21 the agent added tests asserting the
  unauthorized default or shortcut.

## Requirements (proposed)

- **VAC-002-P3-03-R1 (Dokimos).** Rule provenance audit. Every business-rule function, constant or branch in a rules
  module traces to an accepted decision record or requirement. An untraceable exemption, default or superseded rule
  is reported to its owner before new work reuses it, never silently fixed.
- **VAC-002-P3-03-R2 (Ordo).** Construction traceability extends to rules a change *reuses*, not only to rules it
  writes.
- **VAC-002-P3-03-R3 (Dokimos / CBE).** Test a targeted, non-blocking independent review that asks of each change
  which existing rules it reuses and what each one's source is. Findings go to owners.

## Evidence class

- **The mechanism** (incidental code-embedded rules as the source of every confirmed error): Demonstrated for this
  corpus and model.
- **The proposed audit's prevention value:** not tested; Additional experiment required.
