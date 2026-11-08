"""Claims A-F-11/12/13: independent read-only fetch of GitHub Actions data (GET only).
1) list every run CREATED in each rehearsal's [T0, T0+420 min) window (server-side `created` filter);
2) draw a stratified random sample of runs per repository (seed recorded);
3) fetch jobs (filter=all, i.e. every attempt) for each sampled run.
Usage: python3 -I fetch_ci_sample.py OUT_DIR [PER_REPO=30] [SEED=20261108]
Windows are taken from each rehearsal's own documented start (see WINDOWS sources)."""
import json
import os
import random
import subprocess
import sys
import time
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1lib as L  # noqa: E402

OWNER = "kemiller2002"
# T0 per rehearsal, read by V1 from the rehearsal's own evidence file (path:field)
WINDOWS = (
    ("indy-init-rehearsal-002", "2026-10-23T12:14:13Z", "evidence/acceptance/run.json milestones.start"),
    ("indy-init-rehearsal-003", "2026-10-24T07:32:22Z", "evidence/telemetry/timer-start.json timedPhaseStart"),
    ("indy-init-rehearsal-004", "2026-10-27T06:04:39Z", "evidence/rehearsal/checkpoints.json clock (start)"),
    ("indy-init-rehearsal-005", "2026-10-27T20:08:38Z", "evidence/rehearsal/clock.json startUtc"),
    ("indy-init-rehearsal-006", "2026-10-28T20:02:19Z", "evidence/kickoff/kickoff-receipt.json officialStart"),
    ("indy-init-rehearsal-007", "2026-10-29T22:49:55Z", "evidence/telemetry/README.md (deadline 05:49:55Z - 420 min)"),
    ("indy-init-rehearsal-008", "2026-11-01T17:31:24Z", "evidence/SCHEDULE-ACTUALS.md:1"),
    ("indy-init-rehearsal-009", "2026-11-04T00:30:01Z", "evidence/t0/T0.md:3"),
    ("indy-init-rehearsal-010", "2026-11-06T16:40:13Z", "evidence/FINAL-REPORT.md:10 (evidence/t0/t0.json)"),
)


def get(path):
    for attempt in range(4):
        r = subprocess.run(("curl", "-sS", "--fail", "-H", "Accept: application/vnd.github+json",
                            "https://api.github.com" + path), capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(r.stdout)
        time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"GET {path} failed: {r.stderr[:200]}")


def window_str(t0):
    a = L.parse_ts(t0)
    b = a + timedelta(minutes=420) - timedelta(seconds=1)
    f = "%Y-%m-%dT%H:%M:%SZ"
    return a.strftime(f) + ".." + b.strftime(f)


def list_runs(repo, t0):
    runs, page = [], 1
    while True:
        d = get(f"/repos/{OWNER}/{repo}/actions/runs?per_page=100&page={page}&created={window_str(t0)}")
        runs += d["workflow_runs"]
        if len(d["workflow_runs"]) < 100:
            return d["total_count"], runs
        page += 1


def trim_run(r):
    keys = ("id", "name", "path", "event", "status", "conclusion", "head_sha", "head_branch", "created_at",
            "run_started_at", "updated_at", "run_attempt")
    return {k: r.get(k) for k in keys}


def trim_job(j):
    keys = ("id", "run_id", "run_attempt", "name", "status", "conclusion", "created_at", "started_at", "completed_at")
    return dict({k: j.get(k) for k in keys},
                steps=[{k: s.get(k) for k in ("name", "number", "conclusion", "started_at", "completed_at")} for s in j.get("steps") or []])


def fetch_jobs(repo, run_id):
    jobs, page = [], 1
    while True:
        d = get(f"/repos/{OWNER}/{repo}/actions/runs/{run_id}/jobs?filter=all&per_page=100&page={page}")
        jobs += d["jobs"]
        if len(d["jobs"]) < 100:
            return jobs
        page += 1


def main(out_dir, per_repo="30", seed="20261108"):
    per_repo, seed = int(per_repo), int(seed)
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(seed)
    manifest = {"seed": seed, "perRepo": per_repo, "fetchedAtStart": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "method": "curl GET api.github.com via session proxy (read-only)", "repos": []}
    for repo, t0, src in WINDOWS:
        total, runs = list_runs(repo, t0)
        runs = sorted((trim_run(r) for r in runs), key=lambda r: r["id"])
        eligible = [r for r in runs if r["conclusion"] != "skipped"]
        sample = sorted(rng.sample(eligible, min(per_repo, len(eligible))), key=lambda r: r["id"])
        with open(os.path.join(out_dir, f"runs-{repo}.json"), "w") as f:
            json.dump(runs, f)
        sampled = []
        for r in sample:
            sampled.append(dict(r, jobs=[trim_job(j) for j in fetch_jobs(repo, r["id"])]))
        with open(os.path.join(out_dir, f"sample-{repo}.json"), "w") as f:
            json.dump(sampled, f)
        manifest["repos"].append({"repo": repo, "t0": t0, "t0Source": src, "window": window_str(t0),
                                  "apiTotalCount": total, "runsListed": len(runs), "eligibleNonSkipped": len(eligible),
                                  "sampled": len(sample), "sampledRunIds": [r["id"] for r in sample]})
        print(repo, total, len(runs), len(eligible), len(sample), flush=True)
    manifest["fetchedAtEnd"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
