# ADR-S02: Take Praxis `.ros` state out of the Git merge path

- **Status:** Proposed — EXPERIMENTAL evidence
- **Date:** 2026-11-08
- **Drafted by:** Track H (H-001), from Track A recommendation 4 and Track B prevention-plan item 5. Track A2's prototype (SPR-A2-01) is the pending test. This is a candidate, not a decision.
- **Paths:** relative to `research/2026-11-08-compute-sprint/tracks/`.

## Context

**Most conflicts are in Praxis state files.** In multi-lane rehearsals, most merge conflicts are in `.ros/context/current.json` and `.ros/events/events.jsonl`, not in application code. Three independent counts agree:

| Source | Method | R8 | R10 |
|---|---|---|---|
| A-F-07 (VERIFIED) | Coordinator log | 26 of 49 PR merges conflicted, every one in `.ros` only | — |
| B-F-09 (VERIFIED) | `git merge-tree` replay | 56 of 60 conflicted merges were `.ros`-only | 29 of 34 |
| V1 | Independent re-run | Same 26 PRs, all `.ros` | — |

- **Handling time.** Every conflict was resolved by `praxis work history merge --apply` after Git stopped. Conflicted merges took 1,537 of the 2,791 seconds spent merging in R8 (A-F-07; coordinator-logged, not re-verified).
- **Correction to Track A.** A-F-07 says no application-code conflicts occurred. That part is contradicted:
  - B-F-09 counts 4 source-file conflicts in R8.
  - V1 found 6 non-state paths conflicting in branch-side "merge main into lane" merges (Program.fs, Classify.fs, GitHubRequests.fs, StatefulFake.fs, INV22.fs, live.yml).

  See matrix theme X-02. Removing `.ros` from the merge path does not remove all conflicts. Lane file ownership is still needed (B REPORT §5.5).
- **Existing pieces.** Praxis documents a resolver for after a conflict (`docs/work-history-merge.md`, `HistoryMerge.fs`), but no `.gitattributes` merge driver (A2 protocol, Background).
- **Scope.** The problem only appears in multi-lane runs (B-F-09). Single-agent runs had none.

## Decision (proposed)

Make `.ros` history files merge-safe by construction, in order of preference. The final choice depends on the SPR-A2-01 result.

1. **Per-lane, append-only records.** Each lane writes its own event file, keyed by lane or execution. `current.json` becomes derived state, not tracked. Git then has nothing to conflict on.
2. **Interim: a semantic merge driver.** Register Praxis's history-merge logic as a Git merge driver for the two files. Items merge 3-way by id, events are unioned by eventId, and a divergent same-id record is refused, never auto-picked. This is what SPR-A2-01 tests.
3. Either way, keep machine-checked file ownership between lanes for application code (B).

## Consequences

**Expected:**
- Up to 53% of R8 PR merges no longer stop on a conflict (26/49). This is an upper bound from one rehearsal.
- About 26 minutes of coordinator merge handling saved in R8 (A-F-07; ESTIMATE of transferable benefit).

**Limits:**
- GitHub's server-side merge button does not run custom merge drivers (A2 protocol). Option 2 only helps when agents merge locally, as they did in R8. Option 1 has no such limit.
- Option 1 changes the Praxis on-disk format. Every consumer that reads `.ros/events/events.jsonl` directly, including Indy-init's requirements-compiler (C-F-12), would need updating.
- A driver that silently picks one side would corrupt the audit trail. The refusal rule is mandatory.

## Evidence

| Finding | Class | Independent check |
|---|---|---|
| A-F-07 | VERIFIED (A) | V1 PARTIALLY VERIFIED: the `.ros` part reproduced, the no-app-code part contradicted |
| B-F-09 | VERIFIED (B) | V2 pending; per-run counts differ from A2's pre-scan (theme X-03) |
| SPR-A2-01 | PREREGISTERED; results pending | — |
| C-F-12 | SUPPORTED (C): direct readers of `.ros` files exist | — |

Files: `A-economics/findings.json#A-F-07`, `B-forensics/findings.json#B-F-09`, `B-forensics/data/merge-conflicts.json`, `V1-verification/verdicts.json#A-F-07`, `A2-remediation/protocols/SPR-A2-01-ros-merge-driver.md`. Matrix themes X-01, X-02, X-03.

## Open questions

1. Does the semantic driver resolve 26 of 26 R8 conflicts with zero lost or duplicated records (SPR-A2-01 H1/H2)? Does that hold on R10 (H3)?
2. Are the team's own merge results correct? Post-merge edits may make "equivalence to M" a weak oracle (A2 known threats).
3. Is the faster path to change Praxis's format (option 1) or to ship the driver (option 2)? How many external readers of the files exist?
4. Is the 1,537 s figure accurate? It is coordinator-logged and V1 did not re-verify it.
5. Why do B and A2 count different conflicts for R3, R5 and R6 (X-03)?
