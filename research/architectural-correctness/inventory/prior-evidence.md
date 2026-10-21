# Prior evidence inventory: Praxis A021–A024 and REL-001 runs 01–03

Worker F (prior evidence review) for the "Echelon Architectural Correctness" experiment. Read-only review,
2026-10-21. Nothing under `research/experiments/REL-001/` or in the Praxis repository was modified.

**Path note.** The brief named `/home/user/praxis/praxis/research/`. That path holds no research tree. The
records are in `/home/user/praxis/research/`, abbreviated `praxis:` below. Cohort paths are relative to
`/home/user/cohort-based-engineering/research/`.

**Not read on purpose.** A sealed, blinded A022 variant exists on Praxis branch `experiment/a022-orchestration`
(`EX-ROS-2026-A022--cohesion-moderated-grouped-execution.md`, cohort PRAXIS-CTL). Its values are withheld
(`token-efficiency/evidence-index.json` TE-H05/H06), so it was not opened, to avoid unblinding it.

---

## 1. Per-experiment summaries

### 1.1 EX-ROS-2026-A021: grouped versus independent execution (Praxis, completed 2026-09-30)

- **Sources.** `praxis:experiments/EX-ROS-2026-A021--grouped-versus-independent-execution.md`;
  `praxis:evidence/EV-ROS-2026-A064` (results), `-A065` (kit), `-A066`, `-A067` (second evaluation);
  `praxis:experiments/EX-ROS-2026-A021-harness/` (`sessions.json`, `session_metrics.py`, `prompts/`);
  `…-A021-evaluation/evaluation.txt`; `praxis:hypotheses/HY-ROS-2026-A027`, `-A028`.
- **Question.** For one cohort of strongly related items, does one execution that reasons about the whole cohort
  before mutating repeat less work and make more consistent architectural decisions than one fresh execution per
  item? Did the read-only planner predict the scheduling facts?
- **Cohort.** `PRAXIS-GROUP-01..05`, the `work group create|show|add|remove|checkpoint` commands. Repository
  `kemiller2002/praxis`, arm start `8b4ffa3`. The cohort was authored by the experiment designer (a recorded threat).
- **Arms.**
  - **Grouped:** 1 Claude Code session. It must commit `group-analysis.md` (common architecture, invariants,
    reusable abstractions and so on) before any code.
  - **Control:** 1 fresh session per item, run serially on one branch.
- **n.** 1 run per arm. Control used 7 sessions (item 04 needed 3), grouped used 1, plus 1 evaluator. Model
  `claude-opus-5-5` for every session.
- **Primary metric.** None was designated. Metric groups were resources, work, context overhead, context pressure
  and quality (PRX-GRP-085). The outcome was a classification (PRX-GRP-087).
- **Results** (EV-A064).

  | Measure | Grouped | Control |
  |---|---|---|
  | Platform cost | $9.48 | $21.51 |
  | Active time | 61 min | 112 min |
  | Output tokens | 112,377 | 244,630 |
  | AGENTS.md reads | 1 | 5 |
  | Governance reads | 6 | 15 |
  | Model requests | 114 | ≥237 |
  | File reads / searches | 52 / 53 | ≥134 / ≥159 |
  | Tests passing | 811 | 829 |
  | Tests added for the feature | 19 | 37 |
  | Compactions | 0 | 0 |
  | Merge conflicts | 0 | 1 |

  Platform total tokens: −46.2% for grouped (TE-H01, `token-efficiency/HISTORICAL-EVIDENCE.md`).
- **How architecture was scored.**
  - A separate evaluator session that implemented nothing received the arms as `arm-X` / `arm-Y`. The mapping was
    random and sealed, and unsealed after evaluation commit `758724b`.
  - The judgement was qualitative, with file and line evidence and confirmed behaviour. **No score**, by design
    (PRX-GRP-084).
  - A second independent evaluation used the kit (EV-A065 method, EV-A067 report). It ran one shared CLI fixture
    script (steps S0–S34) against both arms, plus concurrency probes. Its blinding was **compromised**: the
    scrubber missed "grouped-arm" and "control branch".
- **Architectural findings.**
  - Grouped arm: "one model": 1 store, 1 join rule, 1 classification, 1 rejection type and error style, 1 JSON
    envelope, 1 mutation pipeline.
  - Control arm: 3 stores, 2 join rules (one inconsistency confirmed), 2 group-ID grammars, 3 member
    classifications, 4 rejection types with inconsistent exit codes, 3 JSON envelopes, 2 CLI parsers.
  - The control arm was better at reusing the existing planner parser and `executionLocation` rule, and at
    checkpoint validation.
  - EV-A067 adds a lost-write defect in control: 8 concurrent creates all exited 0 and only 2 were stored.
- **Stated limitations.** One cohort and one run per arm, so no causal claim; designer-authored cohort that
  extends the grouping feature itself; control-05 started from the wrong commit and item 04 needed 3 sessions;
  partial transcript metrics (lower bounds) and platform-estimated costs; one same-family evaluator with partial
  blinding (commit messages and `.ros` state named labels).

### 1.2 EX-ROS-2026-A021-R2: replication (Praxis)

- **Sources.** `praxis:evidence/EV-ROS-2026-A070`, `praxis:experiments/EX-ROS-2026-A021-R2-blind/` (`README.txt`,
  `arm-M.patch`, `arm-N.patch`, `mapping-commitment.sha256`, `output/EVALUATION.txt`, `findings.json`,
  `POST-UNBLINDING-METRICS.txt`).
