#!/usr/bin/env python3
"""cbe.token-overhead/1 profiler (stdlib only, deterministic).

usage:
  profile.py observations --dataset ID --label TEXT --root DIR --glob PATTERN [--arms A,B]
                          [--price-table FILE] --config FILE [--within-arm-only] --out FILE
  profile.py transcripts  --dataset ID --label TEXT --root DIR --glob PATTERN [--price-table FILE] --out FILE
  profile.py briefs       --root DIR --profile FILE --out FILE
  profile.py check        FILE...

Paths in outputs are relative to --root; no wall-clock time is written, so a re-run on the
same inputs reproduces the same bytes.
"""
import glob
import os
import sys

import briefs
import observations as O
import records as R
import transcripts as T

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "..", "overhead-schema.json")

# Final-message output measured by the orchestrator in run-01 (Praxis ReliabilityReport.fs:240-246):
# 120..761 tokens against 3..24 in the transcript. Used only as a labelled scenario range.
OUTPUT_SCENARIO_PER_REQUEST = (120, 761)


FLAGS = ("--within-arm-only",)


def args_of(argv):
    """({option: value}, {flag}) from `--key value` pairs and bare FLAGS."""
    clean = [a for a in argv if a not in FLAGS]
    return {k.lstrip("-"): v for k, v in zip(clean[::2], clean[1::2])}, {a for a in argv if a in FLAGS}


def files(root, pattern):
    return sorted(glob.glob(os.path.join(root, pattern)))


def rel(root, p):
    return os.path.relpath(p, root)


def load_price(path):
    return R.read_json(path) if path else None


# ---------------------------------------------------------------- observations

def prefix_estimate(config, dataset, facts):
    pair = R.get(config, "coldPairs", dataset)
    if not pair:
        return None, "no cold pair configured"
    by = {f["runId"]: f for f in facts}
    cold, ref = by.get(pair["cold"]), by.get(pair["reference"])
    if not cold or not ref:
        return None, "cold pair not in dataset"
    p = cold["x"]["tokens"]["cacheWrite"] / cold["x"]["agents"] - ref["x"]["tokens"]["cacheWrite"] / ref["x"]["agents"]
    return round(p), f"cacheWrite({pair['cold']}) - cacheWrite({pair['reference']}); {pair['basis']}"


