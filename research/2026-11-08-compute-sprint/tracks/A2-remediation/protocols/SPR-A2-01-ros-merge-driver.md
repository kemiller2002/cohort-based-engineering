# SPR-A2-01 — Can a semantic Git merge driver eliminate `.ros/` state conflicts?

Status: PREREGISTERED (written and committed before any replay was run).
Registered: 2026-11-08 ~14:10 America/Indiana/Indianapolis. Worker A2-001.

## Background (observed before registration)
- R8 `evidence/telemetry/merges.jsonl`: 49 PR merges, 26 flagged `conflict: true`; every conflict
  lists only `.ros/context/current.json` and/or `.ros/events/events.jsonl`; every resolution was
  `praxis work history merge --apply` (Praxis 3.24.0 pinned), run by an agent after Git stopped.
- Merge commits were created locally by the agent (committer "Claude"), so a local Git merge
  driver configured in `.gitattributes` + `.git/config` *would* have run in this workflow.
  (GitHub's server-side merge button does not run custom drivers; this limits generality.)
- Praxis already documents a post-conflict resolver (`docs/work-history-merge.md`,
  `src/Praxis.Domain/Work/HistoryMerge.fs`) but prescribes no `.gitattributes` merge driver.
  Its domain plan: items 3-way by `id`; events unioned by `eventId` with deterministic topological
  order; metadata 3-way and refusing divergence; `updatedAt` = later; base records never removed.
- Pre-scan with `git merge-tree` over every 2-parent merge commit (all refs) found conflicts in
  R3 (3, none in `.ros/`), R5 (15, none in `.ros/`), R8 (60 conflicted merge commits; 58 touch `.ros/`)
  and R10 (34; all touch `.ros/`, 5 also non-`.ros/`). R1, R2, R4, R6, R7, R9: 0 conflicts.

## Hypotheses
- H1: With a per-file semantic merge driver configured for the two history files, 100% of the 26
  logged R8 conflicted PR merges complete with zero `.ros/` conflicts.
- H2: The driver output is semantically equivalent to the merge commit the team produced: same set
  of work-item IDs with identical normalized item content, same set of event IDs; zero records lost
  and zero duplicated.
- H3 (generality): same holds (>=95% of `.ros/` conflicted paths auto-resolved, 0 lost/duplicated)
  over all conflicted merge commits touching `.ros/` in R8 and R10.

## Independent variable
Merge-driver configuration: (a) none (Git default text merge, `ort` strategy); (b) `ros-history`
driver set via `.git/info/attributes` (so the repo tree is not modified) for
`.ros/context/current.json`, `.ros/events/events.jsonl`.

## Procedure
1. Scratch clones under /home/user/sprint-scratch/A2/ (never the originals).
2. For each target merge commit M with parents P1, P2: `git checkout --detach P1`,
   `git merge --no-ff --no-commit P2` under config (a), record unmerged paths; `git merge --abort`;
   repeat under (b); record unmerged paths, driver exit codes, wall time; read resulting files.
3. Compare the (b) result for each `.ros/` file with `git show M:<path>`:
   byte-identical?; semantic equivalence (item-ID set, per-item normalized JSON, event-ID set and
   event order); records lost (ID in P1 or P2 but absent from result); duplicates (ID >1 time).
   Records present in M but in neither parent are reported separately (post-merge edits by the team).
4. `praxis validate` on the driver result if a pinned Praxis binary can be obtained in scratch
   (release artifact or `dotnet build` in a copy); otherwise marked NOT TESTED.
5. Driver unit tests must pass before replay.

## Metrics
- conflicts auto-resolved = merges with 0 remaining `.ros/` unmerged paths under (b) / merges
  with >=1 `.ros/` unmerged path under (a).
- semantic equivalence rate vs M; lost and duplicated record counts; driver refusals; driver time.

## Success criteria
- SUCCESS if H1 (26/26) and H2 (0 lost, 0 duplicated, semantic equivalence on all records that
  exist in the parents) hold. Byte identity with M is reported but NOT required (formatting).
- PARTIAL if >=80% auto-resolve with 0 lost/duplicated. FAIL otherwise or if any record is lost.
- Any divergent same-ID record must cause the driver to REFUSE (leave conflict), never pick a side.

## Known threats
- Team merge commits may themselves be wrong, or include post-merge edits; mismatches are examined
  individually before attribution.
- Driver is per-file: it cannot bind both files to the same commits as Praxis's resolver does.
- `actor` metadata divergence: Praxis refuses it; the driver's policy is declared in its source
  (preregistered choice: take the `actor` of the side whose `updatedAt` is later; tie -> ours) and
  the effect is measured against M.

## Amendment 1 (recorded 2026-11-08T14:06-0500, AFTER the v1 replay; deviation, not preregistered)
- v1 result on the 26 logged R8 merges (raw/replay-r8-logged-v1.jsonl): 16/26 merges fully resolved;
  10/26 still had `.ros/events/events.jsonl` unmerged because the driver REFUSED with
  "base history removed, rewritten or reordered". In 5 of those 10 (PR10, 14, 15, 17, 30) Git's plain
  text merge had merged events.jsonl cleanly, so v1 *added* a conflict there (a regression).
- Cause (inspected PR10): the incoming branch had earlier merged main with the team's DEV-R8-08 fallback
  ("ours in order, then theirs' new lines"), which reorders base events. All base events were present and
  byte-identical; only their relative order differed. Praxis's own resolver has the same strict rule.
- v2 change: if base events are all present with identical content but reordered, the driver no longer
  refuses; it emits ours' order followed by theirs-only events in theirs' order (the order DEV-R8-08 used),
  and logs "relaxed-order" to stderr. Removal, rewrite, duplicate IDs and divergent same-ID content still
  refuse. v1 and v2 are both reported. The extended replays (all R8 and R10 conflicted merges) use v2 only,
  and were not run before this amendment.
