#!/usr/bin/env python3
"""Frozen analysis for SPR-D-03..05 (see protocols/COMMON.md).

Usage: analyze_bench.py RAW.jsonl TREATMENT REFERENCE THRESHOLD SIDE [--no-exit]
SIDE is 'below' (H: ratio < THRESHOLD) or 'above' (H: ratio > THRESHOLD). --no-exit keeps runs with non-zero exit (test experiments).
"""
from __future__ import annotations

import itertools
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reanalysis"))
import stats  # noqa: E402
from bench import median  # noqa: E402

SEED = 20261108


def cpu(r):
    return r["cpuUserS"] + r["cpuSysS"]


def ratio_of_medians_ci(t, ref, n=10000, seed=SEED):
    rng = random.Random(seed)
    draws = sorted(median([rng.choice(t) for _ in t]) / median([rng.choice(ref) for _ in ref]) for _ in range(n))
    return median(t) / median(ref), [stats.percentile(draws, 0.025), stats.percentile(draws, 0.975)]


def permutation_p(t, ref):
    """Exact two-sided permutation test on the difference in means."""
    pooled = list(t) + list(ref)
    k = len(t)
    obs = abs(sum(t) / k - sum(ref) / len(ref))
    total = hits = 0
    for idx in itertools.combinations(range(len(pooled)), k):
        s = set(idx)
        a = [pooled[i] for i in s]
        b = [pooled[i] for i in range(len(pooled)) if i not in s]
        total += 1
        hits += abs(sum(a) / len(a) - sum(b) / len(b)) >= obs - 1e-12
    return hits / total


def decide(ci, threshold, side):
    lo, hi = ci
    if side == "below":
        return "SUPPORTED" if hi < threshold else "CONTRADICTED" if lo > threshold else "INCONCLUSIVE"
    return "SUPPORTED" if lo > threshold else "CONTRADICTED" if hi < threshold else "INCONCLUSIVE"


def analyze(records, treatment, reference, threshold, side, use_exit=True):
    keep = [r for r in records if (r["exit"] == 0 or not use_exit)]
    excluded = [r["seq"] for r in records if r not in keep]
    out = {"treatment": treatment, "reference": reference, "threshold": threshold, "side": side, "excludedSeq": excluded}
    for name, f in (("cpuS", cpu), ("wallS", lambda r: r["wallS"])):
        t = [f(r) for r in keep if r["arm"] == treatment]
        ref = [f(r) for r in keep if r["arm"] == reference]
        point, ci = ratio_of_medians_ci(t, ref)
        out[name] = {"n": [len(t), len(ref)], "medianTreatment": median(t), "medianReference": median(ref),
                     "ratioOfMedians": point, "ci95": ci, "permutationP": permutation_p(t, ref),
                     "valuesTreatment": t, "valuesReference": ref}
    out["decisionPrimaryCpu"] = decide(out["cpuS"]["ci95"], threshold, side)
    out["loadavgRange"] = [min(r["loadavg1Before"] for r in records), max(r["loadavg1Before"] for r in records)]
    counts = {}
    for r in records:
        if r.get("testCounts"):
            counts.setdefault(r["arm"], set()).add(json.dumps(r["testCounts"], sort_keys=True))
    out["testCountsByArm"] = {a: sorted(v) for a, v in counts.items()}
    return out


def main(argv):
    path, t, ref, thr, side = argv[1:6]
    recs = [json.loads(l) for l in open(path) if l.strip()]
    res = analyze(recs, t, ref, float(thr), side, use_exit="--no-exit" not in argv)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