- **Question.** Same as A021, on the same cohort, the same baseline `8b4ffa3` and the same arms.
- **n.** 1 per arm. Control used 5 worker sessions.
- **Results.**

  | Measure | Grouped | Control | Control / grouped |
  |---|---|---|---|
  | Platform cost | $10.75 | $26.05 | 2.42× (grouped −58.7%) |
  | Elapsed | 55m53s | 2h23m35s | 2.57× (grouped −61.1%) |
  | Output tokens | 132,902 | 262,893 | — |
  | Cache-read tokens | 27.9M | 63.0M | — |

  Platform total tokens: −49.0% (TE-H02). Confirmed acceptance defects: **2 in each arm**.
- **How architecture was scored.**
  - Blind arm-M / arm-N bundle with `.ros/` reset, and a salted mapping commitment.
  - The evaluator was **cross-family: OpenAI GPT-5.6 Sol**. It had no .NET SDK and used CI evidence for builds.
  - Qualitative findings, no score. The salt was lost; the mapping was established by exact blob identity.
- **Findings.** Arm N (grouped) was stronger on shared admission rules, repository invariants, locking, one-store
  persistence and JSON/mutation cohesion. Arm M (control) was stronger on checkpoint integrity.
- **Limitations.**
  - Control GROUP-02 started from a stale checkout, which could inflate drift; GROUP-03 also started stale.
  - Same repository, baseline and feature family, so this is not an independent-domain replication.
  - HY-A028 is "supported at low confidence".

### 1.3 EX-ROS-2026-A022: affinity by execution mode, 2×2 (Praxis main; never executed)

- **Sources.** `praxis:experiments/EX-ROS-2026-A022--affinity-by-execution-mode.md`,
  `praxis:evidence/EV-ROS-2026-A072`, `praxis:experiments/EX-ROS-2026-A022-target-gate/`
  (`inventory.py`, `inventory.json`, `signal/`).
- **Question.** Is the grouping benefit larger for high-affinity than for low-affinity work, or is it generic
  one-session setup amortization?
- **Arms.** {high, low affinity} × {grouped, independent}: `a022-hg/hi/lg/li`, 5 items per cohort, all from one
  non-Praxis repository.
- **Planned blinding.** Neutral cohorts Alpha and Beta, and no rubric score. The evaluator reports facts and
  counts of confirmed defects.
- **Planned primary measure.** Resource ratio independent / grouped, with the prediction that the high-affinity
  ratio exceeds the low-affinity ratio. Quality acted as a guardrail only.
- **Outcome.** The target gate failed: 0 of 14 repositories had 10 ready items (largest unfinished count 7, in
  vigila; strata had 1 ready item). Signal has 19 genuine captured items, but 0 of its 11,628 five-item subsets
  are relation-free (every item links to the `WI-0002` contract), and items span 4–52 requirement groups, a scale
  confound. **No arm ran**; EV-A072 is feasibility evidence only.
- **Separate sealed run.** A different "A022" (cohesion-moderated 2×2, PRAXIS-CTL cohort) ran on
  `experiment/a022-orchestration` and is sealed, with condition D incomplete (4 of 5 workers). Its values are
  withheld. TE-H05/H06 record a blinding leak: labels can be inferred from item IDs and from the `g` versus
  `w1..w5` metrics file names.

### 1.4 EX-ROS-2026-A023: affinity moderation across repository blocks (Praxis; proposed, nothing run)

- **Source.** `praxis:experiments/EX-ROS-2026-A023--affinity-moderation-across-repository-blocks.md` (609 lines).
- **Question.** Does the effect of grouped (G) versus independent (I) execution vary with pre-measured affinity,
  when every G/I contrast is made within one repository block?
- **Design.** Randomized complete block design: block = repository × baseline × cohort; affinity is a measured
  moderator; scale class is a stratifier. Minimum: 2 high and 2 low blocks in one scale class, from at least 4
  repositories; preferred 3 and 3 (exact permutation p = 1/20). Estimated about 8 G, 40 I and 6–8 evaluator
  sessions, about $250–450.
- **Primary measures (frozen).** `r_b = ln(I_b/G_b)` on cost; repeated discovery `d_b`; setup-adjusted
  `r*_b = ln((I_b − (n_b−1)·s_b)/G_b)`. Moderation by Spearman with an exact permutation p, plus separation.
- **Architecture.** A blind evaluator reports evidenced findings in 10 areas: duplicated or conflicting
  abstractions, domain-rule consistency, API/storage/serialization consistency, and others. There is **no
  aggregate quality score**. Each block is classified "grouped comparable or better", "mixed", "materially worse"
  or "insufficient".
- **Status.** Preregistered 2026-10-02 (`PRAXIS-PLAN-EXP-03`). No inventory, block or session yet. The next step is
  to build the affinity and scale instrument.

### 1.5 EX-ROS-2026-A024: context continuity and structured handoff (Praxis, completed 2026-10-07)

- **Sources.** `praxis:experiments/EX-ROS-2026-A024--context-continuity-and-externalized-handoff.md`;
  `praxis:evidence/EV-ROS-2026-A074`, `-A075` (results), `-A076`; `praxis:journals/JR-ROS-2026-A024`;
  `…-A024-harness/` (`rubric.txt`, `analysis.py`, `prepare_blind.py`, `handoff.schema.json`);
  `…-A024-run/` (`evaluation/report.txt`, `scores.json`, `FOLLOW-ONS.txt`); `HY-ROS-2026-A030`.
