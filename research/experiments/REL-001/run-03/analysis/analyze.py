#!/usr/bin/env python3
"""REL-001 run-03 preregistered analysis (protocol/run-03.md: primary outcome, H1-H6, exclusions X1-X6).

usage: python3 -I analyze.py [OBSERVATIONS_DIR] [OUT.json] [--include-smoke]
  defaults: run-03/observations and run-03/analysis/results.json. --include-smoke is for selftest.py only.

Reads every OBSERVATIONS_DIR/**/*.json carrying a run03 block. Pilot and smoke observations are ignored; X4 runs
are excluded; a block with an X2 run leaves the paired comparisons that involve that arm; a missing metric
excludes a run only from the comparisons that need that metric (X3, as run-02 fixed it). X5 runs count as
failed (their cost stays in the numerator). Deterministic: paired percentile bootstrap over (task, replicate)
blocks, 10,000 resamples, seed 20261021, one splitmix64 stream per comparison; keys sorted, numbers rounded to
6 decimals, so identical inputs give byte-identical output. Standard library only. Functional style.
"""
import hashlib
import json
import math
import os
import sys
from functools import reduce

SEED = 20261021
RESAMPLES = 10_000
ARMS = ["A", "B", "C", "D"]
CATEGORIES = ["simple", "moderate", "complex", "adversarial"]
CONFLICT_TASKS = {"V7"}
TRAP_TASKS = {"V3", "V4", "V5", "V6", "V8"}   # tasks with a plausible wrong solution that passes the visible tests
MASK = (1 << 64) - 1


# ------------------------------------------------------------------ deterministic PRNG (splitmix64)
def stream(name):
    state = (SEED ^ int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")) & MASK
    def gen():
        nonlocal state
        while True:
            state = (state + 0x9E3779B97F4A7C15) & MASK
            z = state
            z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
            z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
            yield z ^ (z >> 31)
    return gen()


def resample_indices(name, n):
    g = stream(name)
    return [[next(g) % n for _ in range(n)] for _ in range(RESAMPLES)]


# ------------------------------------------------------------------ input
def get(d, *path, default=None):
    return reduce(lambda acc, k: acc.get(k) if isinstance(acc, dict) else None, path, d) if d is not None else default


def metric_value(obs, *path):
    m = get(obs, *path)
    return m.get("value") if isinstance(m, dict) and m.get("availability") in ("available", "partial") else None


def parse(obs):
    r = obs["run03"]
    return {
        "runId": obs["runId"], "supersedes": obs.get("supersedes"), "arm": r["armLetter"], "task": obs["task"]["taskId"],
        "category": r["category"], "block": r["block"], "label": r["label"], "dryRun": r.get("dryRun", False),
        "excluded": obs["status"] == "excluded" or bool(get(r, "exclusions", "x4", "contaminated")),
        "paired": bool(get(r, "eligibility", "pairedComparisons")), "eligible": r.get("eligibility") or {},
        "units": get(r, "units", "total") or 0, "correct": get(r, "units", "correct"),
        "recorded": bool(get(r, "completionEvidence", "recorded")),
        "cost": metric_value(obs, "metrics", "costEstimated"), "tokens": metric_value(obs, "metrics", "tokensTotal"),
        "tokensExcl": metric_value(r, "tokens", "excludingCacheReads"), "coldCost": get(r, "cost", "coldEquivalentUsd"),
        "wallMs": r.get("wallMs"), "toolCalls": r.get("toolCalls"), "testRuns": get(r, "tests", "total"),
        "testMs": (get(r, "tests", "computeMs") or 0), "invalid": get(r, "reliability", "invalidCompletionsAccepted"),
        "escaped": get(r, "reliability", "escapedDefects"), "firstPass": r.get("firstPassCorrect"),
        "timedOut": bool(get(r, "exclusions", "x5", "budgetExceeded")), "tampered": bool(get(r, "exclusions", "x6", "tampered")),
        "coldFirst": get(obs, "cache", "measured", "firstRequestCold"), "cacheShare": get(obs, "cache", "measured", "cacheReadShare"),
        "cacheCondition": get(obs, "cache", "condition")}


def load(directory, include_smoke):
    files = sorted((os.path.join(d, f) for d, _, fs in os.walk(directory) for f in fs if f.endswith(".json")), key=lambda s: s.encode())
    docs = [json.load(open(f)) for f in files]
    runs = [parse(d) for d in docs if isinstance(d, dict) and "run03" in d]
    wanted = [r for r in runs if r["label"] == "trial" or (include_smoke and r["label"] == "smoke")]
    superseded = {r["supersedes"] for r in wanted if r["supersedes"]}
    kept = [r for r in wanted if r["runId"] not in superseded]
    by_key = {}
    for r in sorted(kept, key=lambda r: r["runId"]):
        by_key.setdefault((r["block"], r["arm"]), []).append(r)
    duplicates = sorted(f"{b}/{a}" for (b, a), rs in by_key.items() if len(rs) > 1)
    return {k: rs[-1] for k, rs in by_key.items()}, len(files), len(runs), duplicates


# ------------------------------------------------------------------ statistics
def rnd(x):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, 6)


