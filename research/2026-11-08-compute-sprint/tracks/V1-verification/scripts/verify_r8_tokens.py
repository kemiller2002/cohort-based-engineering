"""Claims A-F-01, A-F-03, A-F-08: recompute from raw R8 Praxis execution records.
Usage: python3 -I verify_r8_tokens.py R8_REPO R3_REPO PRICE_TABLE OUT_JSON"""
import glob
import json
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1lib as L  # noqa: E402


def load_records(repo):
    return tuple(json.load(open(p)) for p in sorted(glob.glob(os.path.join(repo, ".ros/telemetry/executions/*.json"))))


def summary_payload(rec):
    ps = [r["payload"] for r in rec.get("rawTelemetry", []) if isinstance(r.get("payload"), dict) and "requestLedger" in r["payload"]]
    return ps[0] if ps else None


def role_of(rec):
    p = summary_payload(rec)
    if rec["workItemId"] == "WI-R8-COORD":
        return "coordinator"
    a = rec["identity"].get("agentId") or ""
    return a.split("/")[-1] if a else None


def price_entry(table, model):
    return next(e for e in table["entries"] if e["model"] == model)


def per_exec(rec, price):
    b = L.metric_buckets(rec["metrics"])
    p = summary_payload(rec)
    rows = L.ledger_rows(p["requestLedger"]) if p else ()
    led = L.sum_buckets(rows, ("input", "output", "cacheRead", "cacheWrite", "cacheWrite5m", "cacheWrite1h")) if rows else None
    return {
        "workItemId": rec["workItemId"],
        "role": role_of(rec),
        "buckets": b,
        "total4": L.total4(b),
        "costMetrics": L.price_cost(b, price) if L.total4(b) is not None else None,
        "costMetrics5mOnly": L.price_cost(b, price, split_cache_write=False) if L.total4(b) is not None else None,
        "requests": len(rows),
        "ledgerTotals": led,
        "ledgerMatchesMetrics": (led is not None and all(led[k] == b.get(k) for k in L.BUCKETS)),
        "costLedger": sum(L.price_cost(r, price) for r in rows) if rows else None,
        "contexts": tuple(L.context_tokens(r) for r in rows),
        "peak": p.get("peakContextTokens") if p else None,
        "agentSpan": (p["startedAt"], p["endedAt"]) if p else None,
        "rosSpan": (rec["startedAt"], rec.get("finalizedAt")),
    }


def coordinator_split(rows_all):
    coord = [r for r in rows_all if r["role"] == "coordinator"]
    task = [r for r in rows_all if r["role"] not in ("coordinator", None) and r["total4"] is not None]
    tot = sum(r["total4"] for r in rows_all if r["total4"] is not None)
    cost = sum(r["costMetrics"] for r in rows_all if r["costMetrics"] is not None)
    cctx = [c for r in coord for c in r["contexts"]]
    tctx = [c for r in task for c in r["contexts"]]
    ctok = sum(r["total4"] for r in coord)
    ccost = sum(r["costMetrics"] for r in coord)
    return {
        "coordTokens": ctok, "coordTokenShare": ctok / tot,
        "coordCost": ccost, "coordCostShare": ccost / cost,
        "coordRequests": len(cctx), "taskRequests": len(tctx),
        "coordMeanContext": sum(cctx) / len(cctx), "taskMeanContext": sum(tctx) / len(tctx),
        "coordPeakContext": max(cctx), "coordCostPerRequest": ccost / len(cctx),
        "taskCostPerRequest": sum(r["costMetrics"] for r in task) / len(tctx),
    }


def lane_stats(spans, t0, minutes):
    s = L.concurrency_samples(spans, t0, minutes)
    end = t0 + timedelta(minutes=minutes)
    return {"samples": len(s), "mean": sum(s) / len(s), "peak": max(s), "zeroMinutes": sum(1 for x in s if x == 0),
            "utilisationOf6": sum(s) / len(s) / 6, "exactMean": L.exact_mean_concurrency(spans, t0, end),
            "sumSpanMinutes": sum((b - a).total_seconds() for a, b in spans) / 60}


def main(r8, r3, price_path, out):
    table = json.load(open(price_path))
    price = price_entry(table, "claude-opus-5-5")
    recs = load_records(r8)
    rows = tuple(per_exec(r, price) for r in recs)
    with_tokens = [r for r in rows if r["total4"] is not None]
    totals = L.sum_buckets([r["buckets"] for r in with_tokens])
    total = sum(totals.values())
    cost = sum(r["costMetrics"] for r in with_tokens)
    cost5m = sum(r["costMetrics5mOnly"] for r in with_tokens)
    costLedger = sum(r["costLedger"] for r in with_tokens if r["costLedger"] is not None)

    # R3 self-reported $36.01 from its own token file (timed phase)
    r3t = json.load(open(os.path.join(r3, "evidence/telemetry/tokens-final.json")))["timed"]["all"]
    r3b = {"input": r3t["input_tokens"], "output": r3t["output_tokens"], "cacheRead": r3t["cache_read_input_tokens"],
           "cacheWrite": r3t["cache_creation_input_tokens"]}
    r3cost = L.price_cost(r3b, price, split_cache_write=False)

    # Lanes: task-agent transcript spans (exclude coordinator), T0 .. merge freeze
    t0 = L.parse_ts("2026-11-01T17:31:24Z")
    freeze = L.parse_ts("2026-11-01T23:50:28Z")
    task_rows = [r for r in rows if r["role"] not in ("coordinator", None) and r["agentSpan"]]
    agent_spans = tuple((L.parse_ts(a), L.parse_ts(b)) for a, b in (r["agentSpan"] for r in task_rows))
    ros_spans = tuple((L.parse_ts(a), L.parse_ts(b)) for a, b in (r["rosSpan"] for r in rows
                      if r["workItemId"] != "WI-R8-COORD" and r["rosSpan"][1]))
    span_min = int((freeze - t0).total_seconds() // 60)
    lanes = {
        "agentSpans_T0_to_T0+350": lane_stats(agent_spans, t0, 350),
        "agentSpans_T0_to_freeze": lane_stats(agent_spans, t0, span_min),
        "rosSpans_allNonCoord_T0_to_freeze": lane_stats(ros_spans, t0, span_min),
        "taskAgentSessions": len(agent_spans),
        "freezeMinutes": (freeze - t0).total_seconds() / 60,
    }
    roles = {}
    for r in with_tokens:
        roles[r["role"]] = roles.get(r["role"], 0) + r["total4"]

    result = {
        "records": len(recs), "withTokens": len(with_tokens),
        "withoutTokens": sorted(r["workItemId"] for r in rows if r["total4"] is None),
        "ledgers": sum(1 for r in rows if r["requests"]),
        "ledgerMismatches": [r["workItemId"] for r in with_tokens if not r["ledgerMatchesMetrics"]],
        "totalRequests": sum(r["requests"] for r in rows),
        "bucketTotals": totals, "total4": total,
        "costListUSD_split5m1h": round(cost, 4), "costListUSD_all5m": round(cost5m, 4),
        "costListUSD_perRequestLedger": round(costLedger, 4),
        "r3TimedBuckets": r3b, "r3CostAll5m": round(r3cost, 4),
        "coordinator": coordinator_split(rows),
        "tokensByRole": roles,
        "lanes": lanes,
    }
    json.dump(result, open(out, "w"), indent=1, default=str)
    print(json.dumps(result, indent=1, default=str))


if __name__ == "__main__":
    main(*sys.argv[1:5])