- **Question.** How much of the benefit of one continuous context can fresh agents recover from a structured
  durable handoff?
- **Arms.** Same cohort PRAXIS-GROUP-01..05, replayed from `8b4ffa3` (sanitized start `ddda837`). **A:** one
  continuous session. **B:** 5 fresh sessions, code only. **C:** 5 fresh sessions, each given a schema-valid JSON
  handoff.
- **n.** 1 run per arm. Model `claude-opus-5-5`, effort medium. Runtime 2.1.292, then 2.1.293.
- **Primary metric.** `recovery(C) = (S_C − S_B)/(S_A − S_B)` on architecture and discovery. Support required
  recovery ≥ 0.50, C better than B on both, and correctness within 0.05 of B.
- **Results** (EV-A075).

  | Measure | A continuous | B code-only | C handoff |
  |---|---|---|---|
  | Acceptance (blinded) | 36/36 | 36/36 | 36/36 |
  | Confirmed defects | 2 | 1 | 1 |
  | **Architecture composite (D1–D5)** | **5** (1,1,1,1,1) | **10** (2,2,2,2,2) | **8** (2,2,2,1,1) |
  | Divergence points | 8 | 5 | 6 |
  | File reads + searches | 112 | 263 | 276 |
  | Governance reads | 6 | 16 | 21 |
  | Platform cost | $8.27 | $15.30 | $17.43 |
  | Tests at head | 819 | 855 | 841 |

  Recovery on discovery was −13/151 ≈ −0.09. **HY-A030 was not supported.** The A021/R2 architecture
  direction **reversed**; the resource advantage replicated (A/B cost 0.54, elapsed 0.40).
- **How architecture was scored.** This was the **first numeric architecture rubric** in this evidence base.
  - Rubric (`EX-ROS-2026-A024-harness/rubric.txt`): 5 dimensions scored 0/1/2, composite 0–10: (1) persistence
    and state model; (2) admission and validation rules; (3) classification and invariants; (4) error, JSON and
    CLI consistency; (5) mutation and checkpoint reuse.
  - Every score must cite `LABEL/tree/path:line`, a hunk or a command output. The same checks were applied to
    every snapshot.
  - One fresh blinded evaluator (Claude family). Neutral labels P, K and W, with mapping commitment `508a8f94…`
    committed before packaging.
  - Symmetric grep checks and probes: `probe.sh` for JSON refusal shapes, `lockprobe.sh` for the lock.
  - Acceptance was scored separately: 36 criteria per snapshot, a blinded scorer per snapshot.
- **Limitations.** Replayed cohort (not an independent replication); one run per arm (no variance estimate);
  same-family evaluator; B inherits `.ros` checkpoint summaries, an informal handoff.
  - **The guidance confound:** A021's grouped prompt required a written analysis; A024's arm A only asked for the
    architecture to be "decided once".
  - Launcher `outcome_branch` defects (D1–D3) and a runtime update mid-run (D6).
- **Proposed follow-ons** (`FOLLOW-ONS.txt`, not run): (1) guidance ablation, 2×2 of context × required
  analysis artefact, ranked highest value; (2) a fresh verifier after a grouped implementation; (3) model and
  effort sensitivity; (4) cohort size 3/5/8/12; (5) coordinator plus subagent topology; (6) interruption and
  recovery.

### 1.6 REL-001 run-01: ownership, contracts and verification (cohort, completed 2026-10-20)

- **Sources.** `experiments/REL-001/design.md`, `protocol/run-01.md` (amendments A1–A4), `REPORT.md`,
  `analysis/analyze.fsx`, `analysis/exploratory.fsx`, `analysis/results.json`, `gate/gate-report.json`,
  `harness/{a,b,c,d}`, `fixtures/{b,d}`.
- **Question.** Does end-to-end enforcement (Ordo contracts, Praxis ownership, Dokimos verification) change cost
  per verified requirement, rework and coordination failures, without increasing escaped defects?
- **Arms.** Baseline Praxis 3.12.0; treatment Praxis 3.15.0, then 3.16.0, with Dokimos 0.6.0 and Ordo 1.17.0.
- **n.** Experiments A–C are deterministic case tables. Experiment D: 12 agent trials (3 tasks × 2 arms × 2
  replicates).
- **Primary metric.** Cost per independently verified requirement. **Preregistered analysis: inconclusive.** Cost
  was unavailable (no price table), so 0 of the 6 required runs per arm were eligible.
- **Results.** A: duplicate owners 15 → 0. B: invalid contracts accepted 11/11 → 0/11. C: unverified completions
  accepted 8 → 1 (C3b, forged evidence). D, exploratory: tokens per verified requirement +31.7% (CI +14.3% to
  +55.9%), tool calls +36%, test runs +117%; 12/12 verified in both arms, 0 rework, 0 escaped defects.
- **Architecture.** Not scored. Correctness came from a hidden oracle (automated).
- **Limitations.** Ceiling effect on easy tasks; shared prompt cache across sub-agents of one orchestrator (A3);
  tokens attributed by transcript directory, output a lower bound (A4). **Decision: MODIFY.**

### 1.7 REL-001 run-02: four arms (cohort, completed 2026-10-20)

- **Sources.** `protocol/run-02.md` (preregistered at `a00eba0`, amendments A1–A3), `REPORT-run-02.md`,
  `run-02/analysis/` (`analyze-run02.fsx`, `results.json`, `cache-sensitivity.py`, `integrity-d.py`),
  `run-02/review/FAIRNESS-REVIEW.md`, `run-02/observations/` (`protocol-notes.md`, `concurrency.json`).
