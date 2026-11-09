"""Aggregate raw sprint-F measurements into measurements/summary.json (median, spread, n per group).

Usage: python3 summarize.py TRACK_DIR
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats import group_summaries  # noqa: E402


# Rows invalidated by an accidental concurrent duplicate of run_phase2.sh (19:35-20:42 UTC, see CHECKPOINT CP-F-03):
# r010-wasmtools startup rows recorded before the clean rerun, and the r008 batch-2 publish-incr that followed a
# cancelled cold build (effectively a cold build).
EXCLUDED_STARTUP = lambda r: r["label"] == "r010-wasmtools" and r.get("server") in ("python-http", "gzip")
EXCLUDED_BUILD = lambda r: r["timestampUtc"] in ("2026-11-08T20:43:09+00:00",)


def read_csv(paths: list[Path]) -> list[dict]:
    return [r for p in paths if p.exists() for r in csv.DictReader(open(p, encoding="utf-8"))]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()] if path.exists() else []


def startup_groups(rows: list[dict], metric: str) -> list[dict]:
    """Summaries of one startup metric per (label, mode, throttle, server), skipping rows without the metric (pure)."""
    ok = [dict(r, server=r.get("server", "python-http")) for r in rows if r.get(metric) is not None and not r.get("pageErrors")]
    return group_summaries(ok, ["label", "mode", "throttle", "server"], metric)


def main() -> None:
    t = Path(sys.argv[1])
    m = t / "measurements"
    builds = [r for r in read_csv([m / "build-times.csv", m / "build-times-batch2.csv"]) if r["exitCode"] == "0" and not EXCLUDED_BUILD(r)]
    for r in builds:
        r["batch"] = r.get("batch") or "batch1"
    startup = [r for r in read_jsonl(m / "startup.jsonl") if not EXCLUDED_STARTUP(r)]
    summary = {
        "build": group_summaries(builds, ["label", "mode"], "seconds"),
        "buildByBatch": group_summaries(builds, ["label", "mode", "batch"], "seconds"),
        "startup": {k: startup_groups(startup, k) for k in ("readyMs", "domContentLoadedMs", "firstContentfulPaintMs", "transferBytes")},
        "startupFailures": [{k: r[k] for k in ("label", "mode", "throttle", "rep", "pageErrors")} for r in startup if r.get("pageErrors")],
    }
    (m / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("wrote", m / "summary.json", len(builds), "build rows,", len(startup), "startup rows")


if __name__ == "__main__":
    main()
