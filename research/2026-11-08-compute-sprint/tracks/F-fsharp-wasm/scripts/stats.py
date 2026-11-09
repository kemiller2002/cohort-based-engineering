"""Pure summary statistics for sprint timing data (no I/O)."""
from __future__ import annotations

from typing import Iterable, Sequence


def _sorted(xs: Iterable[float]) -> list[float]:
    values = sorted(float(x) for x in xs)
    if not values:
        raise ValueError("no values")
    return values


def quantile(xs: Iterable[float], q: float) -> float:
    """Linear-interpolated quantile (type 7, the numpy/R default)."""
    values = _sorted(xs)
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0,1]")
    pos = (len(values) - 1) * q
    lo, frac = int(pos), pos - int(pos)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * frac


def median(xs: Iterable[float]) -> float:
    return quantile(xs, 0.5)


def summarize(xs: Sequence[float]) -> dict:
    """n, median, min, max, IQR and relative spread ((max-min)/median)."""
    values = _sorted(xs)
    med = median(values)
    return {
        "n": len(values),
        "median": round(med, 3),
        "min": round(values[0], 3),
        "max": round(values[-1], 3),
        "p25": round(quantile(values, 0.25), 3),
        "p75": round(quantile(values, 0.75), 3),
        "iqr": round(quantile(values, 0.75) - quantile(values, 0.25), 3),
        "relSpread": round((values[-1] - values[0]) / med, 3) if med else None,
    }


def group_summaries(rows: Iterable[dict], keys: Sequence[str], value: str) -> list[dict]:
    """Group dict rows by `keys` and summarise the numeric column `value`."""
    groups: dict[tuple, list[float]] = {}
    for row in rows:
        groups.setdefault(tuple(row[k] for k in keys), []).append(float(row[value]))
    return [dict(zip(keys, k), **summarize(v)) for k, v in sorted(groups.items())]
