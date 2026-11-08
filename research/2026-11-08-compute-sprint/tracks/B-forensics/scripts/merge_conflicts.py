"""Replay every two-parent merge in a repository with `git merge-tree --write-tree`
and report which merges actually conflicted (a measured proxy for parallel-write
conflicts). Read-only: merge-tree writes only loose objects, never refs or the
working tree. Pure parsing/aggregation functions are unit-tested; git calls are
isolated in `git()`.

usage: merge_conflicts.py ID=REPO_PATH[@SINCE[@UNTIL]] ...
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from typing import Iterable, Mapping, Optional, Sequence


def parse_merge_list(text: str) -> tuple:
    """Lines of '%H %P %cI' -> tuple of dicts for commits with exactly two parents."""
    out = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 4:
            out.append({"sha": parts[0], "p1": parts[1], "p2": parts[2], "date": parts[3]})
    return tuple(out)


def parse_merge_tree(returncode: int, stdout: str) -> dict:
    """git merge-tree --write-tree --name-only --no-messages output.
    rc 0: clean (first line tree). rc 1: conflicted; following lines are paths."""
    lines = [l for l in stdout.splitlines() if l.strip()]
    if returncode == 0:
        return {"conflicted": False, "paths": ()}
    if returncode == 1:
        return {"conflicted": True, "paths": tuple(sorted(set(lines[1:])))}
    return {"conflicted": None, "paths": (), "error": returncode}


def to_utc(ts: str) -> datetime:
    """ISO-8601 with Z or numeric offset -> aware UTC datetime (commit dates mix offsets)."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def within(date: str, since: Optional[str], until: Optional[str]) -> bool:
    d = to_utc(date)
    return (since is None or d >= to_utc(since)) and (until is None or d <= to_utc(until))


RECORD_PREFIXES = (".ros/", "evidence/", ".sde/", "telemetry/")


def is_record_path(path: str) -> bool:
    """Process/evidence bookkeeping (Praxis .ros state, evidence logs), not product source."""
    return path.startswith(RECORD_PREFIXES)


def classify(paths: Sequence[str]) -> str:
    if not paths:
        return "none"
    return "records-only" if all(is_record_path(p) for p in paths) else "source"


def aggregate(rid: str, results: Sequence[Mapping]) -> dict:
    conflicted = [r for r in results if r["conflicted"]]
    errors = [r for r in results if r["conflicted"] is None]
    paths: dict = {}
    for r in conflicted:
        for p in r["paths"]:
            paths = {**paths, p: paths.get(p, 0) + 1}
    return {
        "id": rid,
        "merges": len(results),
        "conflictedMerges": len(conflicted),
        "replayErrors": len(errors),
        "recordsOnlyConflicts": sum(1 for r in conflicted if classify(r["paths"]) == "records-only"),
        "sourceConflicts": sum(1 for r in conflicted if classify(r["paths"]) == "source"),
        "conflicts": [{"sha": r["sha"][:7], "date": r["date"], "paths": list(r["paths"]), "kind": classify(r["paths"])} for r in conflicted],
        "hotPaths": dict(sorted(paths.items(), key=lambda kv: -kv[1])[:10]),
    }


def git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def replay(rid: str, repo: str, since: Optional[str], until: Optional[str]) -> dict:
    merges = parse_merge_list(git(repo, "log", "--all", "--merges", "--format=%H %P %cI").stdout)
    results = []
    for m in merges:
        if not within(m["date"], since, until):
            continue
        p = git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", m["p1"], m["p2"])
        results.append({**m, **parse_merge_tree(p.returncode, p.stdout)})
    return aggregate(rid, results)


def parse_arg(arg: str) -> tuple:
    rid, rest = arg.split("=", 1)
    bits = rest.split("@")
    return rid, bits[0], (bits[1] if len(bits) > 1 and bits[1] else None), (bits[2] if len(bits) > 2 else None)


if __name__ == "__main__":
    json.dump([replay(*parse_arg(a)) for a in sys.argv[1:]], sys.stdout, indent=1)
    print()
