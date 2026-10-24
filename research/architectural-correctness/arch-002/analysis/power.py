#!/usr/bin/env python3
"""ARCH-002 sample-size planning from the PILOT (adapted from ARCH-001 analysis/power.py; see ../PROVENANCE.md).

usage: python3 -I power.py PILOT_OBSERVATIONS_DIR [OUT.json] [--cap-usd 600] [--tasks N] [--models 2]
                           [--concurrency 3] [--label pilot]

Label: PILOT ESTIMATE (2 tasks: one F1, one F2, x 4 arms x 2 models x 1 replicate). Planning numbers only; the
normal approximation stands in for the stratified cluster bootstrap. ARCH-001's rule, pooled across arms (ARCH-001
pre-freeze amendment: the sample size never depends on an observed treatment advantage):
  1. architectural-acceptance difference D-A (per requirement, 2 per trial; acceptance = zero NEW DET sev>=2):
     two-proportion formula at the POOLED pilot rate (all arms and both models; clamped to [0.05, 0.95]), inflated by
     the design effect 1 + (m - 1) rho for m = 2 requirements per trial (rho = 0.5), detectable difference 0.20;
  2. primary ratio (cost per accepted requirement) D/A: delta method on the ratio of sums with the POOLED per-trial
     log-ratio variance (CV_cost^2 + CV_acc^2 - 2 r CV_cost CV_acc), detectable ratio 0.70.
needed = max(1, 2) in replicates per (task, model, arm) cell = ceil(trials per arm / (TASKS x MODELS)).
Resource view: the pilot's mean cost per trial (pooled over arms and models) x 4 arms x TASKS x MODELS per
replicate; maxReplicatesUnderCap = floor(cap / cost per replicate).
Decision (INTERFACES §5): replicates = max(2, min(needed, maxReplicatesUnderCap, 4)); cap USD 600 of confirmatory
model cost.
"""
import glob
import json
import math
import os
import statistics
import sys

Z = 1.959964 + 0.841621
SCHEMA = "arch002.observation/1"
DELTA = 0.20
RATIO = 0.70
MAX_REPLICATES = 4
MIN_REPLICATES = 2


def load(directory, label):
    docs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(directory, "**", "*.json"), recursive=True))]
    return [d for d in docs if isinstance(d, dict) and d.get("schema") == SCHEMA and d.get("label") == label and not d.get("excluded")]


def per_trial(d):
    reqs = d.get("requirements") or []
    wall = sum((ph or {}).get("wallMs") or 0 for ph in (d.get("phases") or {}).values())
    return {"arm": d["arm"], "model": d.get("modelKey"), "cost": (d.get("cost") or {}).get("totalUsd") or 0.0,
            "accepted": sum(1 for r in reqs if r.get("accepted")), "arch": sum(1 for r in reqs if r.get("archAccept")), "wallMs": wall}


def clamp(p):
    return min(0.95, max(0.05, p))


def cv(xs):
    m = statistics.mean(xs) if xs else 0
    return (statistics.stdev(xs) / m) if len(xs) > 1 and m else 0.0


def corr(xs, ys):
    if len(xs) < 2 or statistics.pstdev(xs) == 0 or statistics.pstdev(ys) == 0:
        return 0.0
    mx, my = statistics.mean(xs), statistics.mean(ys)
    return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / ((len(xs) - 1) * statistics.stdev(xs) * statistics.stdev(ys))


def log_ratio_var(rows):
    c, a = [r["cost"] for r in rows], [max(r["accepted"], 0.5) for r in rows]   # 0.5: continuity floor for zero-accept trials
    return max(cv(c) ** 2 + cv(a) ** 2 - 2 * corr(c, a) * cv(c) * cv(a), 0.01)


def plan(rows, tasks, models, cap, conc):
    if not rows:
        raise SystemExit("power.py needs pilot observations")
    cells = tasks * models
    rate = clamp(sum(r["arch"] for r in rows) / (2 * len(rows)))
    deff = 1 + (2 - 1) * 0.5
    trials_diff = math.ceil((Z ** 2) * (2 * rate * (1 - rate)) / (DELTA ** 2) * deff / 2)
    v = log_ratio_var(rows)
    trials_ratio = math.ceil((Z ** 2) * (2 * v) / (math.log(RATIO) ** 2))
    reps = lambda trials: math.ceil(trials / cells)
    need = max(reps(trials_diff), reps(trials_ratio))
    mean_cost = statistics.mean(r["cost"] for r in rows)
    mean_wall = statistics.mean(r["wallMs"] for r in rows) / 60000
    per_rep = 4 * cells * mean_cost
    cap_reps = math.floor(cap / per_rep) if per_rep else None
    replicates = max(MIN_REPLICATES, min(need, cap_reps if cap_reps is not None else need, MAX_REPLICATES))
    by_model = {m: {"trials": len(rs), "meanCostPerTrialUsd": round(statistics.mean(r["cost"] for r in rs), 4)}
                for m in sorted({r["model"] for r in rows}) for rs in [[r for r in rows if r["model"] == m]]}
    return {
        "decision": {"rule": f"replicates = max({MIN_REPLICATES}, min(needed, maxReplicatesUnderCap, {MAX_REPLICATES})); "
                             f"needed = max(acceptance delta {DELTA}, ratio {RATIO}), per (task, model, arm) cell",
                     "needed": need, "maxReplicatesUnderCap": cap_reps, "replicates": replicates,
                     "capBinds": cap_reps is not None and min(need, MAX_REPLICATES) > cap_reps,
                     "confirmatoryTrials": 4 * cells * replicates,
                     "projectedCostUsd": round(per_rep * replicates, 2)},
        "label": "PILOT ESTIMATE (planning only; pooled across arms and models)", "pilotTrials": len(rows),
        "archAcceptanceRatePooled": {"rate": round(rate, 4), "clampedTo": [0.05, 0.95], "designEffect": deff},
        "acceptanceDifferenceD-A": {"delta": DELTA, "trialsPerArm": trials_diff, "replicatesPerCell": reps(trials_diff)},
        "logRatioVariancePerTrialPooled": round(v, 6),
        "primaryRatioD/A": {"ratio": RATIO, "trialsPerArm": trials_ratio, "replicatesPerCell": reps(trials_ratio)},
        "resource": {"meanCostPerTrialUsd": round(mean_cost, 4), "byModel": by_model, "meanWallMinutesPerTrial": round(mean_wall, 2),
                     "costPerReplicateUsd": round(per_rep, 2), "capUsd": cap,
                     "byReplicates": {str(k): {"trials": 4 * cells * k, "costUsd": round(per_rep * k, 2),
                                               "wallHoursAtConcurrency": round(4 * cells * k * mean_wall / 60 / conc, 2)} for k in (2, 3, 4)}},
        "tasks": tasks, "models": models,
        "assumptions": "two-sided alpha 0.05, power 0.80; normal approximation; rho 0.5 within trial; pilot spread is a floor estimate"}


def main(argv):
    flags = argv[1:]
    opt = lambda k, d: flags[flags.index(k) + 1] if k in flags else d
    pos = [a for i, a in enumerate(flags) if not a.startswith("--") and (i == 0 or not flags[i - 1].startswith("--"))]
    rows = [per_trial(d) for d in load(pos[0], opt("--label", "pilot"))]
    out = pos[1] if len(pos) > 1 else None
    result = plan(rows, int(opt("--tasks", 10)), int(opt("--models", 2)), float(opt("--cap-usd", 600)), int(opt("--concurrency", 3)))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if out:
        open(out, "w").write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv)
