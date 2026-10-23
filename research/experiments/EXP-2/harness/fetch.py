#!/usr/bin/env python3
"""EXP-2 phase 1: fetch push-to-main workflow runs and their jobs (all attempts) for the replay windows.

Uses the `gh api` CLI (read-only GET requests). Writes data/<repo>.runs.json and data/<repo>.jobs.json with a
fixed subset of fields; no token or log body is written. Run with `python3 -I harness/fetch.py` from EXP-2/.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
OWNER = "kemiller2002"

RUN_FIELDS = ["id", "name", "path", "head_sha", "head_branch", "event", "status", "conclusion", "created_at",
              "updated_at", "run_started_at", "run_attempt", "run_number", "workflow_id"]
JOB_FIELDS = ["id", "run_id", "run_attempt", "name", "status", "conclusion", "started_at", "completed_at",
              "labels", "runner_name", "workflow_name", "head_sha"]
STEP_FIELDS = ["number", "name", "status", "conclusion", "started_at", "completed_at"]


def gh(path):
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def window(repo):
    shas = []
    with open(os.path.join(DATA, f"{repo}.window.txt")) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            shas.append(line.split()[0])
    return shas[:60], shas[60]


def main(repos):
    for repo in repos:
        win, _pred = window(repo)
        wanted = set(win)
        runs, page = [], 1
        while True:
            body = gh(f"repos/{OWNER}/{repo}/actions/runs?branch=main&event=push&per_page=100&page={page}")
            batch = body["workflow_runs"]
            if not batch:
                break
            runs.extend(batch)
            # stop once every window SHA is older than this page and the page reaches before the oldest window run
            seen = {r["head_sha"] for r in runs}
            if wanted <= seen and len(batch) == 100:
                # one more page guards against runs of the oldest SHA spilling over
                page += 1
                extra = gh(f"repos/{OWNER}/{repo}/actions/runs?branch=main&event=push&per_page=100&page={page}")
                runs.extend(extra["workflow_runs"])
                break
            if len(batch) < 100:
                break
            page += 1
        runs = [{k: r.get(k) for k in RUN_FIELDS} for r in runs if r["head_sha"] in wanted]
        runs.sort(key=lambda r: (r["created_at"], r["id"]))
        jobs = []
        for r in runs:
            jp = 1
            while True:
                body = gh(f"repos/{OWNER}/{repo}/actions/runs/{r['id']}/jobs?filter=all&per_page=100&page={jp}")
                for j in body["jobs"]:
                    rec = {k: j.get(k) for k in JOB_FIELDS}
                    rec["steps"] = [{k: s.get(k) for k in STEP_FIELDS} for s in (j.get("steps") or [])]
                    jobs.append(rec)
                if len(body["jobs"]) < 100:
                    break
                jp += 1
        missing = sorted(wanted - {r["head_sha"] for r in runs})
        with open(os.path.join(DATA, f"{repo}.runs.json"), "w") as f:
            json.dump({"repository": f"{OWNER}/{repo}", "filter": "branch=main event=push", "runs": runs,
                       "window_shas_without_runs": missing}, f, indent=1)
        with open(os.path.join(DATA, f"{repo}.jobs.json"), "w") as f:
            json.dump({"repository": f"{OWNER}/{repo}", "filter": "filter=all (every attempt)", "jobs": jobs}, f,
                      indent=1)
        print(repo, "runs", len(runs), "jobs", len(jobs), "missing", len(missing), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:] or ["praxis", "dokimos"])
