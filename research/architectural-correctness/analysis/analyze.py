#!/usr/bin/env python3
"""ARCH-001 preregistered analysis (adapted from REL-001 run-03 analysis/analyze.py; see harness/PROVENANCE.md).

usage: python3 -I analyze.py [OBSERVATIONS_DIR] [OUT.json] [--label confirmatory|pilot|smoke]
  defaults: research/architectural-correctness/observations, analysis/results.json, --label confirmatory

Reads every OBSERVATIONS_DIR/**/*.json with schema arch001.observation/1 and the requested label. Standard library
only; deterministic (splitmix64 stream per contrast, 10,000 resamples, keys sorted, numbers rounded to 6 places), so
identical inputs give byte-identical output. Functional style: pure functions, constants only at module level.

Unit and metrics (preregistration draft):
  requirement unit: 2 per trial (R1 initial at S1, R2 follow-up at S2); accepted = functional pass AND architectural
      acceptance (score.py).
  PRIMARY per arm: total model cost over all trials and both phases (failed attempts and X5 timeouts included)
      / number of accepted requirements.  Contrast D vs A: ratio of the two pooled values, reported as ratio - 1.
  cost per completed task: total cost / trials whose phase-2 submit PASSed (correctness ignored); descriptive.
  H1a B-A  DET severity-weighted violations per trial at S2 (ARC-TRC-01 excluded)     predicted < 0
  H1b B-A  architectural acceptance rate (accepted-architecture requirements / 2n)    predicted > 0
  H2  C-B  decision fidelity: oracle decision-test pass rate (tests naming a DEC- id)  predicted > 0
           (ARC-TRC-01 is defined for C/D only and is reported descriptively; T5 conflict refusal descriptively)
  H3  D-C  DET severity-weighted violations per trial at S2                           predicted < 0
  H4  D-C  follow-up rework: lines changed in files that existed before phase 2       predicted < 0
  H5a D/C - 1 and H5b D/A - 1 on the primary metric                                    predicted < 0
  H6  slope, over tasks, of the mean D-A violation difference on task cross-tier count predicted < 0
Inference: two-stage cluster bootstrap (resample tasks with replacement, then replicates within each sampled task;
  a sampled (task, replicate) block carries all its arms), 10,000 resamples, percentile 95% interval, two-sided
  bootstrap p = 2 min(P(T<=0), P(T>=0)). Holm step-down across the secondary family H1a..H6.
Classification: Supported = Holm-adjusted p < 0.05 with the estimate in the predicted direction (primary: the 95%
  interval excludes 0 in the predicted direction); Not supported = the same in the opposite direction, OR the 95%
  interval lies inside the preregistered equivalence margin; otherwise Inconclusive. A contrast with < 2 usable
  blocks or > 1% undefined resamples is Inconclusive (not evaluable).
Exclusions: X1 (no observation exists), X4 contamination and X-integrity tamper (observation .excluded) are removed;
  X5 timeouts are scored as is; the sensitivity block repeats every contrast without X5 trials. A metric missing for
  a trial (e.g. the verifier could not evaluate a commit) removes that trial from that metric's contrasts only.
"""
import hashlib
import json
import math
import os
import sys
from functools import reduce

SEED = 20261022
RESAMPLES = 10_000
ARMS = ["A", "B", "C", "D"]
ALPHA = 0.05
MASK = (1 << 64) - 1
# Preregistered equivalence margins (draft, for coordinator approval): |effect| inside the margin = "no practical effect".
MARGINS = {"primary": 0.10, "H1a": 0.5, "H1b": 0.10, "H2": 0.10, "H3": 0.5, "H4": 10.0, "H5a": 0.10, "H5b": 0.10, "H6": 0.25}


# ------------------------------------------------------------------ deterministic PRNG (splitmix64, run-03)
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


def cluster_resamples(name, clusters):
    """clusters: [(task, [block, ...])] -> RESAMPLES lists of blocks (two-stage: tasks, then replicates within task)."""
    g = stream(name)
    n = len(clusters)
    def one():
        tasks = [clusters[next(g) % n] for _ in range(n)]
        return [blocks[next(g) % len(blocks)] for _, blocks in tasks for _ in range(len(blocks))]
    return [one() for _ in range(RESAMPLES)]


