# VAC-002-P3 protocol

## 1. Repository state and provenance

- **Working branch.** `experiment/vac-002-p3-authority-ablation`, created from `main` at `4c21527` (PR #19).
- **Where P2 lives.** PR #20 (P2) was merged on 2026-10-23 into PR #18's branch, `claude/echelon-vac-002-experiment-wkdvi7`
  (merge commit `10e1adf`), **after** PR #18 itself had been merged into `main` (`836d0bb`). P2's 819 files are
  therefore not on `main`.
- **How P3 recovers it.** The working branch merges `10e1adf` (P2 and its Praxis intake) into `main`'s line. P2's
  artifacts are byte-identical to `10e1adf`, and no P2 file is changed by P3: `git diff 10e1adf -- research/experiments/VAC-002/P2`
  is empty.
- **research-documents PR #23.** Not reachable from this session: the repository is not attached, and GitHub access
  to it was refused. Its contents are not used. The P3 summary PR to research-documents is in `README.md` §Publication.

## 2. What is reused from P2

| P2 component | P3 use |
|---|---|
| Fixtures `P2/fixture/{lending,billing,clinic}/repo` | Read in place, then transformed per tree (§5) |
| Scenarios S01–S12 (overlays, visible tests) | Read in place as D01–D12 |
| Sealed store (oracles, references, traps, valid alternatives, generators, `meta.json`; key published) | Decrypted into `P3_SEALED/p2/` while scoring only |
| Oracle support projects | Same files; project prepared for the TestKit (§5) |
| `p2.sh` execution lifecycle, K1 launcher, gate, cost rule | `harness/p3.sh`, a recorded derivative (`DERIVATION.md`) |
| `p2.fsx` functions (trx, records RC1–RC3, admission A1–A9, stream usage and contamination scan, render, score) | `harness/p3.fsx`, the same functions plus the P3 additions (`DERIVATION.md`) |
| `corpus.sh` tree/oracle/check | `harness/corpus.sh`, the same checks over P3 scenario files |
| Review bundle, runner, rubric, agreement | `harness/review/`, derivatives; `P2/harness/review/agreement.fsx` used unchanged |
| VAC-002 `seal.sh` | Used unchanged for the P3 stores |
| Contract v0.2 specification (P2 `DECISION-AUTHORITY.md` §5) | Implemented as `p3.fsx admit2` for arm E |

## 3. Arms

Every arm gets the same scenario tree (one hash per scenario across all five arms), the same model and
configuration (`harness/agent-config.json`), the same tools (Bash, Read, Edit, Write), the same 30-minute turn
budget, the same report schema, and a fresh agent per execution. Briefs are assembled from one template
(`harness/briefs/brief.md`):

| Arm | Treatment | Brief sections | Turns | After the agent |
|---|---|---|---|---|
| **A** | Requirements only | intro, report | 1 | nothing |
| **B** | + authority contract | intro, **authority**, report | 1 | nothing |
| **C** | + contract + short checklist (3 questions, answered in the report) | intro, authority, **checklist**, report | 1 | nothing |
| **D** | + contract + typed decision records (`echelon.decision-record/0.2`), not checked | intro, authority, **records**, report | 1 | nothing |
| **E** | + contract + typed records + executable authorization: plan, admission (v0.2), implement, gate | intro, authority, records, **plan → implement**, report → repair | 2–3 | admission after the plan; gate with one repair round |

- **Intro and report sections are neutral in every arm.** P2's intro said the README held "the rules for where
  business rules may come from"; P3's says only that it holds the standing requirements. P2's report described
  `openQuestions` as needing "someone with the authority to make it"; P3's says "unresolved questions".
- **D and E use the same record schema.** So D − B measures typed records, and E − D measures checking them.

**Arm E versus production Ordo.** The checker is `p3.fsx admit2`. It is experimental and isolated: it reads only the
starting tree, the final tree, the agent's records and the host's receipt list. It does not use Ordo's code. It
differs from production Ordo in these ways (from P2 `DECISION-AUTHORITY.md` §4):

- Ordo authorizes construction *transitions* by actor; the checker authorizes *business-rule decisions* by the
  status and provenance of the sources they cite.
- Ordo's approved decisions are bound to a blueprint digest; the checker's to files in the repository.
- Ordo's conflict nodes are authored by people; the checker has none, so a conflict the agent does not declare is
  invisible to it.
- Verification receipts are host strings, not Dokimos DSSE signatures; the agent and host share a uid (REL-001 F6).
- Contract v0.2 changes C1–C5 are implemented (`p3.fsx` header). P2's adaptive independent review (P2 arm E) is
  **not** part of any P3 arm.

## 4. Execution

- `harness/p3.sh queue RUN SEED PARALLEL ARMS REPS SCEN...` writes a seeded random order of (scenario, arm,
  replicate) triples to `results/RUN/order.txt`, then runs them PARALLEL at a time.
- Each execution has its own workspace (`/home/user/p3-work/RUN/X`), its own harness state
  (`/home/user/.p3-state/RUN/X`) and its own fresh configuration directory and HOME.
- The executing agent never sees another execution's workspace. The contamination scan flags any tool input naming
  another workspace, harness state, the sealed stores, the experiment repository or the orchestrator's paths.
- Stage 1 runs 2 at a time on a 2-CPU container. P2 ran 3 at a time on 4 CPUs.

## 5. Environment and deviations from P2

| # | Deviation | Why | Effect on comparison |
|---|---|---|---|
| D1 | NuGet is unreachable from this container. Test projects compile a source-compatible stand-in for the xUnit subset these repositories use (`fixture/testkit/`). `dotnet test … --logger trx` keeps working through a `VSTest` target in `Directory.Build.targets`. Test source files are unchanged | No package can be restored | Identical in every arm. The agent sees `tests/TestKit/` and a root `Directory.Build.targets`. The P2 oracle was re-validated under it (`ORACLE-VALIDATION.md`) |
| D2 | Every fixture `README.md` loses its "Authority" section at tree build (`p3.fsx derive`) | It is the confound under test | The treatment |
| D3 | Agents run in an allowlisted environment (`env -i`), not an inherited one minus a fixed list. They get no egress proxy | The orchestrator's environment carries memory, session ingress, skill and plugin sync and git credentials that P2's unset list does not cover | Identical in every arm; stronger isolation than P2. The agent's Bash has no network route |
| D4 | Claude Code 2.1.309 (P2: 2.1.308) | The container's CLI | Identical in every arm |
| D5 | `p3.fsx` drops P2's unused `#r "nuget: FSharp.SystemTextJson"` line | NuGet is unreachable; nothing used it | None |
| D6 | NuGet audit is off in every tree (`NuGetAudit=false`) | The audit's failed lookup adds a timeout and two warnings to every build | Identical in every arm |

## 6. Exposure manifest (the P2 confound, tested)

`harness/p3.sh expose SCEN DIR` builds each arm's workspace and briefs exactly as `exec` does, then for each arm:

- hashes the workspace tree;
- lists the brief headings;
- searches every readable file (briefs, wrapper prompt, the whole tree) for 12 markers: the contract's four
  sentences, eight phrases of P2's Authority section, and P2's two brief phrases that point to authority.

**Checks.** The workspace trees are identical across arms; arm A has zero marker hits; arms B–E contain the contract.
`ARM-EXPOSURE-MANIFEST.json` holds the result for every scenario of the stage. A failing check blocks the stage.

**What the manifest cannot see.**

- The model's own system prompt. It is Claude Code's default, identical across arms, with no CLAUDE.md or skills,
  because the configuration directory is fresh and empty.
- Text an agent writes for itself.

## 7. Oracle and scoring

- **Oracle.** P2's two-dimensional oracle (P2 `ORACLE-SPEC.md`), unchanged, for D01–D12. The same structure for
  D13–D16 and Stage 2.
- **Scoring.** `p3.sh score RUN SCEN ARM REP [LABEL]` scores a recorded head against the sealed store, after every
  agent turn of the stage has ended.
- **E's heads.** E is scored at `implement` and at `final`, which separates prevention from detection and correction.

## 8. Freeze records

| Stage | Commit | Contents |
|---|---|---|
| Stage 1 | the commit that adds this file | Contract, arms, harness, discovery corpus (public part), sealed discovery store (ciphertext; key outside the repository), oracle validation, exposure manifest, preregistration |
| Stage 2 | amendment CR-1 | Confirmatory corpus, sealed store, sample size, seeds |

## 9. Amendments

None yet.
