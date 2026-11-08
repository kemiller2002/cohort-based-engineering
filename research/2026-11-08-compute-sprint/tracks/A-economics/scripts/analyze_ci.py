#!/usr/bin/env python3
"""CI overhead analysis for rehearsal timed windows.

Usage: python3 analyze_ci.py DATA_DIR JOBS_JSONL OUT_JSON
Inputs: DATA_DIR/ci-runs.csv (build_ci.py), JOBS_JSONL (fetch_ci_jobs.py).
Outputs: DATA_DIR/ci-jobs.csv, ci-steps.csv, ci-step-categories.csv, ci-commit-latency.csv,
ci-red-then-green.csv and OUT_JSON (per-repo summary).
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import econ  # noqa: E402


def read_csv(path):
    with open(path) as fh:
        return tuple(csv.DictReader(fh))


def write(path, rows):
    rows = list(rows)
    if not rows:
        return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {path}", file=sys.stderr)


def typed_run(r):
    f = lambda v: float(v) if v not in ("", None) else None  # noqa: E731
    return {**r, "spanSeconds": f(r["spanSeconds"]), "queueSeconds": f(r["queueSeconds"]),
            "id": int(r["id"])}


def repo_summary(repo, runs, jobs, steps, lat, rtg):
    run_concl = {r["id"]: r["conclusion"] for r in runs}
    dur = [j["durationSeconds"] for j in jobs if j["durationSeconds"] is not None and j["durationSeconds"] >= 0]
    q = [j["queueSeconds"] for j in jobs if j["queueSeconds"] is not None and j["queueSeconds"] >= 0]
    red_jobs = [j for j in jobs if run_concl.get(j["runId"]) in ("failure", "timed_out", "startup_failure", "cancelled")]
    bill = sum(econ.billable_minutes(j["durationSeconds"]) for j in jobs)
    bill_red = sum(econ.billable_minutes(j["durationSeconds"]) for j in red_jobs)
    cat_s = econ.group_by([s for s in steps if s["seconds"] is not None and s["seconds"] >= 0], lambda s: s["category"])
    step_total = sum(s["seconds"] for ss in cat_s.values() for s in ss)
    lat_s = [x["latencySeconds"] for x in lat if x["latencySeconds"] is not None]
    return {
        "repo": repo,
        "runsWithJobs": len({j["runId"] for j in jobs}),
        "jobs": len(jobs),
        "jobQueueMedianS": econ.percentile(q, 0.5),
        "jobQueueP90S": econ.percentile(q, 0.9),
        "jobQueueMaxS": max(q) if q else None,
        "jobQueueTotalMin": round(sum(q) / 60, 1),
        "jobDurationMedianS": econ.percentile(dur, 0.5),
        "jobDurationP90S": econ.percentile(dur, 0.9),
        "jobMinutesTotal": round(sum(dur) / 60, 1),
        "billableMinutesESTIMATE": bill,
        "billableMinutesInRedOrCancelledRunsESTIMATE": bill_red,
        "redOrCancelledShareOfBillable": round(bill_red / bill, 3) if bill else None,
        "stepSecondsByCategory": {c: round(sum(s["seconds"] for s in ss)) for c, ss in sorted(cat_s.items())},
        "stepShareByCategory": {c: round(sum(s["seconds"] for s in ss) / step_total, 3)
                                for c, ss in sorted(cat_s.items())} if step_total else {},
        "commitsWithCI": len(lat),
        "commitCILatencyMedianS": econ.percentile(lat_s, 0.5),
        "commitCILatencyP90S": econ.percentile(lat_s, 0.9),
        "commitsAllGreen": sum(1 for x in lat if x["allGreen"]),
        "redThenGreenEvents": len(rtg),
        "redThenGreenSameShaReruns": sum(1 for x in rtg if x["sameSha"]),
        "redToGreenMedianS": econ.percentile([x["redToGreenSeconds"] for x in rtg], 0.5),
    }


def main(argv):
    data, jobs_path, out = argv[1:4]
    runs = tuple(typed_run(r) for r in read_csv(f"{data}/ci-runs.csv") if r["inTimedWindow"] == "True")
    with open(jobs_path) as fh:
        recs = tuple(json.loads(l) for l in fh if l.strip())
    jobs = tuple(j for rec in recs for j in econ.job_rows(rec["repo"], rec["runId"], rec["jobs"]))
    steps = tuple(s for rec in recs for s in econ.step_rows(rec["repo"], rec["runId"], rec["jobs"]))
    lat = econ.commit_ci_latency(runs)
    rtg = econ.red_then_green(runs)
    write(f"{data}/ci-jobs.csv", jobs)
    write(f"{data}/ci-steps.csv", steps)
    write(f"{data}/ci-commit-latency.csv", lat)
    write(f"{data}/ci-red-then-green.csv", rtg)
    cats = econ.group_by([s for s in steps if s["seconds"] is not None and s["seconds"] >= 0],
                         lambda s: (s["repo"], s["category"]))
    write(f"{data}/ci-step-categories.csv",
          [{"repo": k[0], "category": k[1], "steps": len(v), "seconds": round(sum(s["seconds"] for s in v)),
            "failedSteps": sum(1 for s in v if s["conclusion"] == "failure")}
           for k, v in sorted(cats.items())])
    by = lambda rows: econ.group_by(rows, lambda r: r["repo"])  # noqa: E731
    R, J, S, L, G = by(runs), by(jobs), by(steps), by(lat), by(rtg)
    summary = [repo_summary(repo, R[repo], J.get(repo, ()), S.get(repo, ()), L.get(repo, ()), G.get(repo, ()))
               for repo in sorted(R)]
    with open(out, "w") as fh:
        json.dump({"basis": "GitHub Actions runs created inside each rehearsal's timed window (rehearsal-windows.csv); "
                            "jobs/steps from GET /actions/runs/{id}/jobs?filter=all",
                   "repos": summary}, fh, indent=1)
    for s in summary:
        print(s["repo"][-3:], {k: v for k, v in s.items() if not isinstance(v, dict) and k != "repo"})


if __name__ == "__main__":
    main(sys.argv)
