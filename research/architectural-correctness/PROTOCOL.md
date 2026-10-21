# ARCH-001 protocol: Echelon architectural correctness

**Status:** PREREGISTERED. Instruments frozen at 2026-10-21T10:13:56Z (`pins.json`, `sealed/SEAL.json`) in the commit
titled "ARCH-001 PREREGISTRATION". Every later change is a dated amendment in §13. The pilot (§10) runs on these
frozen instruments, and its results are excluded from confirmatory analysis. The confirmatory order is generated
after the pilot by the §9 rule and committed as an amendment before the first confirmatory trial.

**Owner:** coordinator session `session_01E9jW5aZuFTf7HzifRjcs7y`, branch `claude/echelon-architectural-correctness-m4glhq`.

**Independence:** ARCH-001 runs separately from REL-001 run-03. It never writes under `research/experiments/REL-001/`,
and it never uses REL-001's worktrees, state directories, pins or run ids.

## 1. Question and hypotheses

**Do Ordo decision contracts combined with mechanically enforced architectural boundaries produce fewer structural
defects and lower total lifecycle cost than natural-language architectural guidance alone?** This is treated as a
hypothesis to test.

| Id | Hypothesis | Contrast (metric) | Predicted |
|---|---|---|---|
| Primary | Ordo plus enforcement lowers total cost per fully correct requirement against requirements only | D vs A, cost per accepted requirement (ratio − 1) | < 0 |
| H1a | Four-tier guidance reduces architectural violations | B − A, severity-weighted DET violations per trial at S2 | < 0 |
| H1b | Four-tier guidance raises architectural acceptance | B − A, architectural-acceptance rate | > 0 |
| H2 | Ordo contracts improve decision fidelity beyond guidance | C − B, decision-test pass rate | > 0 |
| H3 | Mechanical enforcement reduces violations beyond Ordo contracts | D − C, severity-weighted DET violations at S2 | < 0 |
| H4 | Enforcement reduces lifecycle rework | D − C, phase-2 rework lines in pre-existing files | < 0 |
| H5a / H5b | Ordo plus enforcement lowers cost per fully correct requirement | D / C − 1 and D / A − 1 | < 0 |
| H6 | Benefits grow with cross-tier dependency count | slope over tasks of mean (D − A) violation difference on `crossTierCount` | < 0 |

H7 (continuous grouped execution) is **not** tested here. Every trial is one task, and grouping is not a factor.
H7 is listed as a follow-on experiment in IMPLEMENTATION-RECOMMENDATIONS.md.

## 2. Design

A 4-arm, within-task design with the arms cumulative:

| Arm | Receives (in addition to the previous arm) |
|---|---|
| A | The Lending repository, the requirement, visible acceptance tests, the core brief (role, build/test, `submit`, limits). No architecture material. |
| B | `docs/architecture/`: SDE-DOCTRINE-003 byte for byte, plus `LENDING-ARCHITECTURE.md` (tier map, allowed directions, placement rules). |
| C | `docs/contracts/T<n>.contract.json` (`ecir/1`); the pinned `ordo` on PATH. The brief tells the agent to run `ordo ecir check`, implement only admitted requirements, refuse conflicting parts with the reason, and cite each `DEC-` id in the code that realises it and in a test. |
| D | `archcheck` on PATH with a copy of the policy outside the workspace. The brief tells the agent to run `archcheck verify` during development. `submit` additionally requires `archcheck` to exit 0 on the committed HEAD. |

**C versus D isolation.** Completion orchestration is identical in every arm:

1. Commit.
2. Run `submit` (at most 3 per phase; it checks a fresh clone of HEAD).
3. End with `ARCH001-DONE <head>`.

The only C/D difference is the `archcheck` material and the `archcheck` step inside `submit`. Praxis work protocol
and attested completion are **not** used in any arm. Using them only in C/D would confound workflow with
enforcement, and REL-001 studies that workflow. Conclusions are therefore about Ordo contracts and architecture
enforcement, not the Praxis protocol (§12).

