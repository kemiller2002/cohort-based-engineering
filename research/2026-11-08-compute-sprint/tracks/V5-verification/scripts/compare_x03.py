"""Compare V5 (V4-oracle) scores with committed spr-x-03/results/scores/*.json. Pure core + thin IO edge.

Usage: python3 -I -B scripts/compare_x03.py raw/v5-scores.json COMMITTED_SCORES_DIR OUT.json
"""
import json
import os
import sys


def committed_cells(c):
    traps = c.get("traps", {})
    return {
        "viol": c.get("trap_violations"),
        "acc": c.get("accepted"),
        "ctrl": c.get("controls_passed"),
        "fp": c.get("followed_planted"),
        "trap_violated": {t: v.get("violated_raised_measure") for t, v in traps.items()},
        "planted": {t: v.get("followed_planted") for t, v in traps.items() if "followed_planted" in v},
    }


def v5_cells(s):
    return {
        "viol": s["violations"],
        "acc": s["accepted"],
        "ctrl": s["controls_passed"] if s["fixture"] == "D2c" else None,
        "fp": s["followed_planted"],
        "trap_violated": {t: v["violated"] for t, v in s["traps"].items()},
        "planted": dict(s["followed_planted_detail"] or {}),
    }


def diff_run(mine, theirs):
    out = []
    for k in ("viol", "acc", "ctrl", "fp"):
        if mine[k] != theirs[k]:
            out.append({"field": k, "v5": mine[k], "committed": theirs[k]})
    for fld in ("trap_violated", "planted"):
        for t in sorted(set(mine[fld]) | set(theirs[fld])):
            if mine[fld].get(t) != theirs[fld].get(t):
                out.append({"field": f"{fld}.{t}", "v5": mine[fld].get(t), "committed": theirs[fld].get(t)})
    return out


def compare(v5_scores, committed):
    per = {rid: diff_run(v5_cells(v5_scores[rid]), committed_cells(committed[rid])) for rid in sorted(v5_scores)}
    n_trap = sum(len(v5_scores[r]["traps"]) for r in v5_scores)
    n_planted = sum(len(v5_scores[r]["followed_planted_detail"] or {}) for r in v5_scores)
    bad = {r: d for r, d in per.items() if d}
    return {
        "runs": len(per),
        "runs_agree_all_fields": len(per) - len(bad),
        "trap_cells": n_trap,
        "trap_cells_agree": n_trap - sum(1 for d in bad.values() for x in d if x["field"].startswith("trap_violated")),
        "planted_cells": n_planted,
        "planted_cells_agree": n_planted - sum(1 for d in bad.values() for x in d if x["field"].startswith("planted")),
        "disagreements": bad,
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        v5 = json.load(f)
    committed = {}
    for rid in v5:
        with open(os.path.join(sys.argv[2], f"{rid}.json")) as f:
            committed[rid] = json.load(f)
    res = compare(v5, committed)
    with open(sys.argv[3], "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(json.dumps({k: v for k, v in res.items() if k != "disagreements"}), res["disagreements"])