def run_derived(f, P, cw_median, entry):
    x, tok, n = f["x"], f["x"]["tokens"], f["x"]["requests"] or 0
    cw_agent = (tok["cacheWrite"] or 0) / x["agents"]
    miss = P is not None and cw_median is not None and cw_agent >= cw_median + P / 2
    missed_agents = max(1, min(x["agents"], round(((tok["cacheWrite"] or 0) - x["agents"] * cw_median) / P))) if miss else 0
    prefix = None if P is None else min(tok["cacheRead"] or 0, max(0, n - missed_agents) * P)
    ck = R.cost_by_kind(tok, entry)
    c_total = R.cost(tok, entry)
    lo, hi = (n * OUTPUT_SCENARIO_PER_REQUEST[0], n * OUTPUT_SCENARIO_PER_REQUEST[1])
    add = None if not entry else [round(max(0, v - (tok["output"] or 0)) * entry["output"] / 1e6, 6) for v in (lo, hi)]
    ests = {r["phase"] if r["recordId"].split(":")[-1] != "residual" else "residual": r["tokenEstimate"]["total"]
            for r in f["records"] if r["granularity"] == "run-phase-estimate" and r["tokenEstimate"]}
    est_sum = sum(ests.values())
    ms = {r["recordId"].split(":")[-1]: r["elapsedMs"] for r in f["records"] if r["granularity"] == "run-phase-estimate"}
    all_tokens = sum((tok.get(k) or 0) for k in ("input", "output", "cacheRead", "cacheWrite"))
    workflow_cmds = x["claims"] + x["verifications"] + x["completions"]
    return {
        "runId": f["runId"], "arm": f["arm"], "task": f["task"],
        "requests": n, "agents": x["agents"], "toolCalls": x["toolCalls"],
        "meanContextPerRequest": round(f["meanCtx"]) if f["meanCtx"] else None,
        "cacheWritePerAgent": round(cw_agent),
        "suspectedPrefixCacheMiss": miss,
        "suspectedMissedAgents": missed_agents,
        "avoidableMissCostUsd": round(missed_agents * P * (entry["cacheWrite5m"] - entry["cacheRead"]) / 1e6, 6) if (miss and entry) else (0.0 if entry else None),
        "prefixRereadTokens": prefix,
        "prefixRereadShareOfCacheRead": R.ratio(prefix, tok["cacheRead"]),
        "prefixRereadShareOfAllTokens": R.ratio(prefix, all_tokens),
        "cacheShareOfTokens": R.ratio((tok["cacheRead"] or 0) + (tok["cacheWrite"] or 0), all_tokens),
        "costByKind": ck,
        "costShares": None if not ck or not c_total else {k: R.ratio(v, c_total) for k, v in ck.items()},
        "outputScenarioAddedCostUsd": add,
        "outputScenarioRelativeUnderstatement": None if not add or not c_total else [R.ratio(a, c_total) for a in add],
        "phaseTokenEstimateShares": {k: R.ratio(v, est_sum) for k, v in sorted(ests.items())} if est_sum else None,
        "phaseElapsedMs": ms,
        "phaseElapsedShares": {k: R.ratio(v, x["wallMs"]) for k, v in ms.items() if v is not None} if x["wallMs"] else None,
        "workflowCommands": workflow_cmds,
        "workflowCommandShareOfToolCalls": R.ratio(workflow_cmds, x["toolCalls"]),
        "agentTestRuns": x["agentTestRuns"],
        "boundaryTestRuns": x["boundaryTestRuns"],
        "testRunsBeyondOneBoundaryRun": x["agentTestRuns"] + max(0, x["boundaryTestRuns"] - 1),
        "completionTimingsMs": x["completionTimings"],
        "harnessSubagentTokens": x["harnessSubagentTokens"],
    }


def group_summary(rows, within_arm_only):
    med = lambda k: R.median([r[k] for r in rows])
    med_sub = lambda k, sub: R.median([(r[k] or {}).get(sub) for r in rows])
    phases_ = sorted({p for r in rows for p in (r["phaseTokenEstimateShares"] or {})})
    ms_keys = sorted({p for r in rows for p in (r["phaseElapsedShares"] or {})})
    out = {
        "runs": len(rows),
        "medianRequests": med("requests"),
        "medianToolCalls": med("toolCalls"),
        "medianPrefixRereadShareOfCacheRead": med("prefixRereadShareOfCacheRead"),
        "medianCacheShareOfTokens": med("cacheShareOfTokens"),
        "medianCostShares": {k: med_sub("costShares", k) for k in ("input", "output", "cacheRead", "cacheWrite")},
        "medianOutputScenarioRelativeUnderstatement": [R.median([(r["outputScenarioRelativeUnderstatement"] or [None, None])[i] for r in rows]) for i in (0, 1)],
        "medianPhaseTokenEstimateShares": {p: med_sub("phaseTokenEstimateShares", p) for p in phases_},
        "medianPhaseElapsedShares": {p: med_sub("phaseElapsedShares", p) for p in ms_keys},
        "medianWorkflowCommandShareOfToolCalls": med("workflowCommandShareOfToolCalls"),
        "agentTestRuns": sum(r["agentTestRuns"] for r in rows),
        "boundaryTestRuns": sum(r["boundaryTestRuns"] for r in rows),
        "testRunsBeyondOneBoundaryRun": sum(r["testRunsBeyondOneBoundaryRun"] for r in rows),
        "suspectedPrefixCacheMissRuns": sorted(r["runId"] for r in rows if r["suspectedPrefixCacheMiss"]),
        "avoidableMissCostUsd": round(sum(r["avoidableMissCostUsd"] or 0 for r in rows), 6),
        "medianMeanContextPerRequest": med("meanContextPerRequest"),
    }
    # within-arm-only: keep composition shares (where tokens go), drop counts, costs and
    # anything an arm-vs-arm reader could take as an outcome comparison
    shares_only = ("runs", "medianPrefixRereadShareOfCacheRead", "medianCacheShareOfTokens", "medianPhaseTokenEstimateShares",
                   "medianPhaseElapsedShares", "medianWorkflowCommandShareOfToolCalls")
    return {k: v for k, v in out.items() if k in shares_only} if within_arm_only else out


