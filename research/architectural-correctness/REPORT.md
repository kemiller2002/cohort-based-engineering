# ARCH-001 report: Do Ordo contracts and enforced four-tier boundaries improve correctness and cost?

**Date:** 2026-10-21.
**Status:** confirmatory trials executed. All numbers below come from `RESULTS.json`, which is assembled from
`analysis/results.json` (preregistered), `analysis/results-as-run.json` (sensitivity) and
`analysis/exploratory-results.json` (post hoc).

**Design:**

- [PROTOCOL.md](PROTOCOL.md): the preregistration, with amendments A1–A4 in §13.
- [SCORING.md](SCORING.md): the scoring rules.
- [ARCHITECTURE-RULES.md](ARCHITECTURE-RULES.md): the rule catalog.
- [BASELINE.md](BASELINE.md): what the ecosystem guarantees today.

## Summary

The experiment ran 64 confirmatory trials:

- 8 tasks × 4 arms × 2 replicates;
- 2 phases each (an initial requirement, then a hidden follow-up);
- 128 requirements in total;
- 0 trials excluded.

Every arm reached a ceiling:

- **Functional and architectural acceptance.** All 128 requirements passed the hidden functional oracle and the
  compiler-based architecture verifier (full policy plus sealed per-task probes) with **zero deterministic
  violations in any arm, task or phase**.
- **Decision fidelity.** All 78 decision-labelled oracle tests passed in every arm.
- **Conflicting requirement.** In T5 every arm refused the requirement that conflicts with DEC-006 (2/2 per arm).

None of the architectural benefits could be shown: H1, H2, H3 and H6 are **Not supported**, with zero difference
inside the preregistered equivalence margins. The added material had a measurable cost:

| Arm vs A | Total model cost, 95% CI |
|---|---|
| B (guidance) | +15.3% [+8.2%, +23.5%] |
| C (+ Ordo contracts) | +19.9% |
| D (+ enforcement) | **+24.7% [+20.2%, +29.3%]** |

The primary hypothesis is therefore **Not supported**: arm D's cost per fully correct requirement is significantly
*higher* than arm A's. Enforcement on top of contracts (D vs C) cost +4.0% [−0.3%, +8.0%], which lies inside the
±10% equivalence margin. It made trials about 48% longer in wall time than arm C (9.1 vs 6.2 minutes).

The blinded review is the only signal in which architecture quality differed between arms, and that analysis is
exploratory.

- Architecture guidance raised the blinded reviewers' scores. Combined review score B − A: +0.59 points
  [+0.09, +1.22], p = 0.013 (scale 0–6).
- Heuristic findings that never gate appeared only without guidance:
  - catch-all exception handlers that swallow notifier failures in Tier 3 (T4, arm A, 2 of 2 replicates);
  - a predicate duplicated across tiers (T3, arm A).
- Ordo contracts and mechanical enforcement added nothing beyond guidance: review scores C − B −0.16 and D − C +0.06.

**Scope of these conclusions.** They hold for a small, clean, consistently layered F# codebase and for tasks a
single capable agent completes in about six minutes. They do not show that enforcement is useless where agents
actually make architectural mistakes. In this setting, the mistakes did not occur.

## 1. What was run

| Arm | Material on top of the requirement and repository |
|---|---|
| A | None (core brief only) |
| B | SDE-DOCTRINE-003 v0.2.1 verbatim, plus the Lending instance (tier map, placement rules) |
| C | B plus an Ordo `ecir/1` decision contract, `ordo ecir check` and decision-id citation |
| D | C plus `archcheck` (FCS typed-symbol verifier) during development, and as a required `submit` gate |

The fixture is Lending: four F# projects, one per tier, about 816 lines, with decision records DEC-001 to DEC-008.

| Task | Mission categories | What it involves |
|---|---|---|
| T1 | 1, 5 | Renewals: renewal eligibility shown in the CLI |
| T2 | 2, 3 | Loan history persisted; follow-up adds a second persistence provider |
| T3 | 4 | CSV import |
| T4 | 6 | Asynchronous notices with Succeeded / Failed / Unknown outcomes |
| T5 | 7 | A requirement that conflicts with DEC-006 |
| T6 | 9, 8 | Hold expiry across all four tiers |
| T7 | 10 | A behaviour-preserving refactor; follow-up adds a second UI surface |
| T8 | control | ISBN validation |

Seven tasks have a sealed *trap*: a solution that is functionally correct but architecturally invalid.
`fixtures/check.sh` (126 checks) showed that every trap passes all functional tests and fails `archcheck`. The
measurement could therefore detect the violations it targets (§6).

**Execution.**

