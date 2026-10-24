#!/usr/bin/env python3
"""ARCH-002 preregistered analysis (adapted from ARCH-001 analysis/analyze.py; see ../PROVENANCE.md).

usage: python3 -I analyze.py [OBSERVATIONS_DIR] [OUT.json] [--label confirmatory|pilot|calibration|smoke]
                             [--remediation REMEDIATION.json]
  defaults: arch-002/observations, arch-002/analysis/results.json, --label confirmatory,
            --remediation arch-002/analysis/remediation-lines.json

Reads every OBSERVATIONS_DIR/**/*.json with schema arch002.observation/1 and the requested label. Standard library
only; deterministic (splitmix64 stream per contrast, 10,000 resamples, keys sorted, numbers rounded to 6 places), so
identical inputs give byte-identical output. Functional style: pure functions, constants only at module level.

Unit and metrics (ARCH-001 definitions with the ARCH-002 brownfield baseline-delta measure, INTERFACES §3, §6):
  block: (fixture, task, model, replicate), carrying all four arms of that cell.
  requirement unit: 2 per trial (R1 initial at S1, R2 follow-up at S2); accepted = functional pass AND architectural
      acceptance = zero NEW DET findings of severity >= 2 vs the start commit (score.py).
  violations: NEW DET severity-weighted findings at S2 vs the start commit (ARC-TRC-01 excluded); pre-existing and
      fixed findings never enter it.
  PRIMARY: total model cost / accepted requirements per arm; contrast D/A - 1.
  H1a B-A violations (S2)                 <      H1b B-A architectural acceptance rate          >
  H2  C-B oracle decision-test pass rate  >      H3  D-C violations (S2)                        <
  H4  D-C follow-up rework                <      H5a D/C - 1 primary metric                     <
  H5b D/A - 1 primary metric              <      H6  slope over tasks of mean D-A violations on cross-tier count <
  H8  (D-A violations | opus) - (D-A violations | sonnet): the treatment effect on violations differs by model (two-sided)
Estimation: every contrast is computed WITHIN model and pooled with model as a stratum (the pooled estimate is the
  unweighted mean of the per-model estimates over the models present). Per-model estimates are reported too.
Inference: stratified two-stage cluster bootstrap: within each fixture, resample its tasks with replacement; for each
  sampled task and each model, resample that (task, model)'s replicate blocks with replacement (a block carries all
  its arms); 10,000 resamples, percentile 95% interval, two-sided bootstrap p = 2 min(P(T<=0), P(T>=0)). Holm
  step-down across the secondary family H1a..H6 + H8.
Classification (ARCH-001 rules and margins, plus H8 margin 0.5): Supported = Holm-adjusted p < 0.05 with the estimate
  in the predicted direction (H8: either direction; primary: the 95% interval excludes 0 in the predicted direction);
  Not supported = the same in the opposite direction, OR the 95% interval lies inside the equivalence margin;
  otherwise Inconclusive. A contrast with < 2 usable blocks or > 1% undefined resamples is Inconclusive (not evaluable).
Lifecycle cost (a MODEL, INTERFACES §6; reported next to the raw costs, never a hypothesis):
  lifecycle = cost(phase 1) + cost(phase 2) + remediation;
  remediation = cost per rework line (per model: sum of phase-2 cost / sum of phase-2 rework lines over every included
  trial, pooled across arms) x the rework lines needed to remove the NEW violations left at S2 (per rule, from
  remediation-lines.json: the fixture workers' sealed table, else the reference good-vs-trap diff size per rule;
  see remediation_table.py).
Exclusions: X1 (no observation), X4 contamination and X-integrity tamper (observation .excluded) are removed; X5
  timeouts are scored as is; the sensitivity block repeats every contrast without X5 trials. A metric missing for a
  trial removes that trial from that metric's contrasts only.
"""
import hashlib
import json
import math
import os
import sys
from functools import reduce

