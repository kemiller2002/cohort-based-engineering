# Echelon parallel research: integrated coordinator report

Date: 2026-10-20. Coordinator session `session_0174JuJ3F3WXwdPbjo3Pk5P7`. Pins and workstream state:
[`manifest.json`](manifest.json).

**Scope and integrity.**
- REL-001 run-02 is a preregistered confirmatory run. It was in progress (32 of 88 trials) in another session and was
  not modified.
- Run-02 data appear here only as exploratory, within-arm profiling (Worker D). No run-02 arm comparison is made.
- Historical observations (Worker B), new exploratory profiling (Worker D) and the run-03 draft (Worker C) are kept
  separate.
- Every number is taken from a committed file. Missing metrics are marked unavailable.

**Echelon has not been shown to be more efficient than bare Claude.** No valid controlled comparison of the two exists yet.

| Workstream | Deliverable | Tokens (worker) |
|---|---|---|
| A reliability | [`../reliability/readiness-report.json`](../reliability/readiness-report.json), [`README`](../reliability/README.md) | ~170k |
| B historical audit | [`../token-efficiency/HISTORICAL-EVIDENCE.md`](../token-efficiency/HISTORICAL-EVIDENCE.md), [`evidence-index.json`](../token-efficiency/evidence-index.json) | ~164k |
| C experiment design | [`../experiments/REL-001/protocol/run-03.md`](../experiments/REL-001/protocol/run-03.md) (DRAFT), [`run-03/`](../experiments/REL-001/run-03/) | ~354k |
| D overhead profiling | [`../token-efficiency/OVERHEAD-ANALYSIS.md`](../token-efficiency/OVERHEAD-ANALYSIS.md), [`overhead-schema.json`](../token-efficiency/overhead-schema.json), [`profiling/`](../token-efficiency/profiling/) | ~219k |

## 1. Which previous Echelon optimizations have demonstrated token savings?

The only demonstrated saving is **grouped execution of high-affinity work in one long-lived session**. Every comparison
used the same model (`claude-opus-5-5`) and counted platform total tokens.
- **A021:** −46.2% (TE-H01).
- **A021-R2:** −49.0% (TE-H02).
- **A024:** −40.5%, one continuous session against code-only resets (TE-H03).

Qualifications:
- All three runs come from one cohort family in one repository.
- Quality did not consistently follow tokens: in A024 the architecture score reversed.
- About 98% of the tokens are cache reads, so raw totals overweight the cheap cached prefix.

There are two demonstrated regressions:
- **Structured handoffs:** +10.5% (A024 C, TE-H04).
- **Verified-completion protocol:** +31.7% tokens per verified requirement (REL-001 run-01, exploratory, TE-H07).

A022 is sealed. Its values are **withheld** (TE-H05, TE-H06): condition labels can be inferred from item IDs and metrics
file names, and that inferability is recorded as a blinding-leak finding for A022's owners.

## 2. Which are implemented but unmeasured?

