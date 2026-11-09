# Track B4: Does `percepta spec-preflight` do what Indy-init's docs say? (SPR-B4-01)

> Committed by RD-000 from B4-001's final hand-back text; the harness refuses subagent report-file writes (D-010).
>
> **Commits:**
> - Worker final commit: `7c744aa`.
> - Preregistration: `3b7c9f7`. Protocol and harness were committed before any build, run or test.
> - Raw runs: `2ee03be`.
> - Summaries, comparison and probe: `9a66acf`.
>
> **Outputs:**
> - `protocols/SPR-B4-01.md` (deviations D0–D4), `raw/`, `results.csv`, `comparison.json`, `experiments.json`, `findings.json` (B4-F-01..09), `CHECKPOINT.md`.
> - `harness/`: 12 unittest tests passing. They check that results and comparison rebuild exactly from `raw/` and that input hashes match the git objects.

## 1. Headline

**The claim holds exactly (VERIFIED).** Echelon should reuse spec-preflight for the checks B3 duplicates. Neither tool is shown to work beyond this one specification family.

| Defect | B3 check | spec-preflight 0.4.0 | Agreement |
|---|---|---|---|
| R8 INV-04 vs SM-SAVE | C1-loop CAUGHT (6 alarms: 2 correct, 3 misattributed, plus T-S47) | CAUGHT: 2 blocking likely-contradictions on T-S31 and T-S32, with counterexample | Both |
| R8 CommandEnvelope has no command body | C2 CAUGHT (5 alarms) | CAUGHT: 1 blocking missing-interface; the body is lost through 7 carrier types | Both, but spec-preflight only when `--catalog` is passed |
| DEV-R8-12 (UnknownOutcome, ReconcileReadFailed) | C3 FLAGGED (exploratory) | Non-blocking missing-specification | Both |
| Causa T18↔T20 | C4 DETECTABLE (noisy) | Not detected: takes no slice or plan input, so out of scope by design | B3 only |

**Version tested.** R9 expected percepta-semantic 0.4.0 (`kickoff/rehearsal-009/toolchain.lock.json` at `bc3c381`). The competition lock pins tag `percepta-semantic-v0.4.0` at commit `4a53688`, which is the clone's HEAD. "R9 version" and "current HEAD" are therefore one build.

**Build and runs.** A self-contained linux-x64 `dotnet publish` (matching `package.sh`) took 36 s and reports `percepta 0.4.0`. It was run on 4 packages × 2 conditions × n=5.

**False alarms (DOC condition):**

| Package | spec-preflight | B3 primary (C1-loop, C2) | B3 secondary |
|---|---|---|---|
| v4.1.2 (R8-corrected / R9) | 0 blocking, 0 non-blocking, exit 0 | 0 | C1-cycle 6 |
| v4.1.5 (R10) | 0 / 0, exit 0 | 0 | C1-cycle 6; C4 one 6-slice group |
| v4.1.6 (Causa) | 0 / 0, exit 0 | 0 | C1-cycle 6; C4 noisy |
| v4.1.1 (R8), findings beyond the defects | 1 non-blocking: (UnknownOutcome, CheckAgain), which percepta's own docs call plausibly intended | — | C1-loop: 3 misattributed, plus T-S47 |

**Cost.** spec-preflight's median is 0.34 s on R8 and 0.26–0.35 s on the controls (process wall time, load average 9–11). B3 took 0.33–0.72 s, so the two are comparable. All five repetitions produced identical reports.

## 2. Findings

- **B4-F-01 (VERIFIED): the documented claim reproduces exactly.**
  - On v4.1.1, spec-preflight exits 3 in 5 of 5 runs, with exactly the documented 2 contradictions, 1 missing interface and 2 missing decisions.
  - On v4.1.2, v4.1.5 and v4.1.6 it exits 0 with no findings of any kind.
- **B4-F-02 (VERIFIED): the version is pinned and stable.**
  - R9 pin = competition pin = HEAD = `4a53688`.
  - The first spec-preflight commit, `0ad2bd3`, differs by one regex and gives byte-identical reports on all 8 package × condition cells.
- **B4-F-03 (VERIFIED):** per-defect agreement is as shown in the table above.
- **B4-F-04 (VERIFIED): no false alarms on any control, and fewer extras than B3 on R8.**
  - spec-preflight does not flag T-S47, which B3 judged a related true positive after the fact.
  - The reason: its effect matcher needs the whole phrase "reconciliation read", and T-S47 says "one read on return".
