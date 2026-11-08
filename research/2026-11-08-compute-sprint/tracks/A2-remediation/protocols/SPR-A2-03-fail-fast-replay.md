# SPR-A2-03 — Retrospective counterfactual: fail-fast ordering of CI gates

Status: PREREGISTERED before computation. Registered 2026-11-08 ~15:00 America/Indiana/Indianapolis.
Nature: counterfactual ESTIMATE from historical step timings; nothing is re-run.

## Data
Track A `data/raw/ci-jobs-timed.jsonl` (2,191 runs' jobs with per-step number, timestamps, conclusion;
R2–R10 timed windows). Step categories: Track A's `econ.step_category` (imported unchanged).
Cheap gates = categories {build, test, static-gate}; expensive = {browser-install, browser-test}.

## Hypothesis
H1: Reordering so cheap gates run before browser suites (within a job), and making browser-only jobs
`needs:` the job holding the cheap gates (across jobs), saves >=10% of the job-minutes spent in
failed runs in R2–R10.

## Model (assumptions stated up front)
A1 Failure is detected by the same step (the first step whose conclusion is `failure`) regardless of
   order; a flaky failure would still fail.  A2 GitHub already skips later steps in a job after a failure,
   so within-job savings = seconds of expensive steps that ran BEFORE a failing cheap-gate step in the same
   job.  A3 Across jobs: in a run where some job failed at a cheap-gate step, every other job in that run
   whose steps include an expensive step and which contains no cheap-gate failure of its own would have
   been skipped; saving = its expensive steps' seconds plus its setup (all its steps' seconds) — reported as
   two variants: (V1) expensive-step seconds only; (V2) whole-job seconds.
A4 Cancelled jobs/runs (superseded or timeout) are excluded from savings; failures in browser steps
   themselves yield no savings. A5 Re-ordering costs nothing in minutes for green runs; the latency
   penalty of serializing jobs is estimated separately as the median duration of the gating job in
   successful runs (ESTIMATE).

## Metrics
Per repo: failed-run job-minutes (baseline), within-job savings, across-job savings (V1, V2), and
savings as % of failed-run minutes and of all job-minutes. Success = H1 >= 10% (V1) in aggregate.