# ------------------------------------------------------------------ input
def get(d, *path):
    return reduce(lambda acc, k: acc.get(k) if isinstance(acc, dict) else None, path, d)


def parse(obs):
    reqs = obs.get("requirements") or []
    p2 = get(obs, "architecture", "p2") or {}
    return {
        "runId": obs["runId"], "arm": obs["arm"], "task": obs["task"], "replicate": obs["replicate"], "block": obs["block"],
        "label": obs.get("label"), "excluded": bool(obs.get("excluded")), "exclusionReasons": obs.get("exclusionReasons") or [],
        "timedOut": bool(get(obs, "exclusions", "x5", "timedOut")),
        "cost": get(obs, "cost", "totalUsd"), "units": 2,
        "accepted": sum(1 for r in reqs if r.get("accepted")),
        "functional": sum(1 for r in reqs if r.get("functionalPass")),
        "archAccepted": sum(1 for r in reqs if r.get("archAccept")),
        "completed": bool(obs.get("completed")),
        "violations": p2.get("detSeverityWeighted") if p2.get("evaluable") else None,
        "violationsP1": get(obs, "architecture", "p1", "detSeverityWeighted") if get(obs, "architecture", "p1", "evaluable") else None,
        "decPassed": get(obs, "decisionFidelity", "decisionTests", "passed") or 0,
        "decTotal": get(obs, "decisionFidelity", "decisionTests", "total") or 0,
        "conflict": get(obs, "decisionFidelity", "conflict", "correct"),
        "trc": get(obs, "decisionFidelity", "trc", "p2"),
        "rework": get(obs, "diff", "phase2", "all", "rework"),
        "crossTier": get(obs, "taskMeta", "crossTierCount"),
        "firstPass": [get(obs, "firstPassCorrect", "p1"), get(obs, "firstPassCorrect", "p2")],
        "review": get(obs, "review", "scores"), "reviewCost": get(obs, "review", "evaluationCost", "totalUsd"),
        "cacheCold": [get(obs, "phases", k, "cache", "firstRequestCold") for k in ("1", "2")],
        "costAgrees": get(obs, "cost", "agrees")}


def load(directory, label):
    files = sorted((os.path.join(d, f) for d, _, fs in os.walk(directory) for f in fs if f.endswith(".json")), key=lambda s: s.encode())
    docs = [json.load(open(f)) for f in files]
    runs = [parse(d) for d in docs if isinstance(d, dict) and d.get("schema") == "arch001.observation/1" and d.get("label") == label]
    by_key = {}
    for r in sorted(runs, key=lambda r: r["runId"]):
        by_key.setdefault((r["block"], r["arm"]), []).append(r)
    duplicates = sorted(f"{b}/{a}" for (b, a), rs in by_key.items() if len(rs) > 1)
    return {k: rs[-1] for k, rs in by_key.items()}, len(files), len(runs), duplicates


def blocks_of(runs, keep):
    """{block: {arm: run}} over runs that pass keep (exclusions applied here)."""
    out = {}
    for (b, a), r in sorted(runs.items()):
        if keep(r):
            out.setdefault(b, {})[a] = r
    return out


def clusters_of(blocks):
    by_task = {}
    for b, arms in sorted(blocks.items()):
        task = next(iter(arms.values()))["task"]
        by_task.setdefault(task, []).append(arms)
    return sorted(by_task.items())


# ------------------------------------------------------------------ statistics
def rnd(x):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, 6)


