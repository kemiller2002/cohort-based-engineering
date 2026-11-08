"""Primary + secondary statistics from V4 scores + usage.json. Usage: analyze.py V4SCORES OUT"""
import json
import sys
from fractions import Fraction
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats  # noqa: E402

X02 = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment/spr-x-02"


def arms():
    a = json.load(open(f"{X02}/assignment.json"))
    return {r["runId"]: r for r in a["runs"]}


def split(values_by_run, assign, fixture):
    runs = sorted(r for r, x in assign.items() if x["fixture"] == fixture)
    g = [values_by_run[r] for r in runs if assign[r]["arm"] == "G"]
    m = [values_by_run[r] for r in runs if assign[r]["arm"] == "M"]
    return g, m


def fmt(res):
    return {"stat": float(res["stat"]), "stat_exact": str(res["stat"]), "p": float(res["p"]),
            "p_exact": str(res["p"]), "n_extreme": res["n_extreme"], "N": res["N"]}


def main(v4path, out):
    sc = json.load(open(v4path))
    usage = json.load(open(f"{X02}/results/usage.json"))
    asg = arms()
    runs = list(asg)
    outcome = {
        "viol": {r: sc[r]["violations"] for r in runs},
        "acc": {r: sc[r]["accepted"] for r in runs},
        "tok": {r: usage[r]["total_tokens"] for r in runs},
        "wall": {r: Fraction(usage[r]["duration_ms"], 1000) for r in runs},
        "fp": {r: sc[r]["followed_planted"] for r in runs if asg[r]["fixture"] == "D2c"},
        "ctrl": {r: sc[r]["controls_passed"] for r in runs if asg[r]["fixture"] == "D2c"},
    }
    res = {}
    for k in ["viol", "acc", "tok", "wall"]:
        res[k] = fmt(stats.stratified_perm_test([split(outcome[k], asg, "D2b"), split(outcome[k], asg, "D2c")]))
    for k in ["fp", "ctrl"]:
        res[k] = fmt(stats.stratified_perm_test([split(outcome[k], asg, "D2c")]))
    secondary = ["fp", "acc", "ctrl", "tok", "wall"]
    h = stats.holm({k: Fraction(res[k]["p_exact"]) for k in secondary})
    for k in secondary:
        res[k]["p_holm"] = float(h[k])
    groups = {f"{fx}_{arm}": {k: [float(v) for v in split(outcome[k], asg, fx)[0 if arm == "G" else 1]]
                              for k in outcome if fx == "D2c" or k not in ("fp", "ctrl")}
              for fx in ("D2b", "D2c") for arm in ("G", "M")}
    means = {g: {k: sum(v) / len(v) for k, v in d.items()} for g, d in groups.items()}
    tok_pct = {fx: means[f"{fx}_G"]["tok"] / means[f"{fx}_M"]["tok"] - 1 for fx in ("D2b", "D2c")}
    wall_pct = {fx: means[f"{fx}_G"]["wall"] / means[f"{fx}_M"]["wall"] - 1 for fx in ("D2b", "D2c")}
    pooled = {k: (sum(sum(groups[f"{fx}_G"][k]) for fx in ("D2b", "D2c")) /
                  sum(sum(groups[f"{fx}_M"][k]) for fx in ("D2b", "D2c")) - 1) for k in ("tok", "wall")}
    result = {"tests": res, "groups": groups, "means": means, "tok_pct_by_fixture": tok_pct,
              "wall_pct_by_fixture": wall_pct, "pooled_pct_G_over_M": pooled}
    json.dump(result, open(out, "w"), indent=1)
    return result


if __name__ == "__main__":
    r = main(sys.argv[1], sys.argv[2])
    print(json.dumps(r["tests"], indent=1))
    print(json.dumps(r["means"], indent=1))
    print(r["tok_pct_by_fixture"], r["wall_pct_by_fixture"], r["pooled_pct_G_over_M"])
