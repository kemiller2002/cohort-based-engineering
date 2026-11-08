"""Pure functions for the Track A economics analysis.

Everything here is side-effect free: inputs are parsed JSON / dicts, outputs are new
tuples / dicts. File I/O lives in the `build_*.py` entry scripts.
"""
from __future__ import annotations

from datetime import datetime
from statistics import median
from typing import Iterable, Mapping, Optional, Sequence

# ---------------------------------------------------------------- time helpers


def parse_ts(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def seconds_between(a: Optional[str], b: Optional[str]) -> Optional[float]:
    ta, tb = parse_ts(a), parse_ts(b)
    if ta is None or tb is None:
        return None
    return (tb - ta).total_seconds()


# ---------------------------------------------------------------- pricing

TOKEN_FIELDS = ("tokens.input", "tokens.output", "tokens.cache_read",
                "tokens.cache_write", "tokens.cache_write_5m", "tokens.cache_write_1h",
                "tokens.reasoning")


def price_entry(table: Mapping, model: str) -> Optional[Mapping]:
    """Return the price-table entry for `model`, or None (cost then unavailable)."""
    return next((e for e in table.get("entries", []) if e.get("model") == model), None)


def list_price_cost_usd(tokens: Mapping[str, Optional[int]], price: Optional[Mapping]) -> Optional[float]:
    """ESTIMATE: cost at first-party list price. None if any required bucket is missing.

    Cache writes are priced by TTL partition when both partitions are present (they
    partition tokens.cache_write, never add to it); otherwise all cache writes are
    priced at the 5-minute rate. Reasoning tokens are already inside tokens.output and
    are not priced again.
    """
    if price is None:
        return None
    need = ("tokens.input", "tokens.output", "tokens.cache_read", "tokens.cache_write")
    if any(tokens.get(k) is None for k in need):
        return None
    w5, w1 = tokens.get("tokens.cache_write_5m"), tokens.get("tokens.cache_write_1h")
    if w5 is not None and w1 is not None and w5 + w1 == tokens["tokens.cache_write"]:
        write_cost = w5 * price["cacheWrite5m"] + w1 * price["cacheWrite1h"]
    else:
        write_cost = tokens["tokens.cache_write"] * price["cacheWrite5m"]
    per_m = (tokens["tokens.input"] * price["input"]
             + tokens["tokens.output"] * price["output"]
             + tokens["tokens.cache_read"] * price["cacheRead"]
             + write_cost)
    return round(per_m / 1_000_000, 4)


def total_tokens(tokens: Mapping[str, Optional[int]]) -> Optional[int]:
    need = ("tokens.input", "tokens.output", "tokens.cache_read", "tokens.cache_write")
    if any(tokens.get(k) is None for k in need):
        return None
    return sum(tokens[k] for k in need)


# ---------------------------------------------------------------- execution records

EXEC_METRICS = TOKEN_FIELDS + (
    "model.requests", "tool.calls", "tool.failures", "tool.shell_commands", "tool.file_reads",
    "tool.file_writes", "tool.searches", "tool.build_executions", "tool.test_executions",
    "context.compactions", "context.repeated_file_reads", "context.repeated_file_reads_distinct",
    "context.peak_tokens", "context.governance_reads", "time.wall_ms", "time.blocked_ms",
    "time.active_ms", "time.agent_wall_ms", "time.first_code_change_ms",
    "time.first_productive_change_ms",
)


def metric_values(record: Mapping) -> dict:
    """Map metric id -> value. If an id repeats, the values are summed only for
    aggregation=sum metrics; otherwise the last observation wins (records in this corpus
    carry each id once, which `duplicate_metric_ids` lets callers check)."""
    out: dict = {}
    for m in record.get("metrics", []):
        mid, val = m.get("id"), m.get("value")
        if mid in out and m.get("aggregation") == "sum" and isinstance(val, (int, float)):
            out = {**out, mid: out[mid] + val}
        else:
            out = {**out, mid: val}
    return out


def duplicate_metric_ids(record: Mapping) -> tuple:
    ids = [m.get("id") for m in record.get("metrics", [])]
    return tuple(sorted({i for i in ids if ids.count(i) > 1}))


def execution_row(repo: str, filename: str, record: Mapping, price_table: Mapping) -> dict:
    mv = metric_values(record)
    ident = record.get("identity") or {}
    cs = ((record.get("repository") or {}).get("changeSummary") or {})
    counts = cs.get("counts") or {}
    tokens = {k: mv.get(k) for k in TOKEN_FIELDS}
    model = ident.get("model")
    row = {
        "repo": repo,
        "file": filename,
        "executionId": record.get("executionId"),
        "workItemId": record.get("workItemId"),
        "status": record.get("status"),
        "startedAt": record.get("startedAt"),
        "finalizedAt": record.get("finalizedAt"),
        "agentId": ident.get("agentId"),
        "model": model,
        "runtimeVersion": ident.get("runtimeVersion"),
        "sessionId": ident.get("sessionId"),
        "commits": cs.get("commits"),
        "filesAdded": counts.get("added"),
        "filesModified": counts.get("modified"),
        "linesAdded": cs.get("linesAdded"),
        "linesDeleted": cs.get("linesDeleted"),
        "duplicateMetricIds": ";".join(duplicate_metric_ids(record)),
    }
    row.update({k: mv.get(k) for k in EXEC_METRICS})
    a0, a1, dfr, aerr, retr = agent_span(record)
    row.update({"agentStartedAt": a0, "agentEndedAt": a1, "distinctFilesRead": dfr,
                "apiErrors": aerr, "retries": retr})
    row["tokens.total4"] = total_tokens(tokens)
    row["costUsdListPriceESTIMATE"] = (
        list_price_cost_usd(tokens, price_entry(price_table, model)) if model else None)
    return row


def role_of(agent_id: Optional[str], work_item: Optional[str]) -> str:
    """Role from `claude-code/<role>` agent ids; falls back to 'unattributed'."""
    if agent_id and "/" in agent_id:
        return agent_id.split("/", 1)[1]
    if work_item and "COORD" in work_item:
        return "coordinator"
    return "unattributed"


def is_rework_item(work_item: Optional[str]) -> bool:
    """Heuristic (documented in REPORT): work items that exist to correct earlier work —
    change requests raised by review (CR*), review/defect fix items (*FIX*), and acceptance
    re-runs. Matching is on the R8 work-item naming convention."""
    if not work_item:
        return False
    w = work_item.upper().replace("WI-R8-", "")
    return (w.startswith("CR") or "FIX" in w or w.startswith("EXPVER")
            or w.startswith("T32") or w.startswith("CRFINAL"))


# ---------------------------------------------------------------- CI runs


def ci_row(repo: str, run: Mapping) -> dict:
    q = seconds_between(run.get("created_at"), run.get("run_started_at"))
    e = seconds_between(run.get("run_started_at"), run.get("updated_at"))
    return {
        "repo": repo,
        "id": run.get("id"),
        "workflow": run.get("name"),
        "event": run.get("event"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "headBranch": run.get("head_branch"),
        "headSha": run.get("head_sha"),
        "runAttempt": run.get("run_attempt"),
        "createdAt": run.get("created_at"),
        "runStartedAt": run.get("run_started_at"),
        "updatedAt": run.get("updated_at"),
        "queueSeconds": q,
        # updated_at - run_started_at is an upper bound on execution: updated_at can move
        # later than completion (e.g. re-run bookkeeping). Labelled as such in README.
        "spanSeconds": e,
    }


def percentile(values: Sequence[float], p: float) -> Optional[float]:
    vs = sorted(v for v in values if v is not None)
    if not vs:
        return None
    k = (len(vs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(vs) - 1)
    return round(vs[lo] + (vs[hi] - vs[lo]) * (k - lo), 1)


def summarize_ci(rows: Iterable[Mapping]) -> dict:
    rows = tuple(rows)
    done = tuple(r for r in rows if r["status"] == "completed")
    ran = tuple(r for r in done if r["conclusion"] not in ("skipped",) and r["spanSeconds"] is not None
                and r["spanSeconds"] >= 0)
    red = tuple(r for r in ran if r["conclusion"] in ("failure", "timed_out", "startup_failure"))
    cancelled = tuple(r for r in ran if r["conclusion"] == "cancelled")
    q = [r["queueSeconds"] for r in ran if r["queueSeconds"] is not None and r["queueSeconds"] >= 0]
    s = [r["spanSeconds"] for r in ran]
    total_span = sum(s)
    return {
        "runs": len(rows),
        "completed": len(done),
        "executed": len(ran),
        "skipped": sum(1 for r in done if r["conclusion"] == "skipped"),
        "success": sum(1 for r in ran if r["conclusion"] == "success"),
        "red": len(red),
        "cancelled": len(cancelled),
        "reattempts": sum(1 for r in rows if (r.get("runAttempt") or 1) > 1),
        "queueMedianS": percentile(q, 0.5),
        "queueP90S": percentile(q, 0.9),
        "queueMaxS": max(q) if q else None,
        "queueTotalS": round(sum(q), 1),
        "spanMedianS": percentile(s, 0.5),
        "spanP90S": percentile(s, 0.9),
        "spanTotalS": round(total_span, 1),
        "redSpanS": round(sum(r["spanSeconds"] for r in red), 1),
        "cancelledSpanS": round(sum(r["spanSeconds"] for r in cancelled), 1),
        "redOrCancelledShareOfSpan": (round((sum(r["spanSeconds"] for r in red + cancelled)) / total_span, 3)
                                      if total_span else None),
    }


def group_by(rows: Iterable[Mapping], key) -> dict:
    out: dict = {}
    for r in rows:
        k = key(r)
        out = {**out, k: out.get(k, ()) + (r,)}
    return out


def in_window(ts: Optional[str], start: str, end: str) -> bool:
    t = parse_ts(ts)
    return t is not None and parse_ts(start) <= t <= parse_ts(end)


# ---------------------------------------------------------------- concurrency


def concurrency_profile(intervals: Sequence[tuple], step_s: int = 60) -> tuple:
    """intervals: (start_iso, end_iso). Returns ((iso_minute, active_count), ...) sampled
    every `step_s` seconds over the union span."""
    spans = tuple((parse_ts(a), parse_ts(b)) for a, b in intervals if a and b)
    if not spans:
        return ()
    lo = min(a for a, _ in spans)
    hi = max(b for _, b in spans)
    n = int((hi - lo).total_seconds() // step_s) + 1
    from datetime import timedelta
    return tuple(
        ((lo + timedelta(seconds=i * step_s)).isoformat(),
         sum(1 for a, b in spans if a <= lo + timedelta(seconds=i * step_s) < b))
        for i in range(n))


def busy_fraction(profile: Sequence[tuple], capacity: int) -> Optional[float]:
    """Mean active/capacity across samples (agent-slot utilisation)."""
    if not profile or capacity <= 0:
        return None
    return round(sum(min(c, capacity) for _, c in profile) / (len(profile) * capacity), 3)


def med(xs: Iterable[Optional[float]]) -> Optional[float]:
    v = [x for x in xs if x is not None]
    return median(v) if v else None


# ---------------------------------------------------------------- raw transcript summaries


def payloads(record: Mapping) -> tuple:
    return tuple(rt.get("payload") or {} for rt in record.get("rawTelemetry", [])
                 if (rt.get("payload") or {}).get("schema", "").startswith("praxis.claude-session-summary"))


def agent_span(record: Mapping) -> tuple:
    """(startedAt, endedAt, distinctFilesRead, apiErrors, retries) from the first transcript
    summary, or Nones when no transcript was ingested."""
    ps = payloads(record)
    if not ps:
        return (None, None, None, None, None)
    p = ps[0]
    return (p.get("startedAt"), p.get("endedAt"), p.get("distinctFilesRead"),
            p.get("apiErrors"), p.get("retries"))


def request_rows(record: Mapping, price_table: Mapping) -> tuple:
    """One row per provider request (message id) in the transcript request ledger."""
    out = []
    for p in payloads(record):
        led = p.get("requestLedger") or {}
        cols = led.get("columns") or []
        for seq, r in enumerate(led.get("rows") or []):
            u = dict(zip(cols, r.get("usage") or []))
            t = {"tokens.input": u.get("input"), "tokens.output": u.get("output"),
                 "tokens.cache_read": u.get("cacheRead"), "tokens.cache_write": u.get("cacheWrite"),
                 "tokens.cache_write_5m": u.get("cacheWrite5m"), "tokens.cache_write_1h": u.get("cacheWrite1h")}
            out.append({
                "executionId": record.get("executionId"), "workItemId": record.get("workItemId"),
                "seq": seq, "model": r.get("model"), "agentId": r.get("agentId"),
                "input": u.get("input"), "output": u.get("output"), "cacheRead": u.get("cacheRead"),
                "cacheWrite": u.get("cacheWrite"), "cacheWrite5m": u.get("cacheWrite5m"),
                "cacheWrite1h": u.get("cacheWrite1h"), "reasoning": u.get("reasoning"),
                "contextTokens": sum(x or 0 for x in (u.get("input"), u.get("cacheRead"), u.get("cacheWrite"))),
                "costUsdESTIMATE": list_price_cost_usd(t, price_entry(price_table, r.get("model"))),
            })
    return tuple(out)


def reread_rows(record: Mapping) -> tuple:
    out = []
    for p in payloads(record):
        gov = {g.get("path") for g in p.get("governanceReads") or []}
        for rr in p.get("repeatedReads") or []:
            out.append({"executionId": record.get("executionId"), "workItemId": record.get("workItemId"),
                        "path": rr.get("path"), "reads": rr.get("count"),
                        "governance": rr.get("path") in gov})
    return tuple(out)


def tool_rows(record: Mapping) -> tuple:
    return tuple({"executionId": record.get("executionId"), "workItemId": record.get("workItemId"),
                  "tool": t.get("name"), "calls": t.get("count")}
                 for p in payloads(record) for t in p.get("toolCalls") or [])


def context_cost_split(reqs: Sequence[Mapping], price: Mapping) -> dict:
    """ESTIMATE: share of list-price cost by bucket across request rows."""
    b = {
        "input": sum(r["input"] or 0 for r in reqs) * price["input"],
        "output": sum(r["output"] or 0 for r in reqs) * price["output"],
        "cacheRead": sum(r["cacheRead"] or 0 for r in reqs) * price["cacheRead"],
        "cacheWrite5m": sum(r["cacheWrite5m"] or 0 for r in reqs) * price["cacheWrite5m"],
        "cacheWrite1h": sum(r["cacheWrite1h"] or 0 for r in reqs) * price["cacheWrite1h"],
    }
    tot = sum(b.values())
    return {k: {"usd": round(v / 1e6, 2), "share": round(v / tot, 3) if tot else None} for k, v in b.items()}