def percentile(sorted_xs, q):
    if not sorted_xs:
        return None
    pos = q * (len(sorted_xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def ratio_of_sums(pairs, num_key, den_key):
    """pairs: [(x_run, y_run)]; returns (x pooled num/den, y pooled num/den) or None when a denominator is 0."""
    sx_n, sx_d = sum(p[0][num_key] for p in pairs), sum(p[0][den_key] for p in pairs)
    sy_n, sy_d = sum(p[1][num_key] for p in pairs), sum(p[1][den_key] for p in pairs)
    return (sx_n / sx_d if sx_d else None, sy_n / sy_d if sy_d else None)


def bootstrap(name, pairs, stat):
    """Paired percentile bootstrap of stat(pairs) -> float or None; returns estimate, 95% interval, two-sided p for 0."""
    point = stat(pairs)
    if not pairs or point is None:
        return {"estimate": rnd(point), "ci95": None, "p": None, "undefinedResamples": None, "blocks": len(pairs)}
    draws = [stat([pairs[i] for i in idx]) for idx in resample_indices(name, len(pairs))]
    defined = sorted(d for d in draws if d is not None)
    undefined = len(draws) - len(defined)
    p = min(1.0, 2 * min(sum(d <= 0 for d in defined), sum(d >= 0 for d in defined)) / len(defined)) if defined else None
    return {"estimate": rnd(point), "ci95": [rnd(percentile(defined, 0.025)), rnd(percentile(defined, 0.975))] if defined else None,
            "p": rnd(p), "undefinedResamples": undefined, "blocks": len(pairs)}


def relative(num_key, den_key):
    def stat(pairs):
        x, y = ratio_of_sums(pairs, num_key, den_key)
        return None if x is None or y is None or y == 0 else x / y - 1
    return stat


def difference_of_rates(num_key, den_key):
    def stat(pairs):
        x, y = ratio_of_sums(pairs, num_key, den_key)
        return None if x is None or y is None else x - y
    return stat


def holm(ps):
    """ps: {name: p or None} -> adjusted p (Holm step-down), None stays None."""
    known = sorted(((p, n) for n, p in ps.items() if p is not None), key=lambda t: (t[0], t[1]))
    m = len(known)
    adjusted, running = {}, 0.0
    for i, (p, n) in enumerate(known):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[n] = rnd(running)
    return {n: adjusted.get(n) for n in ps}


# ------------------------------------------------------------------ comparisons with X3 eligibility
def usable(run, metric):
    return run is not None and not run["excluded"] and run["paired"] and run["correct"] is not None \
        and run["eligible"].get("correct", False) and (metric is None or run["eligible"].get(metric, False))


def paired(runs, x, y, metric, blocks):
    return [(runs[(b, x)], runs[(b, y)]) for b in blocks
            if usable(runs.get((b, x)), metric) and usable(runs.get((b, y)), metric)]


def compare(runs, name, x, y, metric_key, eligibility_key, blocks):
    pairs = paired(runs, x, y, eligibility_key, blocks)
    res = bootstrap(name, pairs, relative(metric_key, "correct"))
    sx, sy = ratio_of_sums(pairs, metric_key, "correct") if pairs else (None, None)
    return {**res, "comparison": f"{x} vs {y}", "pooledPerVerifiedRequirement": {x: rnd(sx), y: rnd(sy)},
            "decision": decision(res)}


def decision(res):
    ci = res.get("ci95")
    if not ci or None in ci:
        return "not evaluable"
    if res.get("undefinedResamples", 0) > RESAMPLES // 100:
        return "inconclusive (more than 1% of resamples undefined)"
    return "first arm lower" if ci[1] < 0 else "first arm higher" if ci[0] > 0 else "not distinguishable"


# ------------------------------------------------------------------ per-arm summaries
def arm_summary(rs):
    scored = [r for r in rs if not r["excluded"] and r["correct"] is not None]
    total = lambda k: sum(r[k] for r in scored if r[k] is not None)
    have = lambda k: sum(1 for r in scored if r[k] is not None)
    cost_runs = [r for r in scored if r["eligible"].get("cost")]
    return {
        "runs": len(rs), "scored": len(scored), "excludedX4": sum(1 for r in rs if r["excluded"]),
        "units": total("units"), "correctUnits": total("correct"),
        "verifiedCompletionRate": rnd(total("correct") / total("units")) if total("units") else None,
        "recordedCompletionRate": rnd(sum(r["recorded"] for r in scored) / len(scored)) if scored else None,
        "fullyCorrectRuns": sum(1 for r in scored if r["correct"] == r["units"]),
        "costTotalUsd": rnd(sum(r["cost"] for r in cost_runs)), "costRuns": len(cost_runs),
        "costPerVerifiedRequirement": rnd(sum(r["cost"] for r in cost_runs) / sum(r["correct"] for r in cost_runs)) if cost_runs and sum(r["correct"] for r in cost_runs) else None,
        "tokensTotal": total("tokens"), "tokensExcludingCacheReads": total("tokensExcl"), "coldEquivalentCostUsd": rnd(total("coldCost")),
        "wallMsTotal": total("wallMs"), "testRuns": total("testRuns"), "testComputeMs": total("testMs"), "toolCalls": total("toolCalls"),
        "metricCoverage": {k: have(k) for k in ("cost", "tokens", "tokensExcl", "coldCost", "wallMs", "toolCalls")},
        "reliability": {"invalidCompletionsAccepted": total("invalid"), "escapedDefects": total("escaped"),
                        "budgetExceededX5": sum(r["timedOut"] for r in scored), "tamperingX6": sum(r["tampered"] for r in scored)},
        "firstPassCorrectRate": rnd(sum(1 for r in scored if r["firstPass"]) / have("firstPass")) if have("firstPass") else None,
        "cache": {"coldFirstRequestRuns": sum(1 for r in scored if r["coldFirst"] is True),
                  "measuredRuns": sum(1 for r in scored if r["coldFirst"] is not None),
                  "meanCacheReadShare": rnd(sum(r["cacheShare"] for r in scored if r["cacheShare"] is not None) / have("cacheShare")) if have("cacheShare") else None,
                  "conditions": sorted({r["cacheCondition"] for r in scored if r["cacheCondition"]})}}


def analyse(runs):
    blocks = sorted({b for b, _ in runs}, key=lambda s: s.encode())
    by_arm = {a: [r for (b, x), r in sorted(runs.items()) if x == a] for a in ARMS}
    cat_of = {r["block"]: r["category"] for r in runs.values()}
    task_of = {r["block"]: r["task"] for r in runs.values()}
    no_conflict = [b for b in blocks if task_of[b] not in CONFLICT_TASKS]
    primary = compare(runs, "H1:D-A:cost", "D", "A", "cost", "cost", blocks)
    secondary = {"H2": compare(runs, "H2:D-C:cost", "D", "C", "cost", "cost", blocks),
                 "H3": compare(runs, "H3:B-A:cost", "B", "A", "cost", "cost", blocks),
                 "H4": compare(runs, "H4:C-A:cost", "C", "A", "cost", "cost", blocks)}
    adjusted = holm({k: v["p"] for k, v in secondary.items()})
    secondary = {k: {**v, "pHolm": adjusted[k], "decisionHolm": ("not distinguishable" if adjusted[k] is None or adjusted[k] >= 0.05 else v["decision"])}
                 for k, v in secondary.items()}
    benefit_pairs = paired(runs, "D", "A", None, blocks)
    trap_pairs = paired(runs, "D", "A", None, [b for b in blocks if task_of[b] in TRAP_TASKS])
    h5 = {"verifiedRequirementRateDifference D-A": bootstrap("H5:D-A:rate", benefit_pairs, difference_of_rates("correct", "units")),
          "trapTasksVerifiedRequirementRateDifference D-A": bootstrap("H5:D-A:trap-rate", trap_pairs, difference_of_rates("correct", "units")),
          "escapedPlusInvalid": {a: sum((r["escaped"] or 0) + (r["invalid"] or 0) for r in by_arm[a] if not r["excluded"] and r["correct"] is not None) for a in ARMS},
          "reliabilityNonInferiority": "D has no more escaped defects and no more invalid completions accepted than C (counts above)"}
    sensitivity = {
        "withoutConflictTask": {f"{x} vs {y}": compare(runs, f"S1:{x}-{y}", x, y, "cost", "cost", no_conflict) for x, y in [("D", "A"), ("D", "C"), ("B", "A"), ("C", "A")]},
        "tokensTotal": {f"{x} vs {y}": compare(runs, f"S2:{x}-{y}", x, y, "tokens", "tokensTotal", blocks) for x, y in [("D", "A"), ("D", "C"), ("B", "A"), ("C", "A")]},
        "tokensExcludingCacheReads": {f"{x} vs {y}": compare(runs, f"S3:{x}-{y}", x, y, "tokensExcl", "tokensExcludingCacheReads", blocks) for x, y in [("D", "A"), ("D", "C")]},
        "coldEquivalentCost": {f"{x} vs {y}": compare(runs, f"S4:{x}-{y}", x, y, "coldCost", "coldEquivalentCost", blocks) for x, y in [("D", "A"), ("D", "C")]}}
    per_category = {c: {"blocks": sum(1 for b in blocks if cat_of[b] == c),
                        "descriptiveOnly": sum(1 for b in blocks if cat_of[b] == c) < 6,
                        "D vs A": compare(runs, f"H6:{c}:D-A", "D", "A", "cost", "cost", [b for b in blocks if cat_of[b] == c]),
                        "arms": {a: arm_summary([r for r in by_arm[a] if r["category"] == c]) for a in ARMS}} for c in CATEGORIES}
    per_task = {t: {a: arm_summary([r for r in by_arm[a] if r["task"] == t]) for a in ARMS} for t in sorted({r["task"] for r in runs.values()})}
    return {"blocks": len(blocks), "arms": {a: arm_summary(by_arm[a]) for a in ARMS},
            "primary": {"H1": primary, "rule": "superiority only when the 95% interval of the relative difference excludes 0"},
            "secondary": secondary, "verificationBenefit": h5, "sensitivity": sensitivity,
            "perCategory": per_category, "perTask": per_task}


def canonical(x):
    if isinstance(x, dict):
        return {k: canonical(x[k]) for k in sorted(x)}
    if isinstance(x, list):
        return [canonical(v) for v in x]
    if isinstance(x, float):
        return rnd(x)
    return x


def main(argv):
    flags = [a for a in argv[1:] if a.startswith("--")]
    args = [a for a in argv[1:] if not a.startswith("--")]
    here = os.path.dirname(os.path.abspath(__file__))
    obs_dir = args[0] if args else os.path.join(here, "..", "observations")
    out = args[1] if len(args) > 1 else os.path.join(here, "results.json")
    runs, files, parsed, duplicates = load(obs_dir, "--include-smoke" in flags)
    result = {"schema": "cbe.rel-001.run-03-analysis/1", "seed": SEED, "resamples": RESAMPLES,
              "bootstrap": "paired percentile over (task, replicate) blocks; splitmix64 stream per comparison",
              "input": {"files": files, "run03Observations": parsed, "analysed": len(runs), "duplicateBlockArm": duplicates,
                        "includeSmoke": "--include-smoke" in flags},
              **analyse(runs)}
    text = json.dumps(canonical(result), indent=2, sort_keys=True) + "\n"
    with open(out, "w") as f:
        f.write(text)
    h1 = result["primary"]["H1"]
    print(json.dumps({"out": out, "analysed": len(runs), "H1": {k: h1[k] for k in ("estimate", "ci95", "decision", "blocks")}}))


if __name__ == "__main__":
    main(sys.argv)