def cmd_observations(o, flags):
    root, price = o["root"], load_price(o.get("price-table"))
    config = R.read_json(o["config"])
    arms = set(o["arms"].split(",")) if o.get("arms") else None
    paths = [p for p in files(root, o["glob"]) if p.endswith(".json")]
    obs = [(p, R.read_json(p)) for p in paths]
    obs = [(p, d) for p, d in obs if d.get("schema") == "cbe.rel-001.observation/1" and (arms is None or d.get("arm") in arms) and d.get("status") == "completed"]
    def fact(p, d):
        recs, x, mean_ctx = O.run_records(d, p, rel(root, p), R.sha256_file(p), price)
        return {"runId": d["runId"], "arm": d["arm"], "task": R.get(d, "task", "taskId"), "records": recs, "x": x, "meanCtx": mean_ctx}

    facts = [fact(p, d) for p, d in obs]
    P, P_basis = prefix_estimate(config, o["dataset"], facts)
    cw_median = R.median([f["x"]["tokens"]["cacheWrite"] / f["x"]["agents"] for f in facts])
    entry = R.price_entry(price, facts[0]["x"]["model"]) if facts else None
    rows = [run_derived(f, P, cw_median, entry) for f in facts]
    within = "--within-arm-only" in flags
    by_arm = {a: group_summary([r for r in rows if r["arm"] == a], within) for a in sorted({r["arm"] for r in rows})}
    pooled = group_summary(rows, False)
    pooled_tokens = {k: R.total([f["x"]["tokens"][k] for f in facts]) for k in ("input", "output", "cacheRead", "cacheWrite")}
    summary = {
        "label": o["label"],
        "fixedPrefixTokens": {"value": P, "basis": P_basis, "method": "derived (cold-cache trial minus its warm same-task partner)"},
        "cacheWriteMedianPerAgent": round(cw_median) if cw_median is not None else None,
        "prefixMissRule": "suspected when cacheWrite per agent >= dataset median + fixedPrefixTokens/2 (inferred; per-request data unavailable)",
        "outputScenario": {"perRequestFinalOutputRange": list(OUTPUT_SCENARIO_PER_REQUEST), "basis": "praxis src/Praxis.Domain/Telemetry/ReliabilityReport.fs:240-246 (run-01 final messages: 120-761 actual vs 3-24 in transcript)"},
        "pooled": {**pooled, "tokens": pooled_tokens, "estimatedCostUsd": round(sum(R.cost(f["x"]["tokens"], entry) or 0 for f in facts), 6) if entry else None},
        "byArm": by_arm,
        "perRun": rows if not within else [{k: v for k, v in r.items() if k in (
            "runId", "arm", "task", "agents", "cacheWritePerAgent", "suspectedPrefixCacheMiss", "prefixRereadShareOfCacheRead",
            "phaseTokenEstimateShares", "phaseElapsedShares", "completionTimingsMs")} for r in rows],
    }
    price_input = [{"path": "price-table:" + os.path.basename(o["price-table"]), "sha256": R.sha256_file(o["price-table"])}] if o.get("price-table") else []
    doc = R.document(o["dataset"], o["label"], [{"path": rel(root, p), "sha256": R.sha256_file(p)} for p, _ in obs] + price_input,
                     [r for f in facts for r in f["records"]], summary)
    R.write(o["out"], doc)
    return doc


