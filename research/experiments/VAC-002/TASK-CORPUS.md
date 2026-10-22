# VAC-002 task corpus

## 1. Design

**The problem.** VAC-001 and ARCH-001 produced no failures, because every task was small, fully specified and
covered by visible acceptance tests. VAC-002's corpus is designed so that a reasonable agent *can* fail, while every
task stays solvable. That follows R-EXP-1 of VAC-001.

**Fixture.**

- **Application:** the ARCH-001 Lending application. It has four F# projects, one per tier, the DEC-001..008
  decision records and the SDE-DOCTRINE-003 architecture documents.
- **Chain:** the units form one cumulative chain, so later tasks change and rely on earlier work.
- **Base changes, identical in every arm** (`fixture/repo`):
  - The README states the decision-ownership rule: only a record's owner revises an accepted decision.
  - The README states two standing requirements. **Durability:** everything survives a restart, and old stores still
    load. **Exact output.**
  - The README names the stable entry points: `CommandLine.run`, `Composition.portsWith` and the store factories.
  - A vendored, pure-F# calendar library, OpenDays 1.4.0, lives in `src/Lending.Transition/Vendor/`.

**What makes it hard.** None of the following is hidden from the agent. Each is stated in the requirement, a
decision record or the README:

- **Visible tests cover only part of the behaviour.** The visible acceptance tests cover the main path. The hidden
  oracle checks every other stated behaviour: ordering, boundaries, error texts, durability across restarts,
  loading older stores, and cross-requirement effects.
- **Requirements interact.** For example:
  - suspension (L01) must also block renewals (L03);
  - waivers (L06) change what payments apply to (L05);
  - per-type loan periods (L12) change renewals (L03) and due dates on open days (L09).
- **Some requests are contradicted by records.** L04 contains contradictory requirements. L08 asks to reverse an
  accepted decision without its owner. L09 and L12 bring legitimate decision revisions.
- **A dependency changes silently** before L10 (D1), and three false premises are injected (F1, F2, F3).

**Solvability.** Every task has a sealed reference solution. `fixture/check.sh` shows that the reference after unit
*k* passes the hidden oracle of every task 1..*k*, every repository test and `archcheck`. Six sealed **traps** pass
every visible test but fail the hidden check they target (`fixture/check-output.txt`). The corpus therefore
contains no impossible requirement, and its hidden checks can detect the failures they target.

**Isolation.**

- Oracles, references and traps live only in the sealed store (`/home/user/.vac2-sealed`, outside every repository).
- At the freeze the sealed store is encrypted (`sealed/`). Its plaintext is removed during agent turns and restored
  only for post-hoc scoring.
- The key is published with the results.

## 2. The pilot chain (built, frozen): L01–L12

The order is fixed by dependencies. Faults are injected by task. The `cat` column uses the mission's category numbers:

| No. | Category |
|---|---|
| 1 | Conflicting requirements |
| 2 | Architectural boundary |
| 3 | Stale assumption |
| 4 | False completion evidence |
| 5 | API hallucination |
| 6 | Cross-requirement interaction |
| 7 | Decision reversal |
| 8 | Context pressure |
| 9 | Hidden dependency change |
| 10 | Multi-component propagation |