- Isolated headless Claude Code 2.1.306 sessions, `claude-opus-5-5`, run 3 at a time.
- A fresh configuration directory and session per phase.
- Tools: Bash, Read, Edit and Write.
- Randomised order (seed 20261022).
- Cache: 0 cold first requests. The tool-definition prefix was shared across trials, equally in every arm (§8).

**Sample size.** Fixed by the preregistered §9 rule from pooled pilot variance, never from an arm difference. The
rule gave 2 replicates per cell (amendment A2).

## 2. Hypotheses

| Id | Contrast | Estimate [95% CI] | Holm p | Classification |
|---|---|---|---|---|
| **Primary** | D/A − 1, cost per accepted requirement | **+24.7% [+20.2%, +29.3%]** | — | **Not supported** (opposite direction) |
| H1a | B − A, severity-weighted DET violations per trial | 0 [0, 0] | 1.0 | Not supported (equivalent, ceiling) |
| H1b | B − A, architectural acceptance rate | 0 [0, 0] | 1.0 | Not supported (equivalent, ceiling) |
| H2 | C − B, decision-test pass rate | 0 [0, 0] | 1.0 | Not supported (equivalent, ceiling) |
| H3 | D − C, DET violations | 0 [0, 0] | 1.0 | Not supported (equivalent, ceiling) |
| H4 | D − C, follow-up rework lines | −5.25 [−14.19, +2.69] | 1.0 | **Inconclusive** |
| H5a | D/C − 1, primary metric | +4.0% [−0.2%, +8.1%] | 0.45 | Not supported (inside the ±10% margin) |
| H5b | D/A − 1, primary metric | +24.7% [+20.1%, +29.3%] | <0.001 | Not supported (opposite direction) |
| H6 | slope of the D − A violation difference on cross-tier count | 0 [0, 0] | 1.0 | Not supported (no variation to explain) |
| H7 | grouped execution | not tested (out of scope; PROTOCOL §1) | — | — |

**Sample sizes.** 16 trials per arm and 32 requirements per arm. Each contrast uses 16 paired blocks over 8 tasks.

**Sensitivity analyses.**

- **As-run scoring** (before amendments A3/A4): every classification is identical. Every arm accepted 28/32
  requirements instead of 32/32, because the same superseded-test artifact hit T3 and T5 in every arm.
- **Without timeouts:** identical, since there were no timeouts.

**What "Not supported (equivalent)" means here.** Every trial in every arm had zero violations, so the intervals are
exactly [0, 0]. This is a ceiling. The design cannot distinguish "the treatment has no effect" from "this fixture
gives the treatment nothing to prevent". The second reading is the conservative one. Strong claims of
non-superiority beyond this setting are not warranted.

## 3. Arms in detail

The table shows totals or means per trial over both phases. Sources: `RESULTS.json .preregistered.arms` and
`.exploratory.byArm`.

| | A | B | C | D |
|---|---|---|---|---|
| Accepted requirements | 32/32 | 32/32 | 32/32 | 32/32 |
| First-pass correct (phase 1, phase 2) | 15, 16 | 16, 16 | 16, 16 | 16, 16 |
| DET violations, S1 and S2 | 0 | 0 | 0 | 0 |
| HEU findings per trial | 0.375 | 0 | 0 | 0 |
| Blinded review score (0–6) | 5.19 | 5.78 | 5.63 | 5.69 |
| ARC-REV-01, semantic authority (0–2) | 1.56 | 2.00 | 1.88 | 1.94 |
| Model cost, total USD | 11.51 | 13.27 | 13.81 | 14.35 |
| Cost per accepted requirement, USD | 0.360 | 0.415 | 0.431 | 0.449 |
| Phase-1 cost per trial, USD | 0.389 | 0.434 | 0.454 | 0.475 |
| Phase-2 cost per trial, USD | 0.331 | 0.395 | 0.408 | 0.423 |
| Output tokens per trial | 13,549 | 14,423 | 14,691 | 14,991 |
| Tool calls per trial | 18.4 | 18.3 | 18.6 | 20.8 |
| Test executions per trial | 3.06 | 3.31 | 3.25 | 3.13 |
| Verification executions per trial (submit, ordo, archcheck) | 2.06 | 2.00 | 4.06 | 6.44 |
| Wall time per trial, minutes | 5.6 | 5.9 | 6.2 | 9.1 |
| Phase-2 rework lines | 76.6 | 81.8 | 85.6 | 80.4 |
| Cost cross-check disagreements | 0 | 0 | 0 | 0 |

