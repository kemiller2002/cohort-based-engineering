"""Windowed GitHub Actions metrics per rehearsal (pure functions + thin CLI).

Input: data/rehearsals.json and raw/actions/<repo>.jsonl (from fetch_runs.sh).
Output: JSON on stdout, one object per rehearsal. Every value is MEASURED from the
run list; absent data is reported as None ("unavailable"), never estimated.

Definitions
- window: [t0, t0 + ceilingMinutes] by run created_at.
- firstGreenBuildMin: minutes from t0 to updated_at of the earliest-finishing
  successful run of a build workflow created at or after t0.
- firstDeployMin: same for a deploy workflow.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def minutes_between(a: datetime, b: datetime) -> float:
    return round((b - a).total_seconds() / 60.0, 1)


def in_window(run: Mapping, start: datetime, end: datetime) -> bool:
    created = parse_ts(run["created_at"])
    return start <= created <= end


def window_runs(runs: Iterable[Mapping], start: datetime, end: datetime) -> tuple:
    return tuple(r for r in runs if in_window(r, start, end))


def count_by(runs: Iterable[Mapping], conclusion: str) -> int:
    return sum(1 for r in runs if r.get("conclusion") == conclusion)


def first_success_minutes(runs: Iterable[Mapping], names: Sequence[str], t0: datetime) -> Optional[float]:
    finishes = sorted(
        parse_ts(r["updated_at"])
        for r in runs
        if r.get("name") in names
        and r.get("conclusion") == "success"
        and parse_ts(r["created_at"]) >= t0
    )
    return minutes_between(t0, finishes[0]) if finishes else None


def per_workflow(runs: Iterable[Mapping]) -> dict:
    out: dict = {}
    for r in runs:
        key = r.get("name") or "?"
        c = r.get("conclusion") or "none"
        out = {**out, key: {**out.get(key, {}), c: out.get(key, {}).get(c, 0) + 1}}
    return out


def summarize(meta: Mapping, runs: Sequence[Mapping]) -> dict:
    if not runs:
        return {"id": meta["id"], "repo": meta["repo"], "available": False}
    t0 = parse_ts(meta["t0"])
    end = t0 + timedelta(minutes=meta["ceilingMinutes"])
    w = window_runs(runs, t0, end)
    return {
        "id": meta["id"],
        "repo": meta["repo"],
        "available": True,
        "t0": meta["t0"],
        "totalRuns": len(runs),
        "windowRuns": len(w),
        "windowFailures": count_by(w, "failure"),
        "windowCancelled": count_by(w, "cancelled"),
        "windowSuccess": count_by(w, "success"),
        "firstGreenBuildMin": first_success_minutes(runs, meta["buildWorkflows"], t0),
        "firstDeployMin": first_success_minutes(runs, meta["deployWorkflows"], t0),
        "windowByWorkflow": per_workflow(w),
    }


def load_runs(path: Path) -> tuple:
    if not path.exists():
        return ()
    return tuple(json.loads(line) for line in path.read_text().splitlines() if line.strip())


def main(root: Path) -> list:
    metas = json.loads((root / "data" / "rehearsals.json").read_text())
    return [summarize(m, load_runs(root / "raw" / "actions" / f"{m['repo']}.jsonl")) for m in metas]


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    json.dump(main(root), sys.stdout, indent=1)
    print()
