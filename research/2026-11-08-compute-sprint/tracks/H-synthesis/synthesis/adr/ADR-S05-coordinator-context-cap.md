# ADR-S05: Cap the coordinator's context

- **Status:** Proposed — EXPERIMENTAL evidence. Weakest of the five drafts: the net saving is untested, and one line of evidence points the other way.
- **Date:** 2026-11-08
- **Drafted by:** Track H (H-001), from Track A recommendation 1. This is a candidate, not a decision.
- **Paths:** relative to `research/2026-11-08-compute-sprint/tracks/`.

## Context

**What R8's coordinator cost.** The R8 coordinator (WI-R8-COORD) used 236.2M tokens, which is 44.2% of the rehearsal total and about 31.5% of estimated list-price cost ($61.09). It made 566 requests (A-F-03, VERIFIED; V1 reproduced every figure exactly).

| | Coordinator | Task agents |
|---|---|---|
| Mean context per request (tokens) | 416,786 | 116,721 (3.6× smaller) |
| Peak context (tokens) | 897,198 | — |
| Compactions | 2 | — |

The coordinator's share is understated, because its turns after 23:50:44Z are missing from the data.

**Cost structure.** Cache reads are 98% of tokens and 54% of cost (A-F-04, VERIFIED). Cost therefore scales with how much context is carried per request.

**Track A's estimate.** If the coordinator's context matched a task agent's, its cost would fall toward about $30 per rehearsal (ESTIMATE in A REPORT, recommendation 1).

**Contrary evidence (cross-track theme X-12).** Track D recomputed VAC-001:
- Agent continuity cut cost per accepted requirement by about 41% compared with fresh agents. Track D VERIFIED the arithmetic, though the CI understates replication uncertainty: 3 chains.
- "Fresh from verified state" cost +86% compared with continuous work. This is preliminary, from 1 chain.

Those were implementer agents on fixtures, not an 830k-token coordinator, so this is a tension, not a refutation. It does show that restarting from a checkpoint can cost more in re-reading and rediscovery than it saves on carried context.

**Fixed prefix.** The fixed startup prefix is about 48.7k tokens per execution (A-F-05, ESTIMATE). Every refresh pays it again.

## Decision (proposed, conditional)

Do not adopt a hard cap yet. Instead:

1. Change what reaches the coordinator first: compact structured notifications (status, SHA, gate result) instead of full sub-agent transcripts or long tool outputs. This reduces growth without a restart.
2. Run the controlled comparison in `future-experiments.json` (FX-04): coordinator with a refresh-from-checkpoint cap compared with an uncapped coordinator, on a fixed scope. Adopt a cap only if total tokens and coordination errors both improve.
3. Record coordinator context per request as a standard telemetry series in every rehearsal (A-F-10, A-F-18 gaps).

## Consequences

**If a cap is adopted without testing:**
- Possible savings of about 15% of R8 cost (A ESTIMATE).
- Possible extra cost from re-reading and lost coordination state (VAC-001 direction).
- Possible coordination errors after refresh. These have not been measured anywhere.

**Option 1 alone** has low downside. It changes inputs, not session structure.

## Evidence

| Finding | Class | Independent check |
|---|---|---|
| A-F-03 | VERIFIED (A) | V1 VERIFIED |
| A-F-04 | VERIFIED (A) | none |
| A-F-05 | SUPPORTED, ESTIMATE (A) | none |
| D-F-03 (VAC-001 continuity −40.9%) | VERIFIED arithmetic (D) | Chain-level exact sign p = 0.25 with 3 chains |
| D-F-05 (fresh-from-verified +86%) | VERIFIED (D), 1 chain | — |
| D-F-08 (about 5 blocks would detect the B vs A and DR vs D effects if true) | SUPPORTED (D) | Lower bound |
| A-F-17 | NOT TESTED: effect of topology and agent count | — |

Files: `A-economics/findings.json#A-F-03`, `A-economics/analysis/r8-economics.json`, `V1-verification/verdicts.json#A-F-03`, `D-experiments/reanalysis/CLAIMS.md`. Matrix theme X-12.

## Open questions

1. Is the coordinator's large context a cause of cost, or a symptom of coordinating 47 executions over 6 hours? The answer decides whether a cap or fewer executions is the right lever.
2. How many tokens does a refreshed coordinator spend re-establishing state? Not measured.
3. Do coordination errors (wrong merges, lost change requests) rise after compaction or refresh? R8 had 2 compactions; their effect was not analysed.
4. Single rehearsal, single topology: does the 44% share hold in other topologies?