**Held constant across arms:**

- Model `claude-opus-5-5` and Claude Code 2.1.306 headless.
- Tools: Bash, Read, Edit and Write; no MCP.
- Starting commit (fixed date, identical hash).
- Requirements and visible tests.
- Hidden oracle, policy and probes.
- Budget: 45 min per phase, 3 submits per phase.
- Evaluation environment: .NET SDK 10.0.402.
- Wrapper prompt and core brief.

**Isolation (K1).** Each phase is its own `claude -p` process with:

- a fresh `HOME`, `CLAUDE_CONFIG_DIR` and `--session-id`;
- a per-trial nonce in the appended system prompt;
- the orchestrator's additional directories, skills, messaging, session links and tokens unset (`harness/agent-config.json .environment`).

Workspaces are separate directories under `/home/user/arch001-runs/`. The tool-definition prefix (about 3.3k tokens)
can still be cache-shared between concurrent trials. This is measured per phase and reported, and it is the same
across arms in expectation.

**Randomisation.**

- Confirmatory order: tasks × replicates blocks, with arm order randomised within each block and blocks shuffled
  (`harness/randomize.py`, seed 20261022).
- The runner (`harness/run-queue.sh`) executes the order with concurrency 3 and starts trials in that order.
- The pilot has its own order file.

## 3. Tasks

Eight tasks are run against the fixture `fixtures/repo` (Lending: four F# projects, one per tier, about 816 lines,
DEC-001…DEC-008). Each has:

- an initial requirement and a hidden follow-up;
- visible acceptance tests;
- an `ecir/1` contract per phase;
- sealed oracle tests, sealed probes and sealed reference solutions.

`fixtures/check.sh` shows, for every task:

- the start repository fails the task;
- the good reference passes visible tests, the oracle and `archcheck`;
- the trap reference passes all functional tests but fails `archcheck`;
- the follow-up oracle fails on the initial good solution and passes on the follow-up good solution;
- Ordo admits every contract except T5's initial contract, which it refuses for `UNRESOLVED_CONFLICT`.

| Task | Mission categories | Notes |
|---|---|---|
| T1 Renewals at the command line | 1, 5 | Trap: CLI computes eligibility |
| T2 Loan history persisted | 2, 3 | Follow-up: second persistence provider touching no Tier 1–3 file |
| T3 CSV bulk import | 4 | Trap: CLI bypasses the use case |
| T4 Overdue notices, Succeeded/Failed/Unknown | 6 | Asynchronous outcomes with reconciliation |
| T5 Fines with a requirement conflicting with DEC-006 | 7 | Correct: implement the rest, refuse R3 |
| T6 Hold pickup and expiry across all tiers | 9, 8 | |
| T7 CLI refactor preserving behaviour | 10 | Follow-up: second UI surface |
| T8 ISBN-13 validation | control | Enforcement is expected to give no benefit; measures overhead |

Category 8 (changes that make later requirements expensive) is exercised by every follow-up. Seven tasks admit a
functionally correct but architecturally invalid solution. Trap descriptions and expected placements are sealed
(`sealed:task-private/`).

## 4. Procedure per trial

1. **Setup.** Create the workspace and the base commit, then commit the arm material. Snapshot pristine copies and
   integrity hashes.
2. **Phase 1.** The agent implements the initial requirement. `S1` is the last submitted commit, or HEAD if none.
3. **Transition.** The harness commits the follow-up requirement and its visible tests (and the follow-up contract
   for C/D) on top of `S1`. The follow-up is never present in phase 1.
4. **Phase 2.** A new isolated session works the follow-up. `S2` is defined as for phase 1.
5. **Scoring.** `score.sh`/`score.py` use pristine harness-side inputs only. They produce
   `observations/<RUNID>.json` (`arch001.observation/1`).
