"""Compare V4 scores with committed scores (per run, per trap). Usage: compare.py V4SCORES OUT"""
import json
import os
import sys

T = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment"
VIOLATING = {"violated", "documented"}  # committed categories where code did not raise NotSpecified


def committed_path(rid):
    p = f"{T}/spr-x-02/results/scores/{rid}.json"
    return p if os.path.exists(p) else f"{T}/spr-x-01/results/scores/{rid}.json"


def compare_run(rid, mine, theirs):
    traps = {t: {"v4": mine["traps"][t]["violated"], "committed": theirs["traps"][t]["category"] in VIOLATING,
                 "committed_category": theirs["traps"][t]["category"], "v4_category": mine["traps"][t]["category"],
                 "v4_value": mine["traps"][t]["primary_value"]}
             for t in mine["traps"]}
    for t in traps.values():
        t["agree"] = t["v4"] == t["committed"]
    fields = {"accepted": (mine["accepted"], theirs["accepted"]),
              "violations": (mine["violations"], theirs["trap_violations"]),
              "controls_passed": (mine["controls_passed"] if mine["controls"] else None, theirs.get("controls_passed")),
              "followed_planted": (mine["followed_planted"], theirs.get("followed_planted"))}
    fpt = {t: (mine["followed_planted_detail"][t], theirs["traps"][t].get("followed_planted"))
           for t in (mine["followed_planted_detail"] or {})}
    return {"run": rid, "fields": fields, "fields_agree": all(a == b for a, b in fields.values()),
            "traps": traps, "traps_agree": all(t["agree"] for t in traps.values()),
            "fp_per_trap": fpt, "fp_per_trap_agree": all(a == b for a, b in fpt.values())}


def main(v4path, out):
    mine = json.load(open(v4path))
    res = [compare_run(rid, mine[rid], json.load(open(committed_path(rid)))) for rid in sorted(mine)]
    summary = {"runs": len(res), "runs_fields_agree": sum(r["fields_agree"] for r in res),
               "trap_cells": sum(len(r["traps"]) for r in res),
               "trap_cells_agree": sum(t["agree"] for r in res for t in r["traps"].values()),
               "fp_cells": sum(len(r["fp_per_trap"]) for r in res),
               "fp_cells_agree": sum(r["fp_per_trap_agree"] * len(r["fp_per_trap"]) for r in res),
               "disagreements": [r for r in res if not (r["fields_agree"] and r["traps_agree"] and r["fp_per_trap_agree"])]}
    json.dump({"summary": summary, "per_run": res}, open(out, "w"), indent=1)
    return summary


if __name__ == "__main__":
    s = main(sys.argv[1], sys.argv[2])
    print(json.dumps({k: v for k, v in s.items() if k != "disagreements"}), "disagreements:", len(s["disagreements"]))
    for r in s["disagreements"]:
        print(json.dumps(r)[:600])
