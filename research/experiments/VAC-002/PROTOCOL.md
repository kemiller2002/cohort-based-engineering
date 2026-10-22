# VAC-002 protocol: long-horizon reliability and adaptive enforcement

- **Status:** pilot protocol, frozen before the first agent turn. The commit that adds this file, with
  `PREREGISTRATION.md`, `ARMS.md`, `TASK-CORPUS.md`, `FAULT-CATALOG.md`, `METRICS.md`, `BUDGET.md`, the harness, the
  fixture and the sealed-store digest, is the freeze. Later changes are amendments (§12).
- **Experiment ID:** VAC-002. **Working title:** long-horizon agent reliability and adaptive verification.
- **Baseline:** [`BASELINE.md`](BASELINE.md). **Hypotheses and decision rules:** [`PREREGISTRATION.md`](PREREGISTRATION.md).

## 1. Questions

These are the mission's seven questions, as H1–H7:

1. Do long-lived agents accumulate errors as work progresses?
2. Do Ordo and Dokimos prevent consequential errors?
3. Does verified engineering state improve reliability over long histories?
4. Can selective verification give comparable reliability at lower cost?
5. Does the four-tier architecture prevent drift?
6. Do errors propagate differently through persistent and restarted agents?
7. Which controls justify their overhead?

The objective is to find what works, not to show that Echelon works.

## 2. Substrate

| Part | Location |
|---|---|
| **Fixture** | `fixture/repo`. ARCH-001's Lending application, with the base changes in `TASK-CORPUS.md` §1: README conventions, stable entry points, and vendored OpenDays 1.4.0 |
| **Tasks** | `fixture/tasks/L01..L12`. Requirement, visible acceptance tests, optional `stage/` (decision revisions) and `before/` (harness-made changes), `contract.json` and `task.json` |
| **Hidden material** | `/home/user/.vac2-sealed`: `oracle/` (per-task xUnit oracles, `OracleSupport.fs`, `run.sh`), `ref/` (git repository; tags `ref-L01..ref-L12`, `before-L10`, trap branches) and `propagation-map.json`. Encrypted into `sealed/` at the freeze |
| **Self-check** | `fixture/check.sh` → `fixture/check-output.txt`. Every reference passes every cumulative oracle, the repository tests and `archcheck`; every trap fails what it targets |
| **Tools** | .NET SDK 10.0.402. Ordo `bb43c26` (1.17.0). Praxis `986211c` (3.19.0). ARCH-001 `archcheck` (FCS 43.12.402) with the Lending policy `lending/0.1`. Claude Code 2.1.308 |

## 3. Arms

There are six arms; see [`ARMS.md`](ARMS.md):

| Arm | Agent | Verification |
|---|---|---|
| A | Fresh agent per unit | Baseline |
| B | Long-lived | Baseline |
| C | Long-lived | Ordo constraints |
| D | Long-lived | Full Ordo, Praxis and gate, with verified state |
| E | Long-lived | Adaptive gate (frozen policy 1.0.0) |
| F | Restarted every 4 units | D's controls, with verified-state reconstruction |

## 4. Procedure for one unit (`harness/vac2.sh unit RUN ARM N TASK`)

1. **Stage.**
   - If the task has `before/`, the harness commits those files as its own commit. This is how D1 enters before L10.
   - It copies `stage/` (decision revisions), the requirement, the visible tests and (for C–F) the contract, and
     commits only those paths. An agent's uncommitted work is never swept into a harness commit.
   - It computes the pre-decision signals (`pre-N.json`; every arm, used only by E).
   - It renders the brief (`harness/briefs/brief.md` through `vac2.fsx render`). The brief includes the fault note if
     the task hosts one.