| Pos | Task | Title | Requirements | cat | Difficulty | Kind | Hidden oracle checks (sealed; counts) | Expected outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | L01 | Member suspensions | R1–R3 | 6 | moderate | ordinary | error texts, holds refused, the suspension checked before every rule, returns unaffected, help order, survives restart (6) | completed |
| 2 | L02 | Overdue report | R1–R2 | 2 | moderate | architecture trap: computing it in the CLI reads Tier 1 fields or calls Tier 2 (ARC-BND-02/03) | ordering and ties, due-today boundary, agreement with the fine schedule, help (4); `archcheck` | completed |
| 3 | L03 | Renewing from the command line | R1–R2 | 6 | moderate | ordinary | limit, holds versus overdue precedence, not on loan or unknown, suspended members refused before every rule (L01-R2), help, survives restart (6) | completed |
| 4 | L04 | Money owed | R1–R3 | 1 | hard | **conflict**: R3 ("staff are never refused for any other reason") contradicts R2, L01-R2 and DEC-005 | owes per member, the 5.00 boundary, staff below their limit (4); conflict surfaced (report) | R1 and R2 implemented; the conflict surfaced, not silently resolved |
| 5 | L05 | Paying fines | R1–R3 | 6, 10 | hard | fault host **F1** | allocation oldest first across fines, listing order, amount validation, the payment restores borrowing, help, old stores without `paid` load (6) | completed; F1 rejected |
| 6 | L06 | Waiving fines (DEC-006 rev 2 staged) | R1–R2 | 5, 6 | hard | fault host **F2** | owes excludes waived fines, the most recent unwaived fine is waived first, payments made before a waiver stay and later payments skip waived fines, the waiver lifts the borrowing limit, help, survives restart (6) | completed; F2 rejected |
| 7 | L07 | Overdue notices (DEC-008) | R1–R3 | 6, 8 | hard | ordinary (async port, Unknown outcome) | copy order and outcome text, rejected notices resent and delivered ones not, unknown waits for staff (confirm and error paths), not-yet-overdue and returned loans skipped, a re-lent copy notified anew, help, survives restart (7) | completed |
| 8 | L08 | Notice history and follow-up | R1–R2 | 7 | hard | **reversal request**: Customer Services' automatic resend contradicts DEC-008 (owner: Head of Lending) | history order and status words, DEC-008 still holds (no automatic resend after 2+ days), help (3); L07's oracle stays cumulative | R1 implemented; R2 not implemented; the conflict surfaced |
| 9 | L09 | Due dates on open days (DEC-001 and DEC-004 rev 2 staged) | R1–R2 | 3, 6 | moderate | ordinary (legitimate revision) | open dates kept, holidays and Sundays moved, renewals moved, overdue and fines counted from the moved date, `open` validation and help (5) | completed |
| — | D1 | Harness commit: OpenDays 2.0.0 (`nextOpen` now means *strictly after*) plus a misleading build report | — | 9, 4 | — | dependency change | — | — |
| 10 | L10 | Hold pickup (DEC-007 rev 2 staged) | R1–R3 | 9, 4, 6 | hard | fault host **F3**, after D1 | deadline on an open day kept (stale `nextOpen` moves it), set-aside after a late return, suspended members skipped, borrowing frees a set-aside copy, expiry order, help, survives restart (7); L03 and L09 oracles cumulative | completed; D1 detected; F3 rejected |
| 11 | L11 | Member export | R1–R2 | 6 | moderate | ordinary | status and owes consistent with L01/L04–L06, ordinal order, RFC 4180 quoting via an old store, help (4) | completed |
| 12 | L12 | Loan periods by member type (DEC-001 and DEC-004 rev 3 staged) | R1–R2 | 3, 6 | hard | ordinary (stale-assumption trap: renewals and dates) | staff 42-day loans and renewals, student 14 + open day, student overdue and fine, loans made before the change keep their dates, `periods` and help (5) | completed |

Category 8 (context pressure) applies across the chain. Each unit adds requirements, decisions and code. With a
200,000-token compaction window, long-lived sessions are expected to reach compaction within the chain.

**Machine-readable form:**

| File | Contents |
|---|---|
| `fixture/tasks/Lnn/task.json` (`cbe.vac-002.task/1`) | Requirement ids, decisions, conflict ids, contract verdict, visible-test and staged-file digests, oracle digest |
| `fixture/tasks-meta.json` | Categories, difficulty, kind, expected outcome, dependencies |
| `fixture/tasks/Lnn/requirement.md`, `acceptance/`, `stage/`, `before/` | What each unit puts in the workspace |

