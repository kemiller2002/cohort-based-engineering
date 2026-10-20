# REL-001 run-01: results

Status: **complete** (2026-10-20). Protocol: [`protocol/run-01.md`](protocol/run-01.md) (preregistered, amendments A1–A4).
Gate: [`gate/gate-report.json`](gate/gate-report.json). Every number below is computed from a committed
result file. Nothing is estimated or imputed.

## Pinned systems
| Arm | Praxis | Dokimos | Ordo |
|---|---|---|---|
| baseline | 3.12.0 | — | — |
| treatment | 3.16.0 (`1dc19736…` linux-x64) | 0.6.0 | 1.17.0 (`ab9437f5…` linux-x64) |

## Completion gate
- **First evaluation: FAIL** on evidence binding (REL-GATE-001). Fixed in Praxis 3.15.0.
- **Second evaluation: FAIL** on O2 (REL-GATE-002), after Experiment B showed that contradictory
  decisions and unresolved conflicts reached verified completion. Fixed in Ordo 1.17.0 and Praxis 3.16.0.
- **Final evaluation: PASS**, 16/16 conditions.
- Experiment D ran only after the gate passed. Every evaluation is kept under `history`.

## Experiments A–C (deterministic case tables)
| Experiment | Measure | Baseline 3.12.0 | Treatment 3.15.0 | Treatment 3.16.0 |
|---|---|---|---|---|
| A: concurrent ownership | duplicate active owners | 15 | 0 | 0 |
| | stale completions accepted | 1 | 0 | 0 |
| | lost work | 0 | 0 | 0 |
| B: invalid decisions and contracts | invalid cases accepted (of 11) | 11 | 2 (B5b, B6a) | **0** |
| C: completion verification | unverified completions accepted (17 invalid cases) | 8 | 1 (C3b) | 1 (C3b) |

**C3b** is a forged passing result plus a forged `work.validation.observed` event, written by an actor
with write access to the repository. It remains accepted. Praxis can no longer *construct* a successful
packet without a recorded validation result (`ValidatedEvidence`, `BoundCompletionAuthority`), but the
record lives in the agent-writable tree. Closing this needs attested evidence (follow-up F1).

## Experiment D (agent trials)
12 trials: 3 tasks × 2 arms × 2 replicates, run in the preregistered randomized order.
- Every trial completed.
- 0 exclusions: no X2 model mismatch (every transcript was served `claude-opus-5-5`), no X4 oracle
  contamination, and no budget overrun (longest trial 128 s of the 45-minute budget).

**Preregistered analysis (`analysis/analyze.fsx` → `analysis/results.json`): inconclusive.**
- The script admits only runs with *complete* instrumentation.
- Cost is unavailable in every run, because no versioned price table exists and none is invented.
- So 0 runs per arm are eligible, against a required 6.
- Protocol rule X3 says incomplete instrumentation excludes a run "from token/cost comparisons only",
  so the script is stricter than the protocol text. It was **not** changed after the data were seen.

**Exploratory analysis (`analysis/exploratory.fsx` → `analysis/exploratory-results.json`).** It was
written after the data were seen, so it is not confirmatory. Token instrumentation is complete for all
12 runs. Each row compares 6 paired (task, replicate) blocks with a percentile bootstrap (10,000
resamples, seed 20261019).

| Measure | Baseline | Treatment | Change | 95% bootstrap interval | Pairs where treatment is higher |
|---|---|---|---|---|---|
| Tokens per verified requirement (Praxis report; A4) | 205,274 | 270,402 | **+31.7%** | +14.3% to +55.9% | 6/6 |
| Same, harness per-agent token count | 29,947 | 32,391 | +8.2% | +5.4% to +10.9% | 6/6 |
| Tool calls per run | 7.3 | 10.0 | +36% | +20% to +58% | 6/6 |
| Test runs per run | 1.0 | 2.17 | +117% | +100% to +150% | 6/6 |
| Elapsed time per run | 62.5 s | 99.0 s | +58% | +30% to +82% | 5/6 |
| Verified requirements (total) | 12/12 | 12/12 | 0 | — | — |
| Rework (attempts after the first, plus reverts) | 0 | 0 | 0 | — | — |
| Escaped defects | 0 | 0 | 0 | — | — |

Notes on the token figures:
- Praxis-report tokens are dominated by cache reads: the shared system-prompt prefix (A3).
- Output tokens recorded in the transcripts are a lower bound (A4).
- The harness count measures a different quantity, but it moves in the same direction.

## Hypotheses
| Hypothesis | Target | Result |
|---|---|---|
| Duplicate active claims | 0 | **Supported**: 0 (A, and D gates) |
| Invalid decisions accepted | 0 | **Supported** on 3.16.0: 0/11 (B) |
| Unverified completions | 0 | **Not met**: 1 of 17 invalid completion cases accepted (C3b) |
| H1: tokens per verified requirement | ≤ −20% | **Not supported**: preregistered analysis inconclusive; exploratory direction is the opposite (+32%) |
| H2: rework | ≤ −30% | **Not testable**: 0 rework in both arms |
| No increase in escaped defects | Δ ≤ 0 | **Consistent**: 0 vs 0, but the tasks did not produce defects in either arm |

## Threats to validity
- **Small sample and easy tasks.** Every baseline agent completed correctly on the first attempt.
  This is a ceiling effect: the experiment cannot show quality benefits from verification, only its cost.
  Experiments A–C show the failure classes the treatment removes; D did not exercise them.
- **Shared prompt cache.** Sub-agents of one orchestrating session share the cache, so no trial was
  fully cold (A3). Both arms were equally exposed.
- **Token attribution.** Tokens are attributed by run transcript directory (A4), not by Praxis's
  session-window rule, which cannot separate sub-agents (follow-up F2).
- **Lower-bound output.** Transcript output tokens are a lower bound. The harness count is a separate
  measure, kept as a secondary record.

## Follow-ups
Praxis intake: `.praxis/inbox/documents/2026-10-20-REL-001-results-follow-ups.md` (praxis#276).
- **F1:** attested validation evidence (C3b).
- **F2:** bind the provider session and agent to executions.
- **F3:** verified completion leaves the worktree dirty or moves HEAD past the verified commit
  (4 of 6 and 2 of 6 treatment runs).
- **F4:** reduce protocol overhead (one test run, derived completion arguments).
- **F5:** versioned price table.
- **F6:** gate `requireVerifiedCompletion` (PRAXIS-REL-006) on F1–F3.

Cohort-side (this experiment, for run-02):
- Align `analyze.fsx` eligibility with X3, so a missing metric excludes only its own comparison.
- Fix the D brief's redundant `cd repo` after `env.sh`.
- Populate `servedModels` from transcripts. The X2 check here was done directly on the transcripts.
- Add tasks where an unverified completion would be wrong, so D can measure the benefit, not only the
  cost.

## Recommendation: **MODIFY**
**Adopt** the ownership, readiness and evidence-binding mechanisms. They remove entire failure classes
at a fixed per-completion cost:
- 15 → 0 duplicate owners;
- 11/11 → 0/11 invalid contracts accepted;
- 8 → 1 unverified completions.

**Do not adopt as the default agent workflow yet.** On routine tasks the verified-completion protocol
added about 32% tokens per verified requirement with no measured quality gain. It also conflicts with
clean-commit identity (F3), and it still admits forged evidence from a repository writer (F1).

Ship F1–F4, then re-run D with tasks where completion can be wrong before enabling
`requireVerifiedCompletion` across Echelon repositories.
