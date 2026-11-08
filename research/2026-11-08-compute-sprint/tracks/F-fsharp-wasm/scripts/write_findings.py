"""Write findings.json and experiments.json for track F from measured artefacts (numbers are read, not typed,
where a summary file exists). Usage: python3 write_findings.py TRACK_DIR"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def med(summary: dict, metric: str, label: str, mode: str, throttle: str, server: str = "python-http"):
    for g in summary["startup"][metric]:
        if (g["label"], g["mode"], g["throttle"], g["server"]) == (label, mode, throttle, server):
            return g
    return None


def bmed(summary: dict, label: str, mode: str, batch: str | None = None):
    rows = summary["buildByBatch"] if batch else summary["build"]
    for g in rows:
        if (g["label"], g["mode"]) == (label, mode) and (batch is None or g["batch"] == batch):
            return g
    return None


def fmt(g, unit="ms"):
    return "n/a" if g is None else f"{g['median']:.0f} {unit} (n={g['n']}, range {g['min']:.0f}-{g['max']:.0f})"


def fmts(g):
    return "n/a" if g is None else f"{g['median']:.1f} s (n={g['n']}, range {g['min']:.1f}-{g['max']:.1f})"


def main() -> None:
    t = Path(sys.argv[1])
    s = json.loads((t / "measurements/summary.json").read_text())
    suites = json.loads((t / "measurements/playwright-stability.json").read_text()) if (t / "measurements/playwright-stability.json").exists() else {}
    r = lambda label, mode="cold", thr="none", srv="python-http": med(s, "readyMs", label, mode, thr, srv)
    tb = lambda label, mode="cold", srv="python-http": med(s, "transferBytes", label, mode, "none", srv)
    mb = lambda g: "n/a" if g is None else f"{g['median'] / 1e6:.1f} MB"
    env = "4 vCPU Xeon 2.3 GHz shared container, .NET SDK 10.0.402 (no workloads), headless Chromium 153, measurements/environment.json"
    suite_txt = "; ".join(f"{k}: {v.get('tests')} chromium tests x {v.get('runs')} runs -> {v.get('verdicts')}" for k, v in suites.items())

    findings = [
        dict(id="F-F-01", title="Untrimmed .NET WASM framework dominates payload in R8/R9",
             classification="VERIFIED",
             statement=f"Cold-start transfer (uncompressed static server): R8 {mb(tb('r008'))}, R9 {mb(tb('r009'))}, R10 {mb(tb('r010'))}, minimal F# fixture {mb(tb('fixture'))}. R8/R9 set PublishTrimmed=false (BCL assemblies 20.3 MB on disk); R10 uses TrimMode=partial (BCL 2.9 MB).",
             measuredOrEstimate="measured", evidence=["measurements/startup.jsonl", "measurements/bundles/*.json", "r008/r009/r010 src/Causa.Host/Causa.Host.csproj"],
             limitations="Single snapshot per rehearsal; dist sizes include files never fetched (R8 node_modules); " + env),
        dict(id="F-F-02", title="Time to app-ready in headless Chromium",
             classification="VERIFIED",
             statement=f"Localhost cold ready (engine-set marker): fixture {fmt(r('fixture'))}, R8 {fmt(r('r008'))}, R9 {fmt(r('r009'))}, R10 {fmt(r('r010'))}. Emulated 4G with gzip: fixture {fmt(r('fixture','cold','4g','gzip'))}, R8 {fmt(r('r008','cold','4g','gzip'))}, R9 {fmt(r('r009','cold','4g','gzip'))}, R10 {fmt(r('r010','cold','4g','gzip'))}. Without compression 4G: R8 {fmt(r('r008','cold','4g'))}, R10 {fmt(r('r010','cold','4g'))}.",
             measuredOrEstimate="measured", evidence=["measurements/startup.jsonl", "measurements/summary.json", "scripts/startup.mjs"],
             limitations="Chromium only; CPU contention from other tracks (loadavg up to 14 on 4 vCPU) inflates localhost numbers; 4G is CDP emulation, not a real network; each app's own ready marker differs in meaning. " + env),
        dict(id="F-F-03", title="R10's global fetch no-store override defeats HTTP caching of the WASM runtime",
             classification="VERIFIED",
             statement=f"R10 boundary.js wraps globalThis.fetch so every GET uses cache: 'no-store' (to keep GitHub reads fresh). The .NET runtime loads _framework assets through fetch, so a warm reload re-downloads {mb(tb('r010','warm'))} (R9: {mb(tb('r009','warm'))}, R8: {mb(tb('r008','warm'))}). Warm 4G ready: R10 {fmt(r('r010','warm','4g'))} vs R9 {fmt(r('r009','warm','4g'))}. Root cause: Limen's HttpEffectRequest has no per-request cache mode (0.9.1 and HEAD), so the app patched fetch globally.",
             measuredOrEstimate="measured", evidence=["measurements/startup.jsonl (mode=warm)", "indy-init-rehearsal-010/web/boundary.js:9-15", "limen src/generated/core.ts HttpEffectRequest"],
             limitations="python http.server sends no Cache-Control; R9's warm reuse relies on heuristic caching/revalidation. A CDN with long max-age would not change the no-store behaviour."),
        dict(id="F-F-04", title="Full trimming including FSharp.Core cuts R10 payload by about a third",
             classification="SUPPORTED",
             statement=f"TrimMode=full (+SatelliteResourceLanguages=en) on R10: cold transfer {mb(tb('r010-full'))} vs {mb(tb('r010'))}; FSharp.Core 2.40 -> 0.29 MB; 4G gzip ready {fmt(r('r010-full','cold','4g','gzip'))} vs {fmt(r('r010','cold','4g','gzip'))}. Functional check: R10's own Chromium suite (194 tests, stateful GitHub fake) against the full-trim build, 2 clean runs: 158 pass / 36 fail, the identical failing set as the untrimmed build (3 runs) - no regression detected.",
             measuredOrEstimate="measured", evidence=["measurements/bundles/r010-full.json", "measurements/startup.jsonl", "measurements/playwright-stability.json"],
             limitations="R10 comment warns that F# reflection formatting (%A) may break under trimming; only paths exercised by the suite are checked."),
        dict(id="F-F-05", title="Trimming satellite resources does not change startup",
             classification="CONTRADICTED",
             statement=f"Hypothesis 'removing FSharp.Core satellite resources (0.32 MB, 13 cultures) speeds startup' is contradicted: they are not fetched at startup (cold transfer {mb(tb('r010-sat'))} vs {mb(tb('r010'))}); only deploy size changes.",
             measuredOrEstimate="measured", evidence=["measurements/bundles/r010-sat.json", "measurements/startup.jsonl"], limitations="Invariant-globalization apps only."),
        dict(id="F-F-06", title="wasm-tools workload relinking halves the native runtime but is not needed to build",
             classification="SUPPORTED",
             statement=f"All publishes succeeded without any workload. With wasm-tools installed (isolated SDK copy), R10 publish relinks dotnet.native.wasm 3.00 -> 1.50 MB (total _framework 10.8 -> 9.4 MB); one publish took 83 s vs 34-42 s without (n=1, contended). Startup (clean rerun): localhost {fmt(r('r010-wasmtools','cold','none','python-http-rerun'))} vs R10 {fmt(r('r010'))}; 4G gzip {fmt(r('r010-wasmtools','cold','4g','gzip-rerun'))} vs {fmt(r('r010','cold','4g','gzip'))}.",
             measuredOrEstimate="measured", evidence=["measurements/bundles/r010-wasmtools.json", "measurements/startup.jsonl"],
             limitations="Workload manifest band 10.0.114 may pull a newer runtime pack than 10.0.13; n=1 build."),
        dict(id="F-F-07", title="Build and edit-loop cost of F# WASM apps; trimming doubles the edit-publish loop",
             classification="SUPPORTED",
             statement=f"Release publish of the WASM host (warm NuGet cache). Batch 2 (interleaved, loadavg ~5): cold R8 {fmts(bmed(s,'r008','publish-cold','batch2'))}, R9 {fmts(bmed(s,'r009','publish-cold','batch2'))}, R10 {fmts(bmed(s,'r010','publish-cold','batch2'))}; edit+publish R8 {fmts(bmed(s,'r008','publish-incr','batch2'))}, R9 {fmts(bmed(s,'r009','publish-incr','batch2'))}, R10 {fmts(bmed(s,'r010','publish-incr','batch2'))}. Batch 1 (sequential, loadavg ~12): cold R8 {fmts(bmed(s,'r008','publish-cold','batch1'))}, R9 {fmts(bmed(s,'r009','publish-cold','batch1'))}, R10 {fmts(bmed(s,'r010','publish-cold','batch1'))}; Debug solution build cold R8 {fmts(bmed(s,'r008','sln-cold'))}, R9 {fmts(bmed(s,'r009','sln-cold'))}, R10 {fmts(bmed(s,'r010','sln-cold'))}. All batches pooled: cold R8 {fmts(bmed(s,'r008','publish-cold'))}, R9 {fmts(bmed(s,'r009','publish-cold'))}, R10 {fmts(bmed(s,'r010','publish-cold'))}, fixture {fmts(bmed(s,'fixture','publish-cold'))}; no-op 2.5-3.1 s; one-line F# edit then publish: R8 {fmts(bmed(s,'r008','publish-incr'))}, R9 {fmts(bmed(s,'r009','publish-incr'))}, R10 {fmts(bmed(s,'r010','publish-incr'))}, fixture {fmts(bmed(s,'fixture','publish-incr'))}. Trimmed apps (R10, fixture: TrimMode=partial) re-run ILLink on every publish, so a one-line edit costs 10.6-16 s versus 5.7-8.2 s for untrimmed R8/R9: the trimming that cuts payload 3-4x (F-F-01) roughly doubles the edit-publish loop; a Debug/no-trim dev loop with Release-only trimming avoids paying both. First-ever publish incl. runtime-pack download: 51.3 s (n=1).",
             measuredOrEstimate="measured", evidence=["measurements/build-times.csv", "measurements/build-times-batch2.csv", "measurements/summary.json"],
             limitations="Heavy contention from concurrent tracks (loadavg median 11.7 on 4 vCPU during batch 1); batch 2 interleaved to reduce order effects; MSBuild node reuse on."),
        dict(id="F-F-08", title="Where agents struggle with F#: type mismatches and unresolved names, fixed quickly",
             classification="SUPPORTED",
             statement="34 agent transcripts (construction-by-design experiments): 123 dotnet build/test/run invocations, 30 failed with F# compiler errors; 202 distinct diagnostics: FS0001 type mismatch 70 (35%), FS0039 undefined name 51 (25%, mostly a module alias used before/without definition), FS0003 value applied as function 22, FS0041 overload resolution 16, FS0072 needs type annotation 11, syntax/offside (FS0010/0058/0604) 13. 18 recovery streaks, median ~0.45 min, max 3.5 min. Conventional arm A: median 7.5 distinct errors/run (0-45, n=12); agent plan arm B: 2 (1-7, n=6); mechanical-first arm C: 0.5 (0-7, n=12).",
             measuredOrEstimate="measured", evidence=["data/transcript-builds.jsonl", "data/transcript-errors.jsonl", "scripts/mine_transcripts.py"],
             limitations="Domain-logic tasks, not UI; arms differ in prompt and generated scaffolding, so arm differences are associations; 41 build invocations had undeterminable outcome (output piped/truncated)."),
        dict(id="F-F-09", title="Compile errors rarely reach rehearsal commits or CI; CI failures are infrastructure",
             classification="SUPPORTED",
             statement="Across 1,236 commits (R1-R10 + causa) only 6 non-merge commits match compile-error terms; FS codes in commit messages appear only in R3 (FS3261 nullness from a leaked Directory.Build.props) and R10 (FS1093 negative-contract tests). R10 Actions: 289 runs, 171 success, 82 cancelled (28%), 36 failed; of 5 sampled failure logs: 2 WebKit/apt download timeouts (15 min each), 1 pinned SDK not installed (exit 155), 1 WebKit-only smoke failure, 1 unidentified.",
             measuredOrEstimate="measured", evidence=["data/commit-signals.jsonl", "measurements/ci/runs.csv", "measurements/ci/sampled-failure-logs.csv"],
             limitations="Keyword classification is a screen; only 5 CI logs read (token cost); R8 run list is the first 100 of 642."),
        dict(id="F-F-10", title="WASM interpreter locals limit is now statically checkable; R8-R10 have ample headroom",
             classification="VERIFIED",
             statement="scripts/IlFrame.fsx estimates the Mono interpreter tier-0 frame (8 x (args+locals), 16-aligned). It reproduces R5's start failure: View.project 12,683 locals = 101,472 B (limit 65,535) at 5d8888f, max 4,160 B after the fix a0e7d4a. R8/R9/R10 Causa.App max frames 432 / 1,536 / 2,000 B (>=96.9% headroom). R5 lost about 90 min with a non-starting page while CoreCLR unit tests stayed green.",
             measuredOrEstimate="measured", evidence=["measurements/il-frame.jsonl", "scripts/IlFrame.fsx", "Indy-init docs/engineering-improvement/investigations/wasm.md"],
             limitations="Value-type locals counted as 8 B (under-count); optimiser retry not modelled."),
        dict(id="F-F-11", title="Limen silently drops a second template root, contrary to its docs",
             classification="CONTRADICTED",
             statement="Docs (11-api-reference) say a template with more than one root reports BridgeError{phase: binding}. Probe in Chromium with limen 0.9.0 and 0.9.1: data-if and data-each templates with two element roots mount only the first root, kernel 'running', no diagnostic. The same defect recurred in R7 (D-05, hidden relate form) and causa fda2056.",
             measuredOrEstimate="measured", evidence=["measurements/limen-probe-0.9.0.json", "measurements/limen-probe-0.9.1.json", "scripts/limen-probe/", "data/limen-claims.jsonl LC-07"],
             limitations="HEAD (743cdb9) source shows the same firstElementChild check; HEAD not executed."),
        dict(id="F-F-12", title="Limen limitations claimed by rehearsal teams: mostly real, two misreadings",
             classification="VERIFIED",
             statement="Of 6 rehearsal claims: real gaps - no redirect:'manual' on HTTP effects; nested lists not representable (ViewItem primitives; the JS kernel nevertheless renders nested data when fed untyped JSON); measure does not await fonts.ready. Real by design - no beforeunload (bfcache). Misread - 'no LocationChanged for own navigation' is documented behaviour; 'Limen does not manage focus' ignores the optional focus capability shipped in 0.9.0. New: no per-request cache mode (F-F-03).",
             measuredOrEstimate="measured", evidence=["data/limen-claims.jsonl"], limitations="fonts.ready claim by code inspection only."),
        dict(id="F-F-13", title="Existing contract tooling went unused",
             classification="VERIFIED",
             statement="Limen 0.9.1 ships view-contract tooling (checkPage/checkProjection/checkEvent, docs/28) that rejects unknown keys, nested lists and non-template data-if; 0 *.view.json files exist in R1-R10 or causa. The Limen focus capability was likewise available but R2 hand-wrote focus handling.",
             measuredOrEstimate="measured", evidence=["data/limen-claims.jsonl LC-03, LC-08"], limitations="Adoption barriers not investigated."),
        dict(id="F-F-14", title="Folio is declared but not integrated",
             classification="VERIFIED",
             statement="R10 locks @echelon-foundry/print-components 0.4.1 and lists it in Administration, but its dist ships no Folio asset; the report's print view is hand-written @media print CSS; only the bootstrap print.html uses <ef-print-document>. R8's T30 review recorded the same (Folio only in bootstrap print.html; Report.fs 2 lines).",
             measuredOrEstimate="measured", evidence=["r010 dist listing", "indy-init-rehearsal-010/web/screens/workspace-report.css", "indy-init-rehearsal-008/evidence/reviews/T30-pre-rc.md"],
             limitations="R8 later integrated Folio elements (CR-T26); not re-measured."),
        dict(id="F-F-15", title="Contrast failures in R10 trace to Forma token pairs; reachable screens pass axe",
             classification="VERIFIED",
             statement="axe-core 4.14 (WCAG 2.0/2.1 A+AA) on landing/disconnected routes at 1280x800 and 390x844: 0 violations in 22 scans (R8 8, R9 2, R10 10, fixture 2). R10's own suite reports contrast 4.00:1 and 4.39:1 in workspace states (our run reproduces these messages); Forma's catalog/known-issues.json documents exactly --ef-color-text-secondary on --ef-color-surface-secondary 4.0:1 and accent 4.38:1.",
             measuredOrEstimate="measured", evidence=["measurements/axe/*.json", "/home/user/sprint-scratch pw logs summarised in measurements/playwright-stability.json", "ext/forma catalog/known-issues.json"],
             limitations="axe only on states reachable without a GitHub session; connected states not scanned by axe directly."),
        dict(id="F-F-16", title="Playwright suite stability (Chromium)",
             classification="SUPPORTED",
             statement=(suite_txt + ". No flaky test in any app. R10's 36 stable failures = 17 live-provider tests (no CAUSA_GITHUB_TOKEN, fail as BLOCKED by design) + 19 acceptance obligations, matching the R10 FINAL-REPORT's list of ~20 known Chromium failures (contrast, save-flow re-read, wording/selector mismatches); PERSIST-031-O19, which R10 called timing-sensitive, passed in all 5 runs. Wall time per R10 run 509-743 s.") if suite_txt else "pending",
             measuredOrEstimate="measured", evidence=["measurements/playwright-stability.json", "measurements/playwright-runs.csv"],
             limitations="WebKit project unavailable (R8 config includes webkit; excluded). 3 runs per app, serial, under contention."),
        dict(id="F-F-17", title="Recurring UI defect patterns and the contracts that would catch them",
             classification="SUPPORTED",
             statement="29 curated defects (R1-R10, causa) in 11 patterns: contrast/theme 6, focus management 4, responsive/target size 3, Limen template roots 2, WASM interpreter limits 2, build provenance 2, state presentation not derived 2, duplicate structure 2, Folio not integrated 2, test-harness timing 2, F# build config 2. 6/29 were catchable by tools already available (axe 4, Limen focus capability 2), 10/29 partially, 13/29 need a new contract.",
             measuredOrEstimate="measured", evidence=["data/curated-ui-defects.jsonl"], limitations="Hand-curated from commit messages and defect files; selection bias towards well-described fixes."),
        dict(id="F-F-18", title="Time lost to WASM runtime and deployment issues (estimate)",
             classification="SUPPORTED",
             statement="R4: 19 of 86 commits (22%) are D-HIST-WASM work over 6.2 h of a 13.8 h commit span; R5: ~90 min with a non-starting page; R10: two 15-min WebKit download timeouts and build-and-test cancelled by its 20-min limit once browser suites took ~29 min (R10 final report).",
             measuredOrEstimate="estimate", evidence=["git log indy-init-rehearsal-004", "Indy-init wasm.md", "measurements/ci/sampled-failure-logs.csv", "indy-init-rehearsal-010/evidence/FINAL-REPORT.md:137"],
             limitations="Commit spans overlap other work; lower/upper bounds not separable."),
        dict(id="F-F-19", title="Styling rules worth enforcing automatically",
             classification="INCONCLUSIVE",
             statement="Heuristic lint over app-owned CSS (R1-R10, causa): raw colour literals outside custom properties in R2 (14), R4/R5 (4), R9 (25); rules overriding Forma .ef-* classes 0-25 per app; !important up to 10 (R3); focus outline suppressed 0-2. Forma 0.13 itself hides 9 native controls with opacity 0 (source of causa 3ae3ac9).",
             measuredOrEstimate="measured", evidence=["measurements/style-lint.json", "scripts/style_lint.py"],
             limitations="Counts are candidates, not confirmed defects; no causal link measured between lint counts and defects."),
        dict(id="F-F-20", title="Every app invents its own app-ready signal",
             classification="VERIFIED",
             statement="R8 sets html[data-engine=ready], R9 html[data-causa-ready=running], R10 html[data-causa-started-ms] while its suites wait for the 'Loading Causa' status to hide and the title to change. Suites mostly use role locators (R10: 297 getByRole vs 73 CSS locators; R8 168 vs 265; R9 uses 25 test ids) and 3-10 fixed waitForTimeout calls each.",
             measuredOrEstimate="measured", evidence=["r008/web/boundary.js", "r009/web/main.js", "r010/web/boundary.js", "tests/browser/** grep counts"],
             limitations="Static counts only."),
    ]
    (t / "findings.json").write_text(json.dumps(findings, indent=1), encoding="utf-8")
    print(len(findings), "findings")
    write_experiments(t)


ENV_REF = "measurements/environment.json (4 vCPU Xeon 2.3 GHz shared, 15 GiB, .NET SDK 10.0.402, node 22, Chromium 153 headless)"

EXPERIMENTS = [
    dict(id="SPR-F-01", question="How long do cold, no-op and incremental builds/publishes of F# WASM apps take?",
         procedure="scripts/measure_build.py on git clones of R8/R9/R10 and a minimal fixture under /home/user/sprint-scratch/F: publish-cold (remove bin/obj under src), publish-noop, publish-incr (append a comment to Causa.App/View.fs), sln-cold/noop (dotnet build Causa.slnx Debug). Batch 1: modes in sequence, n=3. Batch 2: publish-cold and publish-incr interleaved across repos, n=3.",
         rawResults=["measurements/build-times.csv", "measurements/build-times-batch2.csv", "measurements/summary.json#build"],
         limitations="Shared host with concurrent heavy jobs from other tracks (loadavg samples in measurements/loadavg-samples.txt); NuGet cache warm; MSBuild node reuse on.",
         reproduction="python3 scripts/measure_build.py OUT.csv REPO LABEL --reps 3 --modes publish-cold,publish-noop,publish-incr,sln-cold,sln-noop"),
    dict(id="SPR-F-02", question="What is the publish/bundle size, total and per asset type?",
         procedure="scripts/bundle_sizes.mjs over each dist/ (build.fsx output; fixture: publish wwwroot/_framework + index.html; variants: R10 with SatelliteResourceLanguages=en, TrimMode=full, wasm-tools relink). Raw, gzip -9 and brotli q11 bytes per category; .br/.gz siblings ignored.",
         rawResults=["measurements/bundles/*.json"], limitations="Includes files never requested at runtime (see SPR-F-03 transferBytes for what loads).",
         reproduction="node scripts/bundle_sizes.mjs LABEL DIST_DIR > out.json"),
    dict(id="SPR-F-03", question="How long until the app is ready in headless Chromium (cold, warm, emulated 4G, with/without compression)?",
         procedure="scripts/startup.mjs: fresh browser context per cold rep (warm: one primed context, timed reloads); init script records performance.now() when the app's own ready attribute appears (R8 data-engine=ready, R9 data-causa-ready=running, R10 data-causa-started-ms, fixture data-fixture-ready); also DOMContentLoaded, FCP, resource transfer bytes. Servers: python http.server and scripts/static_gzip_server.mjs. 4G = CDP 9 Mbit/s / 60 ms. n=7 (cold/warm localhost), n=5 (4G, gzip).",
         rawResults=["measurements/startup.jsonl", "measurements/summary.json#startup"], limitations="Chromium only; CPU contention; ready markers are app-defined and not strictly equivalent.",
         reproduction="node scripts/startup.mjs OUT.jsonl LABEL URL MARKER [--reps N] [--warm] [--throttle 4g] [--server gzip]"),
    dict(id="SPR-F-04", question="Are the existing Playwright suites stable across repeated runs?",
         procedure="Repo suites run 3x serially per app with repo-pinned @playwright/test 1.63.0, --trace off, JSON reporter; R8/R9 via copies of their configs with a private port; R10 playwright.config.ts --project chromium with the stateful GitHub fake on a private port; R10 TrimMode=full build run 2x. Summarised with scripts/playwright_stability.py --project chromium.",
         rawResults=["measurements/playwright-stability.json", "measurements/playwright-runs.csv"], limitations="WebKit unavailable; live-provider tests have no token (BLOCKED/fail by design in R10).",
         reproduction="see /home/user/sprint-scratch/F/run_suites.sh (copied to scripts/run_suites.sh)"),
    dict(id="SPR-F-05", question="Does axe-core find WCAG 2.1 A/AA violations on the apps' reachable screens?",
         procedure="scripts/axe_scan.mjs: wait for ready marker, inject the repo's axe-core 4.14.0, run tags wcag2a/2aa/21a/21aa on each hash route at 1280x800 and 390x844.",
         rawResults=["measurements/axe/*.json"], limitations="Only unauthenticated/disconnected states; workspace states need a GitHub session or fake.",
         reproduction="node scripts/axe_scan.mjs OUT LABEL URL MARKER AXE_JS ROUTES"),
    dict(id="SPR-F-06", question="Does Limen behave as documented for multi-root templates and nested lists?",
         procedure="scripts/limen-probe/probe.html with a fake transport (Legacy handshake) and three view cases, served next to limen 0.9.0 (npm) and 0.9.1 (R10 node_modules) dist/; run_probe.mjs records kernel status, BridgeErrors and DOM.",
         rawResults=["measurements/limen-probe-0.9.0.json", "measurements/limen-probe-0.9.1.json"], limitations="HEAD not executed (source inspected).",
         reproduction="serve probe.html + limen/ (package dist) ; node scripts/limen-probe/run_probe.mjs BASE_URL"),
    dict(id="SPR-F-07", question="Can the WASM interpreter 'locals size too big' failure be predicted statically, and how close are R8-R10?",
         procedure="dotnet fsi scripts/IlFrame.fsx over Release Causa.*.dll of R8/R9/R10 and R5 at 5d8888f (failing) and a0e7d4a (fixed); self-test reproduces wasm.md boundary values.",
         rawResults=["measurements/il-frame.jsonl"], limitations="Value types counted as 8 B.",
         reproduction="dotnet fsi scripts/IlFrame.fsx --self-test ; dotnet fsi scripts/IlFrame.fsx --top 3 ASSEMBLY.dll"),
    dict(id="SPR-F-08", question="Which F# compile errors do agents hit, how often, and how fast do they recover?",
         procedure="scripts/mine_transcripts.py over 34 Claude Code transcripts in research-documents/research/construction-by-design (CONSTRUCT-008, its validation, time-entry-expanded-01): pair Bash dotnet invocations with results, extract FS diagnostics, recovery streaks.",
         rawResults=["data/transcript-builds.jsonl", "data/transcript-errors.jsonl"], limitations="Domain tasks rather than UI; small n per arm.",
         reproduction="python3 scripts/mine_transcripts.py data/transcript $(find research-documents -name 'transcript*.jsonl')"),
    dict(id="SPR-F-09", question="Which defect classes recur in rehearsal history?",
         procedure="scripts/mine_defects.py keyword screen over 1,236 commits (R1-R10, causa) -> data/commit-signals.jsonl; hand curation of 29 defects with sources and contract mapping (scripts/curated_defects.py -> data/curated-ui-defects.jsonl); Limen claim verification (data/limen-claims.jsonl); CI run index via GitHub MCP actions_list and 5 sampled failure logs.",
         rawResults=["data/commit-signals.jsonl", "data/curated-ui-defects.jsonl", "data/limen-claims.jsonl", "measurements/ci/"], limitations="Keyword screen is noisy (e.g. 'token' = design token or credential).",
         reproduction="python3 scripts/mine_defects.py OUT.jsonl REPO... ; python3 scripts/curated_defects.py OUT.jsonl"),
    dict(id="SPR-F-10", question="Do candidate automatic styling rules fire on app CSS?",
         procedure="scripts/style_lint.py over app-owned CSS of R1-R10, causa HEAD, causa before 3ae3ac9 and Forma 0.13 all.css.",
         rawResults=["measurements/style-lint.json"], limitations="Heuristic; no ground truth.", reproduction="python3 scripts/style_lint.py OUT LABEL=FILES..."),
]


def write_experiments(t: Path) -> None:
    exps = [dict(e, environment=ENV_REF) for e in EXPERIMENTS]
    (t / "experiments.json").write_text(json.dumps(exps, indent=1), encoding="utf-8")
    print(len(exps), "experiments")


if __name__ == "__main__":
    main()