- **TE-H12:** compact typed construction handoff (praxis#263).
- **TE-H13:** mechanical-first routing. Reasoning tokens are recorded as `unavailable`.
- **TE-H14:** cumulative usage attribution. This is a measurement capability, and it is validated.
- **TE-H15:** provider usage pacing. It redistributes usage rather than reducing it.
- **TE-H19:** REL-001 F4 (one verifier run, derived completion arguments), shipped in Praxis 3.17.0.
  - The code works: Worker A measured 1 verifier run and 0 `validate-run` calls.
  - Its token effect is measured only by run-02 arm D, which is in progress.
- **TE-H11:** orchestration-waste guards, from the A021 and A024 lessons.

## 3. Where does the current workflow spend the most tokens?

These figures come from Worker D's §3.1, §3.2 and §3.8. Token shares are a turn-equivalent model, because per-request
data is unavailable.
- **The fixed runtime prefix (~40.6k tokens) is re-read on every request.** It accounts for 67–75% of cache reads and
  24–31% of estimated cost. The mean context per request is 57–62k.
- **Cache writes are 57–65% of estimated cost.** In run-02, part of that is inferred cold-prefix misses.
- **Mandated workflow commands are about 27% of tool calls.** Run-01 treatment's extra ~130k tokens per run come to about
  2 extra turns at ~58k context each.
- **Briefs and directives are small** (~0.5k and ~2.7k tokens). They are not a meaningful cost driver.

## 4. What proportion of overhead comes from caching, verification, coordination and repeated context?

Run-02 Echelon arms are pooled and exploratory. Run-01 D is shown in parentheses.

| Class | Share | Basis |
|---|---|---|
| Caching (read + write) | 99.96% of tokens, 98.5% of cost (98.7%) | measured; output is a lower bound |
| Repeated context (prefix re-read) | 66.9% of cache reads, 24.0% of cost (74.5% / 30.8%) | derived |
| Avoidable cache misses | 24% of cost (7%) | inferred |
| Verification | 9.1% of tokens (est.), 10.8% of elapsed time | estimated / measured |
| Coordination | 10.0% of tokens (11.1%) | estimated |
| Completion | 9.1% of tokens (est.), 1.0% of elapsed time | estimated / measured |
| Duplicate tool calls, repeated reads | unavailable | needs per-request data |

Output tokens are a lower bound, so cost is understated by roughly 5.6–43%.

## 5. Which improvements are already implemented?

Praxis 3.17.0 and Dokimos 0.7.0 implement F1–F5:
- **F1:** attested receipts.
- **F2:** per-agent attribution.
- **F3:** clean completion identity.
- **F4:** derived completion and a single verifier run.
- **F5:** price table, which exists only on the run-02 branch.

Worker A verified F2, F3 and F4 in code and against the run-02 arm-D observations. The Praxis test suite passed
2330/2330 against the real Dokimos.

The ownership, readiness and evidence-binding mechanisms from run-01 removed whole failure classes:
- duplicate active owners fell from 15 to 0;
- accepted invalid contracts fell from 11/11 to 0/11.

## 6. Which improvements require additional work?

- **F1 is not trustworthy against the agent being verified.** Worker A's probes on the released binaries showed two
  ways to complete as verified with no genuine test run:
  - **PROBE-3:** the attestation requirement is read from the agent's own `ros.json` (`FileWorkClaims.fs:251`).
  - **PROBE-4:** the agent can pin its own signing key through the caller-chosen authority path
    (`FileDerivedCompletion.fs:260-266, 308`).
  - Filed as **REL-GATE-004** (praxis#279).
- **REL-GATE-003 is open and unclaimed** (non-attested mode is unlabelled and not forced).
- **F6 is open:** the rollout gate (PRAXIS-REL-006) is still captured.
- **Measurement correctness (P1):**
  - per-request usage ledger (REL-TOKEN-001);
  - final output tokens (REL-TOKEN-002);
  - cache state recorded per agent.
- **Removing redundant execution:**
  - `praxis work finish` (REL-TOKEN-003);
  - `verify` as the agent's final test run.

## 7. Is the reliability system ready for controlled comparison?

**No for the optimized treatment. A controlled comparison is not ready.** The readiness report gives
`optimizedWorkflowReady=false` and `attestedConfigurationReady=false`.

| Condition | Status |
|---|---|
| F1 attested forgery refused (harness-controlled trust root) | PASS |
| F1 agent cannot fabricate attestation | **FAIL** (REL-GATE-004) |
| REL-GATE-003 resolved | **FAIL** |
| F2, F3, F4 (derived arguments, single test run), regression tests | PASS |
| F5 price table (not mandatory) | PASS |
| F6 rollout gate | **FAIL** |

Consequences for experiments:
- **Run-02 arm D** was exposed to the PROBE-3 and PROBE-4 attacks, which its scoring would not have detected. No attempt
  is observed in its committed data.
- Worker D also found a cache-state confound in run-02: 9 of 19 Echelon trials look cold-started, unevenly across arms.
- Both points went to the run-02 owner as validity notes. Amendments are their decision.
- **The integration gate for optimized-treatment trials is closed.** Run-03 must not start until all of the following hold:
  - REL-GATE-003 and REL-GATE-004 are fixed and released;
  - the arm-D pins are frozen;
  - the fairness review is done;
  - the protocol is committed as a preregistration.

## 8. What is the next experiment needed to establish Echelon's economic advantage?

1. **Let run-02 finish**, then run its preregistered analysis. It is the first four-arm comparison, but its arm D carries
   the exposures above.
2. **Run REL-001 run-03** (draft ready).
   - Tasks: 8 new tasks with 15 requirement units, including tasks where an unverified completion is wrong, 72 new
     hidden oracle tests and 13 trap variants.
   - Cache: an isolated per-trial cache option (K1), with cache state measured on every trial.
   - Arm D runs on a build that closes REL-GATE-003 and REL-GATE-004, with REL-TOKEN-001 and -002 instrumentation.
   - The primary outcome is cost per independently verified requirement, arm D against bare Claude.
   - Sample: 96 trials, which detects about 20% at the pilot variance.
3. **Test grouping directly.** Grouping is the only demonstrated saving, but it has never been tested against bare
   Claude. A grouping factor (independent against high-affinity grouped) belongs in a follow-on run, not in run-03.

## Prioritized backlog

| # | P | Item | Where | Evidence |
|---|---|---|---|---|
| 1 | P1 / gate | REL-GATE-004: trust root from a protected source (base-branch `ros.json`, host-fixed authority) | praxis inbox (#279) | `../reliability/evidence/`, readiness-report F1 |
| 2 | P1 / gate | REL-GATE-003: label attested or unattested; `requireVerifiedCompletion` implies attestation | praxis inbox (queued, unclaimed) | readiness-report PROBE-2, `gate-report.json` |
| 3 | P1 | REL-TOKEN-001: per-request usage ledger | praxis inbox (#279) | OVERHEAD-ANALYSIS §1, §5.1 |
| 4 | P1 | REL-TOKEN-002: final output tokens | praxis inbox (#279) | OVERHEAD-ANALYSIS §5.2 |
| 5 | P1 | Record per-agent cache state in observations; retain trial transcripts | run-03 harness (done); run-02 (owner's call) | OVERHEAD-ANALYSIS §3.3 |
| 6 | P1 | Move the F5 price table to cohort main | cohort (with run-02 merge) | readiness-report F5 |
| 7 | P2 | `verify` as the final agent test run, with a failure excerpt | Praxis brief and verify output | OVERHEAD-ANALYSIS §3.4, §5.4 |
| 8 | P4/P5 | REL-TOKEN-003: `praxis work finish` | praxis inbox (#279) | OVERHEAD-ANALYSIS §5.6 |
| 9 | P1 / gate | F6: PRAXIS-REL-006 rollout gate, after items 1–2 | praxis queue | readiness-report F6 |
| 10 | P3 | Minimal tool set to shrink the ~40.6k prefix; measure its composition first | harness | OVERHEAD-ANALYSIS §3.2, §5.5 |
| 11 | P5 | Warm one agent, then fan out | orchestrator | OVERHEAD-ANALYSIS §5.7 |
| 12 | P5 | Complete and unseal A022; fix the label leak | praxis experiment owners | HISTORICAL-EVIDENCE TE-H05, TE-H06 |
| 13 | P5 | Default to continuity for high-affinity groups, keeping the per-member criterion check | Praxis planner | TE-H01–H03 |
| 14 | — | Freeze run-03 pins, do the fairness review, commit the preregistration, then the pilot | cohort | run-03 README G1–G8 |
| 15 | P6 | Adaptive routing: **not started**; it waits on run-02 and run-03 evidence | — | — |

Not covered (repositories not attached): `research-documents` (CONSTRUCT-008 raw usage, TE-H08) and `construct-010-trials`.