SEED = 20261023
RESAMPLES = 10_000
ARMS = ["A", "B", "C", "D"]
MODELS = ["opus", "sonnet"]
ALPHA = 0.05
MASK = (1 << 64) - 1
SCHEMA = "arch002.observation/1"
MARGINS = {"primary": 0.10, "H1a": 0.5, "H1b": 0.10, "H2": 0.10, "H3": 0.5, "H4": 10.0, "H5a": 0.10, "H5b": 0.10,
           "H6": 0.25, "H8": 0.5}


# ------------------------------------------------------------------ deterministic PRNG (splitmix64, run-03/ARCH-001)
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
    """clusters: [(fixture, [(task, [(model, [block, ...]), ...]), ...])] -> RESAMPLES flat lists of blocks.
    Stratified by fixture: tasks are resampled within their fixture; then, per sampled task and model, replicates."""
    g = stream(name)
    def one():
        out = []
        for _, tasks in clusters:
            n = len(tasks)
            for _ in range(n):
                _, models = tasks[next(g) % n]
                for _, reps in models:
                    out.extend(reps[next(g) % len(reps)] for _ in range(len(reps)))
        return out
    return [one() for _ in range(RESAMPLES)]


# ------------------------------------------------------------------ input
def get(d, *path):
    return reduce(lambda acc, k: acc.get(k) if isinstance(acc, dict) else None, path, d)


def evaluable_value(arch, key):
    return arch.get(key) if arch.get("evaluable") else None


def parse(obs):
    reqs = obs.get("requirements") or []
    p1 = get(obs, "architecture", "p1") or {}
    p2 = get(obs, "architecture", "p2") or {}
    return {
        "runId": obs["runId"], "fixture": obs["fixture"], "arm": obs["arm"], "task": obs["task"],
        "taskKey": obs.get("taskKey") or f"{obs['fixture']}/{obs['task']}", "model": obs["modelKey"],
        "replicate": obs["replicate"], "block": obs["block"],
        "label": obs.get("label"), "excluded": bool(obs.get("excluded")), "exclusionReasons": obs.get("exclusionReasons") or [],
        "timedOut": bool(get(obs, "exclusions", "x5", "timedOut")),
        "cost": get(obs, "cost", "totalUsd"), "cost1": get(obs, "cost", "byPhase", "1"), "cost2": get(obs, "cost", "byPhase", "2"),
        "units": 2,
        "accepted": sum(1 for r in reqs if r.get("accepted")),
        "functional": sum(1 for r in reqs if r.get("functionalPass")),
        "archAccepted": sum(1 for r in reqs if r.get("archAccept")),
        "completed": bool(obs.get("completed")),
        "violations": evaluable_value(p2, "detNewSeverityWeighted"),
        "violationsP1": evaluable_value(p1, "detNewSeverityWeighted"),
        "newCountS2": evaluable_value(p2, "detNew"), "newByRuleS2": evaluable_value(p2, "newByRule"),
        "fixedS2": evaluable_value(p2, "detFixed"), "preexistingS2": evaluable_value(p2, "detPreexisting"),
        "decPassed": get(obs, "decisionFidelity", "decisionTests", "passed") or 0,
        "decTotal": get(obs, "decisionFidelity", "decisionTests", "total") or 0,
        "conflict": get(obs, "decisionFidelity", "conflict", "correct"),
        "trc": get(obs, "decisionFidelity", "trc", "p2"),
        "rework": get(obs, "diff", "phase2", "all", "rework"),
        "crossTier": get(obs, "taskMeta", "crossTierCount"),
        "control": bool(get(obs, "taskMeta", "control")),
        "firstPass": [get(obs, "firstPassCorrect", "p1"), get(obs, "firstPassCorrect", "p2")],
        "review": get(obs, "review", "scores"), "reviewCost": get(obs, "review", "evaluationCost", "totalUsd"),
        "cacheCold": [get(obs, "phases", k, "cache", "firstRequestCold") for k in ("1", "2")],
        "costAgrees": get(obs, "cost", "agrees")}


