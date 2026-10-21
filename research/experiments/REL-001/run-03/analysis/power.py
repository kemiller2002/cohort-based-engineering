#!/usr/bin/env python3
"""REL-001 run-03 sample-size justification from the run-01 EXPLORATORY pilot (Experiment D, 6 paired blocks).

usage: python3 -I power.py RUN01_OBSERVATIONS_DIR PRICE_TABLE [OUT.json]
  e.g. python3 -I power.py ../../observations ../pricing/anthropic.price-table.json power.json

Label: PILOT ESTIMATE. run-01 had two arms (baseline Praxis 3.12.0, treatment 3.16.0), three routine tasks and
no failures, so its variance is a floor for run-03's, not an estimate of it. The script:
  1. prices each run-01 observation with the run-03 price table (cache writes at the 5-minute rate: run-01 did not
     split them), and forms the paired log ratio of cost per verified requirement for each (task, replicate) block;
  2. takes its standard deviation sigma (and the same for tokens);
  3. gives the blocks needed for a two-sided 5% test with 80% power, n = ((1.96 + 0.8416) * s / ln(1 + delta))^2,
     for minimum detectable ratios of 20%, 25%, 30% and 50%, with s = sigma and s = 1.5 sigma (inflation for
     run-03's heterogeneous tasks and failures), and the minimum detectable ratio at run-03's 24 blocks.
The normal approximation stands in for the paired bootstrap of a ratio of sums; it is a planning number only.
"""
import glob
import json
import math
import os
import re
import statistics
import sys

Z = 1.959964 + 0.841621
KINDS = {"tokensInput": "input", "tokensOutput": "output", "tokensCacheRead": "cacheRead", "tokensCacheWrite": "cacheWrite5m"}


def load(directory, price):
    def one(path):
        d = json.load(open(path))
        m = d["metrics"]
        cost = sum(m[k]["value"] * price[v] for k, v in KINDS.items()) / 1e6
        task, rep = re.search(r"-(T\d)-(r\d)-", d["runId"]).groups()
        return (task, rep), {"arm": d["arm"], "cost": cost, "tokens": m["tokensTotal"]["value"], "verified": m["verifiedRequirements"]["value"]}
    return [one(p) for p in sorted(glob.glob(os.path.join(directory, "*", "*.json")))]


def main(argv):
    obs_dir, table = argv[1], argv[2]
    out = argv[3] if len(argv) > 3 else None
    price = json.load(open(table))["entries"][0]
    rows = load(obs_dir, price)
    blocks = sorted({k for k, _ in rows})
    arm = lambda k, a: next(r for kk, r in rows if kk == k and r["arm"] == a)
    def log_ratios(key):
        return [math.log((arm(k, "treatment")[key] / arm(k, "treatment")["verified"]) / (arm(k, "baseline")[key] / arm(k, "baseline")["verified"])) for k in blocks]
    sig = {key: statistics.stdev(log_ratios(key)) for key in ("cost", "tokens")}
    need = lambda s, d: math.ceil((Z * s / math.log(1 + d)) ** 2)
    mdr = lambda s, n: math.exp(Z * s / math.sqrt(n)) - 1
    result = {
        "label": "PILOT ESTIMATE from run-01 Experiment D (exploratory; 2 arms, 3 routine tasks, no failures); planning only",
        "pilotBlocks": len(blocks), "priceTableVersion": json.load(open(table))["tableVersion"],
        "pairedLogRatioMean": {k: round(statistics.mean(log_ratios(k)), 6) for k in sig},
        "pairedLogRatioSd": {k: round(v, 6) for k, v in sig.items()},
        "blocksNeeded": {f"sigma x{f}": {f"{int(d * 100)}%": need(sig["cost"] * f, d) for d in (0.2, 0.25, 0.3, 0.5)} for f in (1.0, 1.5)},
        "minimumDetectableRatioAt24Blocks": {f"sigma x{f}": round(mdr(sig["cost"] * f, 24), 6) for f in (1.0, 1.5)},
        "assumptions": "two-sided alpha 0.05, power 0.8, normal approximation on paired log ratios of cost per verified requirement"}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if out:
        open(out, "w").write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv)