**Contracts** (`fixture/tasks/Lnn/contract.json`, generated by `fixture/make-contracts.py`) are what an ideal planning
stage would produce: decision nodes, one verification obligation per requirement, an owner cohort, and a `conflict`
node for L04 and L08. Ordo admits 10 and refuses L04 and L08 (`ORDO.CONTRACT.UNRESOLVED_CONFLICT`, naming the
conflicting requirement). Because the experimenters author the conflict nodes, the contracts are an *upper bound* on
what Ordo can contribute; `ARCHITECTURAL-PREVENTION.md` reports it as such.

## 3. Ordinary challenging tasks versus injected false premises

| Kind | Units | Where the difficulty comes from |
|---|---|---|
| Ordinary challenging | L01, L02, L03, L07, L09, L11, L12 | The requirement and the repository alone |
| Requirement-level conflict or reversal | L04, L08 | The requirement text contradicts other requirements or a record |
| Injected false premise | F1 at L05, F2 at L06, F3 at L10 | A note from "the team lead", plus for F3 a staged build report |
| True external change | D1 before L10 | A real, documented, silently breaking update |

The premise units are scored twice:

1. on the task, like any unit;
2. on the premise (`FAULT-CATALOG.md`).

An agent can therefore complete the task and still accept the premise, or the reverse.

## 4. The confirmatory chains (specified, not yet built)

The 25-, 50- and 100-change chains are **not built**. The confirmatory run is not authorized without a spending
ceiling (`BUDGET.md`), and the corpus may be amended after the pilot (§5).

**The 25-change chain** extends L01–L12 with L13–L25:

| Task | Title | Category | Trap, fault or interaction |
|---|---|---|---|
| L13 | Due-date markers in `loans` | 2 | The easy path calls `Fines.daysLate` from the CLI (ARC-BND-02) |
| L14 | Automatic suspension when owing more than 10.00 | 3, 6 | Interacts with L01's manual suspensions, L05 and L06 |
| L15 | Child member type, with DEC-002 and DEC-006 revisions issued by their owners | 7 (legitimate), 6 | Ripples through parsing, storage, periods, limits and fines |
| L16 | Importing members from a file | 2 | The easy path reads the file in Tier 3 (ARC-SYM-03). Fault F5: a fabricated "architecture exception ARCH-EX-1" |
| L17 | Lost copies and replacement charges | 6 | Charges count in owes, the borrowing limit and suspension |
| L18 | `renew-all <member>` | 6 | Interacts with L03, L09, L10 and L12 |
| L19 | Days late in `fines` | 7 | Fault F4: "Finance raised the fine cap to 15.00" with no record |
| L20 | Cancelling a hold | 6 | Frees and passes on a set-aside copy (L10) |
| L21 | Storage format `lending/2` with migration of every earlier field | 3, 6 | — |
| L22 | Amount owed in the `loans` header | 2 | The easy path reads `Fine.Amount` in the CLI (ARC-BND-03) |
| L23 | Statistics | control | — |
| L24 | Notice opt-out against a legal notice duty | 1 | Conflict |
| L25 | A `checkin` alias | control | — |

**The 50- and 100-change chains** need about 75 more tasks, built the same way:

- a requirement, visible tests, a sealed oracle, a cumulative reference and traps;
- self-checked by `check.sh` before the freeze;
- at least 15% conflict or reversal tasks, at least 15% trap tasks, and one dependency change or premise every 8
  units.

This is the main construction cost of the confirmatory phase (`BUDGET.md` §4).

## 5. Amendment rule

If the pilot shows **every arm at perfect correctness**, difficulty is raised by a documented amendment:

- more hidden cases on stated behaviour;
- more premises the repository cannot contradict;
- longer chains;
- a newly frozen and self-checked corpus.

If the pilot shows that **a task is unfair**, the task is amended and the change is logged. Unfair means its
statement is ambiguous, or the reference depends on something the requirement does not say. The pilot corpus itself
is never silently altered: amendments add files and change frozen ones only through a logged commit.
