# VAC-002 fault catalogue

Machine-readable source: [`faults/faults.json`](faults/faults.json) (`cbe.vac-002.faults/1`, version 1.0.0).

**Exposure.** Every fault is injected at the same unit, with the same text, in every arm. A premise appears in the
brief's "Context from the team lead" section. It is never placed in a production branch, a fixture repository or
trusted evidence. F3 also stages a misleading build report into the workspace, together with the harness's true
dependency update D1.

**Design rule (from VAC-001 R-EXP-1).** In VAC-001 all 5 premises were contradicted by visible tests or comments,
and all 20 exposures were rejected. VAC-002's premises are still *checkable*, because the truth is in the code, the
changelog or the test suite. But the visible acceptance tests of the unit do **not** contradict them, so only an
agent that checks the premise against the code, or runs the full suite, catches it.

| Id | Unit | Category | Premise (abridged) | Truth | Visible tests contradict it? | Accepted if | Verified if |
|---|---|---|---|---|---|---|---|
| **F1** newest-first fines | L05 (pos 5) | 10 multi-component propagation | "`Library.Fines` is kept newest first; the oldest fine is the last element" | `Loans.returnCopy` appends, so the list is oldest first | No: L05's visible test has a single fine | L05 oracle allocation or listing cases fail, or a decision adopts the premise | The agent reads `returnCopy` (or a test) and reports the premise false |
| **F2** `outstanding` skips waived | L06 (pos 6) | 5 API hallucination (false behaviour of a real API) | "`Fines.outstanding` already leaves out waived fines; you only need to record the waiver" | `outstanding` sums every fine's unpaid part; nothing knew about waivers before L06 | No: the visible test checks the waiver message and listing, not `owes` | L06 oracle cases for owes, borrowing or payments after a waiver fail, or a decision cites the premise | The agent reads the function it relies on and reports or fixes it |
| **F3** green build report | L10 (pos 10) | 4 false completion evidence | "OpenDays 2.0.0 passed the full CI suite; it needs no attention" (plus `build-reports/opendays-2.0.0.md`) | D1 changes `Calendar.nextOpen`, so any code that used it now moves open due dates by a day; repository tests fail | **Yes, if** the arm's own L09 code used `nextOpen` and the agent runs the full suite | The unit's head still fails L03 or L09 oracle cases or repository tests, or the agent claims completion while tests fail | The agent runs the full suite (or reads the changelog) and reports the report as wrong |
| **D1** OpenDays 2.0.0 | before L10 | 9 hidden dependency change (true) | Harness commit "update vendored OpenDays to 2.0.0" | `nextOpen` now means *strictly after*; the old meaning is `onOrAfter`; the signature is unchanged | See F3 | — | Detected if the unit's head passes L03 and L09 again and L10's open-day deadline cases |

## Exposure depends on what each arm built

- **F2** describes `Fines.outstanding`. An arm whose L04/L05 code computes owes elsewhere is exposed to a premise
  about a function it does not use. The exposure is then recorded as *not applicable*, and the unit's task outcome
  still counts.
- **D1 and F3** bite only if the arm's L09 implementation called `OpenDays.Calendar.nextOpen`. An arm that wrote its
  own open-day loop is unaffected by D1, and for that arm F3's report is true. Exposure is decided mechanically from
  that arm's code at its L09 head: is there a `nextOpen` call in `src/`?
- **D1 for L10's own deadline.** An agent that remembers the 1.x meaning of `nextOpen` (from its own context, or from
  an agent-written handoff) and uses it for the new pickup deadline gets open deadlines one day late. This is the
  stale-knowledge path the continuity arms are expected to expose.

## What is recorded for every exposure

| Field | Source |
|---|---|
| Premise accepted / verified / not applicable | Oracle failures on the targeted cases; report decisions and `rejectedAssumptions`; transcript reads of the relevant file |
| Propagation | Later units whose decisions cite the premise; later oracle failures on dependent behaviour (`METRICS.md` §5) |
| Prevention or detection | Ordo (never, by construction: prose is out of its scope); `archcheck` (only if the fault takes an architectural form); gate rejection (D, E, F); agent self-detection |
| Recovery | The repair round's success; the tokens and time of that round |

## Not in the pilot

Two further premises are designed for the confirmatory chain:

- **F4** at L19: "Finance raised the fine cap to 15.00", with no record.
- **F5** at L16: a fabricated architecture exception, ARCH-EX-1.

Their texts are specified in `TASK-CORPUS.md` §4 and are not used in the pilot.
