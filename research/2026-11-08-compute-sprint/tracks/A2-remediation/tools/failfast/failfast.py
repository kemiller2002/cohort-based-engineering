#!/usr/bin/env python3
"""SPR-A2-03 counterfactual fail-fast replay (ESTIMATE). Pure functions over Track A's timed job data.

Usage: python3 failfast.py TRACK_A_SCRIPTS_DIR CI_JOBS_TIMED_JSONL OUT_JSON
"""
import json
import statistics
import sys
from datetime import datetime

CHEAP = frozenset({"build", "test", "static-gate"})
EXPENSIVE = frozenset({"browser-install", "browser-test"})


def secs(a, b):
    if not a or not b:
        return 0.0
    f = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return max(0.0, (f(b) - f(a)).total_seconds())


def classify_steps(job, categorize):
    return tuple(
        {"n": s.get("number"), "cat": categorize(s.get("name")), "concl": s.get("conclusion"),
         "sec": secs(s.get("started_at"), s.get("completed_at"))}
        for s in sorted(job.get("steps") or (), key=lambda s: s.get("number") or 0))


def first_failure(steps):
    return next((s for s in steps if s["concl"] == "failure"), None)


def within_job_saving(steps):
    """Expensive steps that ran before a failing cheap-gate step (A2)."""
    f = first_failure(steps)
    if f is None or f["cat"] not in CHEAP:
        return 0.0
    return sum(s["sec"] for s in steps if s["n"] < f["n"] and s["cat"] in EXPENSIVE)


def run_savings(jobs, categorize):
    """Returns dict of baseline and savings (seconds) for one run (A1-A4)."""
    js = [(j, classify_steps(j, categorize)) for j in jobs]
    dur = lambda j: secs(j.get("started_at"), j.get("completed_at"))
    failed = any(j.get("conclusion") == "failure" for j, _ in js)
    cheap_failed = [j for j, st in js if j.get("conclusion") == "failure" and (first_failure(st) or {}).get("cat") in CHEAP]
    within = sum(within_job_saving(st) for j, st in js if j.get("conclusion") == "failure")
    across_v1 = across_v2 = 0.0
    if cheap_failed:
        for j, st in js:
            if j in cheap_failed or j.get("conclusion") == "cancelled":
                continue
            exp = sum(s["sec"] for s in st if s["cat"] in EXPENSIVE)
            if exp > 0:
                across_v1 += exp
                across_v2 += dur(j)
    return {
        "allSeconds": sum(dur(j) for j, _ in js),
        "failedRun": failed,
        "failedRunSeconds": sum(dur(j) for j, _ in js) if failed else 0.0,
        "within": within, "acrossV1": across_v1, "acrossV2": across_v2,
    }


def gating_latency(runs, categorize):
    """A5: median duration of jobs containing cheap gates in all-success runs (seconds)."""
    vals = []
    for r in runs:
        jobs = r.get("jobs") or []
        if jobs and all(j.get("conclusion") == "success" for j in jobs):
            for j in jobs:
                cats = {s["cat"] for s in classify_steps(j, categorize)}
                if cats & CHEAP and cats & EXPENSIVE == set() and any(
                        EXPENSIVE & {s["cat"] for s in classify_steps(k, categorize)} for k in jobs if k is not j):
                    vals.append(secs(j.get("started_at"), j.get("completed_at")))
    return statistics.median(vals) if vals else None, len(vals)


def aggregate(runs, categorize):
    by = {}
    for r in runs:
        s = run_savings(r.get("jobs") or [], categorize)
        acc = by.setdefault(r["repo"], {k: 0.0 for k in s if k != "failedRun"} | {"runs": 0, "failedRuns": 0})
        acc["runs"] += 1
        acc["failedRuns"] += int(s["failedRun"])
        for k, v in s.items():
            if k != "failedRun":
                acc[k] += v
    total = {k: sum(v[k] for v in by.values()) for k in next(iter(by.values()))} if by else {}
    def pct(d):
        return {
            "minutes": {k: round(d[k] / 60, 1) for k in ("allSeconds", "failedRunSeconds", "within", "acrossV1", "acrossV2")},
            "runs": d["runs"], "failedRuns": d["failedRuns"],
            "savingV1PctOfFailedRunMinutes": round(100 * (d["within"] + d["acrossV1"]) / d["failedRunSeconds"], 1) if d["failedRunSeconds"] else None,
            "savingV2PctOfFailedRunMinutes": round(100 * (d["within"] + d["acrossV2"]) / d["failedRunSeconds"], 1) if d["failedRunSeconds"] else None,
            "savingV1PctOfAllMinutes": round(100 * (d["within"] + d["acrossV1"]) / d["allSeconds"], 1) if d["allSeconds"] else None,
            "savingV2PctOfAllMinutes": round(100 * (d["within"] + d["acrossV2"]) / d["allSeconds"], 1) if d["allSeconds"] else None,
        }
    return {"byRepo": {k: pct(v) for k, v in sorted(by.items())}, "total": pct(total)}


# Sensitivity (added after first computation, disclosed): failing "test"-category steps that are not cheap
# unit gates (live/acceptance/provider/mutation suites, or an aggregate "fail when ... failed" step).
NOT_CHEAP_RE = r"live|acceptance|evidence failed|provider|mutation|conformance"


def strict_categorize(categorize):
    import re
    def cat(name):
        c = categorize(name)
        return "expensive-test" if c in CHEAP and re.search(NOT_CHEAP_RE, (name or "").lower()) else c
    return cat


def main(argv):
    scripts, jobs_path, out = argv[1:4]
    sys.path.insert(0, scripts)
    from econ import step_category  # Track A's categorizer, unchanged
    runs = [json.loads(l) for l in open(jobs_path) if l.strip()]
    result = aggregate(runs, step_category)
    med, n = gating_latency(runs, step_category)
    result["sensitivityStrictCheapGates"] = {"rule": NOT_CHEAP_RE, **aggregate(runs, strict_categorize(step_category))["total"]}
    result["latencyPenaltyESTIMATE"] = {"medianGatingJobSecondsInGreenRuns": med, "samples": n}
    result["nature"] = "counterfactual ESTIMATE; assumptions A1-A5 in protocols/SPR-A2-03-fail-fast-replay.md"
    json.dump(result, open(out, "w"), indent=1)
    print(json.dumps(result["total"], indent=1))


if __name__ == "__main__":
    main(sys.argv)
