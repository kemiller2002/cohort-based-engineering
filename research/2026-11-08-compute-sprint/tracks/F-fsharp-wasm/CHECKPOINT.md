# Track F checkpoints (F-001: F#, WASM, Forma, Folio)

## CP-F-00 13:40 EST — start
- Plan: (1) clone ext repos read-only; (2) copy R8/R9/R10 to /home/user/sprint-scratch/F; (3) build/publish/startup/Playwright/axe measurements; (4) defect mining over rehearsal git history + evidence; (5) Limen/Forma/Folio doc-vs-claim comparison.

## CP-F-01 14:40 EST — measurements largely collected
- Done: build batch 1 (R8/R9/R10, n=3 per mode) + fixture; bundle sizes (6 variants); startup (python & gzip servers, localhost & 4G, cold & warm; n=5–7); axe 4.14 scans (22 scans, 0 violations on reachable unauthenticated routes); IL-frame scanner validated on R5 pre/post fix; Limen behaviour probe (0.9.0, 0.9.1); transcript and commit mining; curated 29-defect dataset; style lint; CI run index (R10 complete 289 runs; R8 first 100).
- Running: Playwright suites x3 (R9, R8, R10 chromium); queued phase 2: wasm-tools startup, R10 TrimMode=full suite x2, build batch 2 (interleaved).
- Key results so far: R10 warm reload re-downloads 10.1 MB (global fetch no-store override); R8/R9 untrimmed 37.0/27.8 MB cold transfer vs R10 11.1 MB; full trim 7.8 MB; wasm-tools relink halves dotnet.native.wasm (3.0 -> 1.5 MB); Limen drops second template root silently (docs say BridgeError).
- REPORT.md: harness refuses subagent report files; full report text goes in the final reply (Director instruction).
