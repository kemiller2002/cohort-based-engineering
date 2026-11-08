"""SPR-D2-01 preregistered analysis.

Usage:
  python3 -I analyze.py <assignment.json> <usage.json> <score1.json> [<score2.json> ...]  > results.json

usage.json (from the Director, runtime-reported):
  {"r1": {"total_tokens": 51234, "duration_ms": 612000, "tool_uses": 37, "model": "...", "excluded": null}, ...}
  "excluded" is null or a reason string fixed under the protocol's exclusion rules (never chosen from outcomes).
Each score file is the JSON emitted by score.py for one workspace; its run_id is the workspace basename.
"""
import itertools
import json
import math
import sys

PRIMARY = [("H1", "accepted"), ("H2", "trap_violations"), ("H3", "total_tokens")]
SECONDARY_CONT = ["wall_s", "tool_uses", "trap_compliant"]
SECONDARY_BIN = ["any_violation", "questions_md", "evidence_md", "own_tests_pass"]
EPS = 1e-9


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def perm_test(g, m):
    """Exact two-sided permutation test on difference in means (G - M) over all relabelings."""
    pooled, k = list(g) + list(m), len(g)
    obs = abs(mean(g) - mean(m))
    idx = range(len(pooled))
    diffs = [abs(mean([pooled[i] for i in c]) - mean([pooled[i] for i in idx if i not in c]))
             for c in itertools.combinations(idx, k)]
    return sum(1 for d in diffs if d >= obs - EPS) / len(diffs)


def hyper(a, r1, c1, n):
    return math.comb(r1, a) * math.comb(n - r1, c1 - a) / math.comb(n, c1)


def fisher_two_sided(a, b, c, d):
    """Table [[a,b],[c,d]] (rows = arm G, M; cols = yes, no). Two-sided: sum of P(tables) <= P(observed)."""
    r1, c1, n = a + b, a + c, a + b + c + d
    p_obs = hyper(a, r1, c1, n)
    support = range(max(0, c1 - (n - r1)), min(r1, c1) + 1)
    return min(1.0, sum(p for p in (hyper(x, r1, c1, n) for x in support) if p <= p_obs * (1 + 1e-7)))


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def row(assignment, usage, score):
    u = usage.get(score["run_id"], {})
    return {"runId": score["run_id"], "arm": assignment[score["run_id"]]["arm"],
            "batch": assignment[score["run_id"]]["batch"], "excluded": u.get("excluded"),
            "accepted": score["accepted"], "trap_violations": score["trap_violations"],
            "trap_compliant": score["trap_compliant"], "any_violation": score["trap_violations"] > 0,
            "traps": {t: v["violated"] for t, v in score["traps"].items()},
            "questions_md": score["questions_md"], "evidence_md": score["evidence_md"],
            "own_tests_pass": score["own_tests"]["passed"], "own_tests_run": score["own_tests"]["tests_run"],
            "total_tokens": u.get("total_tokens"), "tool_uses": u.get("tool_uses"),
            "wall_s": None if u.get("duration_ms") is None else u["duration_ms"] / 1000, "model": u.get("model")}


def compare(rows, key):
    g = [r[key] for r in rows if r["arm"] == "G" and r[key] is not None]
    m = [r[key] for r in rows if r["arm"] == "M" and r[key] is not None]
    if not g or not m:
        return {"n_G": len(g), "n_M": len(m), "p": None, "note": "missing data"}
    return {"n_G": len(g), "n_M": len(m), "mean_G": mean(g), "mean_M": mean(m), "diff_G_minus_M": mean(g) - mean(m),
            "values_G": g, "values_M": m, "test": "exact permutation, |mean diff|, two-sided",
            "p": perm_test(g, m)}


def compare_bin(rows, key):
    g = [bool(r[key]) for r in rows if r["arm"] == "G"]
    m = [bool(r[key]) for r in rows if r["arm"] == "M"]
    a, b, c, d = sum(g), len(g) - sum(g), sum(m), len(m) - sum(m)
    return {"table_G_yes_no_M_yes_no": [a, b, c, d], "test": "Fisher exact, two-sided",
            "p": fisher_two_sided(a, b, c, d) if g and m else None}


def analyze(assignment, usage, scores):
    a = {r["runId"]: r for r in assignment["runs"]}
    rows_all = [row(a, usage, s) for s in scores]
    rows = [r for r in rows_all if not r["excluded"]]
    primary = {h: {"outcome": k, **compare(rows, k)} for h, k in PRIMARY}
    ps = [primary[h]["p"] for h, _ in PRIMARY]
    if all(p is not None for p in ps):
        for (h, _), q in zip(PRIMARY, holm(ps)):
            primary[h]["p_holm_H1_H3"] = q
    traps = {t: {arm: sum(1 for r in rows if r["arm"] == arm and r["traps"].get(t)) for arm in "GM"}
             for t in ("T1", "T2", "T3")}
    return {"experiment": "SPR-D2-01", "power_class": "EXPLORATORY-POWERED (n=4 per arm): pilot estimate only",
            "runs": rows_all, "n_included": {arm: sum(1 for r in rows if r["arm"] == arm) for arm in "GM"},
            "primary": primary,
            "secondary": {**{k: compare(rows, k) for k in SECONDARY_CONT},
                          **{k: compare_bin(rows, k) for k in SECONDARY_BIN}},
            "per_trap_runs_violating": traps,
            "min_attainable_two_sided_p": 2 / math.comb(len(rows), sum(1 for r in rows if r["arm"] == "G"))
            if rows else None}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    print(json.dumps(analyze(load(sys.argv[1]), load(sys.argv[2]), [load(p) for p in sys.argv[3:]]), indent=1))