- **Question.** Is Echelon (in original or optimized form) more efficient than giving Claude a requirement?
- **Arms.** A bare; B directives; C original Echelon (Praxis 3.16.0); D optimized Echelon (Praxis 3.17.0,
  Dokimos 0.7.0, attested).
- **n.** 88 confirmatory trials (22 blocks × 4 arms over 9 tasks U1–U9) plus a 5-trial pilot; seed 20261020;
  0 exclusions.
- **Primary metric.** Estimated cost (F5 price table) per correctly completed requirement.

  | Arm | Cost per correct requirement |
  |---|---|
  | A | **$0.1147** |
  | B | $0.1390 |
  | C | $0.1520 |
  | D | $0.1555 |

  - Correctness: 39/39 units in every arm, 17/17 correct on first pass.
- **Hypotheses** (paired bootstrap, 10,000 resamples). H2, D vs A: **+35.5%** (CI +24.9% to +49.5%). H1, D vs
  C: +2.3% (−4.8% to +12.1%), not distinguishable. H3, A vs C: −26.2%. H4, B vs A: cost +21.2%, correctness
  difference 0. U6 duplicate-owner reports: A 2, B 2, C 1, D 0 (n = 2 per arm).
- **Architecture.** Not scored directly. Some hidden-oracle traps were architectural but scored behaviourally:
  - U4 `recent` must be built on `postingsOf` (DEC-U4-SHARED-VIEW);
  - U5 all-or-nothing `Store.transferBatch`.

  The fairness review (an independent agent) proved 4 wrong solutions that pass the visible tests and fail the
  oracle (U4 bypass: 2/10 oracle tests fail; U5 store loop: 3/9 fail). It rated 7 of 9 tasks "fair with changes"
  and U6 "unfair as specified".
- **Limitations.** Ceiling effect (no arm made any error); one small F# repository and one model; U6 n = 2; time
  metrics under 4-way concurrency (A3); shared cache (cold-prefix trials A 2/20, B 2/20, C 2/20, D 3/20, no
  decision changes); directives agents stepped outside their workspace twice; REL-GATE-004 trust-root exposure
  present but not exercised. **Decision: MODIFY** (Echelon as an opt-in assurance mode).

### 1.8 REL-001 run-03: verification benefit on trap tasks (cohort; DRAFT, not preregistered, no trial run)

- **Sources.** `protocol/run-03.md` (DRAFT, revision R1 of 2026-10-21), `run-03/README.md`, `run-03/PROVENANCE.md`,
  `run-03/harness/pins.json` (many fields TBD), `run-03/fixtures/check-output.txt`, `run-03/analysis/power.json`.
- **Question.** Does arm D cost more or less than A per independently verified requirement, when tasks can be
  completed wrongly?
- **Arms.** A–D as in run-02. D is the post-REL-GATE-003 / F4 build, pins TBD.
- **n.** 96 trials (8 tasks V1–V8 × 4 arms × 3 replicates = 24 blocks), seed 20261021, plus a 5-trial pilot.
  Fallback: 64 trials.
- **Primary metric (H1).** Cost per verified successful requirement, D/A − 1, with a paired bootstrap.
  - Secondary H2–H5 are Holm-adjusted. H5 is the verification benefit on trap tasks.
  - Power: 24 blocks detect about 20% at σ = 0.317, or 31% at 1.5σ (`power.json`).
- **Architecture.** Not scored. Hidden oracle only: 72 oracle tests and 13 wrong-solution variants.
  - V4 `stale-preview` (the preview keeps the old fee rule) is the only trap whose failure mode is architectural:
    no single source of truth.
- **State.** `observations/` is empty here. Gates G1–G8 are open. **Owned by another session; do not touch.**

---

## 2. What was and was not established about architectural correctness

### Established, with low confidence

1. **The arms do differ in architectural coherence, and blinded evaluators can see the difference.**
   - A021: 1 model against 3 stores / 2 join rules / 4 rejection types.
   - R2: the same shape.
   - A024: composites 5, 10 and 8.
   - These differences were evidenced at file and line level, with confirmed behaviour, while acceptance was
     identical or nearly so (A024 36/36 for all; R2 2 defects each).
   - **So acceptance tests do not capture architecture.** Correctness was at ceiling in A024 and in REL-001 runs
     01 and 02.
2. **A 0/1/2 × 5-dimension rubric with mandatory evidence citations is workable and discriminating.** A024
   produced 5, 10 and 8, with justified per-dimension scores and divergence-point counts.
3. **Symmetric behavioural probes expose architecture-linked defects that tests miss.**
   - Lost writes without a lock: A067 (8 creates, 2 stored); A024 snapshot W wrote while the lock was held.
   - Inconsistent JSON refusal shapes (A024 `probe.sh`).
4. **Some architectural constraints can be made oracle-testable.** REL-001 U4 (`postingsOf` agreement), U5 (store
   atomicity) and V4 (fee rule single source) turn an architectural rule into behaviour a hidden oracle checks.
5. **Continuity reliably cuts resources** (−40% to −49% tokens in 3 of 3 runs; cost 0.41–0.54×). Architecture
   does **not** reliably follow resources.

### Not established

1. **The direction of the effect of execution mode on architecture.** A021 and R2 favour grouped; A024 favours
   code-only fresh sessions (10 against 5). The confound is guidance: an analysis artefact was required in A021
   and not in A024. It is untested; A024 follow-on #1 proposes the ablation.