def percentile(xs, q):
    if not xs:
        return None
    pos = q * (len(xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def pooled(sample, arm, num, den):
    rs = [blk[arm] for blk in sample if arm in blk]
    n, d = sum(num(r) for r in rs), sum(den(r) for r in rs)
    return n / d if d else None


def paired(sample, x, y, field):
    return [blk for blk in sample if x in blk and y in blk and blk[x][field] is not None and blk[y][field] is not None]


def ratio_stat(x, y):
    def stat(sample):
        s = [blk for blk in sample if x in blk and y in blk and blk[x]["cost"] is not None and blk[y]["cost"] is not None]
        px = pooled(s, x, lambda r: r["cost"], lambda r: r["accepted"])
        py = pooled(s, y, lambda r: r["cost"], lambda r: r["accepted"])
        return None if px is None or py is None or py == 0 else px / py - 1
    return stat


def mean_diff_stat(x, y, field):
    def stat(sample):
        s = paired(sample, x, y, field)
        return (sum(b[x][field] for b in s) - sum(b[y][field] for b in s)) / len(s) if s else None
    return stat


def rate_diff_stat(x, y, num, den):
    def stat(sample):
        s = [b for b in sample if x in b and y in b]
        px, py = pooled(s, x, num, den), pooled(s, y, num, den)
        return None if px is None or py is None else px - py
    return stat


def slope_stat(x, y, field):
    """OLS slope over tasks of mean (x - y) per task against the task's cross-tier count."""
    def stat(sample):
        per = {}
        for b in paired(sample, x, y, field):
            if b[x]["crossTier"] is not None:
                per.setdefault(b[x]["task"], (b[x]["crossTier"], []))[1].append(b[x][field] - b[y][field])
        pts = [(ct, sum(ds) / len(ds)) for ct, ds in per.values()]
        if len({p[0] for p in pts}) < 2:
            return None
        mx, my = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        sxx = sum((p[0] - mx) ** 2 for p in pts)
        return sum((p[0] - mx) * (p[1] - my) for p in pts) / sxx
    return stat


def bootstrap(name, clusters, stat):
    flat = [b for _, bs in clusters for b in bs]
    point = stat(flat)
    if len(flat) < 2 or point is None:
        return {"estimate": rnd(point), "ci95": None, "p": None, "undefinedResamples": None, "blocks": len(flat), "tasks": len(clusters)}
    draws = [stat(s) for s in cluster_resamples(name, clusters)]
    defined = sorted(d for d in draws if d is not None)
    p = min(1.0, 2 * min(sum(d <= 0 for d in defined), sum(d >= 0 for d in defined)) / len(defined)) if defined else None
    return {"estimate": rnd(point), "ci95": [rnd(percentile(defined, 0.025)), rnd(percentile(defined, 0.975))] if defined else None,
            "p": rnd(p), "undefinedResamples": len(draws) - len(defined), "blocks": len(flat), "tasks": len(clusters)}


def holm(ps):
    known = sorted(((p, n) for n, p in ps.items() if p is not None), key=lambda t: (t[0], t[1]))
    m, running, adjusted = len(known), 0.0, {}
    for i, (p, n) in enumerate(known):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[n] = rnd(running)
    return {n: adjusted.get(n) for n in ps}


def classify(res, predicted, margin, p_adj):
    ci = res.get("ci95")
    if not ci or None in ci or (res.get("undefinedResamples") or 0) > RESAMPLES // 100:
        return "Inconclusive (not evaluable)"
    sign = 1 if predicted == ">" else -1
    est = res["estimate"] or 0.0
    if p_adj is not None and p_adj < ALPHA and est * sign > 0:
        return "Supported"
    if (p_adj is not None and p_adj < ALPHA and est * sign < 0) or (-margin < ci[0] and ci[1] < margin):
        return "Not supported"
    return "Inconclusive"


def classify_interval(res, predicted, margin):
    """The primary contrast (not in the Holm family): the 95% interval itself decides."""
    ci = res.get("ci95")
    if not ci or None in ci or (res.get("undefinedResamples") or 0) > RESAMPLES // 100:
        return "Inconclusive (not evaluable)"
    favours = ci[1] < 0 if predicted == "<" else ci[0] > 0
    opposes = ci[0] > 0 if predicted == "<" else ci[1] < 0
    if favours:
        return "Supported"
    if opposes or (-margin < ci[0] and ci[1] < margin):
        return "Not supported"
    return "Inconclusive"


# ------------------------------------------------------------------ the analysis
CONTRASTS = [  # (id, description, predicted sign, statistic factory, (x, y, field needed by both))
    ("H1a", "B-A DET severity-weighted violations per trial (S2)", "<", lambda: mean_diff_stat("B", "A", "violations"), ("B", "A", "violations")),
    ("H1b", "B-A architectural acceptance rate (per requirement)", ">", lambda: rate_diff_stat("B", "A", lambda r: r["archAccepted"], lambda r: r["units"]), ("B", "A", None)),
    ("H2", "C-B oracle decision-test pass rate", ">", lambda: rate_diff_stat("C", "B", lambda r: r["decPassed"], lambda r: r["decTotal"]), ("C", "B", None)),
    ("H3", "D-C DET severity-weighted violations per trial (S2)", "<", lambda: mean_diff_stat("D", "C", "violations"), ("D", "C", "violations")),
    ("H4", "D-C follow-up rework (lines changed in pre-existing files)", "<", lambda: mean_diff_stat("D", "C", "rework"), ("D", "C", "rework")),
    ("H5a", "D/C - 1 primary metric (cost per accepted requirement)", "<", lambda: ratio_stat("D", "C"), ("D", "C", "cost")),
    ("H5b", "D/A - 1 primary metric (cost per accepted requirement)", "<", lambda: ratio_stat("D", "A"), ("D", "A", "cost")),
    ("H6", "slope of mean D-A violation difference on task cross-tier count", "<", lambda: slope_stat("D", "A", "violations"), ("D", "A", "violations")),
]


def pair_count(clusters, x, y, field):
    return sum(1 for _, bs in clusters for b in bs if x in b and y in b and (field is None or (b[x][field] is not None and b[y][field] is not None)))


def arm_summary(rs):
    tot = lambda f: sum(r[f] for r in rs if r[f] is not None)
    have = lambda f: sum(1 for r in rs if r[f] is not None)
    cost = tot("cost")
    acc, comp = tot("accepted"), sum(r["completed"] for r in rs)
    reviews = [r["review"] for r in rs if r["review"]]
    rev_mean = {c: rnd(sum(cs.get(c) or 0 for rv in reviews for cs in rv.values()) / sum(len(rv) for rv in reviews))
                for c in ("ARC-REV-01", "ARC-REV-02", "ARC-REV-03")} if reviews else None
    return {"trials": len(rs), "requirements": 2 * len(rs), "acceptedRequirements": acc, "functionalPass": tot("functional"),
            "archAccepted": tot("archAccepted"), "completedTasks": comp, "timedOutTrials": sum(r["timedOut"] for r in rs),
            "costTotalUsd": rnd(cost), "costPerAcceptedRequirement": rnd(cost / acc) if acc else None,
            "costPerCompletedTask": rnd(cost / comp) if comp else None,
            "violationsPerTrialS2": rnd(tot("violations") / have("violations")) if have("violations") else None,
            "violationsEvaluable": have("violations"),
            "decisionTests": {"passed": tot("decPassed"), "total": tot("decTotal")},
            "conflictCorrect": {"correct": sum(1 for r in rs if r["conflict"] is True), "applicable": sum(1 for r in rs if r["conflict"] is not None)},
            "trcFindingsS2": tot("trc") if have("trc") else None,
            "reworkMean": rnd(tot("rework") / have("rework")) if have("rework") else None,
            "firstPassCorrect": {"p1": sum(1 for r in rs if r["firstPass"][0]), "p2": sum(1 for r in rs if r["firstPass"][1])},
            "coldFirstRequests": sum(1 for r in rs for c in r["cacheCold"] if c is True),
            "costCrossCheckDisagreements": sum(1 for r in rs if r["costAgrees"] is False),
            "review": {"meanScores": rev_mean, "reviewed": len(reviews), "evaluationCostUsd": rnd(tot("reviewCost")),
                       "note": "evaluation cost, not arm cost"}}


def contrasts(blocks, tag):
    clusters = clusters_of(blocks)
    primary = bootstrap(f"{tag}:primary:D-A", clusters, ratio_stat("D", "A"))
    primary = {**primary, "contrast": "D/A - 1 cost per accepted requirement", "predicted": "<", "margin": MARGINS["primary"],
               "pairs": pair_count(clusters, "D", "A", "cost"),
               "classification": classify_interval(primary, "<", MARGINS["primary"])}
    sec = {cid: {**bootstrap(f"{tag}:{cid}", clusters, factory()), "contrast": desc, "predicted": pred, "margin": MARGINS[cid],
                 "pairs": pair_count(clusters, *need)}
           for cid, desc, pred, factory, need in CONTRASTS}
    adj = holm({k: v["p"] for k, v in sec.items()})
    sec = {k: {**v, "pHolm": adj[k], "classification": classify(v, v["predicted"], v["margin"], adj[k])} for k, v in sec.items()}
    completed = bootstrap(f"{tag}:completed:D-A", clusters, lambda s: (lambda px, py: None if px is None or py in (None, 0) else px / py - 1)(
        pooled([b for b in s if "D" in b and "A" in b], "D", lambda r: r["cost"] or 0, lambda r: 1 if r["completed"] else 0),
        pooled([b for b in s if "D" in b and "A" in b], "A", lambda r: r["cost"] or 0, lambda r: 1 if r["completed"] else 0)))
    return {"primary": primary, "secondary": sec, "costPerCompletedTask D/A - 1 (descriptive)": completed}


def analyse(runs):
    included = blocks_of(runs, lambda r: not r["excluded"])
    no_x5 = blocks_of(runs, lambda r: not r["excluded"] and not r["timedOut"])
    by_arm = {a: [r for (b, x), r in sorted(runs.items()) if x == a and not r["excluded"]] for a in ARMS}
    excluded = sorted((r["runId"], tuple(r["exclusionReasons"])) for r in runs.values() if r["excluded"])
    tasks = sorted({r["task"] for r in runs.values()})
    return {"arms": {a: arm_summary(by_arm[a]) for a in ARMS},
            "perTask": {t: {a: arm_summary([r for r in by_arm[a] if r["task"] == t]) for a in ARMS} for t in tasks},
            "excluded": [{"runId": i, "reasons": list(rs)} for i, rs in excluded],
            **contrasts(included, "main"),
            "sensitivity": {"withoutX5Timeouts": contrasts(no_x5, "noX5"),
                            "x5Trials": sum(1 for r in runs.values() if r["timedOut"] and not r["excluded"])},
            "rules": {"family": [c[0] for c in CONTRASTS], "holm": True, "alpha": ALPHA, "margins": MARGINS,
                      "bootstrap": "two-stage cluster (tasks, then replicates within task); percentile 95%; splitmix64 stream per contrast"}}


def canonical(x):
    if isinstance(x, dict):
        return {k: canonical(x[k]) for k in sorted(x)}
    if isinstance(x, list):
        return [canonical(v) for v in x]
    if isinstance(x, float):
        return rnd(x)
    return x


def main(argv):
    flags = argv[1:]
    label = flags[flags.index("--label") + 1] if "--label" in flags else "confirmatory"
    args = [a for i, a in enumerate(flags) if not a.startswith("--") and (i == 0 or flags[i - 1] != "--label")]
    here = os.path.dirname(os.path.abspath(__file__))
    obs_dir = args[0] if args else os.path.join(here, "..", "observations")
    out = args[1] if len(args) > 1 else os.path.join(here, "results.json")
    runs, files, parsed, duplicates = load(obs_dir, label)
    result = {"schema": "arch001.analysis/1", "seed": SEED, "resamples": RESAMPLES, "label": label,
              "input": {"files": files, "observations": parsed, "analysed": len(runs), "duplicateBlockArm": duplicates},
              **analyse(runs)}
    text = json.dumps(canonical(result), indent=2, sort_keys=True) + "\n"
    with open(out, "w") as f:
        f.write(text)
    p = result["primary"]
    print(json.dumps({"out": out, "analysed": len(runs), "primary": {k: p[k] for k in ("estimate", "ci95", "classification", "blocks")}}))


if __name__ == "__main__":
    main(sys.argv)
