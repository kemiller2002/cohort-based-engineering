#!/usr/bin/env python3
"""ARCH-001 sample-size planning from the PILOT (adapted from REL-001 run-03 analysis/power.py; see PROVENANCE.md).

usage: python3 -I power.py PILOT_OBSERVATIONS_DIR [OUT.json] [--cap-usd N] [--tasks 8] [--concurrency 3]
                           [--label pilot]

Label: PILOT ESTIMATE (8 trials: T1 and T8 x 4 arms x 1 replicate). Planning numbers only; the normal approximation
stands in for the cluster bootstrap. Two targets, both D versus A, two-sided alpha 0.05, power 0.80:
  1. architectural-acceptance difference (per requirement, 2 per trial): two-proportion formula with the pilot
     rates (clamped to [0.05, 0.95]), inflated by the design effect 1 + (m - 1) rho for m = 2 requirements per trial
     (rho = 0.5, conservative), for a minimum detectable difference of the pilot's observed difference and of
     0.15 / 0.20 / 0.30;
  2. primary ratio (cost per accepted requirement): delta method on the ratio of sums,
     Var(log R_arm) ~ (CV_cost^2 + CV_acc^2 - 2 r CV_cost CV_acc) / n, for detectable ratios 0.8 / 0.7 / 0.6,
     with the pilot spread and 1.5x the pilot spread (run-03's inflation convention).
Coordinator amendment (before preregistration): the sample size must not depend on the observed treatment
advantage, so the planning rates and spreads are POOLED over all pilot arms (no arm difference is used), and the
detectable effects are fixed in advance: acceptance difference 0.20 and cost ratio 0.70 (PROTOCOL.md section 9).
Trials per arm are converted into replicates per (task, arm) cell for TASKS tasks. The resource view multiplies the
pilot's mean cost and wall time per trial by the confirmatory trial count, compares the cost with --cap-usd, and
gives the largest replicate count the cap allows.
"""
import glob
import json
import math
import os
import statistics
import sys

Z = 1.959964 + 0.841621


def load(directory, label):
    docs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(directory, "**", "*.json"), recursive=True))]
    return [d for d in docs if isinstance(d, dict) and d.get("schema") == "arch001.observation/1" and d.get("label") == label and not d.get("excluded")]


def per_trial(d):
    reqs = d.get("requirements") or []
    wall = sum((ph or {}).get("wallMs") or 0 for ph in (d.get("phases") or {}).values())
    return {"arm": d["arm"], "cost": (d.get("cost") or {}).get("totalUsd") or 0.0, "accepted": sum(1 for r in reqs if r.get("accepted")),
            "arch": sum(1 for r in reqs if r.get("archAccept")), "wallMs": wall}


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


def main(argv):
    flags = argv[1:]
    opt = lambda k, d: flags[flags.index(k) + 1] if k in flags else d
    pos = [a for i, a in enumerate(flags) if not a.startswith("--") and (i == 0 or not flags[i - 1].startswith("--"))]
    rows = [per_trial(d) for d in load(pos[0], opt("--label", "pilot"))]
    out = pos[1] if len(pos) > 1 else None
    tasks, cap, conc = int(opt("--tasks", 8)), float(opt("--cap-usd", 2000)), int(opt("--concurrency", 3))
    arm = lambda a: [r for r in rows if r["arm"] == a]
    D, A = arm("D"), arm("A")
    if not D or not A:
        raise SystemExit("power.py needs pilot observations for arms A and D")
    # Pooled over every pilot arm: the planning rate never sees an arm difference.
    pooled_rate = clamp(sum(r["arch"] for r in rows) / (2 * len(rows)))
    pD = pA = pooled_rate
    deff = 1 + (2 - 1) * 0.5
    def trials_for_diff(delta):
        n_req = (Z ** 2) * (pD * (1 - pD) + pA * (1 - pA)) / (delta ** 2) * deff
        return math.ceil(n_req / 2)
    acceptance = {f"delta {d}": {"trialsPerArm": trials_for_diff(d), "replicatesPerCell": math.ceil(trials_for_diff(d) / tasks)}
                  for d in (0.15, 0.2, 0.3)}
    # Pooled spread: the per-trial log-ratio variance is estimated from all pilot trials, not per arm.
    vD = vA = log_ratio_var(rows)
    def trials_for_ratio(r, f):
        return math.ceil((Z ** 2) * (f ** 2) * (vD + vA) / (math.log(r) ** 2))
    ratio = {f"spread x{f}": {f"ratio {r}": {"trialsPerArm": trials_for_ratio(r, f), "replicatesPerCell": math.ceil(trials_for_ratio(r, f) / tasks)}
                              for r in (0.8, 0.7, 0.6)} for f in (1.0, 1.5)}
    mean_cost = statistics.mean(r["cost"] for r in rows)
    mean_wall = statistics.mean(r["wallMs"] for r in rows) / 60000
    per_rep = 4 * tasks * mean_cost
    resource = {"meanCostPerTrialUsd": round(mean_cost, 4), "meanWallMinutesPerTrial": round(mean_wall, 2),
                "costPerReplicateUsd": round(per_rep, 2), "capUsd": cap,
                "maxReplicatesUnderCap": math.floor(cap / per_rep) if per_rep else None,
                "byReplicates": {str(k): {"trials": 4 * tasks * k, "costUsd": round(per_rep * k, 2),
                                          "wallHoursAtConcurrency": round(4 * tasks * k * mean_wall / 60 / conc, 2)} for k in (2, 3, 4, 5, 6)}}
    need = max(acceptance["delta 0.2"]["replicatesPerCell"], ratio["spread x1.0"]["ratio 0.7"]["replicatesPerCell"])
    cap_reps = resource["maxReplicatesUnderCap"] or 0
    decision = {"rule": "replicates = max(2, min(needed, maxReplicatesUnderCap, 5)); needed = max(acceptance delta 0.20, ratio 0.70 at x1.0 spread)",
                "needed": need, "maxReplicatesUnderCap": cap_reps, "replicates": max(2, min(need, cap_reps, 5)),
                "capBinds": min(need, 5) > cap_reps}
    result = {"decision": decision, "label": "PILOT ESTIMATE (planning only; 1 replicate x 2 tasks per arm)", "pilotTrials": len(rows),
              "archAcceptanceRatePooled": {"rate": round(pooled_rate, 4), "clampedTo": [0.05, 0.95], "designEffect": deff},
              "acceptanceDifferenceD-A": acceptance,
              "logRatioVariancePerTrialPooled": round(vD, 6), "primaryRatioD/A": ratio,
              "resource": resource, "tasks": tasks,
              "assumptions": "two-sided alpha 0.05, power 0.80; normal approximation; rho 0.5 within trial; pilot spread is a floor estimate"}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if out:
        open(out, "w").write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv)
