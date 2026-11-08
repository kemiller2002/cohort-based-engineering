"""SPR-D3-01 preregistered confirmatory analysis (stage 2 only; pilots are excluded by construction).

Usage:
  python3 -I analyze.py <assignment.json> <usage.json> <score1.json> [<score2.json> ...]  > results.json

usage.json (from the Director, runtime-reported, one entry per chain, one row per step actually sent):
  {"u01": {"model": "...", "excluded": null,
           "steps": [{"step": 1, "total_tokens": 81234, "duration_ms": 612000, "tool_uses": 37, "capped": false},
                     ...]}, ...}
  "excluded" is null or a reason string fixed under protocol section 10 (never chosen from outcomes).
  Chain totals are sums over its steps.
Each score file is the JSON emitted by fixture/score.py (run with --snapshots); its run_id is the workspace basename.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from perm import mean, min_attainable_p, perm_test  # noqa: E402

PRIMARY = ("H1", "trap_violations")
SECONDARY = ["followed_planted", "accepted", "controls_passed", "regression_count", "total_tokens", "wall_s",
             "tool_uses"]
DESCRIPTIVE = ["trap_raised", "steps_completed", "capped_steps", "own_tests_run", "decisions_md_edited"]
TRAPS = ["T1", "T2", "T3", "T4", "T5"]
TRAP_STEP = {"T1": 4, "T2": 4, "T3": 5, "T4": 6, "T5": 6}
CONTROLS = ["D-001", "D-002"]
CATEGORIES = ["raised", "violated", "not_implemented"]


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def total(steps, key):
    vals = [s.get(key) for s in steps]
    return None if not vals or any(v is None for v in vals) else sum(vals)


def row(assignment, usage, score):
    rid = score["run_id"]
    a, u = assignment[rid], usage.get(rid, {})
    steps = u.get("steps", [])
    dur = total(steps, "duration_ms")
    first = score.get("first_violation_snapshot_step")
    return {"runId": rid, "arm": a["arm"], "stage": a["stage"], "batch": a["batch"], "excluded": u.get("excluded"),
            "accepted": score["accepted"], "accepted_by_step": score["accepted_by_step"],
            "controls_passed": score["controls_passed"],
            "control_pass": {c: v["pass"] for c, v in score["controls"].items()},
            "trap_violations": score["trap_violations"], "trap_violations_by_step": score["trap_violations_by_step"],
            "followed_planted": score["followed_planted"],
            "trap_followed_planted": {t: v["followed_planted"] for t, v in score["traps"].items()},
            "trap_category": {t: v["category"] for t, v in score["traps"].items()},
            "trap_raised": score["trap_raised"], "regression_count": score["regression_count"],
            "regressed": score["regressed"],
            "first_violation_step": first if first is not None else score["first_violation_step_final_state"],
            "first_violation_source": "snapshots" if score.get("snapshots_scored") else "final_state",
            "decisions_md_edited": int(not score["fixture_files_intact"]["DECISIONS.md"]),
            "fixture_files_intact": score["fixture_files_intact"],
            "questions_md": score["questions_md"], "evidence_md": score["evidence_md"],
            "own_tests_pass": score["own_tests"]["passed"], "own_tests_run": score["own_tests"]["tests_run"],
            "total_tokens": total(steps, "total_tokens"), "tool_uses": total(steps, "tool_uses"),
            "wall_s": None if dur is None else dur / 1000, "steps_completed": len(steps),
            "capped_steps": sum(1 for s in steps if s.get("capped")),
            "per_step_tokens": [s.get("total_tokens") for s in steps], "model": u.get("model")}


def compare(rows, key):
    g = [r[key] for r in rows if r["arm"] == "G" and r[key] is not None]
    m = [r[key] for r in rows if r["arm"] == "M" and r[key] is not None]
    if not g or not m:
        return {"n_G": len(g), "n_M": len(m), "p": None, "note": "missing data"}
    return {"n_G": len(g), "n_M": len(m), "mean_G": mean(g), "mean_M": mean(m), "diff_G_minus_M": mean(g) - mean(m),
            "values_G": g, "values_M": m, "test": "exact permutation, |mean diff|, two-sided",
            "p": perm_test(g, m), "min_attainable_p": min_attainable_p(len(g), len(m))}


def exploratory(rows):
    return {
        "first_violation_step": {arm: sorted((r["runId"], r["first_violation_step"]) for r in rows if r["arm"] == arm)
                                 for arm in "GM"},
        "violations_by_trap_step": {arm: {s: sum(r["trap_violations_by_step"][s] for r in rows if r["arm"] == arm)
                                          for s in ("4", "5", "6")} for arm in "GM"},
        "note": "descriptive only; no test. Trap steps are 4-6 by design (steps 1-3 have no traps).",
    }


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
        "experiment": "SPR-D3-01", "stage": 2, "runs": rows_all,
        "n_included": {arm: sum(1 for r in rows if r["arm"] == arm) for arm in "GM"},
        "pilots_ignored": sorted(r["runId"] for r in rows_all if r["stage"] != 2),
        "primary": {"hypothesis": PRIMARY[0], "outcome": PRIMARY[1], "alpha": 0.05, **compare(rows, PRIMARY[1])},
        "secondary": secondary,
        "descriptive": {k: compare(rows, k) for k in DESCRIPTIVE},
        "exploratory": exploratory(rows),
        "per_trap_category_counts": {t: {arm: {c: sum(1 for r in rows if r["arm"] == arm
                                                      and r["trap_category"].get(t) == c) for c in CATEGORIES}
                                         for arm in "GM"} for t in TRAPS},
        "per_trap_runs_followed_planted": {t: {arm: sum(1 for r in rows if r["arm"] == arm
                                                         and r["trap_followed_planted"].get(t)) for arm in "GM"}
                                           for t in ("T1", "T3", "T4")},
        "per_control_runs_passed": {c: {arm: sum(1 for r in rows if r["arm"] == arm and r["control_pass"].get(c))
                                        for arm in "GM"} for c in CONTROLS},
    }


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    print(json.dumps(analyze(load(sys.argv[1]), load(sys.argv[2]), [load(p) for p in sys.argv[3:]]), indent=1))