**Per-task cost.** D cost more than A in every task: +15% (T4) to +31% (T3). On the T8 control, where no architecture
mistake was available, D cost +27.1% over A [+25.2%, +28.9%] and −1.9% versus C. The control shows the overhead
comes mostly from the guidance and contract material, not from the verifier itself.

## 4. Answers to the mission questions

**1. Does four-tier guidance improve architectural correctness?**

- On the preregistered, mechanically decided measure: **no difference**, because unguided Claude already made zero
  deterministic violations.
- Exploratory signals that a mechanical gate does not capture all favour guidance:
  - blinded reviewers scored guided work higher (+0.59 of 6, p = 0.013);
  - guided work never tripped the swallowed-failure heuristic (AR-10) in T4, while unguided work did in both
    replicates.
- Guidance cost +15%.

**2. Does Ordo improve outcomes beyond written guidance?**

- **Not shown.** Decision fidelity was 100% in every arm (78/78 decision tests).
- Every arm refused T5's conflicting requirement, including arm A, which saw only the DEC records in the repository.
- Contract traceability (ARC-TRC-01) was complete in C and D: 0 untraced decisions at S2.
- Ordo added about 4% cost over guidance. C − B in review: −0.16 (exploratory).

**3. Does AST/compiler enforcement prevent additional violations?**

- **Not in these trials:** no arm produced a violation for it to prevent.
- The instrument is validated against planted traps. Every one of the 7 traps that are functionally correct but
  architecturally invalid is caught, and every reference solution passes (`fixtures/check-output.txt`).
- Its value is therefore *potential*. It would show only where agents actually make these mistakes.

**4. Which violations are detectable mechanically?** See ARCHITECTURE-RULES.md and `verifier/README.md`.

- Deterministic from compiler-resolved structure (MSBuild project graph plus FCS typed symbol uses):
  - upward project references;
  - forbidden packages in Tiers 1/2;
  - named I/O, JSON, console, clock, randomness and GUID APIs by tier;
  - presentation touching persistence adapters or calling Tier-2 functions;
  - presentation reading Tier-1 entity fields;
  - decision-id presence.
- Heuristic: swallowed exceptions or Unknown collapsed to failure; duplicated literals or predicates across tiers;
  domain arithmetic in Tier 4; file-size bands.
- Not mechanisable: "Tier 3 is a second semantic authority", effect-flow correctness, single authority for a fact.
  These need review.
- Responsibility placement became decidable only through fixture-specific *boundary proxies* (ARC-BND-01..03), which
  depend on a declared tier map and presentation scope.

**5. Does architectural enforcement increase initial token cost?**

- Over contracts: phase-1 cost D/C +4.4% [−0.4%, +9.5%], not significant. Output tokens D/C +2.0%.
- Over requirements only: phase-1 cost +22.1% [+14.7%, +33.0%].
- The clearer cost is wall time: +2.9 minutes per trial over C (about +48%), mostly verifier runs of about 20–30 s
  each, 6.4 verifications per trial.

**6. Does it reduce subsequent rework?** **Inconclusive.**

- D − C phase-2 rework: −5.3 lines [−14.2, +2.7].
- No trial broke a visible test or a regression test after A3.
- The follow-ups never required restructuring in any arm, because no initial solution had violated a boundary.

**7. Does it reduce total lifecycle cost?** **No.**

- Lifecycle cost per fully correct requirement (both phases) was highest in D: +24.7% versus A.
- D was statistically indistinguishable from C (+4.0%, inside the margin).
- The lifecycle advantage enforcement could offer, avoiding expensive follow-ups after a bad initial structure, never
  arose.

**8. Which architecture controls should be mandatory?**

- On this evidence, **none of the in-loop agent controls should be mandatory.** The evidence does support making
  these cheap, independent controls mandatory *outside* the agent loop:
  - a declared tier map per application (AR-28);
  - a compiler-resolved dependency-direction and forbidden-reference check (AR-01..03, ARC-DEP/SYM) as a CI or
    completion-time verifier.
- Their marginal agent cost is zero, and they would have caught every planted trap.
- Both are unenforced today in Summa and Signal (BASELINE.md §2.1).

**9. Which should be optional?**

- In-loop `archcheck` gating (D): no measured benefit, plus wall-time cost.
- Ordo decision contracts for routine work: no measured fidelity gain over DEC records in the repository.
- Architecture packs in the brief: exploratory quality gain at +15% cost. Worth considering where review-judged
  quality matters; not shown to change mechanically checked outcomes.

**10. How should Praxis, Ordo and Dokimos integrate the findings?** See
[IMPLEMENTATION-RECOMMENDATIONS.md](IMPLEMENTATION-RECOMMENDATIONS.md).

