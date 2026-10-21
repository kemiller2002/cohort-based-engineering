# REL-001 run-02: fairness review of tasks U1–U9 and the directives pack

Reviewer: independent agent (did not design the experiment). Date: 2026-10-20.
Scope: `run-02/fixtures/` (repo, tasks, oracles, references, `check-output.txt`), `run-02/directives/`,
design draft `02-run02-design.md`, run-01 `REPORT.md`. Nothing under review was modified.

Paths below are relative to `research/experiments/REL-001/run-02/` unless stated.

## How this was checked

- Read every requirement, visible test, contract, `task.json`, oracle and reference. Matched each oracle
  assertion to the prose sentence that requires it.
- Checked `DIRECTIVES.md` line by line against the sources at the commits in `PROVENANCE.md`. All seven
  source digests match. Every kept line is a whole source line, except `DIRECTIVES.md:41`, which is a
  declared excerpt.
- Built the starting repo with the pinned SDK: 0 warnings, 0 errors.
- Ran four plausible, non-strawman wrong solutions against visible tests and oracles. Each was made by
  overlaying `reference/U<n>` and changing one function. **All four pass every visible test and fail the
  oracle:**

| Variant | Change from the reference | Oracle |
|---|---|---|
| U3 interleaved | correct shares; existence and funds checked per account, in one pass in list order | fails 1/10: `refusal order` only |
| U7 whole-balance | `interestFor` applies the highest reached tier's rate to the whole balance | fails 8/13 |
| U5 store loop | `Store.transferBatch` folds `Store.transfer` per instruction | fails 3/9 (all R2 store tests) |
| U4 bypass | `recent` filters `ledger.Postings` directly instead of calling `postingsOf` | fails 2/10 (R1-after-R2 tests) |

## Verdicts per task

| Task | Category | Verdict | One-line reason |
|---|---|---|---|
| U1 | simple | **fair** | Fully specified; every oracle assertion is stated. Ceiling expected. |
| U8 | simple | **fair** | Fully specified; inclusive bounds, ordering and refusal order are stated. Ceiling expected. |
| U4 | moderate | **fair with changes** | Oracle matches the prose. The trap fires only if the agent ignores an explicit instruction (`requirement.md:23-26`). The trap is unproven in `check.sh`. |
| U5 | moderate | **fair with changes** | Oracle matches the prose. The trap is very weak: `Store.commit` makes the right solution one line. The trap is unproven in `check.sh`. |
| U7 | complex | **fair with changes** | The contract hands C/D the resolution that A/B must find in the design note. The trap is unproven in `check.sh`. |
| U9 | complex | **fair with changes** | Oracle matches the prose. Its traps are named outright in the prose (`requirement.md:77-81, 97-99`) and are unproven in `check.sh`. |
| U2 | adversarial | **fair with changes** | Reachable from the prose in A/B. The scoring rule, the "completion" signal in A/B and C's wiring are undefined. C/D receive an experimenter-authored conflict node. |
| U3 | adversarial | **fair with changes** | The rounding trap is a strawman. The realistic discriminator is a refusal-order reading that should be made explicit. |
| U6 | adversarial | **unfair as specified** | Only arms with a claim mechanism can meet "exactly one completion / no duplicate owner". A/B are not told that a second agent exists, and the metrics are undefined for them. |

## Findings

### 1. Representativeness
- **The tasks read as specifications, not tickets.** Every task supplies exact signatures, error cases,
  refusal order and worked examples, on a repository of about 150 lines. Ordinary work requires finding
  impact sites and inferring behaviour. Results will generalise to well-specified changes in tiny
  codebases only. This cuts both ways: Echelon's fixed overhead is proportionally large, and its
  context-discovery value is not exercised.
- **The category labels in the prose cue the agent.** `Category: adversarial|complex|…` is line 3 of
  every `requirement.md`, for example `tasks/U3/requirement.md:3`. Real tickets do not announce
  "adversarial", and the label invites extra scrutiny in every arm. It also raises a construct question:
  is the agent detecting a trap, or reacting to a label?
- **The categories are not validated.** U5 is closer to simple than moderate. U3's "adversarial" nature
  is weak test coverage of a fully specified algorithm. U6 is adversarial only through the harness.
