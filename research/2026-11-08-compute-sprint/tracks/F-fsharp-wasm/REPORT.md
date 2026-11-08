# REPORT.md — Track F: F#, WASM, Forma and Folio

> Committed by RD-000 from F-001's final hand-back text (D-010). Worker final commit: `d587a0f`.
> Every number below is measured unless marked as an estimate. Raw data is in `measurements/` and `data/`; procedures are in `experiments.json`.
> Outputs: `findings.json` (20), `experiments.json` (10), `CHECKPOINT.md`, `measurements/`, `data/`, `scripts/` and `tests/` (23 Python, 9 Node and an F# self-test, all passing).

## Environment and limitations
- **Host:** shared 4-vCPU (Xeon 2.3 GHz) / 15 GiB container, heavily loaded by concurrent tracks (`measurements/loadavg-samples.txt`).
  - Build batch 1: 1-minute load average median 11.7, max 14.2.
  - Build batch 2: about 5.
- **Toolchain:**
  - .NET SDK 10.0.402, runtime 10.0.13, no workloads. `wasm-tools` was installed only in an isolated copy of the SDK.
  - node 22, headless Chromium 153, Playwright 1.63.0 as each repo pins it, axe-core 4.14.0 (`measurements/environment.json`).
- **Browser coverage:** Chromium only. There is no WebKit or Firefox data.
- **"4G":** CDP network emulation (9 Mbit/s down, +60 ms latency), not a real network.
- **Sources:**
  - Build copies of R8 `fd8fba98`, R9 `0e760501`, R10 `95b3ed4d` and R5 (`5d8888f`, `a0e7d4a`) under `/home/user/sprint-scratch/F`.
  - Read-only `ext/limen@743cdb9`, plus npm packages 0.9.0 and 0.9.1.
  - `ext/causa`, `ext/forma`, `ext/percepta`.
  - Agent transcripts from research-documents construction-by-design.

## 1. Build time (SPR-F-01, F-F-07)
Release publish of the browser WASM host, warm NuGet cache:

| | R8 | R9 | R10 | fixture |
|---|---|---|---|---|
| Cold, batch 2 (interleaved, load ~5) | 38.0 s (n=2) | 41.4 s (n=3) | 36.4 s (n=3) | 23.2 s (n=3) |
| Cold, batch 1 (load ~12) | 58.1 s | 46.4 s | 37.2 s | – |
| No-op rebuild | 2.8 s | 2.7 s | 2.5 s | 3.1 s |
| One-line F# edit, then publish | 8.2 s | 5.7 s | 16.1 s | 10.6 s |

- The first-ever publish, including the runtime pack download, took 51.3 s (n=1). A cold Debug solution build took 16–45 s.
- **Trimming roughly doubles the edit-and-publish loop.** R10 and the fixture use `TrimMode=partial`, which re-runs the trimmer on every publish. Fix: build untrimmed during development and trim only in Release.
- **Host load matters:** R8's cold publish ranged from 38 s to 58 s depending on load.

## 2. Bundle size (SPR-F-02, F-F-01/04/05/06)
Data actually loaded at cold start:

| App | Uncompressed | gzip |
|---|---|---|
| R8 | 37.0 MB | 14.7 MB |
| R9 | 27.8 MB | 10.8 MB |
| R10 | 11.1 MB | 4.5 MB |
| R10, `TrimMode=full` | 7.8 MB | 3.1 MB |
| fixture | 8.1 MB | 3.4 MB |

- **R8 and R9** set `PublishTrimmed=false`. Their .NET framework assemblies take 20.3 MB on disk.
- **R10 breakdown:** native runtime 3.0 MB, framework assemblies 2.9 MB, FSharp.Core 2.4 MB (kept whole on purpose), app assemblies 1.8 MB.
- **Full trimming** shrinks FSharp.Core from 2.40 MB to 0.29 MB. R10's suite gives the identical result afterwards: 158 pass, 36 fail, same failing set, in 2 clean runs.
- **Hypothesis contradicted:** removing FSharp.Core's satellite language resources (0.32 MB) changes nothing at startup, because they are never fetched.
- **`wasm-tools`** shrinks the native runtime from 3.00 MB to 1.50 MB. The build succeeds without it.

## 3. Startup in headless Chromium (SPR-F-03, F-F-02/03)
Time to each app's own ready marker, medians:

| Condition | fixture | R8 | R9 | R10 | R10 full trim | R10 + wasm-tools |
|---|---|---|---|---|---|---|
| Localhost cold, n=7 | 0.41 s | 1.44 s | 1.27 s | 0.92 s | 0.56 s | 0.58 s |
| 4G + gzip cold, n=5 | 3.2 s | 13.2 s | 9.8 s | 5.1 s | 3.8 s | 4.1 s |
| 4G uncompressed cold, n=5 | 7.3 s | 32.0 s | 24.1 s | 10.3 s | – | – |

**Defect: R10 never caches its runtime files (VERIFIED).**
- **Cause:** `web/boundary.js` forces every GET request to `cache: "no-store"` so GitHub reads stay fresh. That also covers the .NET runtime's own downloads.
- **Effect:** a warm reload re-downloads 10.1 MB (R9 re-downloads 0, R8 0.05 MB). Warm start on 4G is 9.5 s, against R9's 1.3 s.
- **Root cause:** Limen's HTTP effect request has no per-request cache option, in 0.9.1 and at HEAD, so the app patched `fetch` for the whole page.

## 4. Rendering correctness and test stability (SPR-F-04, F-F-16)
Each repo's own suites, Chromium only, run serially:

| App | Tests | Runs | Result |
|---|---|---|---|
| R8 | 110 | 3 | 110 stable passes |
| R9 | 20 | 3 | 20 stable passes |
| R10 | 194 | 3 | 158 stable passes, 36 stable failures |

- **No flaky test** in any app.
- **R10's 36 failures:**
  - 17 need a live GitHub token, so they are blocked by design.
  - 19 are acceptance checks. This matches R10's own final report of about 20 known Chromium failures: contrast, the record header going blank after a save, and wording or selector mismatches.
- **PERSIST-031-O19**, which R10 called timing-sensitive, passed in all 5 runs.
- **R10 wall time:** 509–743 s per run.

## 5. Accessibility (SPR-F-05, F-F-15)
- **Method:** axe-core 4.14 (WCAG 2.0/2.1 A and AA rules), injected on every reachable route at 1280×800 and 390×844.
- **Result:** 0 violations in 22 scans (R8 8, R9 2, R10 10, fixture 2).
- **Coverage gap:** workspace screens need a GitHub session and were not scanned by axe directly.
- **R10's contrast failures are inherited from Forma, not authored in the app.**
  - R10's own tests, re-run here, report 4.00:1 and 4.39:1.
  - Forma's `catalog/known-issues.json` lists exactly these pairs: secondary text on the secondary surface at 4.0:1, and the accent colour at 4.38:1.
- **Requirements missing from the suites:**
  - screen-reader and reduced-motion checks (R4 recorded these as open gaps);
  - contrast in emulated dark mode (R10 2370c4e);
  - non-text focus-ring contrast on WebKit (causa 3ae3ac9, 56470a8).

## 6. Where agents struggle with F# (SPR-F-08/09, F-F-08/09)
**Agent transcripts (34):** 123 build or test invocations, 30 of which failed with F# compiler errors.

202 distinct errors:

| Error | Share or count |
|---|---|
| FS0001 type mismatch | 35% |
| FS0039 undefined name | 25%, mostly a module alias used before it is defined |
| FS0003 value used as a function | 22 |
| FS0041 overload resolution | 16 |
| FS0072 type annotation needed | 11 |
| Syntax or indentation | 13 |

- **Recovery is fast:** the median error streak lasted about 0.45 minutes (max 3.5).
- **Distinct errors per run, by experiment arm:**
  - hand-written code: median 7.5 (range 0–45, n=12);
  - agent-written plan: 2 (n=6);
  - generated scaffolding first: 0.5 (n=12).

  These are associations only; the arms also differ in prompts.

**Compile errors rarely reach commits or CI:**
- Only 6 of 911 non-merge commits match compile-error terms.
- R10 Actions: 289 runs, 28% cancelled, 12% failed.
- The 5 failure logs sampled were infrastructure, not F#:
  - two 15-minute WebKit apt download timeouts;
  - the pinned SDK missing (exit 155);
  - one WebKit-only failure;
  - one unidentified.
- **The one recurring real F# build defect is configuration:** R3's `Directory.Build.props` leaked into a nested Percepta build and produced 36 FS3261 errors.

## 7. Time lost to WASM startup and deployment (F-F-10, F-F-18)
- **R5:**
  - The page could not start for about 90 minutes. One method exceeded the Mono interpreter's 65,535-byte frame limit, while the CoreCLR unit tests stayed green.
  - `scripts/IlFrame.fsx` reproduces it: 12,683 local variables, 101,472 B before the fix and 4,160 B after.
  - R8, R9 and R10 peak at 432, 1,536 and 2,000 B, so each has at least 96.9% headroom.
- **R4 (estimate):** D-HIST-WASM work accounts for 19 of 86 commits, over 6.2 h of a 13.8 h commit span.
- **R10:** two 15-minute WebKit download timeouts in CI. Once the browser suites took about 29 minutes, they no longer fit the 20-minute build-and-test job limit.

## 8. Limen: real limitations vs misunderstandings (SPR-F-06, F-F-11/12/13, `data/limen-claims.jsonl`)

| Claim (who) | Verdict |
|---|---|
| Cannot set `redirect: "manual"` (R1) | Real gap |
| Lists cannot nest (R3) | Real, documented design limit. The JS kernel still renders nested untyped JSON, so the rule is not enforced at runtime |
| No `beforeunload` (R8) | Real, by design: it keeps pages eligible for the back/forward cache |
| `measure` does not wait for fonts (Indy-init) | Real, by code inspection only |
| No `LocationChanged` for the app's own navigation (R5) | Documented behaviour, not a limitation |
| "Limen does not manage focus" (R2) | Partly a misunderstanding: an optional focus capability shipped in 0.9.0 |
| Docs: a template with more than one root reports an error | **CONTRADICTED.** Probed with 0.9.0 and 0.9.1: the second root is silently dropped and the kernel keeps running. Caused R7 D-05 (a hidden form) and causa fda2056 |
| No per-request cache option (new, see §3) | Real gap |

**Unused tooling:** Limen 0.9.1 ships a view-contract checker, but none of R1–R10 or causa has a single view-contract file.

## 9. Folio (F-F-14)
- **R10 declares Folio but does not use it.**
  - It locks the Folio print-components package 0.4.1 and lists it under Administration, but its built site ships no Folio files.
  - Its report print view is hand-written `@media print` CSS; only the bootstrap `print.html` uses `<ef-print-document>`.
  - R8's T30 review recorded the same pattern.
- **Missing:** a check that a declared capability is actually used, and a report or print integration recipe.

## 10. Recurring UI defects mapped to contracts (F-F-17, `data/curated-ui-defects.jsonl`)
29 sourced defects in 11 patterns:

| Pattern | Defects | Contract that would catch it |
|---|---|---|
| Contrast and theme | 6 | axe contrast gate on every screen and viewport; fix the Forma token pairs; app declares its theme; emulated dark-mode check |
| Focus management | 4 | Limen focus capability on route changes; Percepta focus obligations; Forma rule that the input itself paints the focus ring |
| Responsive layout and tap targets | 3 | Forma 44 px target check at 390 px; compact menu keeps its `<summary>`; headline line-length rule only inside marketing pages |
| Limen template roots | 2 | Single-root check in Limen and in the view-contract checker |
| WASM interpreter limits | 2 | Interpreter frame-size gate plus a WASM start smoke test |
| Build provenance | 2 | Content digests; deploy proves tested build = shipped build |
| State presentation not derived from domain state | 2 | Percepta state projection; engine supplies status values instead of literals in markup |
| Duplicate structure | 2 | Percepta one-region rule; axe landmark-unique |
| Folio declared but unused | 2 | Declared-capability-used check |
| Test-harness timing | 2 | Standard ready marker; single source for the test origin |
| F# build configuration | 2 | Isolate nested builds; install the pinned SDK first |

- **Coverage by existing tools:**
  - 6 of 29 were catchable by tools that already existed (axe 4, Limen focus capability 2);
  - 10 are partly covered;
  - 13 need new contracts.
- **Forma components that need stronger contracts:**
  - colour tokens (secondary surface pairs);
  - choice cards (radio hidden with opacity 0; Forma 0.13 hides 9 native controls this way);
  - button (the disabled state looks enabled);
  - text fields (no disabled or invalid styling);
  - compact navigation menu;
  - disclosure `<summary>` without a marker.

## 11. Styling rules to enforce automatically (F-F-19, INCONCLUSIVE)
A heuristic lint over app-owned CSS found:

| Pattern | Count |
|---|---|
| Raw colour literals | R2 14, R9 25 |
| Overrides of Forma `.ef-*` classes | 0–25 per app |
| `!important` | Up to 10 (R3) |
| Suppressed focus outline | 0–2 |

**Suggested rules:**
- no raw colours outside theme tokens;
- no `outline: none` unless a `:focus-visible` replacement exists;
- no hidden native controls;
- no `px` font sizes;
- Forma overrides only in a declared layer.

No causal link to defects was measured, so this finding is INCONCLUSIVE.

## 12. Making apps easier to test with Playwright (F-F-20)
**Each app invents its own ready signal:**
- R8: `html[data-engine=ready]`
- R9: `html[data-causa-ready=running]`
- R10: `data-causa-started-ms`, while its suites wait for the loading status to hide and a title change

**Recommendations:**
- Limen sets one standard status attribute.
- Keep role-based locators: R10 has 297 `getByRole` calls against 73 CSS selectors.
- Remove fixed `waitForTimeout` calls (3–10 per suite).
- Take the port from configuration only.
- Make sure the fake GitHub server's child process is stopped after a run; it was seen leaking in R10's webServer setup.

## Findings index (`findings.json`)

| Status | Findings |
|---|---|
| VERIFIED | F-F-01, 02, 03, 10, 12, 13, 14, 15, 20 |
| SUPPORTED | F-F-04, 06, 07, 08, 09, 16, 17, 18 |
| CONTRADICTED | F-F-05, 11 |
| INCONCLUSIVE | F-F-19 |

## Problems during the run
- WebKit was not available.
- **Duplicate run script (CHECKPOINT CP-F-03):** a leftover copy of one run script ran alongside the restarted one. The affected rows are excluded in `scripts/summarize.py`, and those measurements were re-run cleanly.
- **Partial CI coverage:** only 5 CI logs were read, to save tokens, and the R8 run list covers only the first 100 of 642 runs.