6. **Review.** `review.sh` runs a blinded review of the scrubbed change sets. Its cost is recorded as evaluation cost.

## 5. Measurements

The full list is in SCORING.md and `scoring-spec.json`.

- **Per phase:**
  - input, output, cache-read and cache-write tokens, taken from the session log (deduplicated by message id);
  - model cost (`total_cost_usd`, cross-checked against the price table);
  - tool calls by tool;
  - test executions and verification executions;
  - wall time.
- **Per requirement:** functional pass, architectural acceptance and acceptance itself.
- **Per trial:**
  - severity-weighted DET violations, HEU findings and new violations;
  - decision-test pass rate, conflict handling and ARC-TRC-01 coverage (C and D);
  - phase-2 files changed, files rewritten, rework lines, broken visible tests and regression failures;
  - first-pass correctness and escaped defects;
  - human interventions (expected 0; any is recorded).

## 6. Integrity of evidence

- **Independence.** Scoring never uses anything from the workspace except the evaluated commit. The verifier refuses
  a policy, contract or probe file inside the evaluated repository.
- **Sealed material.** Oracle tests, probes, reference solutions and private task metadata are kept in
  `/home/user/arch001-sealed`, outside every repository. At the freeze, an encrypted archive of the sealed tree is
  committed (`sealed/arch001-sealed.tar.gz.enc`, AES-256-CBC with PBKDF2, 180 files). `sealed/SEAL.json` records the
  plaintext tarball's sha256 and the sha256 of the per-file manifest. The manifest itself stays unpublished until the
  results, because its file names would hint at the trap locations. The key and manifest are published with the
  results, so anyone can verify that the oracle was not changed after the freeze.
- **Agents cannot change the oracle, the policy or the verifier.**
  - OS-level separation (a different Unix user) was unavailable: the environment's policy refused it.
  - Agents therefore run as the same user, and two controls compensate. Every tool call is scanned for access to
    protected locations (X4). Every protected artefact is hashed before and after each trial (X-integrity).
  - Both conditions exclude the trial.
  - A tampered copy cannot change a score, because scoring uses pristine copies.
- **Exact-revision binding.** Every `submit` verdict, oracle run and verifier report names the commit and the tree
  hash it evaluated.
- **No concealment.** Failed submits are in the harness-side ledger. Oracle and verifier outcomes are produced by the
  harness. An agent's final claims are never scored.

## 7. Analysis (preregistered code: `analysis/analyze.py`)

**Primary metric.** For each arm:

- numerator: total model cost over all non-excluded trials and both phases, including failed attempts, retries and
  timeouts;
- denominator: the number of accepted requirements (2 per trial).

The primary contrast is D/A − 1. The companion metric is cost per completed task (phase-2 submit PASS).

**Inference.**

- Two-stage cluster bootstrap: resample tasks, then replicates within each task. A sampled block carries all of its
  arms.
- 10,000 resamples, seed 20261022, percentile 95% intervals and bootstrap p-values.
- Holm step-down across the secondary family H1a–H6.

**Classification.**

- **Supported:** Holm-adjusted p < 0.05 with the estimate in the predicted direction. For the primary contrast, the
  interval excludes 0 in the predicted direction.
- **Not supported:** the same in the opposite direction, or the 95% interval lies inside the equivalence margin:

  | Contrast | Margin |
  |---|---|
  | Primary, H5 | 10% |
  | H1a, H3 | 0.5 severity points |
  | H1b, H2 | 0.10 |
  | H4 | 10 lines |
  | H6 | 0.25 |

- **Inconclusive:** otherwise, or fewer than 2 usable blocks.

**Descriptive.**

- every metric by arm and by task;
- HEU and review scores;
- the cache share;
- a sensitivity analysis without X5 trials;
- the T8 control task separately (overhead).

Architecture claims never rest on functional tests alone.

## 8. Exclusions

