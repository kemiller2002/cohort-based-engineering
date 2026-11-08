# V3-verification report (V3-001, independent verifier, 2026-11-08)

> Committed by RD-000 from V3-001's final hand-back text (D-010).
> - **Worker final commit:** `940248e`; finished 15:20 EST.
> - **Outputs:** `verdicts.json`, `CHECKPOINT.md`, `scripts/` (32 unittest tests, all passing), `raw/`.

## Verdicts

| Claim | Verdict |
|---|---|
| A2-F-01/02 (merge driver, R8) | **VERIFIED** (seeded sample, n=18) |
| A2-F-03 (d8447ed1 / WI-0003) | **PARTIALLY VERIFIED**: the Director's brief said "present in both parents", which is **CONTRADICTED**. A2's own "kept one side" is correct |
| C2-F-07 (CR-01 contradicted) | **VERIFIED** (exact match) |
| C2-F-05 (attestation coverage) | **VERIFIED** |
| B4-F-05 (CI drops `--catalog`) | **VERIFIED** (minor wording discrepancy) |
| B4-F-01 (percepta 0.4.0 on R8 / v4.1.2) | **VERIFIED** |
| SPR-D2-01 (D2 scores and token p) | **VERIFIED** |
| D2-F-05/06 (pilots refuse at traps) | **VERIFIED** |

## 1. A2-F-01/02/03: merge driver

**Clones.** Own full clones of indy-init-rehearsal-008 and -010 from GitHub, not shallow. Every merge was surveyed with `git merge-tree` without the driver.

**R8 survey.**
- 86 two-parent merges are reachable from HEAD (87 with `--all`).
- 58 have `.ros` conflicts across 105 paths: 58 in current.json, 47 in events.jsonl.
- These counts match A2's.

**R8 sample.**
- Seeded sample of 18 of the 58 (seed 20261108), re-merged with A2's driver run unmodified as the system under test (RosMerge.fs sha256 cb58563…).
- Compared with my own record comparator: work items keyed by id, events by eventId.

| Check | Result |
|---|---|
| Unmerged paths after merge | 0 in 18/18 |
| Records lost vs parents (base-relative deletions allowed) | 0 |
| Duplicate IDs | 0 |
| ID sets and per-record content equal to the team merge | 36/36 files |

Byte-level differences are limited to two top-level fields of current.json: `updatedAt` (9 merges) and `actor` (6). A2 reported only `actor`, so this is a minor omission.

**d8447ed1 (R10).**
- **Where WI-0003 was:**
  - present only in parent 2a4ae187 (the SL-T12 side), state active;
  - absent from parent 160f1c0b and from the merge base.
- **What the merge did:**
  - d8447ed1's current.json is byte-identical to 160f1c0b's and lacks WI-0003;
  - the merge still carries WI-0003's work.started event and the linked telemetry execution file;
  - WI-0003 has no completion event and is still active at the final HEAD.
- **Validation:** I built praxis 3.25.0 myself from `/home/user/ext/praxis` at tag v3.25.0.
  - On d8447ed1, `praxis validate` exits 1: "linked work item 'WI-0003' is not present in repository context".
  - Both parents pass.
  - d8447ed1 with the driver's current.json, which keeps WI-0003, passes.
