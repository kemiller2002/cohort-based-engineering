#!/usr/bin/env python3
"""ARCH-001 EXPLORATORY analysis (not preregistered; written after the confirmatory results were known).

usage: python3 -I exploratory.py [OBSERVATIONS_DIR] [OUT.json]

Descriptive breakdowns that the preregistered analysis (analyze.py) does not report, plus exploratory contrasts that
use analyze.py's own two-stage cluster bootstrap (tasks, then replicates; 10,000 resamples) so the intervals are
comparable. Nothing here changes a hypothesis classification; every number is labelled exploratory. Pure functions;
standard library only.
"""
import importlib.util
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location("analyze", os.path.join(HERE, "analyze.py"))
AN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AN)

ARMS = ["A", "B", "C", "D"]
REV = ("ARC-REV-01", "ARC-REV-02", "ARC-REV-03")


def load(directory):
    paths = sorted(os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".json"))
    docs = (json.load(open(p)) for p in paths)
    return [d for d in docs if d.get("schema") == "arch001.observation/1" and d.get("label") == "confirmatory" and not d.get("excluded")]


def phase(d, k):
    return (d.get("phases") or {}).get(str(k)) or {}


def verif(ph):
    v = ph.get("verificationExecutions") or {}
    return sum(v.values()) if isinstance(v, dict) else (v or 0)


def review_total(d, k):
    s = ((d.get("review") or {}).get("scores") or {}).get(str(k)) or {}
    return sum(s.get(c) or 0 for c in REV) if s else None


def row(d):
    """One flat record per trial: the fields every breakdown and contrast below reads."""
    p1, p2 = phase(d, 1), phase(d, 2)
    tok = lambda ph, key: (ph.get("tokens") or {}).get(key) or 0
    heu = lambda k: ((d.get("architecture") or {}).get(f"p{k}") or {}).get("heu") or 0
    r1, r2 = review_total(d, 1), review_total(d, 2)
    return {"arm": d["arm"], "task": d["task"], "block": d["block"],
            "cost1": p1.get("costUsd") or 0.0, "cost2": p2.get("costUsd") or 0.0,
            "cost": (d.get("cost") or {}).get("totalUsd") or 0.0,
            "coldEquivalent": (p1.get("coldEquivalentUsd") or 0.0) + (p2.get("coldEquivalentUsd") or 0.0),
            "input": tok(p1, "input") + tok(p2, "input"), "output": tok(p1, "output") + tok(p2, "output"),
            "cacheRead": tok(p1, "cacheRead") + tok(p2, "cacheRead"), "cacheWrite": tok(p1, "cacheWrite") + tok(p2, "cacheWrite"),
            "toolCalls": (p1.get("toolCalls") or 0) + (p2.get("toolCalls") or 0),
            "testExecutions": (p1.get("testExecutions") or 0) + (p2.get("testExecutions") or 0),
            "verificationExecutions": verif(p1) + verif(p2),
            "wallMin": ((p1.get("wallMs") or 0) + (p2.get("wallMs") or 0)) / 60000,
            "heu": heu(1) + heu(2),
            "rework": (((d.get("diff") or {}).get("phase2") or {}).get("all") or {}).get("rework") or 0,
            "filesChanged2": (((d.get("diff") or {}).get("phase2") or {}).get("all") or {}).get("filesModified") or 0,
            "review": None if r1 is None or r2 is None else (r1 + r2) / 2,
            "reviewRev01": None if not d.get("review") else statistics.mean(
                [((d["review"].get("scores") or {}).get(k) or {}).get("ARC-REV-01") or 0 for k in ("1", "2")])}


