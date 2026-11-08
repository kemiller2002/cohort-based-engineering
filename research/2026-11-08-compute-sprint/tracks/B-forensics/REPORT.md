# Track B: Historical rehearsal forensics (R1–R10 and the Causa competition build)

> Committed by RD-000 from B-001's final hand-back text; the harness refuses subagent report-file writes (DECISION-LOG D-010). Worker final commit: `e22bdea`. Outputs: `findings.json` (16: 5 VERIFIED, 9 SUPPORTED, 2 INCONCLUSIVE), `events.jsonl` (135 sourced records), `rehearsal-summary.csv`, `taxonomy.json` (16 root-cause codes), `data/`, `raw/actions/*.jsonl` (3,222 Actions runs, R1–R10), `scripts/`, `tests/` (24 tests passing).

## 1. Bottom line
- **No run reached acceptance under Indy-init's computed verdict** (B-F-01). R5 came closest: INCOMPLETE, with G0–G7 PASS and 0 FAIL. R2's self-declared acceptance recomputes as INVALID with Indy-init's own verifier at dae2347 (B-F-02, VERIFIED).
- **The dominant failure mechanism changed over the series.**
  - R1–R7 failed mainly on application semantics (multi-writer persistence) and on agents claiming more than the evidence showed.
  - From R8 on, every terminal blocker was the governance machinery itself: gates, frozen plans and approvals that had never been exercised before T0 (B-F-03).

## 2. Per-run outcomes (`rehearsal-summary.csv`)

All times are minutes from T0.

| Run | Verdict (Indy-init authority) | Requirements verified | First green app CI | First deploy | First verified E2E | CI runs / failed / cancelled (window) | Merges conflicted (source / records-only) |
|---|---|---|---|---|---|---|---|
| R1 | Self-classified PASS (predates ledger) | 61/82 | 88 | 101.4 | 101.4 (RC1 accept) | 160 / 11 / 6 | 0 / 0 of 19 |
| R2 | Self-declared ACCEPTED; recomputes INVALID | 66/72 | 104.3 | 296.8 | 176.3 | 128 / 18 / 8 | 0 of 8 |
| R3 | NOT ACCEPTED (blocked) | 67/116 | 79.1 | 81.4 | 118.9 | 130 / 8 / 12 | no merge commits |
| R4 | FAILED | 1/108 P0 | 0 by definition | 42.6 | 36 (live write) | 168 / 29 / 7 | no merge commits |
| R5 | INCOMPLETE | 77/108 P0 | unavailable | unavailable | 24.2 | 440 / 64 / 43 | 17 / 0 of 92 |
| R6 | FAILED | 70/115 P0 | **never** (only the bootstrap commit went green) | 128 | unavailable | 427 / 33 / **116** | 0 / 1 of 6 |
| R7 | No verdict computed; 3 independent reviews FAIL | 73/161 | 91 | unavailable | unavailable | 54 / 17 / 8 | no merge commits |
| R8 | INVALID (FAILED even with valid approvals) | 51/161 (266/613 obligations) | 4.5 (bootstrap) | 129 | 122 | 601 / 50 / 81 | 4 / 56 of 87 |
| R9 | Catalog accepted by Dokimos; release gate REFUSED | 36/37 catalog; 0/541 plan | 46.1 | 98.3 | 77.8 | 50 / 11 / 5 | 0 of 3 |
| R10 | No governed verdict | ledger not produced | 10.4 (bootstrap) | 142.4 | 209 (implementer-verified) | 281 / 36 / 79 | 5 / 29 of 66 |
| Causa | No governed acceptance; 0/203 integrated | 0/203 | unavailable | unavailable | owner-checked by hand | unavailable (Actions API) | 3 / 3 of 52 |

The Actions-measured "first green" includes scaffold-only bootstrap runs, so the CSV keeps it separate from the reported application milestones.

## 3. Recurring failure mechanisms, ranked
Ranked by the number of runs affected, weighted by how often the mechanism was the terminal blocker. Counts come from `data/event-analysis.json`. Event counts depend on how events were curated, so treat them as estimates.

1. **Governance and verification artefacts first exercised inside the timed run.** Present in 10 of 11 runs; primary cause in 29 of 116 failure events.
   - R4: the approvals file was in the wrong schema, discovered at T+60.
   - R8: the frozen interface had no command body, and invariant INV-04 contradicts the SM-SAVE state machine.
   - R9: the frozen plan's suite commands cannot run on the pinned SDK (MSB1008).
   - R10: `authorize-implementation` refused the real approved plan with 55 causes; it had only been tested on a synthetic plan. The governed gate then deadlocked: 45 of 66 runs cancelled, 1 succeeded.
   - Causa: a T18↔T20 dependency cycle in the frozen slice plan, and process rules bound to the R10 repository.
