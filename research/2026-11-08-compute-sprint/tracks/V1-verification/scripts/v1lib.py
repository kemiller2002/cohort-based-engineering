"""V1 verifier: pure helper functions (no I/O). Written independently of other tracks' code."""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import Iterable, Mapping, Sequence

BUCKETS = ("input", "output", "cacheRead", "cacheWrite")
METRIC_TO_BUCKET = {
    "tokens.input": "input",
    "tokens.output": "output",
    "tokens.cache_read": "cacheRead",
    "tokens.cache_write": "cacheWrite",
    "tokens.cache_write_5m": "cacheWrite5m",
    "tokens.cache_write_1h": "cacheWrite1h",
    "tokens.reasoning": "reasoning",
}


# ---------- time ----------
def parse_ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def minutes_between(a: str, b: str) -> float:
    return (parse_ts(b) - parse_ts(a)).total_seconds() / 60.0


# ---------- statistics ----------
def median(xs: Sequence[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return float("nan")
    return float(s[n // 2]) if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def quantile_nearest_rank(xs: Sequence[float], q: float) -> float:
    s = sorted(xs)
    if not s:
        return float("nan")
    k = max(1, math.ceil(q * len(s)))
    return float(s[k - 1])


def ceil_minutes(seconds: float) -> int:
    """GitHub per-job billing rounding: each job rounded up to the next whole minute (0 s -> 0)."""
    return int(math.ceil(seconds / 60.0)) if seconds > 0 else 0


# ---------- tokens and pricing ----------
def metric_buckets(metrics: Iterable[Mapping]) -> Mapping[str, int]:
    """Map a Praxis execution record's metrics list to token buckets (only token metrics)."""
    return {METRIC_TO_BUCKET[m["id"]]: m["value"] for m in metrics if m.get("id") in METRIC_TO_BUCKET}


def total4(b: Mapping[str, int]) -> int | None:
    if not all(k in b for k in BUCKETS):
        return None
    return sum(b[k] for k in BUCKETS)


def sum_buckets(items: Iterable[Mapping[str, int]], keys: Sequence[str] = BUCKETS) -> Mapping[str, int]:
    acc = {k: 0 for k in keys}
    for it in items:
        acc = {k: acc[k] + it.get(k, 0) for k in keys}
    return acc


def price_cost(b: Mapping[str, int], price: Mapping[str, float], split_cache_write: bool = True) -> float:
    """List-price USD for one usage mapping. If split_cache_write and the 5m/1h split is present
    (and sums to cacheWrite), each part is priced at its own rate; otherwise all cache writes at 5m."""
    per = 1_000_000.0
    cw = b.get("cacheWrite", 0)
    has_split = split_cache_write and "cacheWrite5m" in b and "cacheWrite1h" in b and \
        b["cacheWrite5m"] + b["cacheWrite1h"] == cw
    cw_cost = (b["cacheWrite5m"] * price["cacheWrite5m"] + b["cacheWrite1h"] * price["cacheWrite1h"]) if has_split \
        else cw * price["cacheWrite5m"]
    return (b.get("input", 0) * price["input"] + b.get("output", 0) * price["output"]
            + b.get("cacheRead", 0) * price["cacheRead"] + cw_cost) / per


def ledger_rows(ledger: Mapping) -> tuple:
    cols = tuple(ledger["columns"])
    return tuple(dict(zip(cols, r["usage"]), key=r.get("key"), model=r.get("model")) for r in ledger["rows"])


def context_tokens(row: Mapping[str, int]) -> int:
    return row["input"] + row["cacheRead"] + row["cacheWrite"]


# ---------- concurrency ----------
def concurrency_samples(spans: Sequence[tuple], start: datetime, minutes: int, step_s: int = 60) -> tuple:
    """Count spans [a, b) active at each sample start + i*step, i in [0, minutes)."""
    pts = tuple(start + timedelta(seconds=i * step_s) for i in range(minutes))
    return tuple(sum(1 for a, b in spans if a <= t < b) for t in pts)


def union_minutes(spans: Sequence[tuple]) -> float:
    s = sorted(spans)
    total, cur_a, cur_b = 0.0, None, None
    for a, b in s:
        if cur_b is None or a > cur_b:
            if cur_b is not None:
                total += (cur_b - cur_a).total_seconds()
            cur_a, cur_b = a, b
        else:
            cur_b = max(cur_b, b)
    if cur_b is not None:
        total += (cur_b - cur_a).total_seconds()
    return total / 60.0


def exact_mean_concurrency(spans: Sequence[tuple], a: datetime, b: datetime) -> float:
    """Exact time-averaged concurrency over [a, b) (clip each span)."""
    win = (b - a).total_seconds()
    tot = sum(max(0.0, (min(y, b) - max(x, a)).total_seconds()) for x, y in spans)
    return tot / win


# ---------- merges ----------
def parse_merge_tree_conflicts(output: str) -> tuple:
    """Parse `git merge-tree --write-tree --name-only` output: first line is the tree OID,
    then conflicted file names, then a blank line and informational messages."""
    lines = output.split("\n")
    names = []
    for ln in lines[1:]:
        if ln == "":
            break
        names.append(ln)
    return tuple(dict.fromkeys(names))


def is_praxis_state(path: str) -> bool:
    return path.startswith(".ros/")


# ---------- CI ----------
RED = frozenset({"failure", "cancelled", "timed_out", "startup_failure", "action_required"})


def in_window(ts: str, t0: str, minutes: int = 420) -> bool:
    t = parse_ts(ts)
    a = parse_ts(t0)
    return a <= t < a + timedelta(minutes=minutes)


def job_seconds(job: Mapping) -> float:
    if not job.get("started_at") or not job.get("completed_at"):
        return 0.0
    return max(0.0, (parse_ts(job["completed_at"]) - parse_ts(job["started_at"])).total_seconds())


def queue_seconds(job: Mapping) -> float | None:
    if not job.get("started_at") or not job.get("created_at"):
        return None
    return (parse_ts(job["started_at"]) - parse_ts(job["created_at"])).total_seconds()