2. **Any variance estimate.** Every Praxis comparison has n = 1 per arm, from one cohort family
   (PRAXIS-GROUP-01..05) in one repository, designed by its own author.
3. **Inter-rater reliability.** Each architecture judgement came from one evaluator per run. Only A021 had a
   second evaluator (corroborating, but with broken blinding). No agreement statistic (kappa or ICC) exists.
4. **Evaluator-family independence.** Only R2 used a cross-family evaluator (GPT-5.6). A021 and A024 used Claude
   evaluators on Claude implementations.
5. **Construct validity of the rubric beyond one feature.** The 5 dimensions are specific to PRAXIS-GROUP
   (persistence, admission, classification, JSON/CLI, checkpoint). No general rubric was validated.
6. **Whether architecture ratings predict later cost.** A021 argued that "every later verb changes in 2–3
   places", but no follow-on change task was run to measure that.
7. **Whether Echelon directives or verification improve architecture.** REL-001 never scored architecture.
   Directives cost +21.2% with no measured correctness benefit, and their architectural effect is unmeasured.
8. **Automated architecture metrics.** There is no static or structural metric: no count of duplicate
   abstractions, no dependency rule checks, no layer-violation scan. Every architecture finding was produced by an
   LLM evaluator.
9. **Ground truth.** No experiment had a reference architecture against which arms were scored. Scores were
   relative and comparative.

---

## 3. REL-001 run-03 harness reuse map

**Convention.** Copy, then adapt, into the new experiment's own directory. Record the source path and sha256 of
each copy in a `PROVENANCE.md`, with tables for "Copied byte for byte", "Changed copies", "Adapted" and "New", as
`run-03/PROVENANCE.md` does. Never edit REL-001 files.

**Cross-cutting couplings to change in every copy.**
- Env prefix `REL003_` everywhere; default state roots `/tmp/claude-0/rel003/{runs,host,state}` (`lib.sh`). A
  copy that keeps them collides with run-03 on a shared host.
- Run-ID regex `^REL-001-R3-…` (`setup.sh`; labels from `-SMOKE-`/`-PILOT-`); `lib.sh` computes the checkout as
  `CBE=$R3/../../../..`, which depends on directory depth.
- Ledger paths: `tests/Ledger.Tests/Acceptance/`, `Ledger.slnx`, `src/Ledger/Ledger.fsproj` (oracle
  `LEDGER_PROJECT_PATH`), "Implement it in `src/Ledger`" in `briefs/core.md`. Task lists V1..V8 in
  `randomize.py`, `analyze.py` (`CONFLICT_TASKS={"V7"}`, `TRAP_TASKS`) and `check-static.py` S8.