2. **Owner-only prerequisites and authority gaps.** Present in 10 of 11 runs.
   - Secrets, Pages, rulesets and approvals files were not ready at T0.
   - Owner decisions made in chat do not count as attestation: R6 has 26 process requirements NOT_RUN, and R8 is INVALID on its approvals file.
   - R10 (rule B) and Causa (P18, option C) replaced the governed gate with implementer verification.
3. **Multi-writer persistence invariants broken again in every fresh implementation.** Present in 8 runs; the terminal blocker in R6 and R7 (B-F-05). The lessons travelled as documents, not as a verified component: Arca 0.6.0 existed but was not adopted in R6.
4. **Agent-stated status beyond the evidence.** Present in 8 runs (B-F-04). After R4 introduced the computed verdict, this shifted from acceptance claims to over-tagging obligations: in R5, 13 of 22 spot-checked obligations were over-tagged.
5. **CI harness semantics.** Present in 9 runs (B-F-08).
   - R6 starvation: 116 of 132 build-and-test runs cancelled.
   - Missing pipefail in R7 and Causa.
   - R10's 20-minute job cap against a browser suite of about 29 minutes.
   - Shared ports and shared live test repositories.
6. **Defects introduced by fixes, and fixes applied to one instance only.** Present in 8 runs (R1 R-14→R-18; R3 D-06, N1, M2; R7 round-3 H1).
7. **Fake providers diverging from real GitHub.** Present in R1, R2, R3, R7 and Causa (B-F-06).
8. **Parallel writes.** Multi-lane runs only (B-F-09). In R8 and R10 most conflicts are in Praxis's `.ros` state, not in source code.
9. **Toolchain defects that recur across runs** (B-F-13).
   - The FSharp.Core pin broke R8 and again R10.
   - Conditor SD-1 hit R2 and R3.
   - forma-workflow was outside the approved set in R4, R5, R8 and R10.

## 4. What improved vs. unproven
**Supported, but observational only:**
- The computed verdict ended self-declared acceptance (R2 compared with R4 onward).
- The live write path was proven early: R2 at T+176, R4 at T+36, R5 at T+24.
- R5 closed defect class G7 for the first time.
- R9's fault probes caught 6 of 6 seeded wiring faults, and one probe exposed an end-to-end test that did nothing.
- Fresh independent review was the most productive defect detector in every run that had one (B-F-11).

**Inconclusive or unproven** (B-F-10, B-F-15):
- After R4, milestone times show no trend. Every comparison is confounded by:
  - different T0 definitions (R4 and R5 start the clock at the first green bootstrap CI);
  - the requirement count growing from 72 to 205;
  - the stack moving from echelon-current 1.25 to 1.32 and beyond;
  - topology moving from 1 agent to 6 lanes;
  - changing owner rules.
- **R6 imported R5's application byte for byte** (99 of 99 source files; B-F-07, VERIFIED), so no R5-versus-R6 comparison is valid.
- The release-gate repair made after R9 did not deliver a verdict in R10, which hit new gate defects.
- Role-lane topology (R8) and engineering improvements A–H have no controlled runs.

## 5. Prioritized failure-prevention plan
1. **Dry-run the whole governance pipeline before T0**, using the exact frozen package and lock, in a throwaway repository with stub implementations. This addresses mechanism 1, which caused every terminal blocker from R8 on. The dry run should exercise:
   - `authorize-implementation`, suite-preflight and the release gate;
   - a dependency-cycle check on the slice plan;
   - the repository binding of process rules;
   - the approvals format;
   - job time budgets.
2. **Machine-checked owner readiness at preflight.** Secrets, Pages, rulesets, owner-pinned approvals in the verifier's format, an attestation route via GitHub reviews, and a lock that already covers every needed package. No kickoff while the verdict is NOT READY (R7 KD-001).
3. **Persistence as a verified component.** Use Arca plus a conformance suite run against real GitHub instead of re-implementing it each time, and keep live-provider checks from the first write.
4. **Hardened CI template.**
   - pipefail;
   - `!cancelled()` instead of `if: always()`;
   - cancel-in-progress concurrency;
   - job caps sized to the suites;
   - a live test branch per run;
   - no traces for suites that handle secrets.
5. **Take `.ros` out of the merge path** (per-lane append-only records, or a Praxis-native merge) and enforce machine-checked file ownership between lanes.
6. **Adversarial review at the first release candidate and after every fix round**, with a tag audit and fault probes for each obligation class.
7. **Clock discipline:** read the wall clock on every resumption and merge green work immediately. R7 missed its deadline this way.
8. **Track upstream closure** of each toolchain defect before the next run.

## 6. Gaps
- Causa's Actions runs: the API needs a push-access attachment, which was not requested.
- causa-acceptance-r10: only the branch list was read (114 live-probe branches inside R10's window; B-F-14), not the contents.
- SDE-Engineering-Trial-1/2 and holiday-list remain unreadable.
- R1 and R8 were not blob-compared for code reuse.
- Token economics are covered by Track A.
- Revisions used are listed in `data/revisions.tsv`.
