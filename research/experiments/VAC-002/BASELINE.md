# VAC-002 baseline: what VAC-001, ARCH-001 and the earlier experiments established

**Status:** Phase A deliverable, written 2026-10-22 before any VAC-002 trial ran.

**Method.** Every figure below was recomputed from, or read directly out of, the committed observation and analysis
files named beside it. PR descriptions were not used as evidence; where a PR summary and a record disagree, the record
wins, and the disagreement is noted (§1.4).

**Inspection pass.** One coordinated discovery pass over the repositories below. Later VAC-002 documents cite this file
rather than re-reading those repositories.

| Repository | Commit inspected | What it holds for this question |
|---|---|---|
| cohort-based-engineering | `main` `ca082c2` (ARCH-001 merged); VAC-001 on the open draft PR #14, branch `claude/verified-agent-continuity-vfjrrx` at `e06717f` | REL-001 run-01..03, VAC-001, ARCH-001, token-efficiency, reliability readiness |
| research-documents | `main` `62bf983` | CONSTRUCT-007/008, time-entry, indy-init rehearsal, ai-drift plan (no agent-continuity trials) |
| praxis | `main` `6400515`; VAC-001/ARCH-001 pin `986211c` (v3.19.0) | Work protocol, telemetry, EX-ROS-2026-A020…A024 |
| ordo | `main` `f69f8ac`; pin `bb43c26` (1.17.0) | `ecir/1` constructibility contracts, `ordo ecir check` |
| dokimos | `main` `c99c21b`; pin `04b5f85` (0.7.0) | Completion verification, DOK-R008 |
| percepta | `main` `1eb43a9` | UI semantic contracts only (see §5) |

Since the pins, ordo, praxis and dokimos `main` gained only ARCH-001 intake documents (`ARCH-001-01..03`), no
implementation change. VAC-002 therefore keeps the VAC-001/ARCH-001 pins (§6).

**PR state.**

