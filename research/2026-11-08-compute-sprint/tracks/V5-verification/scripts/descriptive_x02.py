"""Descriptive (NOT randomized) comparison of X-03 arms C/K with X-02 arms G/M. Usage: descriptive_x02.py raw/v5-stats.json OUT.json

X-02 per-run data: committed spr-x-02/results/per-run.json (V4 verified its violations 28/28) cross-checked against V4's raw scores.
Unadjusted exact two-group permutation p values are reported as context only.
"""
import json
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v5stats as st  # noqa: E402

T = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment"
V4SCORES = "/home/user/sprint-wt/V4-verification/research/2026-11-08-compute-sprint/tracks/V4-verification/raw/v4-scores.json"


def table(runs):
    keys = ("viol", "tok", "wall")
    groups = {}
    for r in runs:
        groups.setdefault((r["fixture"], r["arm"]), []).append(r)
    return {f"{fx}_{arm}": dict({k: float(st.mean([x[k] for x in rs])) for k in keys}, n=len(rs),
                                per_run_viol=[x["viol"] for x in rs])
            for (fx, arm), rs in sorted(groups.items())}


def contrast(runs, key, a, b, fixtures):
    """Exact unadjusted permutation (stratified by fixture) of mean(b)-mean(a); a/b are arm labels."""
    strata = [([r[key] for r in runs if r["fixture"] == fx and r["arm"] == a],
               [r[key] for r in runs if r["fixture"] == fx and r["arm"] == b]) for fx in fixtures]
    res = st.perm_test(strata)
    return {"stat_sum_of_mean_diffs": float(res["stat"]), "p_unadjusted": float(res["p"]), "p_exact": str(res["p"])}


def build(x03_rows, x02_rows):
    runs = x03_rows + x02_rows
    both = ("D2b", "D2c")
    return {
        "means": table(runs),
        "contrasts_descriptive": {
            "C_vs_G_viol (G-C)": contrast(runs, "viol", "C", "G", both),
            "C_vs_G_viol_D2b": contrast(runs, "viol", "C", "G", ("D2b",)),
            "C_vs_G_viol_D2c": contrast(runs, "viol", "C", "G", ("D2c",)),
            "C_vs_M_tok (M-C)": contrast(runs, "tok", "C", "M", both),
            "C_vs_M_wall (M-C)": contrast(runs, "wall", "C", "M", both),
            "C_vs_M_viol (M-C)": contrast(runs, "viol", "C", "M", both),
            "K_vs_M_viol_D2b (K-M)": contrast(runs, "viol", "M", "K", ("D2b",)),
            "K_vs_M_viol_D2c (K-M)": contrast(runs, "viol", "M", "K", ("D2c",)),
            "K_vs_G_tok (G-K)": contrast(runs, "tok", "K", "G", both),
            "K_vs_G_wall (G-K)": contrast(runs, "wall", "K", "G", both),
        },
    }


if __name__ == "__main__":
    x03 = [dict(r, wall=Fraction(str(r["wall"]))) for r in json.load(open(sys.argv[1]))["per_run"]]
    x02 = json.load(open(f"{T}/spr-x-02/results/per-run.json"))["runs"]
    v4 = json.load(open(V4SCORES))
    v4_mismatch = [r["runId"] for r in x02 if v4[r["runId"]]["violations"] != r["viol"]]
    x02 = [{"runId": r["runId"], "arm": r["arm"], "fixture": r["fixture"], "viol": r["viol"], "tok": r["tok"],
            "wall": Fraction(str(r["wall"]))} for r in x02]
    x03 = [{k: r[k] for k in ("runId", "arm", "fixture", "viol", "tok", "wall")} for r in x03]
    res = build(x03, x02)
    res["x02_viol_vs_v4_oracle_mismatches"] = v4_mismatch
    json.dump(res, open(sys.argv[2], "w"), indent=1)
    print(json.dumps(res, indent=1))
