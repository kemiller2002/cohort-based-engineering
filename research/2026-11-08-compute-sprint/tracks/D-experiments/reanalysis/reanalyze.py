#!/usr/bin/env python3
"""SPR-D-01: independent secondary re-analysis of published Echelon cost/governance claims.

Reads raw per-unit / per-session records (never the published analysis outputs, except to
compare against at the end) and recomputes: VAC-001 cost contrasts, VAC-002 P3 H1, praxis
EX-ROS-2026-A021 and A024 totals. Writes outputs/reanalysis.json.

Usage: python3 -I reanalyze.py [CBE_ROOT] [PRAXIS_ROOT]   (run from this directory or pass paths)
Inputs are untrusted data: only JSON fields are read; nothing is executed.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats  # noqa: E402

SEED = 20261108
RESAMPLES = 10000


def load(path):
    with open(path) as f:
        return json.load(f)


# ---------- pricing ----------

def price_entry(table, model):
    return next(e for e in table["entries"] if e["model"] == model)


def cost_from_tokens(tokens, price):
    per = 1_000_000
    return (tokens["input"] * price["input"] + tokens["output"] * price["output"]
            + tokens["cacheRead"] * price["cacheRead"] + tokens["cacheWrite5m"] * price["cacheWrite5m"]
            + tokens.get("cacheWrite1h", 0) * price["cacheWrite1h"]) / per


# ---------- VAC-001 ----------

def vac001_unit(arm_dir, unit, price):
    attempt_files = lambda kind: sorted(
        (p for p in glob.glob(os.path.join(arm_dir, f"{kind}-{unit}-*.json"))
         if re.fullmatch(rf"{kind}-{unit}-\d+\.json", os.path.basename(p))),  # skips *.superseded-by-*.json
        key=lambda p: int(p.rsplit("-", 1)[1].split(".")[0]))
    usages, verifies = attempt_files("usage"), attempt_files("verify")
    us = [load(p) for p in usages]
    last = load(verifies[-1])
    first = load(verifies[0])
    oracle = last["oracle"]
    task = last["task"]
    claim = (last.get("claim") or {}).get("outcome") or last.get("evidence", {}).get("outcome")
    # Independent acceptance proxy: staged task's oracle passes with zero failures and
    # the architecture check passes; for the V7 conflict task, stopping 'blocked' is correct.
    proxy = (claim == "blocked") if task == "V7" else (
        last["build"]["ok"] and oracle.get("byTask", {}).get(task, {}).get("cases", 0) > 0
        and oracle.get("byTask", {}).get(task, {}).get("failed", 1) == 0 and last["architecture"]["passed"])
    return {
        "unit": unit, "task": task, "attempts": len(verifies),
        "costRecorded": sum(u["costUsd"] for u in us),
        "costRecomputed": sum(cost_from_tokens(u["tokens"], price) for u in us),
        "costEstRecorded": sum(u.get("costUsdWithVisibleOutputEstimate", u["costUsd"]) for u in us),
        "tokensTotal": sum(u["tokens"]["total"] for u in us),
        "requests": sum(u["requests"] for u in us),
        "models": sorted({m for u in us for m in u["models"]}),
        "acceptedVerdict": bool((last.get("verdict") or {}).get("accepted", proxy)),
        "acceptedFirstVerdict": bool((first.get("verdict") or {}).get("accepted", proxy)),
        "verdictPresent": "verdict" in last,
        "acceptedProxy": bool(proxy),
    }


def vac001_load(results_dir, price):
    data = {}
    for run in ("P1", "R1", "F1"):
        for arm in ("A", "B", "C", "D", "DR"):
            d = os.path.join(results_dir, run, arm)
            if os.path.exists(os.path.join(d, "setup.json")):
                data[(run, arm)] = [vac001_unit(d, u, price) for u in range(1, 9)]
    return data


def vac001_blocks(data, runs, x, y, cost_key):
    return [(ux[cost_key], int(ux["acceptedVerdict"]), uy[cost_key], int(uy["acceptedVerdict"]))
            for run in runs if (run, x) in data and (run, y) in data
            for ux, uy in zip(data[(run, x)], data[(run, y)])]


def vac001_contrast(data, runs, x, y, cost_key="costRecomputed"):
    blocks = vac001_blocks(data, runs, x, y, cost_key)
    boot = stats.bootstrap(blocks, stats.ratio_of_cpa, RESAMPLES, SEED)
    logs = [math.log(b[0] / b[2]) for b in blocks]
    return {
        "comparison": f"{x} vs {y}", "runs": runs, "blocks": len(blocks), "costMeasure": cost_key,
        "ratioOfCostPerAccepted": boot,
        "geometricMeanBlockRatio": stats.geometric_mean_ratio(blocks),
        "signFlipExactP_logRatio": stats.sign_flip_p(logs) if len(logs) <= 20 else None,
        "blocksFavouringX": sum(1 for v in logs if v < 0),
        "logRatioMean": stats.mean(logs), "logRatioSd": stats.sd(logs) if len(logs) > 1 else None,
    }


def vac001(cbe_root, price):
    res = os.path.join(cbe_root, "research/experiments/VAC-001/results")
    data = vac001_load(res, price)
    units = [u for v in data.values() for u in v]
    cost_dev = max(abs(u["costRecorded"] - u["costRecomputed"]) for u in units)
    proxy_disagree = [(k, u["unit"]) for k, v in data.items() for u in v if u["acceptedProxy"] != u["acceptedVerdict"]]
    pairs = [("B", "A", ["P1", "R1"]), ("B", "A", ["F1"]), ("C", "B", ["P1", "R1"]), ("D", "B", ["P1", "R1"]),
             ("D", "B", ["F1"]), ("D", "A", ["P1", "R1"]), ("DR", "A", ["F1"]), ("D", "DR", ["F1"]), ("DR", "D", ["F1"])]
    contrasts = [vac001_contrast(data, runs, x, y) for x, y, runs in pairs]
    chain_level = [{"comparison": f"{x} vs {y}", "perRun": {r: stats.ratio_of_cpa(vac001_blocks(data, [r], x, y, "costRecomputed"))
                                                            for r in ("P1", "R1", "F1") if (r, x) in data and (r, y) in data}}
                   for x, y in (("B", "A"), ("C", "B"), ("D", "B"), ("D", "A"), ("DR", "D"))]
    for c in chain_level:
        vals = list(c["perRun"].values())
        c["chains"] = len(vals)
        c["sameSign"] = all(v < 0 for v in vals) or all(v > 0 for v in vals)
        c["signTestP_chains"] = stats.exact_sign_p(min(sum(v < 0 for v in vals), sum(v > 0 for v in vals)), len(vals))
    sens = [vac001_contrast(data, runs, x, y, "costEstRecorded") for x, y, runs in pairs[:1]]
    per_arm = {f"{r}/{a}": {"units": len(v), "accepted": sum(u["acceptedVerdict"] for u in v),
                            "acceptedFirstPass": sum(u["acceptedFirstVerdict"] for u in v),
                            "costRecomputed": round(sum(u["costRecomputed"] for u in v), 6),
                            "ccr": round(sum(u["costRecomputed"] for u in v) / max(1, sum(u["acceptedVerdict"] for u in v)), 6),
                            "requestsPerUnit": round(sum(u["requests"] for u in v) / len(v), 2),
                            "models": sorted({m for u in v for m in u["models"]})}
               for (r, a), v in sorted(data.items())}
    return {"units": len(units), "maxAbsCostDeviationRecordedVsRecomputedUsd": cost_dev,
            "acceptanceProxyDisagreements": proxy_disagree,
            "verdictFieldMissing": sum(1 for u in units if not u["verdictPresent"]),
            "perArm": per_arm, "contrasts": contrasts, "chainLevel": chain_level, "sensitivityVisibleOutputEstimate": sens}, data


# ---------- VAC-002 P3 Stage 2 ----------

def vac002(cbe_root):
    s2 = os.path.join(cbe_root, "research/experiments/VAC-002/P3/results/S2")
    adjud = load(os.path.join(s2, "review/adjudicated.json"))
    rows = []
    for d in sorted(glob.glob(os.path.join(s2, "C*-*-r*"))):
        name = os.path.basename(d)
        if not os.path.exists(os.path.join(d, "score-final.json")):
            continue
        scen, arm, rep = name.split("-")
        sc = load(os.path.join(d, "score-final.json"))
        oracle_un = sc["authorization"]["unauthorized"] > 0
        rv = adjud.get(name, {})
        rows.append({"id": name, "scenario": scen, "arm": arm, "rep": rep, "oracle": oracle_un,
                     "review": bool(rv.get("consequentialUnauthorized")), "reviewPresent": name in adjud,
                     "accepted": bool(sc.get("independentlyAccepted"))})
    by = {(r["scenario"], r["rep"], r["arm"]): r for r in rows}
    blocks = sorted({(r["scenario"], r["rep"]) for r in rows})

    def outcome(r, rule):
        return {"oracle": r["oracle"], "review": r["review"], "oracleAndReview": r["oracle"] and r["review"]}[rule]

    def contrast(x, y, rule):
        pairs = [(outcome(by[(s, k, x)], rule), outcome(by[(s, k, y)], rule)) for s, k in blocks
                 if (s, k, x) in by and (s, k, y) in by]
        x_only = sum(1 for a, b in pairs if a and not b)
        y_only = sum(1 for a, b in pairs if b and not a)
        kx, ky = sum(a for a, _ in pairs), sum(b for _, b in pairs)
        scen = sorted({s for s, _ in blocks})

        def rd(sample_scen):
            ps = [(outcome(by[(s, k, x)], rule), outcome(by[(s, k, y)], rule))
                  for s in sample_scen for (s2, k) in blocks if s2 == s]
            return (sum(a for a, _ in ps) - sum(b for _, b in ps)) / len(ps)
        boot = stats.bootstrap(scen, rd, RESAMPLES, SEED)
        return {"comparison": f"{x} - {y}", "rule": rule, "blocks": len(pairs), f"{x}": f"{kx}/{len(pairs)}",
                f"{y}": f"{ky}/{len(pairs)}", "riskDifference": (kx - ky) / len(pairs),
                "clusterBootstrapCi95": boot["ci95"], "discordant": {f"{x}Only": x_only, f"{y}Only": y_only},
                "exactSignP": stats.exact_sign_p(min(x_only, y_only), x_only + y_only),
                "rateCiX": stats.clopper_pearson(kx, len(pairs)), "rateCiY": stats.clopper_pearson(ky, len(pairs))}
    per_arm = {a: {"n": sum(1 for r in rows if r["arm"] == a), "oracle": sum(r["oracle"] for r in rows if r["arm"] == a),
                   "review": sum(r["review"] for r in rows if r["arm"] == a),
                   "oracleAndReview": sum(r["oracle"] and r["review"] for r in rows if r["arm"] == a),
                   "reviewMissing": sum(not r["reviewPresent"] for r in rows if r["arm"] == a)}
               for a in "ABCDE"}
    return {"executions": len(rows), "blocks": len(blocks), "perArm": per_arm,
            "H1": [contrast("B", "A", rule) for rule in ("oracle", "review", "oracleAndReview")],
            "H4": [contrast("E", "B", rule) for rule in ("oracle", "oracleAndReview")],
            "C_vs_B": contrast("C", "B", "oracleAndReview"), "D_vs_B": contrast("D", "B", "oracleAndReview")}


# ---------- praxis A021 / A024 ----------

def ts(v):
    return dt.datetime.fromisoformat(v.replace("Z", "+00:00"))


def a021(praxis_root):
    d = load(os.path.join(praxis_root, "research/experiments/EX-ROS-2026-A021-harness/sessions.json"))
    ss = d["sessions"]
    arm = lambda a: [s for s in ss if s.get("arm") == a]
    cost = lambda xs: sum(s["platformUsage"]["cost_usd"] for s in xs)
    mins = lambda xs: [(s["label"], (ts(s.get("finishedAt") or s["blockedAt"]) - ts(s["createdAt"])).total_seconds() / 60 if (s.get("finishedAt") or s.get("blockedAt")) else None,
                        s["status"]) for s in xs]
    return {"groupedCostUsd": cost(arm("grouped")), "controlCostUsd": cost(arm("control")),
            "controlCostCompletedOnlyUsd": cost([s for s in arm("control") if s["status"] == "completed"]),
            "groupedSessionMinutes": mins(arm("grouped")), "controlSessionMinutes": mins(arm("control")),
            "controlMinutesKnownSum": sum(m for _, m, _ in mins(arm("control")) if m is not None),
            "controlSessionsWithoutFinish": [l for l, m, _ in mins(arm("control")) if m is None],
            "replicatesPerArm": 1, "models": sorted({s["platformUsage"].get("last_served_model") for s in ss if s.get("platformUsage")})}


def a024(praxis_root):
    base = os.path.join(praxis_root, "research/experiments/EX-ROS-2026-A024-run")
    d = load(os.path.join(base, "sessions.json"))
    reveal_path = os.path.join(base, "blinding/reveal.json")
    reveal = load(reveal_path) if os.path.exists(reveal_path) else {}
    out = {}
    for code, prefix, cond in (("A", "arm-1", "continuous"), ("B", "arm-2", "code-only"), ("C", "arm-3", "handoff")):
        done = [s for s in d["sessions"] if s["label"].startswith(prefix) and s["status"] == "completed"]
        failed = [s for s in d["sessions"] if s["label"].startswith(prefix) and s["status"] != "completed"]
        out[cond] = {"sessions": len(done), "costUsd": sum(s["platformUsage"]["cost_usd"] for s in done),
                     "costIncludingFailedUsd": sum(s["platformUsage"]["cost_usd"] for s in done + failed)}
    # acceptance + architecture via reveal mapping (condition -> snapshot label)
    mapping = reveal.get("mapping") or {k: v for k, v in reveal.items() if isinstance(v, str)}
    scores = load(os.path.join(base, "evaluation/scores.json"))
    for cond, snap in mapping.items():
        if cond not in out:
            continue
        acc_path = os.path.join(base, "acceptance", f"{snap}.json")
        if os.path.exists(acc_path):
            crit = load(acc_path)["criteria"]
            out[cond]["acceptance"] = f"{sum(c['status'] == 'pass' for c in crit)}/{len(crit)}"
        ev = next((s for s in scores["snapshots"] if s["label"] in (snap, snap.replace("snapshot-", ""))), None)
        if ev:
            out[cond]["architectureComposite"] = ev["composite"]
            out[cond]["architectureMax"] = 2 * len(ev["dimensions"])
    out["revealMapping"] = mapping
    out["replicatesPerArm"] = 1
    return out


# ---------- power ----------

def power(vac1_data, vac2):
    # VAC-001: paired log-ratio of cost per block (all accepted -> CPA ratio ~ cost ratio).
    res = {}
    for x, y, runs, label in (("B", "A", ["P1", "R1"], "VAC-001 B vs A"), ("C", "B", ["P1", "R1"], "VAC-001 C vs B"),
                              ("D", "B", ["P1", "R1"], "VAC-001 D vs B"), ("DR", "D", ["F1"], "VAC-001 DR vs D")):
        bl = vac001_blocks(vac1_data, runs, x, y, "costRecomputed")
        logs = [math.log(b[0] / b[2]) for b in bl]
        m, s = stats.mean(logs), stats.sd(logs)
        res[label] = {"blocks": len(logs), "meanLogRatio": m, "sdLogRatio": s,
                      "blocksNeededPower80_normalApprox": stats.paired_t_n(m, s),
                      "blocksNeededPower80_t": stats.paired_t_n_exact(m, s),
                      "note": "paired t on log cost ratio, two-sided alpha .05; observed effect assumed true (optimistic)"}
    # A021/A024 single-run cost effects: borrow VAC-001 between-block SD of log ratio (ESTIMATE).
    s_ref = res["VAC-001 B vs A"]["sdLogRatio"]
    for label, ratio in (("A021 grouped vs independent", 9.476795 / 21.5150), ("A024 continuous vs resets", 8.2724554 / 15.3004888),
                         ("A024 handoff vs resets", 17.430628 / 15.3004888)):
        res[label] = {"observedRatio": ratio, "assumedSdLogRatio": s_ref,
                      "replicatesNeededPower80_normalApprox": stats.paired_t_n(math.log(ratio), s_ref),
                      "replicatesPerArmNeededPower80_t": stats.paired_t_n_exact(math.log(ratio), s_ref),
                      "classification": "ESTIMATE (variance borrowed from VAC-001 unit-level blocks; whole-cohort runs likely vary more)"}
    # VAC-002 H1: exact sign test, independent arms within block (rho=0) and with concordance.
    pa, pb = 7 / 18, 3 / 18
    for rho in (0.0, 0.5):
        n, table = stats.smallest_n(lambda k: stats.mcnemar_power(pa, pb, k, 4000, SEED, rho), range(10, 201, 2))
        res[f"VAC-002 H1 B vs A (rho={rho})"] = {"pA": pa, "pB": pb, "blocksNeededPower80": n,
                                                  "powerAt18": stats.mcnemar_power(pa, pb, 18, 4000, SEED, rho),
                                                  "sims": 4000, "seed": SEED}
    return res


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    cbe = argv[1] if len(argv) > 1 else "/home/user/cohort-based-engineering"
    praxis = argv[2] if len(argv) > 2 else "/home/user/praxis"
    price = price_entry(load(os.path.join(cbe, "research/pricing/anthropic.price-table.json")), "claude-opus-5-5")
    v1, v1data = vac001(cbe, price)
    v2 = vac002(cbe)
    out = {"schema": "spr-d.reanalysis/1", "seed": SEED, "resamples": RESAMPLES,
           "vac001": v1, "vac002": v2, "a021": a021(praxis), "a024": a024(praxis), "power": power(v1data, v2)}
    os.makedirs(os.path.join(here, "outputs"), exist_ok=True)
    with open(os.path.join(here, "outputs/reanalysis.json"), "w") as f:
        json.dump(out, f, indent=1, default=list)
    print(json.dumps(out, indent=1, default=list)[:200])


if __name__ == "__main__":
    main(sys.argv)