| Component | What it does | Inputs → outputs | Reuse by a new experiment |
|---|---|---|---|
| `harness/lib.sh` (154 lines) | Shared helpers: arm letters, `require_pins` (gate G4), `sha`/`tree_sha`, dotnet and praxis logging shims (`write_dotnet_shim` logs every `dotnet` call to `logs/dotnet.jsonl`), `run_paths`, `verifier_stop`, Echelon tool copying | `pins.json`, `REL003_*` env → functions | **Adapt.** Keep the shims, digests and pin gate. Change the prefix, roots and depth. Drop the Echelon parts if the arms are not Echelon arms |
| `harness/setup.sh` (194 lines) | Builds 3 trees per run: the workspace (`repo/` with one initial commit, `AGENT_BRIEF.md`, `env.sh`, tool shims), host (contract, authority, policy, D verifier daemon) and state (`run.json`, `host-digests.json`, brief values). Refuses pilot or confirmatory runs while a pin is TBD or a digest differs | ARM, TASK, RUNID; `fixtures/repo`, `tasks/<T>/{requirement.md, *AcceptanceTests.fs, task.json, contract.json}` → workspace + `run.json` (fixture, oracle, acceptance digests; cache condition; model configuration digest) | **Adapt.** The 3-tree isolation and digests are generic and valuable. The Ledger paths, the Echelon blocks and the `ros.json` attested policy are specific |
| `harness/trial.sh` (70 lines) | `start` (setup; X1 when setup fails, exit 4 when refused by the pin gate), `launch` (K1, then finish), `finish` (endedAt, `praxis.agent-binding/1` file, transcript copy, verifier stop, score, observation copy) | RUNID, transcript dir, agent id → `observations/<arm>/<RUNID>.json` | **Copy almost unchanged.** It is generic apart from `lib.sh`. Smoke runs stay in state only |
| `harness/launch-agent.sh` (58 lines), **K1** | One headless `claude -p` per trial, run under `env -i` with a fresh `CLAUDE_CONFIG_DIR` and `HOME`, a fresh `--session-id`, a random nonce in `--append-system-prompt`, `--strict-mcp-config` with no servers, `--tools` from `agent-config.json` (`Bash,Read,Edit,Write`), `--permission-mode bypassPermissions`, `--output-format stream-json`, `timeout` = budget (exit 124 means X5) | `run.json`, `agent-config.json` (`.prompt` with `{BRIEF}`, `.budgetMinutes`, `.tools.builtIn`) → `launch.json` (argv, version, nonce), `stream.jsonl`, `final-message.txt`, transcript under `$CFG/projects` | **Copy and adapt (high value).** Only the nonce text and the env prefix are run-03 specific. Caveats: bypassPermissions is refused as root unless `IS_SANDBOX=1` (R1 note); K1 with a live agent has **not** been verified (no pilot ran); credentials come from `ANTHROPIC_API_KEY` or `REL003_CLAUDE_CREDENTIALS` |
| `harness/score.sh` (57 lines) | In state only: hidden oracle at the final HEAD (`git archive` → temporary tree, `Oracle.fsproj` with `LEDGER_PROJECT_PATH` substituted, `dotnet test` → TRX); in C/D also at the first completion commit; Praxis `telemetry reliability-report --agent-binding --price-table`; D `completion-identity`; then `score.py` | RUNID → `score/{final,first}/…`, `reliability-report.json`, `observation.json` | **Adapt.** The oracle-out-of-workspace pattern is directly reusable. Architecture scoring would be a **new** step here (for example static probes run on the archived tree) |
| `harness/score.py` (513 lines) | Builds `cbe.rel-001.observation/1` plus a `run03` block. Applies R5 (completion evidence), R6′ (V7 conflict), R9 (requirement unit); per-requirement oracle pass from the TRX by test-name prefix; M1 cross-check; M2 cache; X2 served model; X4 regex scan; X6 digest diff; test-run counts from the dotnet log | `run.json`, score dir, report exit → JSON on stdout | **Partly reusable.** Generic and worth copying: `usage_by_message` (one usage record per message id, keeping the maximum output), `usage_tokens` (cache-write split 5m/1h), `priced`, `cross_check`, `served_models`, `x4_hits`, `oracle_result`, `test_runs`. Task-specific: R6′/V7, the Echelon event parsing, `X4_PATTERNS` (`run-03/fixtures`, `OracleV\d`) |
| `harness/randomize.py` (69 lines) | Blocked randomization: blocks (task, replicate), block order shuffled, then the arm order inside each block, from one `random.Random(seed)`. Fixed pilot | seed → `order.json`, `pilot-order.json` | **Copy and change constants** (ARMS, TASKS, REPLICATES, seed, run-ID format, pilot) |
| `analysis/analyze.py` (269 lines) | Preregistered analysis, standard library only, deterministic (splitmix64, 10,000 resamples, keys sorted, rounded to 6 places). Pooled Σcost/Σcorrect per arm, paired percentile bootstrap over blocks, Holm for the secondary family; X2 removes the block from that arm's comparisons, X3 per-metric eligibility, X4 excludes the run, X5 counts as failed | `observations/**` → `results.json` | **Adapt.** The engine (PRNG, bootstrap, Holm, exclusion handling) is generic. Metric definitions and constants must be rewritten for architecture outcomes. `selftest.py` (T1–T5 on synthetic data) shows how to prove determinism and the exclusion rules; copy that pattern |
| `analysis/power.py` (66 lines) | Normal-approximation sample size on paired log ratios: n = ((1.96+0.8416)·s/ln(1+δ))², with σ and 1.5σ | run-01 observations, price table → `power.json` (σ_cost = 0.317, σ_tokens = 0.219, 6 pilot blocks) | **Copy the formula.** The run-01 σ is a cost-ratio σ from routine tasks. An architecture rubric outcome needs its own pilot variance; none exists anywhere |
| `fixtures/check-static.py` (171 lines) | S1 files and digests match `task.json`; S2 every test name starts with a requirement ID, and every requirement has visible and oracle tests; S3 isolation (nothing given to an agent names the oracle, references or `task.json`); S4 no oracle test name shared with run-02; S5 `make-references.py` and `make-contracts.py` reproduce committed files; S6 wrong variants differ from the reference; S7 F# hygiene; S8 fsproj order | fixture dir (+ run-02 fixtures) → PASS/MISMATCH lines (24/24 PASS) | **Adapt.** S1–S3, S5 and S6 are generic. Add an S4-style check against **both** run-02 and run-03 fixtures, so no oracle or task id is shared |
| Oracle structure | `fixtures/oracle/Oracle.fsproj`, a template project referencing `LEDGER_PROJECT_PATH`, plus `oracle/<T>/OracleTests.fs` (module `OracleV<n>`, tests named `LEDGER-<T>-R<k> …`). `reference/<T>/` and `reference/<T>-<variant>/` are generated by exact edits (`make-references.py`). `check.sh` proves the reference passes and each wrong variant *builds* and fails (about 10 min with .NET 10.0.402) | — | **Pattern reusable.** An architecture experiment can use the same mechanics for "architecturally wrong but behaviourally passing" variants. Those need structural probes, not only oracle tests |
| Brief rendering | `render-brief.py`: `{{NAME}}` substitution; a line holding only an empty placeholder is dropped; an unknown placeholder is an error. Templates `core.md`, `directives.md`, `workflow-c.md`, `workflow-d.md`, `outcome.md` (byte copies of run-02's) | values JSON + templates → `AGENT_BRIEF.md` (sha256 recorded in `run.json`) | **Copy `render-brief.py` byte for byte.** Write new templates; `core.md` hard-codes `src/Ledger` and the 45-minute budget |
| Pricing table | `pricing/anthropic.price-table.json` (`praxis.price-table/1`, tableVersion 2026-10-20.1, sha256 `dd58c305…`). claude-opus-5-5 per MTok: input $4, output $20, cache read $0.20, cache write 5m $5, cache write 1h $8; plus the source excerpt | — | **Copy byte for byte** with provenance, as run-03 did from `research/pricing/` |
| Token accounting and M1/M2 | Primary: the pinned Praxis `telemetry reliability-report` over the copied transcripts with an agent binding. Cross-check M1: transcript usage deduplicated by message id and priced with the same table; G3 requires report and harness within 1% on cost and total tokens. M2: first-request cache read and write, `firstRequestCold`, cache-read share, and cold-equivalent cost (cache reads repriced at the input rate) | transcripts → `observation.run03.{cost, crossCheck, cache}` | **Reusable.** The harness cross-check alone works without the Praxis measurement binary (it is what dry runs use). Transcript output tokens are a lower bound (run-01 A4; REL-TOKEN-002 is open) |
| `smoke.sh`, `smoke-agent.sh` | A stand-in agent applies the reference or a wrong variant; dry-run mode needs no .NET | — | **Adapt.** Useful to prove that the scorer separates architecture variants before any live trial |

### Lessons and amendments relevant to a new experiment

- **Cache isolation (run-01 A3, run-02 threats, run-03 K1).** K0 (Agent-tool sub-agents) shares the
  orchestrator's prompt cache, so no trial is cold; run-02's post-hoc check found cold prefixes balanced (2–3 of 20
  per arm), with no decision changed. Prefer K1 and *measure* cache state on every trial. `--tools` cut the
  first-request context from 16,513 to 5,821 tokens (n = 3, `token-efficiency/prefix/PREFIX-COMPOSITION.md`);
  K0 cannot take `--tools`.
- **K0 versus K1 is a P1 decision made on pilot instrumentation only,** never on outcomes. Use the same condition
  in every arm and record it in `pins.json` before trial 1.
- **Exclusions X1–X6 are fixed in advance.** X1 setup failure: rerun with a new id (the only allowed rerun). X2
  served-model mismatch: drops the block's comparisons for that arm. X3 missing metric: excluded per metric only
  (run-01 broke this by being stricter than the protocol). X4 oracle contamination: run excluded. X5 budget
  exceeded or gave up: scored as failed, cost kept. X6 host-file digest changed: scored as an invalid attempt.
- **Contamination.** Two run-02 directives agents moved the visible test file outside the workspace
  (`protocol-notes.md`); not X4, scored as is. A024 forbids reading main, other arms or prior results (its audit
  flagged own-branch `FETCH_HEAD` falsely). The A021/A024 rubric and evaluations are readable inside the Praxis
  repository; keep agents away from them (A023 excludes Praxis as a block for this reason).
- **Oracle hiding.** The oracle, references and `task.json` live only under `fixtures/` and the state tree;
  `score.sh` runs them on a `git archive` copy; S3 proves agent inputs do not name them; X4 regexes scan
  transcripts. Any architecture rubric, probe script or reference architecture must be hidden the same way (A024
  shortened its prompt "so as not to paraphrase the rubric").
- **Timeouts.** 45-minute budget, `timeout 2700` in K1 (exit 124 means X5). The longest single-task trials took
  166 s (run-02) and 128 s (run-01), so budgets never bound; A021 and A024 multi-item sessions ran 51–61 min.
- **Wall time** ends at the last transcript event (run-02 A2). Run trials serially: run-02 A3 concurrency
  contaminated time metrics.
- **Ceiling effect.** Every REL-001 arm passed every requirement (12/12, 39/39) and A024 passed 36/36; run-03
  answers this with trap variants. An architecture experiment needs outcomes that are not at ceiling.
- **Orchestration waste counts against many-session arms.** The A021 control spent 5.66M tokens (12.2%) in
  stalled sessions; A024 lost 0.87M to the stale launcher (TE-H11). Never use `outcome_branch` for branches that
  earlier sessions advanced (A024 D1–D3).
- **Blinding pitfalls.** Unscrubbed "grouped-arm" and "control branch" strings (A067); R2's lost salt (mapping
  recovered by blob identity); labels inferable from file names (A022 orchestration leak). Scrub with
  `(control|grouped)[- ](arm|branch)`-style patterns and reset `.ros/`.
