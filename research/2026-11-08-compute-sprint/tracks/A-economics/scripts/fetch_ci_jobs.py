#!/usr/bin/env python3
"""Fetch jobs (with step timings) for selected workflow runs, read-only GET.

Usage: python3 fetch_ci_jobs.py CI_RUNS_CSV OUT_JSONL [--timed-only]
Resumable: run ids already present in OUT_JSONL are skipped.
Each output line: {"repo", "runId", "jobs": [trimmed job]}.
"""
import csv
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

JOB_KEEP = ("id", "name", "status", "conclusion", "created_at", "started_at", "completed_at",
            "runner_name", "labels", "run_attempt")
STEP_KEEP = ("name", "number", "status", "conclusion", "started_at", "completed_at")


def trim_job(job: dict) -> dict:
    return {**{k: job.get(k) for k in JOB_KEEP},
            "steps": [{k: s.get(k) for k in STEP_KEEP} for s in job.get("steps") or []]}


def fetch(repo: str, run_id: str) -> dict:
    res = subprocess.run(
        ["gh", "api", "-X", "GET", f"repos/kemiller2002/{repo}/actions/runs/{run_id}/jobs?per_page=100&filter=all"],
        capture_output=True, text=True)
    if res.returncode != 0:
        return {"repo": repo, "runId": int(run_id), "error": res.stderr.strip()[:200], "jobs": []}
    return {"repo": repo, "runId": int(run_id), "jobs": [trim_job(j) for j in json.loads(res.stdout).get("jobs", [])]}


def main(argv):
    src, out = argv[1], argv[2]
    timed_only = "--timed-only" in argv
    done = set()
    if os.path.exists(out):
        with open(out) as fh:
            done = {json.loads(l)["runId"] for l in fh if l.strip()}
    with open(src) as fh:
        todo = [(r["repo"], r["id"]) for r in csv.DictReader(fh)
                if (not timed_only or r["inTimedWindow"] == "True") and int(r["id"]) not in done
                and r["conclusion"] != "skipped"]
    print(f"{len(todo)} runs to fetch", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=4) as pool, open(out, "a") as fh:
        for rec in pool.map(lambda t: fetch(*t), todo):
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()


if __name__ == "__main__":
    main(sys.argv)
