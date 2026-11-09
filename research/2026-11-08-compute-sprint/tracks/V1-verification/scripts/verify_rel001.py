"""Claim G-F-08: recompute REL-001 run-02 cost per correct requirement per arm from the per-trial
observation token buckets (not from the experiment's cost fields or analysis scripts).
Usage: python3 -I verify_rel001.py OBS_DIR PRICE_TABLE OUT_JSON"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1lib as L  # noqa: E402

KIND = {"input": "input", "output": "output", "cacheRead": "cacheRead", "cacheWrite": "cacheWrite",
        "cacheWrite5m": "cacheWrite5m", "cacheWrite1h": "cacheWrite1h"}


def buckets(obs):
    bk = obs["run02"]["tokens"]["byKind"]
    return {KIND[k]: (bk[k]["value"] or 0) for k in KIND if k in bk}


def trial_row(obs, price):
    b = buckets(obs)
    return {"runId": obs["runId"], "arm": obs["arm"], "task": obs["task"]["taskId"],
            "pilot": obs["run02"].get("pilot"), "label": obs["run02"].get("label"), "status": obs["status"],
            "excluded": obs.get("exclusion") is not None,
            "unitsTotal": obs["run02"]["units"]["total"], "unitsCorrect": obs["run02"]["units"]["correct"],
            "cost": L.price_cost(b, price), "recordedCost": obs["metrics"]["costEstimated"]["value"],
            "tokens": L.total4(b), "output": b.get("output", 0), "outputCost": b.get("output", 0) * price["output"] / 1e6,
            "requests": obs["run02"]["tokens"]["byKind"]["output"].get("denominator") or 0,
            "outputAvailability": obs["run02"]["tokens"]["byKind"]["output"]["availability"]}


def arm_summary(rows):
    c = sum(r["cost"] for r in rows)
    u = sum(r["unitsCorrect"] for r in rows)
    return {"trials": len(rows), "correct": u, "total": sum(r["unitsTotal"] for r in rows),
            "costUSD": round(c, 6), "costPerCorrect": round(c / u, 4) if u else None,
            "tokensPerCorrect": round(sum(r["tokens"] for r in rows) / u) if u else None,
            "maxAbsDiffVsRecordedCost": max(abs(r["cost"] - (r["recordedCost"] or 0)) for r in rows)}


def main(obs_dir, price_path, out):
    price = next(e for e in json.load(open(price_path))["entries"] if e["model"] == "claude-opus-5-5")
    rows = tuple(trial_row(json.load(open(p)), price) for p in sorted(glob.glob(os.path.join(obs_dir, "*", "*.json"))))
    conf = tuple(r for r in rows if not r["pilot"] and r["task"] != "U6" and not r["excluded"])
    arms = sorted({r["arm"] for r in rows})
    res = {a: arm_summary([r for r in conf if r["arm"] == a]) for a in arms}
    bare = res["bare"]["costUSD"] / res["bare"]["correct"]
    opt = res["echelon-optimized"]["costUSD"] / res["echelon-optimized"]["correct"]
    out_d = {"trialsTotal": len(rows), "confirmatoryNonU6": len(conf), "byArm": res,
             "optimizedVsBarePct": round((opt / bare - 1) * 100, 2),
             "outputCostShareByArm": {a: round(sum(r["outputCost"] for r in conf if r["arm"] == a) / sum(r["cost"] for r in conf if r["arm"] == a), 4) for a in arms},
             "meanOutputTokensPerRequestByArm": {a: round(sum(r["output"] for r in conf if r["arm"] == a) / max(1, sum(r["requests"] for r in conf if r["arm"] == a)), 1) for a in arms},
             "outputAvailabilityCounts": {k: sum(1 for r in conf if r["outputAvailability"] == k) for k in {r["outputAvailability"] for r in conf}}}
    json.dump(dict(out_d, rows=rows), open(out, "w"), indent=1)
    print(json.dumps(out_d, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