| Code | Condition | Handling |
|---|---|---|
| X1 | Harness failure before the agent starts (no observation) | Re-run under the same id |
| X4 | Contamination | Excluded |
| X-integrity | Tamper | Excluded |
| X5 | Timeout | Scored as is |

A commit the verifier cannot evaluate counts as not accepted. It is removed only from violation-count metrics.
Exclusions are decided by the scan and the hashes before any outcome is inspected, and every exclusion is reported.

## 9. Sample size (decided from pilot variance, never from the observed treatment effect)

`analysis/power.py` on the pilot observations computes two figures:

- replicates per (task, arm) cell for 80% power, two-sided α = 0.05, on:
  - a D − A architectural-acceptance difference of **0.20**, using the acceptance rate **pooled over all pilot arms**;
  - a D/A cost ratio of **0.70**, using the log-ratio variance **pooled over all pilot trials**;
- the largest replicate count the resource cap allows. The cap is **USD 1,500** of confirmatory model cost.

The rule is fixed in advance:

```
replicates = max(2, min(needed, maxReplicatesUnderCap, 5))
```

If the cap binds, the report says the experiment is underpowered for the stated effects. The detectable effects,
the cap and the rule are fixed before the pilot runs.

## 10. Pilot

**Scope:** T1 and T8 × 4 arms × 1 replicate, both phases (`harness/pilot-order.json`). The label is `pilot`, and the
pilot is excluded from confirmatory analysis.

**Purpose:**

1. Verify instrumentation end to end: stream capture, cost cross-check within 1%, submit ledger, oracle,
   `archcheck`, scan and integrity.
2. Confirm the tasks are solvable within budget in every arm.
3. Supply the variance inputs for §9.

The pilot may only change the instruments, through a dated amendment, when it reveals a defect. It must not change
the hypotheses, the metrics or the sample-size rule.

## 11. Version pins (frozen at preregistration)

Recorded in `pins.json` (freeze 2026-10-21T10:13:56Z):

- cohort-based-engineering commit;
- ordo, praxis and dokimos commits;
- the ordo binary sha256;
- the `archcheck` dist sha256 and its source commit;
- the policy sha256;
- the pack file sha256;
- the doctrine sha256;
- the fixture-tree and sealed-tree digests (from `fixtures/check-output.txt`);
- the sealed archive sha256;
- the brief template sha256;
- the agent-config sha256;
- the price-table sha256;
- the .NET SDK, Claude Code and model versions.

## 12. Threats to validity and narrowed conclusions

- **One fixture, one language, one model.** The fixture is small and synthetic. External validity to Summa and
  Signal is argued, not shown.
- **The doctrine's own evidence is thin.** SDE-DOCTRINE-003's supporting theory rests on a single application
  (confidence 0.75). Its rules are taken as normative here (A8).
- **Praxis is not tested.** No Praxis workflow runs in any arm. C and D test Ordo contracts and `archcheck`
  enforcement.
- **D sees the same deterministic rules that score it.** This is the treatment. Probes, oracle, HEU findings and the
  blinded review measure beyond it, and conclusions about H3 are stated as "violations of the enforced rule set".
- **Most traps hit the boundary rules.** Several traps violate ARC-BND-03, so H3's sensitivity is concentrated on
  presentation/projection placement.
- **Concurrency and the shared cache prefix** add wall-time and cache noise. Both are measured.
- **Exposure of pilot oracle test names.** Commit `8fb76b5` briefly published the pilot observations, which include the hidden T1 and T8 oracle test names. Observations stay out of git until all trials end (`.gitignore`). Any agent reading the repository or GitHub is excluded as X4.
- **Exposure of trap metadata.** Trap descriptions were briefly public in commit `2f15e59` before being moved to the
  sealed store. The contamination scan covers the GitHub organisation and the local research checkout.

## 13. Amendments