- Dokimos should own a compiler-derived architecture rule family, with independent, commit-bound evidence. It would
  supersede DOK-R008's regex.
- Praxis should attach that check as a host-verifier `validations[]` entry when a repository declares a tier map,
  rather than injecting it into agent briefs.
- Ordo should not add architecture-rule contracts until a replication with violation-prone work shows benefit.
- The next experiment should use brownfield and violation-prone fixtures.

## 5. Evidence integrity

- **Exclusions:** none among the 64 confirmatory trials. Every contamination scan was clean, and every integrity
  hash matched.
- **Sealed oracle:** `sealed/arch001-sealed.tar.gz.enc` was committed at the freeze. Its plaintext sha256 is
  `887e9383…bf91f` (180 files). The key (`sealed/arch001-sealed.key`) and the manifest (`sealed/MANIFEST.sha256`) are
  published with these results.
  To verify:

  ```
  openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass file:sealed/arch001-sealed.key -in sealed/arch001-sealed.tar.gz.enc | sha256sum
  ```
- **Binding to commits:** every verdict in every observation names its commit and tree hash.
- **Scoring inputs:** scoring used pristine copies only.
- **Cost:** the reported cost matches the price-table recomputation in all 128 phases.

**Amendments after the freeze** (PROTOCOL §13; all arm-blind):

| Amendment | Defect found | Fix |
|---|---|---|
| A1 | In the pilot, arm D never received enforcement: the verifier refused a contract path inside the workspace. | Arm D contract path fixed. The two arm D pilot trials were re-run. |
| A2 | — | Confirmatory order generated from the preregistered power rule. |
| A3 | The follow-up deliberately supersedes some initial-oracle tests, but the scorer counted them as regression failures. | Superseded tests excluded from regression, derived from the sealed follow-up reference rather than any trial. |
| A4 | Feature detection under `pipefail` silently dropped the sealed probes from scoring. | Probes always passed. The verifier steps were re-run at the recorded commits. |

The as-run scoring is kept in `observations-as-run/` and `analysis/results-as-run.json`. It gives identical
classifications.

**Disclosed exposures.**

- Trap metadata (commit `2f15e59`) and the pilot oracle test names (commit `8fb76b5`) were briefly public.
- The scan would have excluded any agent that read the repository or GitHub. None did.

## 6. Threats to validity

1. **Ceiling.** This is the dominant threat. Zero violations in 128 requirements means the fixture and tasks did not
   elicit the mistakes the treatments target. Three things likely contributed:
   - the starting code was cleanly layered (Views, use cases, ports) and its own code cites its decision records;
   - the tasks were small (about 3 minutes per phase on average);
   - the model is strong.
   The traps were *available*, but no arm took them.
2. **n = 2 per cell.** This is adequate to detect the cost differences observed. It is underpowered for small quality
   effects, and the review contrasts are exploratory.
3. **One fixture, one language, one model.** External validity to Summa, Signal or other models is argued, not
   shown. The doctrine itself rests on single-application evidence (TH-SDE-2026-0001, confidence 0.75).
4. **Praxis was held out of all arms** to isolate enforcement. The results say nothing about the Praxis work protocol
   (studied in REL-001).
5. **The enforced rule set scores arm D too.** Because no arm violated it, this did not bias any contrast.
6. **Review blinding.** Scrubbing removed arm-identifying text. Residual style cues, such as the decision-id comments
   arm C/D agents wrote, could have unblinded reviewers to C/D. Review results are exploratory for this reason too.
7. **Wall time includes concurrency** (3 trials at a time). Cost and tokens are unaffected.

## 7. Raw evidence

| What | Where |
|---|---|
| Per-trial observations | `observations/ARCH-001-CONF-*.json` (64) and `observations/ARCH-001-PILOT-*.json` (10, excluded) |
| Pre-amendment observations | `observations-as-run/` |
| Analyses | `analysis/results.json`, `analysis/results-as-run.json`, `analysis/exploratory-results.json`, `analysis/pilot/power.json` |
| Instruments and pins | `pins.json`, `fixtures/check-output.txt`, `verifier/` (selftest: 22 samples) |
| Superseded tests (A3) | `harness/amendments/A3-superseded.json` |
| Trial transcripts and workspaces | `/home/user/arch001-runs/` on the run host. Not committed: they are large, and the session logs contain environment details. |

**Spend.**

| Item | Amount |
|---|---|
| Confirmatory trial model cost | USD 52.95 |
| Blinded review (evaluation) | USD 17.99 |
| Pilot | USD 6.52 |
| Worker sub-agents | about 1.64M tokens |
| Coordinator tokens | Not exposed by the runtime, so unavailable (not zero) |