def describe(rows):
    fields = ["cost1", "cost2", "cost", "coldEquivalent", "input", "output", "cacheRead", "cacheWrite", "toolCalls",
              "testExecutions", "verificationExecutions", "wallMin", "heu", "rework", "filesChanged2", "review", "reviewRev01"]
    def per_arm(a):
        xs = [r for r in rows if r["arm"] == a]
        mean = lambda f: AN.rnd(statistics.mean([r[f] for r in xs if r[f] is not None])) if xs else None
        return {"trials": len(xs), "sum": {"cost1": AN.rnd(sum(r["cost1"] for r in xs)), "cost2": AN.rnd(sum(r["cost2"] for r in xs)),
                                          "cost": AN.rnd(sum(r["cost"] for r in xs))},
                "meanPerTrial": {f: mean(f) for f in fields}}
    return {a: per_arm(a) for a in ARMS}


def per_task_cost(rows):
    tasks = sorted({r["task"] for r in rows})
    return {t: {a: AN.rnd(sum(r["cost"] for r in rows if r["task"] == t and r["arm"] == a)) for a in ARMS} for t in tasks}


def clusters(rows):
    """[(task, [block {arm: row}])] in the shape analyze.cluster_resamples expects."""
    blocks = {}
    for r in rows:
        blocks.setdefault((r["task"], r["block"]), {})[r["arm"]] = r
    by_task = {}
    for (t, _), b in sorted(blocks.items()):
        by_task.setdefault(t, []).append(b)
    return sorted(by_task.items())


def boot(name, cl, stat):
    """analyze.py's own bootstrap (sorted percentile interval and two-sided bootstrap p) for an exploratory statistic."""
    return AN.bootstrap(name, cl, stat)


def mean_diff(x, y, f):
    def stat(blocks):
        ds = [b[x][f] - b[y][f] for b in blocks if x in b and y in b and b[x][f] is not None and b[y][f] is not None]
        return statistics.mean(ds) if ds else None
    return stat


def ratio(x, y, f):
    def stat(blocks):
        num = sum(b[x][f] for b in blocks if x in b and y in b)
        den = sum(b[y][f] for b in blocks if x in b and y in b)
        return (num / den - 1) if den else None
    return stat


def contrasts(rows):
    cl = clusters(rows)
    pairs = [("B", "A"), ("C", "B"), ("D", "C"), ("D", "A")]
    out = {}
    for x, y in pairs:
        out[f"review {x}-{y} (mean of 3 criteria x 2 phases summed /2)"] = boot(f"x:rev:{x}{y}", cl, mean_diff(x, y, "review"))
        out[f"ARC-REV-01 {x}-{y}"] = boot(f"x:rev01:{x}{y}", cl, mean_diff(x, y, "reviewRev01"))
        out[f"phase-1 cost {x}/{y} - 1"] = boot(f"x:c1:{x}{y}", cl, ratio(x, y, "cost1"))
        out[f"phase-2 cost {x}/{y} - 1"] = boot(f"x:c2:{x}{y}", cl, ratio(x, y, "cost2"))
        out[f"total cost {x}/{y} - 1"] = boot(f"x:c:{x}{y}", cl, ratio(x, y, "cost"))
        out[f"output tokens {x}/{y} - 1"] = boot(f"x:out:{x}{y}", cl, ratio(x, y, "output"))
    control = [r for r in rows if r["task"] == "T8"]
    out["T8 control: total cost D/A - 1"] = boot("x:t8", clusters(control), ratio("D", "A", "cost"))
    out["T8 control: total cost D/C - 1"] = boot("x:t8dc", clusters(control), ratio("D", "C", "cost"))
    return out


def main(argv):
    src = argv[1] if len(argv) > 1 else os.path.join(HERE, "..", "observations")
    dst = argv[2] if len(argv) > 2 else os.path.join(HERE, "exploratory-results.json")
    rows = [row(d) for d in load(src)]
    doc = {"schema": "arch001.exploratory/1", "label": "EXPLORATORY (not preregistered; post hoc)", "trials": len(rows),
           "byArm": describe(rows), "costByTaskAndArm": per_task_cost(rows), "contrasts": contrasts(rows),
           "method": "two-stage cluster bootstrap from analyze.py (seeded streams named x:*), percentile 95% intervals; no multiplicity correction"}
    text = json.dumps(AN.canonical(doc), indent=2, sort_keys=True) + "\n"
    open(dst, "w").write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv)