| PR | Status | Meaning |
|---|---|---|
| ARCH-001 (#16) | Merged into `main` | Final |
| VAC-001 (#14) | Open draft, not merged | Its records are complete, but its conclusions are not yet accepted on `main` |
| ARCH-002 (#17) | Open draft, in progress, started 2026-10-22 | VAC-002 does not depend on it and does not touch its files |

## 1. VAC-001: verified agent continuity

**Records:**

- `research/experiments/VAC-001/results/{P1,R1,F1}/<arm>/verify-*.json` and `usage-*.json`;
- `results/pooled-P1-R1.json`, `results/F1/analysis.json` and `results/F1/fault-evaluation.json`;
- `results/layer3-summary.json`;
- the protocol `research/verified-agent-continuity/research-protocol.md`.

### 1.1 Required baseline figures, verified

| Claim in the VAC-002 brief | Record value | Source | Verdict |
|---|---|---|---|
| ≈40.9% lower cost per accepted requirement, continuous vs fresh | B vs A **−40.86%**, 95% CI [−48.07%, −32.97%], 16 blocks (P1+R1), lower-bound cost | `pooled-P1-R1.json .contrasts[0]` | **Verified.** The visible-output-estimate sensitivity gives −36.6% [−42.4, −30.3] |
| ≈38.1% improvement in replication | F1 B vs A **−38.06%** [−47.07%, −26.07%], 8 blocks | `F1/analysis.json .contrasts[0]` | **Verified.** F1 was the fault-injection run, not a clean replication: 5 of its 8 units carried a false premise |
| Control overhead ≈14–31% | C vs B +14.1% [+2.7, +27.4]; D vs B +16.8% [+6.4, +29.6] (P1+R1); D vs B +31.0% [+21.4, +43.0] (F1) | pooled and F1 analyses | **Verified** |
| Context-reconstruction overhead ≈86% | D vs DR −46.15% [−56.6, −32.4], so DR/D = 1/(1 − 0.4615) = **+85.7%**; DR vs A +50.6% | `F1/analysis.json .contrasts[4,5]` | **Verified.** One chain (F1) only |
| No regressions, false completions or architecture violations | 96/96 units accepted at first pass; regressions 0; FCR 0/84 claimed; AVR 0 | 96 `verify-N-1.json` (recounted: 8/8 accepted in each of the 12 run×arm chains) | **Verified** |
| 0 of 20 injected false premises accepted | 20 exposures, `acceptedPremise.value = false` in all 20; every one reported as rejected | `F1/fault-evaluation.json` | **Verified** |

**One correction.** The VAC-001 README says "8/202 adjudicated decisions were unsupported". The Layer 3 summary
labels 10 of 202 as not supported:

- 8 `unsupported-requirement`;
- 2 `unverified-completion-claim`.

The other 192 are 177 `supported` and 15 `recorded-assumption`.

**Reviewer agreement:** Cohen's κ = 0.905 on the 8-way label and 0.740 on the binary call. **Layer 1** passed every
`unsupported-requirement` decision, so existence-of-evidence checks did not detect scope additions.

### 1.2 Conditions

| Factor | VAC-001 value |
|---|---|
| Workload | REL-001 run-03 Ledger tasks V1–V8: a single F# project, small and well specified, with visible acceptance tests for every task. V7 is an unresolvable decision conflict whose correct outcome is a stop |
| Difficulty | Simple V1–V2, moderate V3–V4, complex V5–V6, adversarial V7–V8. Every arm solved every task |
| Chain length | 8 successive changes per chain; 11 chains; 96 units |
| Sample sizes | P1 4×8, R1 4×8, F1 4×8 (A, B, D, DR); 2 no-fault chains per arm (1 for DR) |
| Model and configuration | `claude-opus-5-5`, effort `medium`, Claude Code sub-agents of the orchestrating session (cache condition **K0**: shared prompt-cache prefix with the orchestrator) |
| Verification | Host-held cumulative hidden oracle, lexical VAC-RULES `archcheck`, Layer 1 evidence existence, blinded Layer 3 review by two same-family reviewers plus a third adjudicator |
| D's gate | The host gate ran the **hidden oracle** and fed failing requirement IDs and test names back to the agent (one repair round). It never fired: there were 0 failures |
| Statistics | Paired by block (run × position); percentile bootstrap, 10,000 resamples, seed 20261021. Kaplan–Meier longevity was all censored. The preregistered logistic model was not estimable (0 events) |
| Cost | REL-001 price table `2026-10-20.1`. Lower bound, because transcript `output_tokens` is recorded at stream start (amendment A4); a visible-output estimate is reported beside it. The orchestrator's cost is unavailable |

### 1.3 Limitations and threats to validity (as recorded, and checked)

1. **Ceiling.** With 0 failure events, H2–H7 are untested, not refuted.
2. **K0 cache sharing.** Sub-agents shared the orchestrator's cached prefix, which can shrink a fresh agent's
   cache-write penalty and so the A–B gap.
3. **Short chains.** 8 units, at most 167k prompt tokens, 0 compactions. Context pressure was never reached.
4. **D's gate used the hidden oracle**, so the "independent verification" control and the scoring instrument were
   the same artefact. Had the gate ever fired, D's repairs would have been graded by the test suite that guided them.
5. **Lexical architecture rules.** VAC-RULES are regex-level, with 2 measured false positives (`ref'`). Ledger is
   one project, so four-tier layering was not exercised.
6. **Faults the repository contradicts.** All 5 premises were contradicted by visible tests, comments, accepted notes
   or the compiler. R-EXP-1 asked next for premises the repository cannot contradict.
7. **Concurrent arms.** Wall-clock time is not comparable.
8. **Same-family reviewers.** Reviewers and implementers were the same model family, and blinding was partial.

### 1.4 What VAC-001 left open (its own R-EXP list)

| ID | Open item |
|---|---|
| R-EXP-1 | A fixture whose baseline fails, with these candidates: premises only decision records or verified state can contradict; underspecified requirements with hidden expectations; cross-feature invariants without visible tests |
| R-EXP-2 | Chains of ≥24 changes past the compaction threshold, run in **K1** (isolated CLI processes), with Layer 3 reviewers from another model family |
| R-PRAXIS-1 | Per-work-item usage windows and compaction counts |
| R-DOK-1 | Chained re-verification of every earlier accepted requirement |

These are the input requirements in `.praxis/inbox/documents/2026-10-21-VAC-CBE-001-…md` (VAC-CBE-001-R3, R4).
VAC-002 is designed against them.

## 2. ARCH-001: Ordo contracts and enforced four-tier boundaries

**Records:** `research/architectural-correctness/RESULTS.json` (assembled from `analysis/results.json`,
`results-as-run.json` and `exploratory-results.json`), `observations/*.json`, `REPORT.md` and `PROTOCOL.md`.

### 2.1 Required baseline figures, verified

| Claim | Record value | Source | Verdict |
|---|---|---|---|
| 64 confirmatory trials | `sampleSize.trials = 64` (8 tasks × 4 arms × 2 replicates), 128 phases, 0 excluded; 10 pilot trials excluded from analysis | `RESULTS.json .sampleSize` | **Verified** |
| 128/128 requirements accepted | 32/32 per arm (after amendments A3/A4; as-run scoring gives 28/32 per arm, the same in every arm) | `.preregistered.arms` | **Verified** |
| No detected architectural violations | 0 DET violations of severity ≥ 2 in any arm, task or phase, under the full policy plus sealed probes | `REPORT.md` §2, `.preregistered` | **Verified** |
| ≈24.7% additional cost for the fully controlled arm | D/A − 1 = **+24.67%**, 95% CI [+20.24%, +29.28%], 16 paired blocks. Primary hypothesis **Not supported** (opposite direction) | `.preregistered.primary` | **Verified** |

Cost per accepted requirement by arm:

| Arm | Cost per accepted requirement |
|---|---|
| A | $0.360 |
| B | $0.415 |
| C | $0.431 |
| D | $0.449 |

**Trial spend:** $52.95, plus $17.99 of review and evaluation and $6.52 of pilot.

### 2.2 Conditions

| Factor | ARCH-001 value |
|---|---|
| Workload | The Lending fixture: 4 F# projects, one per tier, about 816 lines, decision records DEC-001..008. Tasks T1–T8 have a follow-up each. Seven sealed traps are functionally correct but architecturally invalid |
| Agent | **K1**: an isolated headless `claude -p` per phase, Claude Code 2.1.306, `claude-opus-5-5`, tools Bash/Read/Edit/Write, run 3 at a time, seed 20261022 |
| Arms | A requirements only · B + SDE-DOCTRINE-003 pack · C + Ordo `ecir/1` contract · D + in-loop `archcheck` and a `submit` gate |
| Verifier | `archcheck`: compiler-resolved (MSBuild project graph plus FCS typed symbol uses). Every trap is caught and every reference passes (`fixtures/check-output.txt`, 126 checks) |
| Statistics | Preregistered; paired blocks; Holm correction; ±10% equivalence margins |

### 2.3 Limitations

1. **Ceiling.** Unguided agents made 0 deterministic violations, so H1/H2/H3/H6 are "equivalent at ceiling". Those
   findings carry no information about prevention.
2. **Single-agent tasks.** About 6 minutes each, on a clean, consistently layered codebase. There are no chains and no
   accumulated history.
3. **Exploratory quality signal.** Blinded review favoured guidance by +0.59 of 6 (p = 0.013), and the
   swallowed-failure heuristic fired only without guidance. This is exploratory, not confirmatory.

## 3. Other records relevant to VAC-002

| Record | Finding used by VAC-002 | Strength |
|---|---|---|
| REL-001 run-02 (`experiments/REL-001/run-02/analysis/results.json`) | 4 arms × 22 runs, 43/43 requirements correct in every arm. Echelon-optimized vs bare: cost per correct requirement $0.191 vs $0.134 | Ceiling again. Cost direction consistent with VAC-001 and ARCH-001 |
| Token efficiency (`token-efficiency/OVERHEAD-ANALYSIS.md`) | Mandated workflow commands are a median of 27–29% of tool calls. Protocol overhead ≈ extra turns × per-turn context. Transcript `output_tokens` is a lower bound | Measured (exploratory) |
| REL-001 reliability readiness (`reliability/readiness-report.json`) | Dokimos receipts are not independent when the verifier and the agent share a uid (item F6) | Open limitation, still present in this container |
| praxis EX-ROS-2026-A021/A021-R2/A024 (summarised in `verified-agent-continuity/evidence-baseline.md`) | Grouped or continuous execution was cheaper (−46% to −59%). Structured handoffs cost +10.5% over code-only resets. A024's continuous session scored lowest on its architecture rubric (5/10) | n = 1 per arm; promising |
| CONSTRUCT-007/008 (research-documents) | Construction-by-design trials on Ordo-generated code. No agent-continuity or verification-overhead measurement | Not applicable |

## 4. Classification of the questions VAC-002 inherits

| Question | Status before VAC-002 |
|---|---|
| Continuity lowers cost per accepted requirement | **Supported but preliminary.** Replicated within one fixture family, K0, 8-unit chains |
| Reliability degrades with chain length (H1) | **Inconclusive** (0 events) |
| Verified state lowers consequential errors (H2) | **Inconclusive** |
| Ordo / executable constraints prevent architectural violations (H3) | **Inconclusive.** At ceiling in two experiments |
| Adaptive verification is noninferior at lower cost (H4) | **Not studied** |
| Error propagation differs by persistence and verification (H5) | **Inconclusive** (0 propagated faults) |
| Selective enforcement improves cost per accepted requirement (H6) | **Not studied.** Full enforcement costs +14–31% (VAC-001) and +25% (ARCH-001) with no measured benefit |
| Verified-state reconstruction recovers more cheaply (H7) | **Contradicted on cost** (+86% vs continuity, one chain). Recovery after a real context loss is **not studied** |

## 5. Deviations from the brief's assumptions

- **No "VAC-001" on `main`.** VAC-001 exists only on the unmerged draft PR #14. VAC-002 builds on that branch, with
  `main` (ARCH-001) merged in, so both harnesses are available. If PR #14 changes before merge, VAC-002 cites commit
  `e06717f`.
- **Percepta does not own agent metrics.** Percepta is the Echelon UI-system repository. Its experiments test UI
  semantic contracts, as VAC-001's baseline also found. The agent-experiment conventions live in
  cohort-based-engineering (REL-001, VAC-001, ARCH-001), and VAC-002 follows those. `METRICS.md` maps each VAC-002
  metric to its VAC-001 counterpart.
- **Dokimos is represented by the host gate.** The uid limitation (REL-001 readiness F6) still holds in this
  container. As in VAC-001, a host-run gate plays Dokimos's completion-verification role and is labelled as such.
- **Praxis ingestion convention confirmed.** `.praxis/inbox/documents/` exists in cohort-based-engineering and
  already holds `ENGINEERING-RELIABILITY-001`, `ARCH-001-04` and `VAC-CBE-001`. VAC-002 requirements go there and in
  the matching folders of the affected repositories. No GitHub Issues are created.

## 6. Pins carried into VAC-002

| Item | Value | Note |
|---|---|---|
| Ordo | `bb43c26c106f4cbe972234636c5c67edc235c188`, built here | `sde.dll` sha256 `37c52bf3…d7a7` |
| Praxis | `986211c19161bab339eebc565fb4d8edb2007d38`, built here | — |
| Dokimos | `04b5f856367b47a087285109c1fc5923ec351389` | Not invoked (uid) |
| archcheck | ARCH-001 `verifier/` at `ca082c2`, published with SDK 10.0.402 | — |
| .NET SDK | 10.0.402, plus the .NET 8 runtime for Ordo | As in VAC-001 and ARCH-001 |
| Claude Code | 2.1.308 | ARCH-001 used 2.1.306; recorded as a deviation |
| Model | `claude-opus-5-5`, effort `medium` (inherited `CLAUDE_EFFORT`) | — |