- **Praxis research-tree quirk.** Every `.md` under Praxis `research/experiments` is parsed as a record. Keep
  harness documents as `.txt` (A024 D4). This does not apply to the cohort repository.

---

## 4. The run-03 Ledger fixture

- **Domain.** A small in-memory double-entry-style ledger in F# (.NET SDK 10, xunit). It covers accounts, dated
  postings (positive amounts credit, negative debit), balances, transfers, a business date and period close with a
  fee.
- **Origin.** It is the run-02 Ledger, copied byte for byte (`PROVENANCE.md`), minus U7's `docs/design/interest.md`
  and plus `docs/design/standing-orders.md`.
- **Structure** (`run-03/fixtures/repo/`, 302 lines of code, tests and docs).

  | Path | Lines | Content |
  |---|---|---|
  | `src/Ledger/Domain.fs` | 40 | Types `AccountId`, `Posting`, `LedgerError` (6 cases), `PeriodSummary`, `LedgerState` (postings newest first) |
  | `src/Ledger/Ledger.fs` | 88 | Pure operations: `openAccount`, `setDate`, `postings`, `postingsOf` (the shared per-account helper), `balance`, private `post`, `credit`, `debit`, `transfer` (documented refusal order), `closePeriod` (idempotent per period, 1.00 fee) |
  | `src/Ledger/Store.fs` | 55 | Stateful `LedgerStore`: journal ref plus a **balance cache** kept in step by every operation; refused operations change nothing |
  | `tests/Ledger.Tests/BaseTests.fs` | 91 | Base xunit tests; `Acceptance/` is empty until setup copies a task's visible tests |
  | `docs/design/standing-orders.md` | 28 | V5 design note (shortfall rule) |

  Plus `Ledger.slnx`, `Directory.Build.props`, `global.json` and `README.md`. **One project**; the compile order is
  `Domain.fs`, `Ledger.fs`, `Store.fs`.