- **B4-F-05 (VERIFIED): Indy-init's CI step drops the carrier check.**
  - `.github/workflows/preflight-tooling.yml` (at `dae2347`) runs spec-preflight on v4.1.5 without `--catalog`, and asserts only that `blockingContradictions` is empty.
  - In that mode the carrier rule cannot fire. On R8, the same invocation still exits 3 but misses the CommandEnvelope defect.
  - The `r9.fsx` wrapper in the startup instructions passes `--catalog` and refuses on every blocking section, so it is not affected.
- **B4-F-06 (VERIFIED): the tool was not built blind.**
  - R8 ran on 2026-11-01: run commits from 17:36Z to 23:53Z, with DEV-R8-09, -11 and -12 recorded between 18:22Z and 23:04Z.
  - spec-preflight's first commit is 2026-11-02 01:23Z. Its docs use the R8 package as the regression case and say two false positives seen on it were fixed.
  - One Claude-Session trailer appears on the tool's commits, the 0.4.0 release, the R9 handoff that makes the claim, the v4.1.2 amendment and the compiled v4.1.2 control.
  - Commit `92527ed` was tuned on draft v4.1.2 wording, though the frozen v4.1.2 also passes the pre-fix build.
  - v4.1.5 and v4.1.6 came after the release and are the same specification lineage. v4.1.5 was gated by this tool in CI.
- **B4-F-07 (SUPPORTED, post-hoc probe): both tools are tuned to this wording.** R8 inputs were rewritten eight ways (P0–P7), each keeping the defects in place:

  | Rewrite | spec-preflight | B3 |
  |---|---|---|
  | P1: bound reworded to "no more than … in any 60-second window" | Misses INV-04 | C1-loop alarms only via the misattributed clause |
  | P2: bound stated "per minute" | Catches | Catches |
  | P3: loop becomes a 2-cycle | Misses INV-04 | C1-loop misses; C1-cycle catches |
  | P4: effect reworded | Misses INV-04 | C1-loop and C1-cycle miss |
  | P5: CommandEnvelope gains an irrelevant string field | Misses the carrier gap | C2 catches |
  | P6: catalog says "travels in" instead of "is carried inside" | Misses the carrier gap | C2 catches |
  | P7: carrier renamed everywhere | Catches | C2 catches, only because the names contain "Command" |

  No requirement ID is hard-coded in spec-preflight, but its trigger phrases match this family: "at most N X in T seconds", "carried inside", "spent", "already made/sent".
- **B4-F-08 (VERIFIED): the counter rule conflates two different counters.**
  - (UnknownOutcome, CheckAgain) is left unspecified while automatic reads remain, in v4.1.1, v4.1.2 and v4.1.5 alike, but it is reported only on v4.1.1.
  - In v4.1.2 the guard gained "fewer than four … in the 60 s". That refers to a different counter, yet it satisfies the rule's "below the limit" pattern.
  - Whether failing closed there is intended remains an owner question.
- **B4-F-09 (SUPPORTED): recommendation.**
  - Reuse spec-preflight instead of building B3's C1-loop, C2 and C3 as a new tool. It is released, pinned and wired into Indy-init's r9.fsx gate, and it matched or beat them on these packages.
  - Contribute B3's distinctive parts to the percepta Specification module rather than keeping a parallel tool: C4 slice-dependency cycles (the T18↔T20 class) and the C1-cycle 2-cycle extension.
  - Fix the Indy-init CI step: pass `--catalog` and check every blocking section.
  - Keep routing findings to the owner rather than blocking automatically. False-alarm rates on independent specifications are unmeasured for both tools.

## 3. Limitations
- **Build source:** rebuilt from the tagged source, not from the downloaded GitHub release archive.
- **Controls are not independent:** they are successive amendments of one specification, and v4.1.2 was co-developed with the tool. A zero false-alarm count here says little about other specifications.
- **Probe:** post hoc, chosen adversarially after reading both rule sets, and run on R8 only.
- **Timings:** include process start-up on a loaded host.
- **B3 results:** taken from committed records. A scratch re-run gave identical results on all four packages.

## Reproduce
```
python3 -m unittest discover -s harness/tests -v
python3 -I harness/run_preflight.py --exe /home/user/sprint-scratch/B4/bin-4a53688/Percepta.Cli --version-label v0.4.0-4a53688 --out raw --runs 5
python3 -I harness/summarize.py
python3 -I harness/probe.py --exe /home/user/sprint-scratch/B4/bin-4a53688/Percepta.Cli --b3 /home/user/sprint-scratch/B4/b3-copy/checks --out raw/probe.json
```
Build steps are in `protocols/SPR-B4-01.md`.