def load(directory, label):
    files = sorted((os.path.join(d, f) for d, _, fs in os.walk(directory) for f in fs if f.endswith(".json")), key=lambda s: s.encode())
    docs = [json.load(open(f)) for f in files]
    runs = [parse(d) for d in docs if isinstance(d, dict) and d.get("schema") == SCHEMA and d.get("label") == label]
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
    tree = {}
    for _, arms in sorted(blocks.items()):
        r = next(iter(arms.values()))
        tree.setdefault(r["fixture"], {}).setdefault(r["taskKey"], {}).setdefault(r["model"], []).append(arms)
    return [(f, [(t, sorted(ms.items())) for t, ms in sorted(ts.items())]) for f, ts in sorted(tree.items())]


def flat(clusters):
    return [b for _, tasks in clusters for _, models in tasks for _, reps in models for b in reps]


# ------------------------------------------------------------------ statistics
def rnd(x):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, 6)


def percentile(xs, q):
    if not xs:
        return None
    pos = q * (len(xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def model_of(blk):
    return next(iter(blk.values()))["model"]


def within(model, stat):
    """The statistic on the blocks of one model."""
    return lambda sample: stat([b for b in sample if model_of(b) == model])


def stratified(stat):
    """Pooled with model as a stratum: the unweighted mean of the per-model estimates over the models present."""
    def pooled(sample):
        present = [m for m in MODELS if any(model_of(b) == m for b in sample)]
        vals = [within(m, stat)(sample) for m in present]
        return None if not vals or any(v is None for v in vals) else sum(vals) / len(vals)
    return pooled


def pooled_rate(sample, arm, num, den):
    rs = [blk[arm] for blk in sample if arm in blk]
    n, d = sum(num(r) for r in rs), sum(den(r) for r in rs)
    return n / d if d else None


def paired(sample, x, y, field):
    return [blk for blk in sample if x in blk and y in blk and blk[x][field] is not None and blk[y][field] is not None]


def ratio_stat(x, y, num="cost", den="accepted"):
    def stat(sample):
        s = [blk for blk in sample if x in blk and y in blk and blk[x][num] is not None and blk[y][num] is not None]
        px = pooled_rate(s, x, lambda r: r[num], lambda r: r[den])
        py = pooled_rate(s, y, lambda r: r[num], lambda r: r[den])
        return None if px is None or py is None or py == 0 else px / py - 1
    return stat


def sum_ratio_stat(x, y, field):
    def stat(sample):
        s = paired(sample, x, y, field)
        den = sum(b[y][field] for b in s)
        return (sum(b[x][field] for b in s) / den - 1) if s and den else None
    return stat


def mean_diff_stat(x, y, field):
    def stat(sample):
        s = paired(sample, x, y, field)
        return (sum(b[x][field] for b in s) - sum(b[y][field] for b in s)) / len(s) if s else None
    return stat


def rate_diff_stat(x, y, num, den):
    def stat(sample):
        s = [b for b in sample if x in b and y in b]
        px, py = pooled_rate(s, x, num, den), pooled_rate(s, y, num, den)
        return None if px is None or py is None else px - py
    return stat


def slope_stat(x, y, field):
    """OLS slope over tasks of mean (x - y) per task against the task's cross-tier count."""
    def stat(sample):
        per = {}
        for b in paired(sample, x, y, field):
            if b[x]["crossTier"] is not None:
                per.setdefault(b[x]["taskKey"], (b[x]["crossTier"], []))[1].append(b[x][field] - b[y][field])
        pts = [(ct, sum(ds) / len(ds)) for ct, ds in per.values()]
        if len({p[0] for p in pts}) < 2:
            return None
        mx, my = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        sxx = sum((p[0] - mx) ** 2 for p in pts)
        return sum((p[0] - mx) * (p[1] - my) for p in pts) / sxx
    return stat


def interaction_stat(stat, a="opus", b="sonnet"):
    """H8: the contrast in model a minus the same contrast in model b (both must be present)."""
    def s(sample):
        va, vb = within(a, stat)(sample), within(b, stat)(sample)
        return None if va is None or vb is None else va - vb
    return s


def bootstrap(name, clusters, stat):
    blocks = flat(clusters)
    point = stat(blocks)
    tasks = sum(len(ts) for _, ts in clusters)
    if len(blocks) < 2 or point is None:
        return {"estimate": rnd(point), "ci95": None, "p": None, "undefinedResamples": None, "blocks": len(blocks), "tasks": tasks}
    draws = [stat(s) for s in cluster_resamples(name, clusters)]
    defined = sorted(d for d in draws if d is not None)
    p = min(1.0, 2 * min(sum(d <= 0 for d in defined), sum(d >= 0 for d in defined)) / len(defined)) if defined else None
    return {"estimate": rnd(point), "ci95": [rnd(percentile(defined, 0.025)), rnd(percentile(defined, 0.975))] if defined else None,
            "p": rnd(p), "undefinedResamples": len(draws) - len(defined), "blocks": len(blocks), "tasks": tasks}


def holm(ps):
    known = sorted(((p, n) for n, p in ps.items() if p is not None), key=lambda t: (t[0], t[1]))
    m, running, adjusted = len(known), 0.0, {}
    for i, (p, n) in enumerate(known):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[n] = rnd(running)
    return {n: adjusted.get(n) for n in ps}


def not_evaluable(res):
    ci = res.get("ci95")
    return not ci or None in ci or (res.get("undefinedResamples") or 0) > RESAMPLES // 100


def classify(res, predicted, margin, p_adj):
    if not_evaluable(res):
        return "Inconclusive (not evaluable)"
    ci, est = res["ci95"], res["estimate"] or 0.0
    inside = -margin < ci[0] and ci[1] < margin
    if predicted == "!=":   # two-sided (H8)
        if p_adj is not None and p_adj < ALPHA and est != 0:
            return "Supported"
        return "Not supported" if inside else "Inconclusive"
    sign = 1 if predicted == ">" else -1
    if p_adj is not None and p_adj < ALPHA and est * sign > 0:
        return "Supported"
    if (p_adj is not None and p_adj < ALPHA and est * sign < 0) or inside:
        return "Not supported"
    return "Inconclusive"


def classify_interval(res, predicted, margin):
    """The primary contrast (not in the Holm family): the 95% interval itself decides."""
    if not_evaluable(res):
        return "Inconclusive (not evaluable)"
    ci = res["ci95"]
    favours = ci[1] < 0 if predicted == "<" else ci[0] > 0
    opposes = ci[0] > 0 if predicted == "<" else ci[1] < 0
    if favours:
        return "Supported"
    if opposes or (-margin < ci[0] and ci[1] < margin):
        return "Not supported"
    return "Inconclusive"


# ------------------------------------------------------------------ the analysis
ARCH_RATE = (lambda r: r["archAccepted"], lambda r: r["units"])
DEC_RATE = (lambda r: r["decPassed"], lambda r: r["decTotal"])
CONTRASTS = [  # (id, description, predicted, per-model statistic factory, (x, y, field needed by both))
    ("H1a", "B-A new DET severity-weighted violations per trial at S2 (vs start)", "<", lambda: mean_diff_stat("B", "A", "violations"), ("B", "A", "violations")),
    ("H1b", "B-A architectural acceptance rate (per requirement; zero new DET sev>=2)", ">", lambda: rate_diff_stat("B", "A", *ARCH_RATE), ("B", "A", None)),
    ("H2", "C-B oracle decision-test pass rate", ">", lambda: rate_diff_stat("C", "B", *DEC_RATE), ("C", "B", None)),
    ("H3", "D-C new DET severity-weighted violations per trial at S2 (vs start)", "<", lambda: mean_diff_stat("D", "C", "violations"), ("D", "C", "violations")),
    ("H4", "D-C follow-up rework (lines changed in pre-existing files)", "<", lambda: mean_diff_stat("D", "C", "rework"), ("D", "C", "rework")),
    ("H5a", "D/C - 1 primary metric (cost per accepted requirement)", "<", lambda: ratio_stat("D", "C"), ("D", "C", "cost")),
    ("H5b", "D/A - 1 primary metric (cost per accepted requirement)", "<", lambda: ratio_stat("D", "A"), ("D", "A", "cost")),
    ("H6", "slope over tasks of mean D-A new-violation difference on task cross-tier count", "<", lambda: slope_stat("D", "A", "violations"), ("D", "A", "violations")),
]
H8 = ("H8", "(D-A new violations | opus) - (D-A new violations | sonnet): treatment effect differs by model", "!=",
      ("D", "A", "violations"))


def pair_count(clusters, x, y, field):
    return sum(1 for b in flat(clusters) if x in b and y in b and (field is None or (b[x][field] is not None and b[y][field] is not None)))


def models_in(clusters):
    return [m for m in MODELS if any(model_of(b) == m for b in flat(clusters))]


def contrast_block(tag, clusters, cid, desc, pred, factory, need, margin):
    res = bootstrap(f"{tag}:{cid}", clusters, stratified(factory()))
    by_model = {m: bootstrap(f"{tag}:{cid}:{m}", clusters, within(m, factory())) for m in models_in(clusters)}
    return {**res, "contrast": desc, "predicted": pred, "margin": margin, "pairs": pair_count(clusters, *need),
            "byModel": by_model, "pooling": "stratified by model (mean of per-model estimates)"}


def contrasts(blocks, tag):
    clusters = clusters_of(blocks)
    primary = contrast_block(tag, clusters, "primary:D-A", "D/A - 1 cost per accepted requirement", "<",
                             lambda: ratio_stat("D", "A"), ("D", "A", "cost"), MARGINS["primary"])
    primary["classification"] = classify_interval(primary, "<", MARGINS["primary"])
    sec = {cid: contrast_block(tag, clusters, cid, desc, pred, factory, need, MARGINS[cid]) for cid, desc, pred, factory, need in CONTRASTS}
    cid, desc, pred, need = H8
    sec[cid] = {**bootstrap(f"{tag}:{cid}", clusters, interaction_stat(mean_diff_stat("D", "A", "violations"))),
                "contrast": desc, "predicted": pred, "margin": MARGINS[cid], "pairs": pair_count(clusters, *need),
                "models": models_in(clusters)}
    adj = holm({k: v["p"] for k, v in sec.items()})
    sec = {k: {**v, "pHolm": adj[k], "classification": classify(v, v["predicted"], v["margin"], adj[k])} for k, v in sec.items()}
    completed = bootstrap(f"{tag}:completed:D-A", clusters, stratified(ratio_stat("D", "A", "cost", "completedN")))
    return {"primary": primary, "secondary": sec, "costPerCompletedTask D/A - 1 (descriptive)": completed}


# ------------------------------------------------------------------ lifecycle cost (a model; INTERFACES §6)
def remediation_lines(table, fixture, rule):
    """Lines of rework to remove one new violation of `rule` in `fixture`; None when the table has no basis for it."""
    f = (table.get("fixtures") or {}).get(fixture) or {}
    d = table.get("default") or {}
    for v in ((f.get("rules") or {}).get(rule), f.get("*"), (d.get("rules") or {}).get(rule), d.get("*")):
        if isinstance(v, (int, float)):
            return v
    return None


def unit_costs(runs):
    """Per model: sum of phase-2 cost / sum of phase-2 rework lines, pooled across arms (and fixtures)."""
    out = {}
    for m in MODELS:
        rs = [r for r in runs if r["model"] == m and r["cost2"] is not None and r["rework"] is not None]
        lines = sum(r["rework"] for r in rs)
        out[m] = {"costPerReworkLineUsd": rnd(sum(r["cost2"] for r in rs) / lines) if lines else None,
                  "trials": len(rs), "reworkLines": lines, "phase2CostUsd": rnd(sum(r["cost2"] for r in rs))}
    return out


def with_lifecycle(runs, table):
    units = unit_costs(runs)
    def one(r):
        unit = (units.get(r["model"]) or {}).get("costPerReworkLineUsd")
        by_rule = r["newByRuleS2"]
        if by_rule is None or unit is None or r["cost"] is None:
            return {**r, "remediationLines": None, "remediationUsd": None, "lifecycle": None}
        per = [(n, remediation_lines(table, r["fixture"], rule)) for rule, n in sorted(by_rule.items())]
        if any(l is None for _, l in per):
            return {**r, "remediationLines": None, "remediationUsd": None, "lifecycle": None}
        # Amendment A8: a reference good-vs-trap diff removes ALL of a rule's findings in that change, so each rule
        # with new findings costs its diff size once per trial (not once per finding, which overcounted ~30x).
        lines = sum(l for n, l in per if n > 0)
        return {**r, "remediationLines": lines, "remediationUsd": unit * lines, "lifecycle": r["cost"] + unit * lines}
    return [one(r) for r in runs], units


def lifecycle_summary(runs, blocks, tag):
    def arm_cell(rs):
        have = [r for r in rs if r["lifecycle"] is not None]
        return {"trials": len(rs), "withLifecycle": len(have), "rawCostUsd": rnd(sum(r["cost"] or 0 for r in rs)),
                "remediationLines": rnd(sum(r["remediationLines"] for r in have)), "remediationUsd": rnd(sum(r["remediationUsd"] for r in have)),
                "lifecycleUsd": rnd(sum(r["lifecycle"] for r in have)),
                "lifecyclePerTrialUsd": rnd(sum(r["lifecycle"] for r in have) / len(have)) if have else None}
    clusters = clusters_of(blocks)
    return {"byArm": {a: arm_cell([r for r in runs if r["arm"] == a]) for a in ARMS},
            "byArmAndModel": {m: {a: arm_cell([r for r in runs if r["arm"] == a and r["model"] == m]) for a in ARMS} for m in MODELS},
            "contrast lifecycle D/A - 1 (descriptive, model)": bootstrap(f"{tag}:lifecycle:D-A", clusters, stratified(sum_ratio_stat("D", "A", "lifecycle"))),
            "contrast raw cost D/A - 1 (descriptive)": bootstrap(f"{tag}:rawcost:D-A", clusters, stratified(sum_ratio_stat("D", "A", "cost")))}


# ------------------------------------------------------------------ summaries
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
            "newViolationsPerTrialS2": rnd(tot("violations") / have("violations")) if have("violations") else None,
            "newViolationsPerTrialS1": rnd(tot("violationsP1") / have("violationsP1")) if have("violationsP1") else None,
            "trialsWithNewViolationS2": sum(1 for r in rs if (r["violations"] or 0) > 0),
            "violationsEvaluable": have("violations"),
            "fixedPerTrialS2 (descriptive)": rnd(tot("fixedS2") / have("fixedS2")) if have("fixedS2") else None,
            "preexistingPerTrialS2 (descriptive)": rnd(tot("preexistingS2") / have("preexistingS2")) if have("preexistingS2") else None,
            "decisionTests": {"passed": tot("decPassed"), "total": tot("decTotal")},
            "conflictCorrect": {"correct": sum(1 for r in rs if r["conflict"] is True), "applicable": sum(1 for r in rs if r["conflict"] is not None)},
            "trcFindingsS2": tot("trc") if have("trc") else None,
            "reworkMean": rnd(tot("rework") / have("rework")) if have("rework") else None,
            "firstPassCorrect": {"p1": sum(1 for r in rs if r["firstPass"][0]), "p2": sum(1 for r in rs if r["firstPass"][1])},
            "coldFirstRequests": sum(1 for r in rs for c in r["cacheCold"] if c is True),
            "costCrossCheckDisagreements": sum(1 for r in rs if r["costAgrees"] is False),
            "review": {"meanScores": rev_mean, "reviewed": len(reviews), "evaluationCostUsd": rnd(tot("reviewCost")),
                       "note": "evaluation cost, not arm cost"}}


def analyse(runs, table):
    included = [r for r in runs.values() if not r["excluded"]]
    with_lc, units = with_lifecycle(included, table)
    lc_by_id = {r["runId"]: r for r in with_lc}
    runs = {k: ({**lc_by_id[r["runId"]], "completedN": 1 if r["completed"] else 0} if r["runId"] in lc_by_id
                else {**r, "lifecycle": None, "remediationLines": None, "remediationUsd": None, "completedN": 1 if r["completed"] else 0})
            for k, r in runs.items()}
    main = blocks_of(runs, lambda r: not r["excluded"])
    no_x5 = blocks_of(runs, lambda r: not r["excluded"] and not r["timedOut"])
    by_arm = {a: [r for (b, x), r in sorted(runs.items()) if x == a and not r["excluded"]] for a in ARMS}
    excluded = sorted((r["runId"], tuple(r["exclusionReasons"])) for r in runs.values() if r["excluded"])
    tasks = sorted({r["taskKey"] for r in runs.values()})
    return {"arms": {a: arm_summary(by_arm[a]) for a in ARMS},
            "byModel": {m: {a: arm_summary([r for r in by_arm[a] if r["model"] == m]) for a in ARMS} for m in MODELS},
            "perTask": {t: {a: arm_summary([r for r in by_arm[a] if r["taskKey"] == t]) for a in ARMS} for t in tasks},
            "excluded": [{"runId": i, "reasons": list(rs)} for i, rs in excluded],
            **contrasts(main, "main"),
            "lifecycle": {"label": "MODEL (INTERFACES §6), not a hypothesis; reported next to the raw costs",
                          "unitCost": units, "remediationTable": {"source": table.get("source"), "sha256": table.get("sha256")},
                          **lifecycle_summary([r for r in runs.values() if not r["excluded"]], main, "main")},
            "sensitivity": {"withoutX5Timeouts": contrasts(no_x5, "noX5"),
                            "x5Trials": sum(1 for r in runs.values() if r["timedOut"] and not r["excluded"])},
            "rules": {"family": [c[0] for c in CONTRASTS] + [H8[0]], "holm": True, "alpha": ALPHA, "margins": MARGINS,
                      "bootstrap": "stratified two-stage cluster: tasks within fixture, then replicates within (task, model); "
                                   "percentile 95%; splitmix64 stream per contrast",
                      "pooling": "within model, pooled with model as a stratum (mean of per-model estimates)",
                      "violationMeasure": "new DET severity-weighted at S2 vs the start commit (baseline-delta)"}}


def canonical(x):
    if isinstance(x, dict):
        return {k: canonical(x[k]) for k in sorted(x)}
    if isinstance(x, list):
        return [canonical(v) for v in x]
    if isinstance(x, float):
        return rnd(x)
    return x


def load_table(path):
    try:
        text = open(path, "rb").read()
    except OSError:
        return {"source": None, "sha256": None, "missing": path}
    doc = json.loads(text)
    return {**doc, "source": path, "sha256": hashlib.sha256(text).hexdigest()}


def main(argv):
    flags = argv[1:]
    opt = lambda k, d: flags[flags.index(k) + 1] if k in flags else d
    label = opt("--label", "confirmatory")
    args = [a for i, a in enumerate(flags) if not a.startswith("--") and (i == 0 or not flags[i - 1].startswith("--"))]
    here = os.path.dirname(os.path.abspath(__file__))
    obs_dir = args[0] if args else os.path.join(here, "..", "observations")
    out = args[1] if len(args) > 1 else os.path.join(here, "results.json")
    table = load_table(opt("--remediation", os.path.join(here, "remediation-lines.json")))
    runs, files, parsed, duplicates = load(obs_dir, label)
    result = {"schema": "arch002.analysis/1", "seed": SEED, "resamples": RESAMPLES, "label": label,
              "input": {"files": files, "observations": parsed, "analysed": len(runs), "duplicateBlockArm": duplicates},
              **analyse(runs, table)}
    text = json.dumps(canonical(result), indent=2, sort_keys=True) + "\n"
    with open(out, "w") as f:
        f.write(text)
    p = result["primary"]
    print(json.dumps({"out": out, "analysed": len(runs), "primary": {k: p[k] for k in ("estimate", "ci95", "classification", "blocks")},
                      "H8": {k: result["secondary"]["H8"][k] for k in ("estimate", "ci95", "classification")}}))


if __name__ == "__main__":
    main(sys.argv)