- **Is any task built so that only Echelon can succeed?** U6, as specified (see section 6). U2 is
  partially affected: in C/D, Ordo refuses the contract mechanically, but only because the experimenter
  modelled the conflict (section 3).
- **Is Echelon needlessly penalised?** No. The overhead on U1/U8 is the intended contrast for H3.

### 2. Solvability from prose: oracle assertions not clearly stated
Every oracle assertion maps to a prose sentence. The items below are required only by inference, or can
reasonably be misread.

| Task | Oracle | Issue |
|---|---|---|
| U3 | `oracle/U3/OracleTests.fs:82` (`[a; ghost]` with `a` short of funds → `UnknownAccount ghost`) | `requirement.md:18-26` lists the checks "in this order". It never says that every account's existence is checked before any account's funds. A natural per-account implementation reads it the other way and fails only this test (variant above). **Misreadable; clarify.** |
| U4 | `OracleTests.fs:33-42` (`count` applied after hiding; a reversed transfer hidden on both accounts) | Follows from "shows exactly the postings that `postingsOf` lists" (`requirement.md:23-26`). Stated, but only by inference. |
| U4 | `OracleTests.fs:77-82` (reversing `fee:P1` across accounts) | Follows from "every posting whose reference is exactly `reference` (on any account)". Stated. |
| U6 | `OracleTests.fs:25` (`Assert.Equal(frozenA (), l)`: structural equality of `LedgerState`) | "changes nothing" (`requirement.md:20`) supports it. It fails for a representation that changes on re-freeze, such as a timestamped freeze. Acceptable. |
| U7 | `OracleTests.fs:42` (5,000 → 90) and `:47` (1,100 → 12) | They rely on the design note, which the prose makes binding (`requirement.md:46-48`). Stated. |
| U9 | `OracleTests.fs:48` (`-12.045 → -12.04`) | Banker's rounding of a negative is implied by "half to even". Stated. |
| U1 | `OracleTests.fs:58-62` | Vacuous: it checks `l0`, which is immutable. Harmless, but it inflates the oracle test count. |

The prose is otherwise sufficient in every arm. No task needs an Echelon artefact to be solvable.

