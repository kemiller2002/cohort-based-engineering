"""SPR-D2-02 preregistered confirmatory analysis (stage 2 only; pilots are excluded by construction).

Usage:
  python3 -I analyze.py <assignment.json> <usage.json> <score1.json> [<score2.json> ...]  > results.json

usage.json (from the Director, runtime-reported):
  {"s01": {"total_tokens": 51234, "duration_ms": 612000, "tool_uses": 37, "model": "...", "excluded": null}, ...}
  "excluded" is null or a reason string fixed under protocol section 10 (never chosen from outcomes).
Each score file is the JSON emitted by fixture/score.py; its run_id is the workspace basename.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from perm import mean, min_attainable_p, perm_test  # noqa: E402

PRIMARY = ("H2", "trap_violations")
SECONDARY = ["accepted", "total_tokens", "wall_s", "tool_uses"]
DESCRIPTIVE = ["trap_violations_lenient", "trap_raised", "trap_documented", "own_tests_run"]
TRAPS = ["T1", "T2", "T3", "T4", "T5"]
CATEGORIES = ["raised", "documented", "both", "violated", "not_implemented"]


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def row(assignment, usage, score):
    rid = score["run_id"]
    a, u = assignment[rid], usage.get(rid, {})
    return {"runId": rid, "arm": a["arm"], "stage": a["stage"], "batch": a["batch"], "excluded": u.get("excluded"),
            "accepted": score["accepted"], "trap_violations": score["trap_violations"],
            "trap_violations_lenient": score["trap_violations_lenient"], "trap_raised": score["trap_raised"],
            "trap_documented": score["trap_documented"],
            "trap_category": {t: v["category"] for t, v in score["traps"].items()},
            "questions_md": score["questions_md"], "evidence_md": score["evidence_md"],
            "errors_py_intact": score["errors_py_intact"], "own_tests_pass": score["own_tests"]["passed"],
            "own_tests_run": score["own_tests"]["tests_run"], "total_tokens": u.get("total_tokens"),
            "tool_uses": u.get("tool_uses"),
            "wall_s": None if u.get("duration_ms") is None else u["duration_ms"] / 1000, "model": u.get("model")}


def compare(rows, key):
    g = [r[key] for r in rows if r["arm"] == "G" and r[key] is not None]
    m = [r[key] for r in rows if r["arm"] == "M" and r[key] is not None]
    if not g or not m:
        return {"n_G": len(g), "n_M": len(m), "p": None, "note": "missing data"}
    return {"n_G": len(g), "n_M": len(m), "mean_G": mean(g), "mean_M": mean(m), "diff_G_minus_M": mean(g) - mean(m),
            "values_G": g, "values_M": m, "test": "exact permutation, |mean diff|, two-sided",
            "p": perm_test(g, m), "min_attainable_p": min_attainable_p(len(g), len(m))}


def analyze(assignment, usage, scores):
    a = {r["runId"]: r for r in assignment["runs"]}
    rows_all = [row(a, usage, s) for s in scores]
    rows = [r for r in rows_all if r["stage"] == 2 and not r["excluded"]]
    secondary = {k: compare(rows, k) for k in SECONDARY}
    sec_p = [secondary[k]["p"] for k in SECONDARY]
    if all(p is not None for p in sec_p):
        for k, q in zip(SECONDARY, holm(sec_p)):
            secondary[k]["p_holm_secondary"] = q
    return {
        "experiment": "SPR-D2-02", "stage": 2,
        "runs": rows_all,
        "n_included": {arm: sum(1 for r in rows if r["arm"] == arm) for arm in "GM"},
        "pilots_ignored": sorted(r["runId"] for r in rows_all if r["stage"] != 2),
        "primary": {"hypothesis": PRIMARY[0], "outcome": PRIMARY[1], "alpha": 0.05, **compare(rows, PRIMARY[1])},
        "secondary": secondary,
        "descriptive": {k: compare(rows, k) for k in DESCRIPTIVE},
        "per_trap_category_counts": {t: {arm: {c: sum(1 for r in rows if r["arm"] == arm
                                                      and r["trap_category"].get(t) == c) for c in CATEGORIES}
                                         for arm in "GM"} for t in TRAPS},
        "per_trap_runs_violating_raised_measure": {
            t: {arm: sum(1 for r in rows if r["arm"] == arm and r["trap_category"].get(t) in ("violated", "documented"))
                for arm in "GM"} for t in TRAPS},
    }


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    print(json.dumps(analyze(load(sys.argv[1]), load(sys.argv[2]), [load(p) for p in sys.argv[3:]]), indent=1))