- **Tier structure.** There are no separate projects or assemblies and no enforced dependency rules. Inside one
  project there is an informal 3-layer split: domain types → pure core (`Ledger.Ledger`) → stateful store
  (`Ledger.Store`). F# compile order enforces that the store depends on the core and never the reverse.
  - Embedded architectural conventions: "Public signatures in this module are the module's contract; keep them";
    "Every per-account query in this module is built on it" (`postingsOf`); "`Store` is the one place where ledger
    state changes"; "balance cache kept in step".
  - "Tiers" in run-02 U7 meant tiered interest *rates*, a domain rule, not architectural tiers. U7 is not in
    run-03.
- **Tasks already on it.**
  - Run-02: U1–U9.
  - Run-03: V1–V8, with 15 requirement units, 72 oracle tests and 13 wrong variants.
  - V5 and V6 add new modules (`StandingOrders.fs`, `Reconciliation.fs`).
  - V3 (holds must apply to `debit` **and** `transfer`) and V4 (a single fee rule shared by `closePeriod` and
    `feeFor`) are the closest to architecture tasks.
- **Suitability as a base for architecture tasks.**
  - **For.** It is small and fast: full `check.sh` takes about 10 min, and trials take 2–3 min. It is
    deterministic, has explicit layering and contract comments, has a proven oracle/reference/trap pipeline, and
    every arm solved it at ceiling. Its natural architecture hazards are real: bypassing `postingsOf`, mutating
    state outside `Store`, letting the balance cache drift from the journal, duplicating the fee rule, adding a
    second refusal-order convention.
  - **Against.**
    - At 183 lines of production code there is little room for divergent *cross-item* architecture of the A021 or
      A024 kind (stores, parsers, envelopes).
    - Single project, no persistence, no I/O, no API or CLI layer, no dependency-injection seams.
    - Run-02 and run-03 agents have already seen it, but only fresh sessions ran, so memorization risk is low.
    - **Collision risk.** Reusing the V or U task ids, oracle names or the run-03 state roots would interfere with
      run-03, which is owned elsewhere.
  - **Verdict.** It is usable as the *starting* repository for a copied, renamed fixture (new task ids, new oracle
    module names, an S4-style uniqueness check against both run-02 and run-03). It is better for *single-task
    architectural-conformance* traps (behaviourally passing, structurally wrong) than for multi-item coherence. A
    multi-item architecture study would need the fixture extended (for example a second project or tier) or a
    larger base. Any extension must be a new copy, never an edit of `run-03/fixtures/`.

---

## 5. Ongoing or planned work a new experiment must not duplicate or disturb

| Work | Owner / status | Constraint for the new experiment |
|---|---|---|
| REL-001 run-03 | Another session; DRAFT with pins TBD, gates G1–G8 open, no trial run (`protocol/run-03.md`; manifest workstream C "draft-complete") | Do not modify `REL-001/**`. Do not use `/tmp/claude-0/rel003/*` or the `REL003_` env names. Do not reuse V1–V8 ids or `OracleV*` names. Do not run trials concurrently on the same host while run-03 runs (run-02 A3: shared CPU contaminated time metrics). Its question is verification cost and benefit, not architecture |
| REL-001 run-02 (done) | Complete, merged (`REPORT-run-02.md`) | Do not re-ask "is Echelon cheaper than bare?"; the answer is +35.5% for D vs A at ceiling |
| Praxis A022 on main | `blocked`: gate failed, no arm (EV-A072) | Do not substitute a two-repository design under the A022 id |
| Praxis A022 orchestration variant (sealed) | `experiment/a022-orchestration`, sealed, condition D 4 of 5 | Do not read, cite values from or unblind it. It covers cohesion × grouping on the PRAXIS-CTL cohort |
| Praxis A023 | `proposed` (2026-10-02); instrument not built | Owns grouped versus independent × affinity across repository blocks, including its blind architecture findings. Do not run G/I contrasts on Echelon repositories without coordinating |
| Praxis A024 follow-ons | `FOLLOW-ONS.txt`, not preregistered | #1 **guidance ablation** (context × required analysis artefact, scored with the A024 architecture rubric) overlaps most with an architectural-correctness study. Coordinate, or cite it explicitly as out of scope. #2 (fresh verifier after a grouped implementation) is also architecture-adjacent |
| Praxis hypotheses | HY-A028 `supported` (architecture disjunct reversed in A024); HY-A029, HY-A030 `active` | Results bear on these. Do not edit Praxis registries from the cohort repository |
| Coordination backlog | `coordination/FINAL-REPORT.md` items 1–15 (REL-GATE-004 release, REL-TOKEN-001/-002, grouping against bare Claude as "a follow-on run, not in run-03") | "Test grouping directly against bare Claude" is earmarked as a separate follow-on. Do not fold it in unannounced |
| Other repositories | `ordo/research`, `dokimos/research` and `visual-engineering/research` have experiment trees; not reviewed here. HISTORICAL-EVIDENCE lists CONSTRUCT-008 and Ordo boundary hardening (TE-H08–H10) | Check before claiming novelty in mechanical-first or construct experiments |