### 3. Leakage
- **Oracle to agents: none found.** No oracle-only value (3.34, 16.65, 24.08/24.09, 123.57, 0.0125,
  `fee:P1`) appears in `repo/`, `tasks/*/{requirement.md,*AcceptanceTests.fs,contract.json}` or
  `directives/`. Prose examples that recur in the oracle (0.125/0.135 in U3; 6,000 → 120 in U7's design
  note) are prose-stated facts, which is legitimate. `task.json` describes oracle content (for example
  U3's "uneven splits, remainders"), so it must stay a harness-only input.
- **Isolation is by instruction only.** Run-01's brief says "Do not read anything outside
  `$RUN_DIR`" (`harness/d/setup.sh`), while oracles and references sit on the same host and on the
  pushed branch. X4 detection must actively look for reads of them.
- **The contract is extra specification for C/D:**
  - **U7:** `DEC-U7-MARGINAL-TIERS.justification` = "interest is marginal per tier". A/B must open
    `docs/design/interest.md` to learn this. It hands C/D the resolution of the one stated ambiguity
    that the task exists to test.
  - **U2:** the contract carries `CONFLICT-U2-REOPEN` "contradict; unresolved", and Ordo refuses it.
    The conflict was detected by the experimenter, not by Echelon or the agent. U2 in C/D therefore
    measures admission of a correctly pre-modelled conflict, not conflict detection.
  - **U3, U4, U5, U6, U9:** the justifications restate the prose. No extra information.
  - The A/B prose is sufficient in every case.

### 4. Trap validity and strength

| Task | What the trap really tests | Strength | Notes |
|---|---|---|---|
| U3 | Implementing a stated algorithm beyond even-split visible tests | **low** | `reference/U3-naive` ignores the stated rounding and remainder rules: a strawman. .NET `Math.Round(decimal, 2)` already rounds half to even. The realistic failure is refusal order (builder caveat confirmed), not rounding. |
| U4 | Bypassing a helper the prose says to use, or completing before R2 | **low** | The builder's caveat is confirmed: a prose-compliant `recent` passes automatically. The R1-only state cannot pass the visible R2 test, which blocks compilation, so premature completion is also unlikely. |
| U5 | Store-level atomicity | **very low** | The builder's caveat is confirmed: the trap lives in `Store`, where the existing private `commit` (`repo/src/Ledger/Store.fs:13-15`) makes `commit (Ledger.transferBatch batch)` the obvious solution. The variant shows the oracle discriminates when the trap fires. |
| U7 | Reading a referenced design note | **low–moderate** | The prose names both readings and points to the note. The oracle discriminates strongly (8/13 fail). |
| U2 | Stopping instead of forcing a choice when the prose states a contradiction | **moderate, brief-dependent** | Detection is trivial (`requirement.md:19-20`: "Both decisions apply"). The real discriminator is whether the brief lets the agent stop without penalty (section 5). |
| U6 | Coordination without being told there is anything to coordinate | **by construction** | See section 6. |

The traps are not comparable in strength. Only U2 and U6 are likely to separate arms. U3's
discriminator is a spec-reading detail (section 2), not the advertised verification-scope effect. The
design's claim that U3 and U4 isolate "verification-scope effects" (`02-run02-design.md:100-101`) is
unlikely to be testable.

### 5. U2 fairness
- **Reachable in A/B?** Yes. The prose states both decisions, says both apply, and gives the error
  cases for each (`tasks/U2/requirement.md:16-33`).
- **The brief creates a bias.** C/D have a refusal path: Ordo or Praxis refuse, and the agent reads a
  diagnostic. A's brief (design `:10-11`) is "commit your work, and state when you stop", with no
  vocabulary for "blocked". The visible test file does not compile until `PeriodNotClosed` and
  `PeriodFinal` exist, so the default pressure in A/B is to make the build green, which means
  implementing something.
- **Is the scoring rule objectively checkable?** Not yet.
  - "Completion" has no defined signal in A/B. C/D have a recorded `complete-verified`.
  - The rule does not say what to do when the agent partly implements (the uncontested
    `PeriodNotClosed` path, or one rule) **and** reports the conflict.
  - "Naming both rules" does not say whether the IDs are required or whether "Finance vs Audit"
    counts.
  - The Authority paragraph in the directives (`DIRECTIVES.md:20`: "When same-level sources conflict,
    prefer the narrower and newer accepted record and document the resolution; escalate if…") can
    lead a B/C/D agent to pick one rule and document it. The rubric must state whether that is wrong.
    By the fixture's definition it is wrong.
- **C wiring is undefined.** In run-01, setup aborts when Ordo refuses (`fixtures/README.md:104-106`).
  If that is unchanged, a C trial of U2 becomes an X1 setup failure that is "rerun" forever.
- **The cost structure differs.** In C/D, U2 can finish almost immediately at near-zero cost, and it
  adds a full correct requirement to the pooled denominator. U2 can move the primary ratio on its own.

### 6. U6 fairness
- `task.json` expects "exactly one completion, no lost work, no duplicate active owner". A/B have no
  owner concept, and their brief does not say that a second agent exists. Two A agents will both
  implement and both report done, so A/B fail the coordination criteria by construction. The task
  measures whether a claim mechanism exists, which is known in advance (run-01 Experiment A: 15 → 0).
- "Duplicate owner", "lost work" and "completion" are not operationally defined for A/B.
- The design says U6 is "never pooled into the efficiency headline" (`:55-56`). H2 "per category" and
  H5 would still include it in "adversarial" unless it is excluded explicitly.

### 7. Directives pack
- **Faithful:** yes. Verbatim against recorded commits and digests (verified). Removals are listed and
  justified.
- **Tool-neutral:** mostly. These remnants could send a B agent looking for artefacts that do not
  exist, at a cost borne only by arms without Echelon records:
  - "canonical domain records", "update affected records", "REPs" (`DIRECTIVES.md:13,16,20`);
  - Dokimos detector signals (`:71-80`);
  - "track it in the work queue" (`:76`);
  - a dangling link to `BOUNDARY-PRESERVATION.md` (`:119`);
  - the Start Here list begins at "2." (`:12`).
- **Engineering Standards are omitted.** `GV-ENG-001` (`/home/user/praxis/docs/00-governance/Engineering-Standards.md`)
  is the document `AGENTS.md` names for engineering ("engineering follows the Engineering Standards").
  Without it, the pack contains almost no coding standard or testing expectation: one clause, "testing
  in proportion to risk" (`:27`), plus the skipped-tests rule. The design describes the pack as
  "coding standards, architectural conventions, testing expectations" (`02-run02-design.md:15-17`),
  which it does not currently deliver. This biases B toward looking weaker than "agent + Echelon
  standards" really is.
- **Biased toward the oracle?** No. Nothing about rounding, atomicity, shared helpers or tiers. The
  doctrine line "Establish semantic decisions once and derive their consequences" (`:87-88`) is generic.
  The conflict and escalation guidance (`:20,26`) bears on U2. That is legitimate treatment content, but
  it must be reported as a mechanism through which B can differ from A on U2.
- **The fixture triggers the pack.** `repo/Directory.Build.props:4` sets
  `<TreatWarningsAsErrors>false</TreatWarningsAsErrors>`, which DOK-R002 (`DIRECTIVES.md:74`) lists as a
  suppression signal. It invites out-of-scope edits in B/C/D only. The value is the default, so the line
  is redundant.

### 8. Difficulty spread (estimates for a run-01-class model, which completed 12/12 first-pass)

| Task | P(oracle failure or rework) per trial | Likely cause |
|---|---|---|
| U1, U8, U5 | ≤ 5% | none: ceiling |
| U4 | 5–15% | reversal edge cases; compile-order friction from the R2 visible test |
| U3 | 15–30% | refusal-order reading (section 2); zero-share handling when shares are posted via `debit` |
| U7 | 10–25% | schedule validation edges; accrual tracking; compile order of the new module |
| U9 | 15–35% | the largest surface (3 modules, 5 types, compile order); error precedence in `statementIn` |
| U2 | 10–40% in A, lower in B/C/D | forcing a choice to make the build green; depends on the brief |
| U6 | ~100% "coordination failure" in A/B | by construction |

**Expected result:** a ceiling persists on 4 of the 7 implementation tasks. With 2 replicates per arm,
the per-task contrasts will mostly read 2/2 against 2/2. Most outcome variance will come from U2 and U6,
both of which are partly driven by the brief and the harness. So the primary outcome will mostly measure
cost, as in run-01, unless the changes below are made.

## Required changes (before preregistration)

1. **Remove the `Category:` line** from every `tasks/U*/requirement.md`, keeping it in `task.json`. Then
   regenerate contracts and digests and re-run `check.sh`.
2. **U3: make the refusal order explicit** in `requirement.md:18-26`. For example: "every account's
   existence is checked, in list order, before any account's funds". Otherwise the oracle's
   `refusal order` test (`oracle/U3/OracleTests.fs:79-83`) depends on one reading of an ambiguous
   sentence.
3. **U7: neutralise the contract justification** to what the prose says, for example "binding rule in
   docs/design/interest.md". Do not state "marginal". Apply the same rule to every contract: a
   justification may not carry information that is absent from the prose.
4. **Prove every claimed trap in `check.sh`**, as is already done for U2/U3. Add the four variants in
   the table at the top (U4 bypass, U5 store loop, U7 whole-balance, U3 interleaved) and a U9 variant
   (statement balance accumulated from rounded amounts; total = rounded exact sum). Each must
   pass the visible tests and fail the oracle.
5. **Give every arm the same outcome vocabulary in its brief.** Require a final line such as
   `OUTCOME: completed` or `OUTCOME: blocked — <reason>`, and say that stopping blocked is an acceptable
   result. In A/B, this line is the completion signal.
6. **Preregister the U2 rubric.**
   - It is correct when `OUTCOME: blocked` (or no recorded completion in C/D) **and** the final report
     names both `DEC-U2-REOPEN-ALLOWED` and `DEC-U2-PERIOD-FINAL` and says that they conflict.
   - Implementing only the uncontested `PeriodNotClosed` path is allowed.
   - Implementing either rule and claiming completion is wrong, even if the conflict is mentioned.
   - A tool refusal alone, without the agent's report, is not correct.
   - Score by a deterministic text check, with a second blind rater for edge cases.
7. **Wire arm C for U2** so that Ordo's refusal reaches the agent as a run-time diagnostic, not a setup
   abort. State how D derives completion when the contract is refused.
8. **U6:**
   - Tell every arm the same facts: another agent may be assigned this item, and both share the bare
     remote. Do not give A/B a claim tool.
   - Define completion, duplicate owner and lost work per arm from observable artefacts: the final
     `OUTCOME` lines, the commits that reached the remote, and the commits overwritten or dropped.
   - Exclude U6 explicitly from H1–H4 and from H5's per-category "adversarial" cell, and report it
     only in its own table.
9. **Define the unit of the primary denominator.** Tasks carry 1–3 requirement IDs. Say whether the
   unit is the task or the requirement ID, and whether a task with partial oracle failures earns
   partial credit. Preregister a **sensitivity analysis of H1–H4 excluding U2**, because U2's correct
   outcome can be near-free in C/D.
10. **Add the Engineering Standards to the pack** (from `praxis/docs/00-governance/Engineering-Standards.md`
    at the recorded Praxis commit), verbatim under the same selection rule:
    - keep line 23 (Principles), lines 29-34 (Repository Hygiene and Code Quality), lines 43-53
      (Testing and Validation) and line 69 (Definition of Done);
    - remove lines 1-17 (metadata), 25 (Phase 1 note), 35 (Praxis instrumentation), 37-39 (`DF-`
      records) and 55-65 (accessibility, security, documentation: Praxis governance, or not
      applicable);
    - update `PROVENANCE.md` and the pack digest.
11. **Give B, C and D the same pack bytes.** C/D workspaces must contain no other Echelon guidance
    (for example a Praxis `AGENTS.md` or governance docs) that B lacks.
12. **Enforce oracle isolation in the run-02 harness**, beyond the instruction "do not read outside the
    run dir": run agents where `fixtures/oracle`, `fixtures/reference` and the cohort repository are not
    readable. Make X4 scan transcripts for `oracle/`, `OracleTests`, `reference/` and `task.json`.

## Recommended changes

- **Make tasks harder in the realistic direction.** Leave out some stated signatures or refusal orders
  where existing code conventions imply them, or add impact sites the prose names only generically (for
  example, U6 "every operation that sends money" with `Store` and a batch path present). This breaks the
  ceiling without making the oracle check unstated behaviour.
- **Replace `reference/U3-naive`** with the interleaved variant (or keep both) as the documented trap
  proof. The current naive solution ignores the prose and will not occur.
- **Add a one-sentence assembler preamble** to the pack, applied identically in B/C/D: "Documents,
  records or tools these directives mention that are not in your repository do not exist for this
  task." It limits wasted searches in B.
- **Remove the redundant `TreatWarningsAsErrors=false`** from `repo/Directory.Build.props:4`. It is the
  default and triggers DOK-R002 in B/C/D only.
- **Remove or fix the vacuous U1 oracle test** (`oracle/U1/OracleTests.fs:57-62`).
- **Increase replicates** for U3, U7, U9 and U2 (the tasks likely to vary) rather than for U1/U5/U8.
  Otherwise, label per-task correctness contrasts as descriptive only.
- **Report the builder-assigned categories as unvalidated.** Add the observed failure rate per task as
  an exploratory difficulty measure.
- **Optional U2 variant for C/D:** the same contract without the `conflict` node, to show whether
  admission catches the contradiction when no one pre-models it. Report it as exploratory.

## Residual biases to report as limitations

1. **Specification-style tasks on a small repository.** The results do not cover vague tickets or large
   codebases. Echelon's fixed overhead is proportionally inflated, and its context value is not
   exercised.
2. **U2 in C/D tests admission of an experimenter-modelled conflict**, not detection. The contract
   author is the experimenter in every task.
3. **U6's coordination outcome is largely determined by arm design.** Report it as a demonstration and
   as a cost measure, not as a comparison of judgement.
4. **Trap strength is uneven and mostly low** (U3, U4, U5, U7). A null result on quality is weak
   evidence that verification has no benefit.
5. **The directives pack contains conflict and escalation guidance** (`DIRECTIVES.md:20,26`). B−A on U2
   may reflect that guidance specifically, not "directives" in general. The pack also carries
   Echelon vocabulary that may cost B tokens it does not cost C/D.
6. **Visible tests are protected only in D.** A–C could edit visible tests. Oracle scoring is
   unaffected, but rework and test-run counts may differ for that reason alone.
7. **Two replicates per cell.** Per-task and per-category correctness contrasts are descriptive.
8. **Oracle isolation depends on the harness.** Fixtures are on the pushed branch, so any agent with
   network or wider filesystem access could in principle reach them. X4 is the only defence.