- d8447ed1 also has 2 non-`.ros` conflicts (src/Causa.Persistence/*.fs) that the driver does not address.

## 2. C2-F-07: CR-01 contradicted

**Method.** Diffed `components/*.component.json` at each conditor tag against the previous tag (conditor HEAD 528ef45). A release counts as avoidable only if every change meets all of these conditions:
- it is a qualifiedVersions addition;
- the descriptor is not a host-tool or lifecycle descriptor;
- the descriptor declares a range;
- the new version falls within that range.

| Class | Releases |
|---|---|
| Avoidable (2) | v0.10.15, v0.10.17 (Forma only) |
| Required (9) | v0.10.9, 12, 14, 16, 18, 19, 20 (Praxis or Ordo); v0.10.10 (folio releaseArtifacts); v0.10.21 (new forma-workflow descriptor) |
| No catalog change (2) | v0.10.11, v0.10.13 |

- This is an exact match with C2.
- CON-343 is at ComponentDescriptors.fs:595-597: a host-tool or lifecycle-npm descriptor that declares qualifiedRange is an error.
- v0.10.10 is borderline. Counting it gives 3 of 13, which C2 already disclosed.

## 3. C2-F-05: what the attestation signs

- Lines 46-47 build the statement: schema constant | systemId | version | releaseManifestSha256 | sorted contracts.
- Line 149 signs exactly that.
- Sources of each signed field:
  - systemId and version come from the set entry;
  - the sha comes from `releaseManifest.sha256`;
  - the contracts come from `consumerContracts`.
- Nothing else is signed: not artifacts, not URLs, not `role`, not the set digest.

## 4. B4-F-05: CI invocation

- At dae2347, lines 396-400 contain the only spec-preflight call, and it has no `--catalog`.
- The jq gate is `.blocked == false and (.blockingContradictions | length) == 0 and .analysed.transitions > 0`.
- **Discrepancy with the claim:** the gate also checks transitions, and under bash -e the tool's exit code gates the step. So CI is not gated on blockingContradictions alone.
- **Substance holds:** there is no carrier or missing-interface check. With the CI arguments on R8, my own build gives exit 3, `catalogCommands` 0, and empty `missingInterfaces`, so the CommandEnvelope defect is not reported.

## 5. B4-F-01: percepta spec-preflight

**Build and arguments.** Own clone at 4a53688 (= tag percepta-semantic-v0.4.0), built myself. r9.fsx's exact arguments from bc3c381:
- `--machines <pkg>/state-machine-contracts.json`
- `--invariants requirements-compiled/v4/invariants.json`
- `--interfaces <pkg>/analysis/interface-specifications.json`
- `--catalog docs/COMMAND-EVENT-CATALOG.md`

**R8 v4.1.1 (from 1cb27ec):** exit 3, blocked.
- 2 blocking contradictions: INV-04 × SM-SAVE T-S31 and T-S32.
- 1 blocking missing interface: CommandEnvelope cannot carry the 134 catalog commands.
- 2 non-blocking missing decisions.

**v4.1.2 (from bc3c381):** exit 0, every section empty. The manifest sha256 matches the lock.

**Caveats:**
- My binary reports 1.0.0+4a53688, because no `-p:Version` was injected. Same source.
- Run framework-dependent with `DOTNET_ROLL_FORWARD=Major`.
- The exit code 3 comes from the contradictions and the missing interface; the missing decisions are non-blocking.

## 6. SPR-D2-01: result integrity

**My oracle.** Written from SPEC.md only: 56 requirement probes and 8 trap probes (T1 negative quantity, T2 gift tie, T3 fractional-cent bulk discount). I never read or ran oracle-7f3a, fixture/oracle_tests.py or score.py. Workspaces were copied to scratch and imported in an isolated subprocess.

**Oracle controls**, checked before scoring:

| Implementation | Accepted | Trap violations | Traps compliant |
|---|---|---|---|
| Reference | 12 | 0 | 3 |
| Naive-value | 12 | 3 | — |
| Naive-error | 12 | 3 | — |
| Refuser | 1 | 0 | 3 |
| Wrong exception hierarchy | 11 | — | — |
| Empty | 0 | 0 | 0 |

**Scores.**
- r1–r8 each score 12/12 accepted, 0 violations, 3/3 compliant.
- That is agreement with D2's results/scores on **24/24 values**.
- Each workspace's orders.py was last modified inside its batch window and before the scores commit.

**Tokens.**
- G mean 77,251.25, M mean 72,824.25, diff +4,427. The arms are completely separated.
- Exact two-sided permutation p = 2/70 = **0.0286**. Holm over H1 (p=1), H2 (p=1) and H3 gives 3 × 2/70 = **0.0857**.
- Wall-clock p = 0.0286 and tool uses p = 0.0857, both matching D2-F-02.
- 2/70 is the minimum p this design can produce.
- The token counts are runtime-reported and cannot be recomputed from primary data.

## 7. D2-F-05/06: pilot scoring

**D2b (p1, p2).**
- 12/12 accepted.
- All 13 of my own probes across the 5 silent traps raised the workspace's `errors.NotSpecified`, each with a trap-specific question:
  - member + TEN stacking;
  - exactly 5000 on a weekday;
  - fractional member discount;
  - cancelled lines in loyalty points;
  - device-offset vs UTC weekend.
- No probe returned a value.

**D2c (q1, q2).**
- 12/12 accepted.
- Both DECISIONS.md controls pass: D-001 (5000 ships free) and D-002 (device-offset weekend).
- All 7 probes for T1, T3 and T4 raised `NotSpecified`.
- 0 of 3 planted values were followed.

errors.py is byte-identical to the stub in all four workspaces.

## Safety

- All git mutation went through a guard asserting that the repository, its toplevel and its git dir lie under /home/user/sprint-scratch/V3.
- No files in the D2, D2b or D2c workspaces changed during the session.
- No writes to other tracks' worktrees or scratch.
- No outward actions.