| Date | Change | Reason |
|---|---|---|
| 2026-10-21 (pre-freeze) | `power.py` pools rates and spreads across arms and drops the observed-difference target | Sample size must not depend on the observed treatment advantage |
| 2026-10-21 (pre-freeze) | ARC-BND-01..03 scope changed from `Lending.Host.Cli` to all Host presentation (every Host module except Persistence and Composition); pack text and probes updated; verifier sample `bnd03-relocated` added | Closes an evasion in which logic moved into a new Host namespace escaped the boundary rules |
| 2026-10-21 (pre-freeze) | Every arm's core brief: "do not add, remove or rename projects" | An unmapped project makes `archcheck` exit 2; the rule is operational and identical in every arm |
| 2026-10-21 A1 (post-freeze, from the pilot) | Arm D's contract is passed to `archcheck` from outside the workspace: the agent's copy is in `tools/contracts/`, and `submit` uses the pristine copy. `submit` prints the verifier's own error text when it cannot evaluate. The scan fixes a run-id boundary bug, where `cd RUN;` was read as another run. Own-state X4 is narrowed to session logs of another phase, scores, reviews and pristine copies; the gate's agent-facing outputs are advisory. Arm D's two pilot trials are re-run as replicate 2. | Instrument defect revealed by the pilot. In pilot T1-r1-D and T8-r1-D, every `archcheck` run (dev-time and in `submit`) exited 2 because the verifier refuses a contract inside the evaluated repository (an integrity rule), so arm D received no enforcement. The empty error message sent the agents into their own harness state, which the scan then flagged as X4. No hypothesis, metric, task, oracle or sample-size rule changed. Arms A–C are unaffected. |
| 2026-10-21 A2 (post-pilot, before any confirmatory trial) | Confirmatory sample size = 2 replicates per (task, arm) cell: 64 trials, 128 phases. `harness/order.json` regenerated with `randomize.py --replicates 2` (seed 20261022; order sha256 0cf65f1974f0e044…); planning output in `analysis/pilot/power.json` | The §9 rule applied to the pilot's pooled inputs: acceptance rate 0.95 (clamped), log-ratio variance 0.0466, mean cost USD 0.60 per trial. needed = 2, the cap allows 77, so replicates = max(2, min(2, 77, 5)) = 2. No arm difference was used. The report states the power limits that follow from n = 2 near ceiling. |
| 2026-10-21 A3 (during confirmatory scoring; arm-blind) | Phase-2 regression excludes initial-oracle tests that the follow-up deliberately supersedes. "Superseded" means the InitialOracle tests that fail on the sealed follow-up-good reference (`harness/amendments/superseded.sh`, giving `A3-superseded.json`: T1 1, T3 2, T5 2, T6 3, T8 2, others 0). Conflict tests are scored at S1, where the conflict exists. Phase-2 decision tests count only the regression subset. All 64 observations are re-assembled. The as-run scoring is kept and reported as a sensitivity analysis. | Scoring defect seen in T3 and T5. Their initial oracles have no regression labels, so the fallback scored every initial test at S2, including tests their follow-ups change on purpose (T5 approves an amended DEC-006; T3 changes the CSV header and the copies rule). Every arm failed R2 identically on exactly those tests. The rule comes from the references, not from any trial or arm. |
| 2026-10-21 A4 (during confirmatory scoring; arm-blind) | Scoring passes the sealed per-task probes to `archcheck` unconditionally. The verifier steps are re-run at the recorded S1 and S2 commits (`score.sh --arch-only`), then observations are re-assembled. | Defect: `score.sh` detected `--probes` support through `archcheck verify --help \| grep -q` under `pipefail`. archcheck exits 2 on `--help`, so the detection always failed and the probes were silently dropped in every trial (`probesApplied: false`). The policy-level rules had run. The same detection dropped `--require-clean` from arm D's `submit` gate. That is harmless because `submit` evaluates a fresh clone of the committed HEAD, so it is recorded only. |
