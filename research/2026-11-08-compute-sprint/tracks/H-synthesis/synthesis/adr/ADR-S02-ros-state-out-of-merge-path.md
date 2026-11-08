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

## A2 prototype result (SPR-A2-01, replay only)

`A2-remediation/findings.json`; DECISION-LOG D-028.

- **Conflicts.** With the `ros-history` driver (v2), 0 of 170 previously conflicted `.ros` paths remain unmerged:
  - R8: 105 paths in 58 merges, including all 26 logged PR merges.
  - R10: 65 paths in 34 merges.
  - No new conflicts appeared in clean merges (A2-F-01, VERIFIED).
- **Disclosed amendment.** The relaxed event-order rule was added after v1 resolved only 16/26.
- **Correctness.** 0 records lost and 0 duplicated. Content equals the team's merge commit except in one file, where the team's merge was wrong. Pinned `praxis validate` passes on 92/92 driver results (A2-F-02, VERIFIED).
- **A real defect found.** R10 merge d8447ed1 dropped live work item WI-0003, and `praxis validate` fails on that commit. The driver keeps the item (A2-F-03).
- **Limits found.**
  - 9 merges still need human resolution because of application-code conflicts (A2-F-04).
  - Praxis's documented strict ordering rule fails on real histories (A2-F-05).
  - `praxis validate` does not detect duplicated event lines (A2-F-02 negative control).
  - The driver runs only for local merges; GitHub's merge button ignores it (A2-F-06).
- **Speed.** About 6.5 s per merge with no agent turn, against 1,537 s of agent handling across R8's 26 conflicted PR merges (A2-F-06).

## Decision (proposed)

Make `.ros` history files merge-safe by construction, in order of preference. The final choice depends on the SPR-A2-01 result.

1. **Per-lane, append-only records.** Each lane writes its own event file, keyed by lane or execution. `current.json` becomes derived state, not tracked. Git then has nothing to conflict on.
2. **Interim: a semantic merge driver.** Register Praxis's history-merge logic as a Git merge driver for the two files. Items merge 3-way by id, events are unioned by eventId, and a divergent same-id record is refused, never auto-picked. This is what SPR-A2-01 tests.
3. Either way, keep machine-checked file ownership between lanes for application code (B). DECISION-LOG D-019 records that a `.ros` merge driver cannot remove R8's 4 application-code branch merges.

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
| A2-F-01..F-06 | VERIFIED (A2, replay) | V3 pending |
| C-F-12 | SUPPORTED (C): direct readers of `.ros` files exist | — |

Files: `A-economics/findings.json#A-F-07`, `B-forensics/findings.json#B-F-09`, `B-forensics/data/merge-conflicts.json`, `V1-verification/verdicts.json#A-F-07`, `A2-remediation/protocols/SPR-A2-01-ros-merge-driver.md`. Matrix themes X-01, X-02, X-03.

## Open questions

1. ~~Does the driver work on replay?~~ Yes: A2-F-01/F-02, with the v2 ordering amendment. Will the Praxis owners accept relaxed event ordering as policy (A2-F-05)? Should `validate` detect duplicate event lines? Both are recorded as owner follow-ups in D-028.
2. Are the team's own merge results correct? Post-merge edits may make "equivalence to M" a weak oracle (A2 known threats).
3. Is the faster path to change Praxis's format (option 1) or to ship the driver (option 2)? How many external readers of the files exist?
4. Is the 1,537 s figure accurate? It is coordinator-logged and V1 did not re-verify it.
5. Why do B and A2 count different conflicts for R3, R5 and R6 (X-03)?
