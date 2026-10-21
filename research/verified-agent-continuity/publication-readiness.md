# VAC-001: publication readiness

Status: 2026-10-21, after P1, R1 and F1. This file covers three things: what could be published now, what would be
needed before anything stronger is published, and what must not be claimed.

## 1. Claims and their readiness

| # | Claim | Evidence | Readiness |
|---|---|---|---|
| C1 | Continuing one agent across a chain of 8 related, independently verified changes cost ~40% less per accepted requirement than a fresh agent per change with an agent-written handoff, at equal correctness | B vs A −40.9% (CI −48.1% to −33.0%, 16 blocks); F1 replication −38.1%; both cost measures agree; consistent with praxis A021/A024 | **Ready as a scoped result.** One fixture, one model, K0 cache condition. State all three |
| C2 | Token totals hid this: A and B differed by ≤ 10% in tokens per accepted requirement but ~40% in cost | `agent-longevity-analysis.md` §2 | **Ready** (measurement-practice note) |
| C3 | Adding Ordo admission, rules and decision records (C), or the full Echelon protocol with gate and verified state (D), raised cost by +14% to +31% over continuity alone, with no measured correctness, drift or hallucination benefit in this fixture | C vs B +14.1%, D vs B +16.8% / +31.0%; all reliability metrics at ceiling | **Ready as a null result.** Must say "at ceiling": the benefit is unmeasured, not shown absent |
| C4 | Reconstructing context from verified state with a fresh agent per change preserved traceability and correctness, but cost +86% vs continuous D and +51% vs a plain handoff | F1, n = 1 chain each | **Preliminary.** One chain per arm |
| C5 | No fabricated premises, stale decisions or false completions in 441 decisions and 96 units, in any arm | Layers 1–3; hallucination class 0/202 reviewed (upper 95% 1.5%) | **Ready with scope.** Easy, well-specified tasks with visible tests |
| C6 | All 20 injected false premises were refused when repository evidence contradicted them | F1 (0/20 accepted; per-arm upper 95% bound ≈ 45%) | **Ready as a descriptive result.** Not a comparison between arms |
| C7 | The dominant unsupported decision is scope expansion presented as settled, and no deterministic check catches it | 8/202 reviewed, κ 0.90 | **Ready as an observation.** The arm difference (A 1/62 vs B 4/52) is not significant |
| C8 | Verified engineering state makes agent reliability independent of session length | No failures occurred to compare | **Not supported. Must not be claimed** |
| C9 | Echelon controls prevent hallucination, drift or propagation | Baseline arms also scored 0 | **Not supported. Must not be claimed** |

## 2. What is needed before publishing stronger claims

1. **Room to fail** (R-EXP-1). A fixture where the baseline fails measurably. The candidates:
   - premises the repository cannot contradict;
   - decisions that live only in records or verified state;
   - underspecified requirements with hidden expectations;
   - cross-feature invariants without visible tests.

   Without baseline failures, no reliability benefit can be shown.
2. **Longer chains and compaction** (R-EXP-2). At least 24 changes per chain, reaching the compaction threshold, so
   that H2 (lifetime-dependence) and the compaction questions become testable.
3. **Replication across substrate:**
   - at least one more fixture family, for example a TypeScript or C# service;
   - the K1 isolated-CLI cache condition (REL-001 run-03), so cache sharing with the orchestrator is ruled out;
   - at least one other model or effort level.
4. **Sample size.** To detect a 10-percentage-point difference in per-unit failure (for example 15% vs 5%) at
   α = 0.05 and power 0.8, roughly 140 units per arm are needed. VAC-001 has 24.
5. **Independent reviewers from another model family.** A different family for Layer 3, as in praxis A021-R2 (GPT
   evaluator), plus snapshots that keep git history (§3.2 of the hallucination evaluation).
6. **Preregistration hygiene.** Run-level analysis scripts frozen before data. The VAC-001 protocol was
   preregistered at commit `05b3cf2`. The analysis code (`vac.fsx analyze`) and Layer 3 tooling were written during
   the runs, before any arm comparison was reported; four amendments are logged. A confirmatory run should freeze
   them in advance.
7. **Orchestrator cost.** The harness session's own model cost is not attributed. A publishable total-cost-of-method
   figure needs it.

## 3. Reproducibility status

| Item | Status |
|---|---|
| Fixture, oracle and self-check | Committed (REL-001 run-03); `evidence/fixture-check-output.txt` PASS |
| Harness, briefs, faults, rules, directives | Committed under `research/experiments/VAC-001/` |
| Tool versions | Ordo `bb43c26` and Praxis `986211c`, built from source; .NET 10.0.402 + runtime 8.0 |
| Per-unit observations, usage, verified states | Committed (`results/`) |
| Layer 3 labels and unblinding key | Committed (`results/layer3/`) |
| Agent transcripts | **Not committed.** Raw transcripts (≈ 0.3–0.9 MB per chain, 28 MB in total) contain the session's environment and user-identity context, so they must not go in a public repository. Instead, a **content-free per-request ledger** is committed (`results/<run>/<arm>/requests.jsonl`: timestamps, model, effort, token fields, tool names). It reproduces every usage file exactly: 96/96 checked for request count and cache reads |
| Agent workspaces (git histories) | **Not committed** (`/home/user/vac-work`). Per-unit trees were exported to harness state, and the commit SHAs are in the observations |

**Before external publication:** archive the transcripts and workspace bundles as a release asset, with checksums.

## 4. Verification limitations to disclose

- **Praxis/Dokimos completion.** Never used as acceptance. The rollout gate (F6) is open, and verifier and agent
  share a uid in this container.
- **Acceptance oracle.** Shared with REL-001, so the model may have seen similar tasks in earlier sessions. No
  oracle content entered any workspace (X4 = 0).
- **Blinding.** Partial, as the hallucination evaluation describes.
- **Output tokens.** A lower bound (amendment A4; Praxis REL-TOKEN-002 is the open fix).

## 5. Recommendation

**Publish internally now** as an Echelon research note. Scope the findings C1–C7 to "one fixture, one model,
8-change chains, at ceiling correctness".

**Do not publish externally** any claim about verified state improving reliability (C8, C9) until R-EXP-1 and
R-EXP-2 produce baseline failures for verified state to prevent.
