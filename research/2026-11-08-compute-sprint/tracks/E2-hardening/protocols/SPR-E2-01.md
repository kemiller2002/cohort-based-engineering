# SPR-E2-01 — Praxis claim guard and queue integrity (E-F-03, E-F-11)

Preregistered 2026-11-08 ~14:40 EST, before any patched build. Start revision: praxis 12bf995 (RELEASE-3-25-0),
scratch clone /home/user/sprint-scratch/E2/praxis, branch `e2-hardening`. EXPERIMENTAL; nothing is pushed or applied
to a real repository.

## Baseline observations that motivate the design (probe, baseline binary)
- `work claim` writes `work.claim.acquired` ONLY to the out-of-tree store log `<git-common-dir>/praxis/events.jsonl`
  and the claim record to `<git-common-dir>/praxis/claims/ID`. The tracked log `.ros/events/events.jsonl` gets nothing.
  Hence there is currently no tracked fact from which "claimed" could be derived; the fix must add one.
- `work complete` writes a tracked `work.completed`; `complete-verified` writes a tracked `work.completion.verified`.
- `work validate` = work-attribution findings only; backlog rows are checked only by `work backlog-validate`/`validate`,
  and only against the live context (`contextDisagreements`), so a captured (never started) row edited to `complete` is
  invisible (E-F-11).

## Hypotheses
- H1 (E-F-03): if `work claim` also appends a token-free `work.claim.recorded` marker to the tracked log, and the plain
  completion guard treats "tracked log (working tree ∪ HEAD blob) shows a claim and no `work.completion.verified`" as
  claimed even when the store record is absent, then deleting `<git-common-dir>/praxis/claims/ID` no longer lets plain
  `work complete` succeed; it is refused with a distinct code `PRX.COMPLETION.CLAIM_RECORD_MISSING` (exit 3).
- H2 (E-F-11): if `work validate` (and `backlog-validate` / unified `validate`) cross-check every queue row with status
  `complete` against tracked completion events (`work.completed` | `work.completion.verified`), a hand-edited row is
  reported with code `PRX.QUEUE.UNRECORDED_COMPLETION` and a non-zero exit.

## Attack cases (each in a fresh fixture repo under /home/user/sprint-scratch/E2/fixtures/, own .git)
- A1 = E NX-2b / V2 case B: claim, plain complete (expect refused, VERIFIED_COMPLETION_REQUIRED), `rm -rf` claim dir, plain complete.
- A1b: as A1 but also delete the uncommitted marker line from the working-tree tracked log after the claim was committed
  (tests the HEAD-blob union). A1c: as A1b but the claim marker was never committed (EXPECTED to still bypass —
  recorded as residual risk, not a success criterion).
- A2 = E NX-9: capture, hand-edit queue.json status to `complete`, run `work validate`, `work backlog-validate`, `validate`.

## Positive controls
- C1: claim → validate-run → complete-verified (real Dokimos 0.11.1 at fecbe0c, Ordo db6d39e contract) still succeeds;
  subsequent `work validate` reports no new findings.
- C2: unclaimed item, default policy, plain `work complete` with in-repo evidence still succeeds (no false refusal).
- C3: legitimately completed item (start → complete) produces no queue finding.
- C4: run the new queue cross-check read-only over real repositories' `.ros` files (praxis, ordo, signal, mercatus,
  Indy-init, rehearsals) to measure the false-positive rate on legacy data.

## Measures
Exit codes, refusal codes, finding codes; existing test-suite pass/fail counts before (baseline build) and after
(patched build), with names of any newly failing tests and whether they encode the old behaviour; suite wall time.

## Success criteria
- A1, A1b refused with exit 3 and code CLAIM_RECORD_MISSING; A2 reported with UNRECORDED_COMPLETION and exit != 0.
- C1–C3 pass. New unit tests pass. Any newly failing existing test is explained as encoding the old behaviour
  (e.g. "claiming never touches the tracked tree") or is a regression to fix.
- Classification: VERIFIED if all attack/control criteria met on the built binary; SUPPORTED if met only partially.