# ---------------------------------------------------------------- transcripts

def cmd_transcripts(o, flags):
    root, price = o["root"], load_price(o.get("price-table"))
    paths = files(root, o["glob"])
    def one(p):
        with open(p, encoding="utf-8") as fh:
            entries, malformed = T.parse_lines(fh.read())
        recs, found = T.profile(entries, rel(root, p), R.sha256_file(p), price, execution_id=os.path.splitext(os.path.basename(p))[0])
        return p, recs, {**found, "malformedLines": malformed}

    results = [one(p) for p in paths]
    recs = [r for _, rs, _ in results for r in rs]
    by_phase = {
        ph: {
            "requests": len(rs),
            "tokens": sum(sum((r["tokens"].get(k) or 0) for k in ("input", "output", "cacheRead", "cacheWrite")) for r in rs),
            "cacheRead": sum(r["tokens"]["cacheRead"] or 0 for r in rs),
            "cacheWrite": sum(r["tokens"]["cacheWrite"] or 0 for r in rs),
            "toolResultBytes": sum(r["toolResultBytes"] or 0 for r in rs),
            "testRuns": sum(r["testRuns"] or 0 for r in rs),
        }
        for ph in sorted({r["phase"] for r in recs})
        for rs in [[r for r in recs if r["phase"] == ph]]
    }
    grand = sum(v["tokens"] for v in by_phase.values())
    summary = {
        "label": o["label"],
        "byPhase": {k: {**v, "shareOfTokens": R.ratio(v["tokens"], grand)} for k, v in sorted(by_phase.items())},
        "perTranscript": {rel(root, p): f for p, _, f in results},
        "firstRequestCacheWrites": [r["recordId"] for r in recs if "first-request-cache-write" in r["flags"]],
        "outputLowerBound": True,
    }
    doc = R.document(o["dataset"], o["label"], [{"path": rel(root, p), "sha256": R.sha256_file(p)} for p in paths], recs, summary)
    R.write(o["out"], doc)
    return doc


# ---------------------------------------------------------------- briefs / check

def cmd_briefs(o, flags):
    sizes = briefs.run02(o["root"])
    prof = R.read_json(o["profile"])
    n = R.get(prof, "summary", "pooled", "medianRequests") or 0
    d_tok = sizes["directives"]["tokensEstimate"]
    carry = {
        arm: {
            "pooledMedianRequests": n,
            "briefTokensEstimate": t["tokensEstimate"],
            "briefCarryCacheReadEstimate": briefs.carry(t["tokensEstimate"], n - 1),
            "directivesCarryCacheReadEstimate": briefs.carry(d_tok, n - 2),
            "assumption": "pooled median request count of the profile (both arms); brief read by request 1, directives by request 2, both stay in context to the end; estimate (bytes//4)",
        }
        for arm, t in sizes["briefTemplates"].items()
    }
    out = {"schema": "cbe.token-overhead/1#context-sizes", "generator": R.GENERATOR, "sizes": sizes, "carry": carry}
    R.write(o["out"], out)
    return out


def cmd_check(paths):
    schema = R.read_json(SCHEMA_PATH)
    errs = [(p, R.check(schema, R.read_json(p))) for p in paths]
    for p, e in errs:
        print(f"{p}: {'ok' if not e else str(len(e)) + ' violation(s)'}")
        for line in e[:20]:
            print("  " + line)
    return 1 if any(e for _, e in errs) else 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "check":
        return cmd_check(argv[2:])
    opts, flags = args_of(argv[2:])
    {"observations": cmd_observations, "transcripts": cmd_transcripts, "briefs": cmd_briefs}[argv[1]](opts, flags)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
