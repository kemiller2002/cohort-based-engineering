# VAC-002-P2-02: Decision authority contract v0.2 (five defects found by pilot P1)

Priority: P1
Owner system: Cohort-Based Engineering (method); Ordo and Dokimos are consumers
Intake: Praxis document ingestion. Source material, not a canonical requirement.
Experimental finding: `research/experiments/VAC-002/P2/DECISION-AUTHORITY.md` §5, `PILOT-RESULTS.md` §5,
`RECOMMENDATIONS.md` R-CON-1..5.

## Finding

The v0.1 checker rejected correct work and caused three harms; it prevented no error, because none was proposed:

- 5 false plan rejections;
- 13 first-gate rejections, none of them for an unauthorized decision;
- S05-D implemented nothing after three rejections;
- S02-D reverted a correct same-owner revision.

## Requirements (implement in the contract specification now; in any checker before its next use)

- **R1.** The agent's record carries no status. Status is computed and held by the host. (A1 fired only on agents
  echoing the host's verdict: 6 / 24.)
- **R2.** Separate `evidenceRefs` (anything the implementer produced, including its tests) from `verificationRefs`
  (host receipts only), and tell the agent. (22 / 36 executions listed their own tests as verification.)
- **R3.** A6 applies to exceptions to and overrides of decision records, approvals, or *other owners'* requirements.
  It does not apply to a same-owner requirement revising an earlier one.
- **R4.** Judge implementer authorship per section for headed documents.
- **R5.** A rejection names the unauthorized behaviour and, where the sources settle it, the authorized behaviour.

## Evidence class

Each defect is **Demonstrated**: observed and traced in the committed observations.
