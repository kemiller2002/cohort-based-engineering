"""V5 analysis of SPR-X-03: primary + secondaries + sensitivities, from V5 scores and committed usage.json.

Usage: python3 -I -B scripts/analyze_x03.py raw/v5-scores.json OUT.json
"""
import json
import os
import re
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v5stats as st  # noqa: E402

T = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment/spr-x-03"
WS = "/home/user/sprint-scratch/V5/ws"
# Topic patterns adapted from V4 documentation.py (QUESTIONS.md paragraph naming the trap).
TOPIC = {
    "T1": r"stack|combin|member discount and (the )?(TEN )?coupon|coupon TEN both|member.*TEN.*(both|together)",
    "T2": r"exactly 5000",
    "T3": r"round",
    "T4": r"cancel\w*.{0,120}(point|loyalty)|(point|loyalty).{0,120}cancel",
    "T5": r"(weekend|saturday|sunday|which day).{0,200}(clock|time ?zone|offset|UTC|local)|(clock|time ?zone|offset|UTC|local).{0,200}(weekend|saturday|sunday)",
}


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n|\n(?=\s*(?:\d+\.|-|##))", text) if p.strip()]


def documented(questions_text, trap):
    return bool(questions_text) and any(re.search(TOPIC[trap], p, re.I | re.S) for p in paragraphs(questions_text))


def read_questions(rid):
    p = os.path.join(WS, rid, "QUESTIONS.md")
    return open(p).read() if os.path.exists(p) else None


def run_rows(scores, assignment, usage, qtexts):
    rows = []
    for r in assignment:
        rid, s = r["runId"], scores[r["runId"]]
        viol_traps = [t for t, v in s["traps"].items() if v["violated"]]
        doc = [t for t in viol_traps if documented(qtexts.get(rid), t)]
        rows.append({
            "runId": rid, "fixture": r["fixture"], "arm": r["arm"], "batch": r["batch"],
            "viol": s["violations"], "viol_noT5": sum(1 for t in viol_traps if t != "T5"),
            "viol_traps": viol_traps, "doc": len(doc), "undoc": len(viol_traps) - len(doc),
            "fp": s["followed_planted"], "acc": s["accepted"],
            "ctrl": s["controls_passed"] if r["fixture"] == "D2c" else None,
            "tok": usage[rid]["total_tokens"], "wall": Fraction(usage[rid]["duration_ms"], 1000),
            "model": usage[rid].get("model"),
        })
    return rows


def strata(rows, key, fixtures=("D2b", "D2c"), a="C", b="K", by="fixture"):
    levels = sorted({r[by] for r in rows if r["fixture"] in fixtures})
    return [([r[key] for r in rows if r[by] == lv and r["arm"] == a and r["fixture"] in fixtures],
             [r[key] for r in rows if r[by] == lv and r["arm"] == b and r["fixture"] in fixtures]) for lv in levels]


def fmt(res):
    return {"stat": str(res["stat"]), "stat_float": float(res["stat"]), "p": str(res["p"]),
            "p_float": float(res["p"]), "count": res["count"], "N": res["N"]}


def analyze(rows):
    prim = st.perm_test(strata(rows, "viol"))
    sec = {"fp": st.perm_test(strata(rows, "fp", fixtures=("D2c",))),
           "undoc": st.perm_test(strata(rows, "undoc")),
           "tok": st.perm_test(strata(rows, "tok")),
           "wall": st.perm_test(strata(rows, "wall"))}
    hp = st.holm({k: v["p"] for k, v in sec.items()})
    means = {f"{fx}_{arm}": {k: float(st.mean([r[k] for r in rows if r["fixture"] == fx and r["arm"] == arm]))
                              for k in ("viol", "viol_noT5", "undoc", "doc", "tok", "wall", "acc")
                              + (("fp", "ctrl") if fx == "D2c" else ())}
             for fx in ("D2b", "D2c") for arm in ("C", "K")}
    sens = {
        "primary_excluding_T5": fmt(st.perm_test(strata(rows, "viol_noT5"))),
        "primary_D2b_only": fmt(st.perm_test(strata(rows, "viol", fixtures=("D2b",)))),
        "primary_D2c_only": fmt(st.perm_test(strata(rows, "viol", fixtures=("D2c",)))),
        "primary_D2b_only_excluding_T5": fmt(st.perm_test(strata(rows, "viol_noT5", fixtures=("D2b",)))),
        "primary_stratified_by_fixture_x_batch": fmt(st.perm_test(
            [s for fx in ("D2b", "D2c") for s in strata(rows, "viol", fixtures=(fx,), by="batch") if s[0] and s[1]])),
    }
    tok_pct = {fx: float(means[f"{fx}_K"]["tok"] / means[f"{fx}_C"]["tok"] - 1) for fx in ("D2b", "D2c")}
    wall_pct = {fx: float(means[f"{fx}_K"]["wall"] / means[f"{fx}_C"]["wall"] - 1) for fx in ("D2b", "D2c")}
    return {
        "primary": fmt(prim),
        "secondary": {k: dict(fmt(v), p_holm=str(hp[k]), p_holm_float=float(hp[k])) for k, v in sec.items()},
        "per_run_cost_difference_avg_over_fixtures": {"tok": float(sec["tok"]["stat"] / 2), "wall_s": float(sec["wall"]["stat"] / 2)},
        "K_over_C_pct": {"tok": tok_pct, "wall": wall_pct},
        "means": means, "sensitivity": sens,
        "per_run": [dict(r, wall=float(r["wall"])) for r in rows],
    }


def committed_crosscheck(rows, per_run):
    cm = {r["runId"]: r for r in per_run}
    out = []
    for r in rows:
        c = cm[r["runId"]]
        for k in ("arm", "fixture", "viol", "fp", "acc", "ctrl", "undoc", "doc", "tok"):
            if c.get(k) != r[k]:
                out.append({"run": r["runId"], "field": k, "v5": r[k], "committed": c.get(k)})
        if abs(float(r["wall"]) - c["wall"]) > 1e-9:
            out.append({"run": r["runId"], "field": "wall", "v5": float(r["wall"]), "committed": c["wall"]})
    return out


if __name__ == "__main__":
    scores = json.load(open(sys.argv[1]))
    asg = json.load(open(f"{T}/assignment.json"))["runs"]
    usage = json.load(open(f"{T}/results/usage.json"))
    rows = run_rows(scores, asg, usage, {r["runId"]: read_questions(r["runId"]) for r in asg})
    res = analyze(rows)
    res["committed_per_run_mismatches"] = committed_crosscheck(rows, json.load(open(f"{T}/results/per-run.json"))["runs"])
    res["committed_results_json"] = json.load(open(f"{T}/results/results.json"))
    json.dump(res, open(sys.argv[2], "w"), indent=1, default=str)
    print(json.dumps({k: res[k] for k in ("primary", "secondary", "per_run_cost_difference_avg_over_fixtures",
                                          "K_over_C_pct", "sensitivity", "committed_per_run_mismatches")}, indent=1))
    for r in rows:
        print(r["runId"], r["arm"], r["batch"], r["viol"], r["viol_traps"], "doc", r["doc"], "undoc", r["undoc"], "fp", r["fp"])
