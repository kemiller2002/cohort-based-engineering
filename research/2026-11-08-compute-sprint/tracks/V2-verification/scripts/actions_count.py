#!/usr/bin/env python3
"""V2 claim 5: count workflow-run conclusions, all-time and inside a window,
and diff two run lists by id (independent API fetch vs another track's raw data).

Usage: actions_count.py RUNS.jsonl WORKFLOW_NAME T0 DEADLINE [OTHER.jsonl]
Input lines are JSON objects with id, name, conclusion/status, created_at.
"""
import json
import sys
from collections import Counter


def load(path):
    with open(path) as fh:
        return tuple(json.loads(l) for l in fh if l.strip())


def outcome(run):
    return run.get("conclusion") or run.get("status")


def count(runs, name, start=None, end=None):
    """Counter of outcomes for runs of `name`, optionally created in [start, end]."""
    inside = lambda r: (start is None or r["created_at"] >= start) and (end is None or r["created_at"] <= end)
    return Counter(outcome(r) for r in runs if r.get("name") == name and inside(r))


def diff(a, b, name):
    """Runs of `name` whose outcome differs, or that exist in only one list."""
    am = {r["id"]: outcome(r) for r in a if r.get("name") == name}
    bm = {r["id"]: outcome(r) for r in b if r.get("name") == name}
    return {
        "only_in_first": sorted(set(am) - set(bm)),
        "only_in_second": sorted(set(bm) - set(am)),
        "outcome_mismatch": sorted(i for i in set(am) & set(bm) if am[i] != bm[i]),
        "compared": len(set(am) & set(bm)),
    }


def main(argv):
    runs = load(argv[0])
    name, t0, deadline = argv[1], argv[2], argv[3]
    out = {
        "all_time": dict(count(runs, name)),
        "all_time_total": sum(count(runs, name).values()),
        "in_window": dict(count(runs, name, t0, deadline)),
        "in_window_total": sum(count(runs, name, t0, deadline).values()),
    }
    if len(argv) > 4:
        out["diff_vs_other"] = diff(runs, load(argv[4]), name)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
