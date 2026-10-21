"""REL-001 run-02 cache-state sensitivity (exploratory; added after a cache-state confound was reported).

For every agent of every confirmatory trial, this reads the first API request's usage from the copied transcript.
A trial counts as a "cold prefix" when any agent's first request wrote more cache than it read.
The warm-cache sensitivity cost reprices each agent's first-request cache write at the cache-read price, as if the
shared prefix had already been cached. It then recomputes pooled cost per correct requirement per arm, without U6 (R8).

Usage: python3 -I cache-sensitivity.py STATE_ROOT OBSERVATIONS_DIR PRICE_TABLE > cache-sensitivity.json
"""
import json, os, sys, glob
from collections import defaultdict

STATE, OBS, PRICES = sys.argv[1:4]
MODEL = "claude-opus-5-5"


def per_mtok(table):
    entry = next(e for e in table["entries"] if e.get("model") == MODEL)
    return {k: entry[k] / 1e6 for k in ("input", "output", "cacheRead", "cacheWrite5m", "cacheWrite1h")}


def first_usage(transcript):
    for line in open(transcript):
        e = json.loads(line)
        u = (e.get("message") or {}).get("usage")
        if e.get("type") == "assistant" and u:
            cc = u.get("cache_creation") or {}
            return {"cacheWrite5m": cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) if not cc else 0),
                    "cacheWrite1h": cc.get("ephemeral_1h_input_tokens", 0),
                    "cacheWrite": u.get("cache_creation_input_tokens", 0),
                    "cacheRead": u.get("cache_read_input_tokens", 0)}
    return None


def trial(obs_path, price):
    obs = json.load(open(obs_path))
    r2 = obs["run02"]
    run_id = os.path.basename(obs_path)[:-5]
    firsts = [u for u in (first_usage(t) for t in sorted(glob.glob(os.path.join(STATE, run_id, "transcripts", "*.jsonl")))) if u]
    cold = any(u["cacheWrite"] > u["cacheRead"] for u in firsts)
    saving = sum(u["cacheWrite5m"] * (price["cacheWrite5m"] - price["cacheRead"]) +
                 u["cacheWrite1h"] * (price["cacheWrite1h"] - price["cacheRead"]) for u in firsts)
    cost = r2["cost"]["estimated"]["value"]
    return {"runId": run_id, "arm": r2["armLetter"], "task": r2["workItem"], "block": r2["block"],
            "agents": len(firsts), "coldPrefix": cold, "firstRequest": firsts,
            "cost": cost, "warmCost": round(cost - saving, 6), "correct": r2["units"]["correct"]}


price = per_mtok(json.load(open(PRICES)))
rows = [trial(p, price) for p in sorted(glob.glob(os.path.join(OBS, "*", "*.json")))
        if not json.load(open(p))["run02"].get("pilot")]
pooled = defaultdict(lambda: {"cost": 0.0, "warmCost": 0.0, "correct": 0, "runs": 0, "coldPrefix": 0})
for r in (r for r in rows if r["task"] != "LEDGER-U6"):
    a = pooled[r["arm"]]
    a["cost"] += r["cost"]; a["warmCost"] += r["warmCost"]; a["correct"] += r["correct"]; a["runs"] += 1; a["coldPrefix"] += r["coldPrefix"]
summary = {k: {**v, "costPerCorrect": round(v["cost"] / v["correct"], 6), "warmCostPerCorrect": round(v["warmCost"] / v["correct"], 6)}
           for k, v in sorted(pooled.items())}
ratio = lambda f, x, y: round(summary[x][f] / summary[y][f] - 1, 6)
print(json.dumps({"label": "exploratory cache-state sensitivity; not preregistered",
                  "price": {k: v * 1e6 for k, v in price.items()},
                  "perArm": summary,
                  "relative": {f"{x} vs {y}": {"asMeasured": ratio("costPerCorrect", x, y), "warmCache": ratio("warmCostPerCorrect", x, y)}
                               for x, y in [("D", "A"), ("D", "C"), ("A", "C"), ("B", "A")]},
                  "coldPrefixByArm": {k: f'{v["coldPrefix"]}/{v["runs"]}' for k, v in summary.items()},
                  "runs": rows}, indent=1, sort_keys=True))