2. **Turn.**
   - One K1 process: `claude -p` in the repository, with a fresh `CLAUDE_CONFIG_DIR` and `HOME` per session.
   - The orchestrator's directories, CLAUDE.md files, skills, plugins, messaging, GitHub tokens and harness variables
     are unset.
   - Tools: Bash, Read, Edit, Write. `bypassPermissions`. No MCP servers. `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000`.
     Timeout 45 minutes.
   - Session lifetime: a **new** session for A at every unit, for F at units 1, 5 and 9, and for every arm at unit 1.
     Otherwise the turn **resumes** the arm's session.
   - Usage: the CLI's result event gives final usage and cost per turn. VAC-001's `vac.fsx usage` gives request-level
     context size, compactions, the X4 contamination scan and the scope scan, over the session transcript window.
3. **Gate** (D and F at the high tier; E at the tier its policy selects; never A, B or C).
   - The host clones the head and runs the tier's checks (`ARMS.md`).
   - On failure the agent gets one repair turn in the same session, with only the failing checks, and the gate runs
     again.
   - D and F then get the verified state written and committed by the harness.
4. **Score** (post hoc, after the whole run; never during agent turns).
   - For every unit's final attempt (and attempt 1 of gated arms), the host clones the recorded head and runs:
     - the repository tests;
     - the hidden oracle of **every task staged so far** (each task in its own project, so one task's compile
       failure cannot hide another's result);
     - `archcheck`;
     - Layer 1 evidence.
   - The result is written to `score-N-K.json`.

## 5. Isolation and independence

- **Separate trees.** Each arm has its own workspace (`/home/user/vac-work/RUN/ARM`), bare git remote and harness
  state (`/home/user/.vac2-state/RUN/ARM`). The trees are never nested.
- **No shared starting point.** No arm's implementation becomes another's starting point. Every arm starts from
  `fixture/repo`.
- **The oracle is sealed** during agent turns: its plaintext is moved out of reach and only the encrypted archive
  remains on disk. Scoring decrypts it afterwards. This is stronger than VAC-001, whose plaintext oracle was present
  throughout.
- **Contamination (X4).** Every turn's tool inputs are scanned for:
  - `.vac2-sealed`, `.vac2-state`, `cohort-based-engineering`, `/oracle` and `OracleTests`;
  - another arm's workspace;
  - `task.json` and `faults.json`.

  A hit excludes the unit (X4) and is reported.
- **No self-grading.** No agent grades its own work. Acceptance is the hidden oracle plus `archcheck`. The gate is
  host-run and the agent cannot alter it.
- **Layer 3 independence.** Layer 3 reviewers are separate reviewer sessions, blinded to arm and lifetime (§9). A
  reviewer from another model family, as VAC-CBE-001-R4 asks, is **not available** in this environment. That is a
  stated limitation.

## 6. Runs

| Run | Purpose | Arms | Chain | Faults | Replicates |
|---|---|---|---|---|---|
| **P1, pilot** | Feasibility, discrimination, variance and cost | A–F | L01–L12 (12 units) | F1 at L05, F2 at L06, D1 + F3 at L10 | 1 |
| **R25 / R50 / R100, confirmatory** | H1–H7 | A–F | 25 / 50 / 100 units (`TASK-CORPUS.md` §4) | As in the corpus | By `PREREGISTRATION.md` §3 |

**Confirmatory runs are not authorized** without an explicit spending ceiling (`BUDGET.md`).

**Order.**

- The chain order is fixed by task dependencies.
- Arm launch order is randomized: `random.Random(20261022).sample` of A–F.
- All six arms of a run execute concurrently. Wall-clock time is therefore exploratory, as in VAC-001.
- Tokens, cost and correctness are unaffected by concurrency.

## 7. Discrimination check (pilot → confirmatory gate)

The corpus **discriminates** if, in P1, both hold:

- (a) at least two arms have at least one unit failure (UF) or consequential error;
- (b) the arms' CE counts are not all equal.

If every arm is at ceiling (no CE anywhere), the corpus is amended for difficulty (`TASK-CORPUS.md` §5), self-checked
and frozen again, and a new pilot runs before any confirmatory run.

## 8. Analysis

The full plan is in `PREREGISTRATION.md` and `STATISTICAL-ANALYSIS.md` (post-run).

**Method.**

- Paired blocks are (replicate, position).
- Cluster bootstrap over chains, 10,000 resamples, seed 20261022.
- Logistic IRLS for slopes.
- Kaplan–Meier for survival.
- Holm correction across the primary tests.

Correlation is not reported as causation. Only arm contrasts are randomized; context size and position are
observational.

**The pilot is reported descriptively.**

## 9. Evaluation layers

| Layer | What |
|---|---|
| 1, deterministic | Build, tests, cumulative oracle, `archcheck`, clean tree, per-decision evidence existence, conflict-surfaced first pass, fault acceptance indicators, X4 and scope scans |
| 2, structured | One row per reported decision (`results/RUN/decision-dataset.jsonl`), reusing VAC-001's `decisions.py` shape: ID, requirement refs, evidence, Layer 1 validity, applicability, outcome |
| 3, blinded adjudication | A seeded sample: every fault-unit and conflict-unit decision, every Layer 1 invalid or no-evidence decision, and 25% of the rest. Arm, run and lifetime are stripped. Two independent reviewer sessions use the VAC-001 rubric (`../VAC-001/results/layer3/RUBRIC.md`), extended with a `silent-conflict-resolution` label; a third adjudicates disagreements. Agreement is Cohen's κ |

## 10. Reporting

- Every number cites a committed observation or analysis file.
- Missing values are `unavailable` with a reason.
- A Praxis or agent completion record alone is labelled **unverified**.
- Negative and null results are reported with equal prominence.

## 11. Deviations from VAC-001 and ARCH-001 (designed, recorded before the run)

| Change | Reason |
|---|---|
| K1 isolated CLI agents (ARCH-001's launcher) instead of K0 sub-agents; long-lived arms continue with `--resume` | VAC-CBE-001-R4 asks for K1; it removes the orchestrator's shared cache prefix |
| The gate uses no hidden-oracle information; scoring is post hoc | VAC-001's gate fed the oracle back to the agent |
| The compiler-resolved `archcheck` replaces lexical VAC-RULES; the four-tier Lending fixture replaces single-project Ledger | ARCH-001's validated instrument; the four-tier architecture is exercised |
| Cost from the CLI's final usage (`cli-estimate`), not the transcript lower bound | The result event reports final output tokens; VAC-001's amendment A4 limitation removed |
| Compaction window set to 200,000 tokens in every arm | To reach context management within the chain (VAC-001 saw 0 compactions) |
| A sixth arm, E (adaptive), and F replaces DR (restart every 4 units, not every unit) | Mission arms |
| Reviewers are the same model family | Another family is not available here |
| Claude Code 2.1.308 (ARCH-001 used 2.1.306) | The installed version |

## 12. Freeze record and amendments

**Freeze (pilot P1).** Made before any agent turn. It consists of this commit together with:

- the corpus self-check `fixture/check-output.txt`: `RESULT: PASS (119 passed, 0 failed)`;
- the harness smoke (`harness/smoke/SMOKE3/`). Arms E and F ran the full 12-unit chain with the reference-applying
  stand-in agent. In each arm, 10 of 12 units are accepted; the other two (L04, L08) are correctly not accepted,
  because the stand-in's report does not surface the conflict. The gate rejected them for the same reason;
- the sealed store, `sealed/SEAL.json`:
  - plaintext tar.gz sha256 `98e2ec9f20592b168c5b8c9c7a382b7053268787fcc7285c32bfa40b4d6d48bc`;
  - ciphertext sha256 `0371c9c9cbfddc099a565905e7c77f2899ded8ca9b2c5bcced21c5d45adb11a7`;
  - 508 files.

**Pre-freeze calibration.** Adaptive policy S6 and S7 were narrowed on the base rates of the reference diffs only
(`harness/policy/adaptive-policy.json` `calibrationNote`). Before the change, S7 fired on any `.fsproj` edit and S6 on
3 or more tiers, which escalated nearly every unit to the high tier.

**Run discipline.** The pilot runs from a git worktree of the freeze commit (`harness/pilot.sh`), so no later edit
can reach a running chain. The plaintext sealed store is removed from disk while agents run.

*Amendments: none yet.*
