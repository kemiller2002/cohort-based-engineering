#!/usr/bin/env python3
"""SPR-A2-01 replay harness (EXPERIMENTAL). Re-merges the parents of historical merge commits in a
SCRATCH clone, without and with the ros-history merge driver, and compares the driver's result with
the merge commit the team actually produced.

Usage: python3 replay_merges.py SCRATCH_CLONE DRIVER_FSX TARGETS_JSON OUT_JSONL
TARGETS_JSON: [{"repo": "...", "merge": "<sha>", "label": "..."}]
"""
import json
import re
from datetime import datetime, timezone
import subprocess
import sys
import time

ROS = (".ros/context/current.json", ".ros/events/events.jsonl")


def git(repo, *args, check=True):
    p = subprocess.run(("git", "-C", repo) + args, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {args}: {p.stderr}")
    return p


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def instant(s):
    """Normalize an ISO-8601 timestamp to a UTC instant string (7-digit fractions truncated to 6)."""
    s = re.sub(r"Z$", "+00:00", s)
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)
    return datetime.fromisoformat(s).astimezone(timezone.utc).isoformat()


def parse_context(text):
    d = json.loads(text)
    items = [(w.get("id"), canonical(w)) for w in d.get("workItems", [])]
    meta = {k: (instant(v) if k == "updatedAt" else canonical(v)) for k, v in d.items() if k != "workItems"}
    return {"records": items, "meta": meta}


def parse_events(text):
    evs = [json.loads(l) for l in text.splitlines() if l.strip()]
    return {"records": [(e.get("eventId"), canonical(e)) for e in evs], "meta": {}}


PARSERS = {ROS[0]: parse_context, ROS[1]: parse_events}


def show(repo, rev, path):
    p = git(repo, "show", f"{rev}:{path}", check=False)
    return p.stdout if p.returncode == 0 else None


def compare(path, result_text, m_text, p1_text, p2_text):
    """Pure comparison of one history file. Returns a dict of measured facts."""
    parse = PARSERS[path]
    res, mm = parse(result_text), parse(m_text)
    parents = [parse(t) for t in (p1_text, p2_text) if t is not None]
    res_ids = [i for i, _ in res["records"]]
    m_ids = [i for i, _ in mm["records"]]
    parent_ids = {i for p in parents for i, _ in p["records"]}
    res_map, m_map = dict(res["records"]), dict(mm["records"])
    return {
        "path": path,
        "byteIdentical": result_text == m_text,
        "resultRecords": len(res_ids),
        "mergeCommitRecords": len(m_ids),
        "duplicatesInResult": len(res_ids) - len(set(res_ids)),
        "lostVsParents": sorted(parent_ids - set(res_ids)),
        "idSetEqualToMergeCommit": set(res_ids) == set(m_ids),
        "orderEqualToMergeCommit": res_ids == m_ids,
        "inMergeCommitNotInResult": sorted(set(m_ids) - set(res_ids)),
        "inResultNotInMergeCommit": sorted(set(res_ids) - set(m_ids)),
        "inMergeCommitNotInParents": sorted(set(m_ids) - parent_ids),
        "recordsWithDifferentContent": sorted(i for i in set(res_ids) & set(m_ids) if res_map[i] != m_map[i]),
        "metaDifferences": sorted(k for k in set(res["meta"]) | set(mm["meta"]) if res["meta"].get(k) != mm["meta"].get(k)),
    }


def unmerged(repo):
    out = git(repo, "diff", "--name-only", "--diff-filter=U").stdout.split()
    return sorted(set(out))


def attempt(repo, p1, p2, driver):
    git(repo, "reset", "-q", "--hard")
    git(repo, "clean", "-qfdx")
    git(repo, "checkout", "-q", "--detach", p1)
    attrs = f"{repo}/.git/info/attributes"
    with open(attrs, "w") as f:
        if driver:
            f.write("".join(f"{p} merge=ros-history\n" for p in ROS))
    t0 = time.monotonic()
    p = git(repo, "merge", "--no-ff", "--no-commit", "--no-edit", p2, check=False)
    secs = time.monotonic() - t0
    return {"exit": p.returncode, "seconds": round(secs, 2), "unmerged": unmerged(repo),
            "driverStderr": [l for l in p.stderr.splitlines() if "ros-merge" in l]}


def replay(repo, driver_fsx, target):
    m = target["merge"]
    parents = git(repo, "rev-list", "--parents", "-n", "1", m).stdout.split()[1:]
    p1, p2 = parents
    git(repo, "config", "merge.ros-history.name", "Praxis .ros history semantic merge (A2 prototype)")
    git(repo, "config", "merge.ros-history.driver", f"dotnet fsi {driver_fsx} %O %A %B %P")
    without = attempt(repo, p1, p2, driver=False)
    git(repo, "merge", "--abort", check=False)
    with_ = attempt(repo, p1, p2, driver=True)
    comparisons = []
    for path in ROS:
        if path in with_["unmerged"]:
            continue
        m_text = show(repo, m, path)
        if m_text is None:
            continue
        a, b = show(repo, p1, path), show(repo, p2, path)
        if a == b:
            continue  # file not involved in this merge
        with open(f"{repo}/{path}") as f:
            comparisons.append(dict(compare(path, f.read(), m_text, a, b), conflictedWithoutDriver=path in without["unmerged"]))
    git(repo, "merge", "--abort", check=False)
    ros_without = [p for p in without["unmerged"] if p.startswith(".ros/")]
    ros_with = [p for p in with_["unmerged"] if p.startswith(".ros/")]
    return dict(target, p1=p1, p2=p2, withoutDriver=without, withDriver=with_,
                rosConflictedWithout=ros_without, rosConflictedWith=ros_with,
                nonRosConflictedWith=[p for p in with_["unmerged"] if not p.startswith(".ros/")],
                comparisons=comparisons)


def main(argv):
    repo, driver, targets_path, out = argv[1:5]
    targets = json.load(open(targets_path))
    with open(out, "w") as f:
        for t in targets:
            r = replay(repo, driver, t)
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(t.get("label", t["merge"][:8]), "ros-without", len(r["rosConflictedWithout"]),
                  "ros-with", len(r["rosConflictedWith"]), "secs", r["withDriver"]["seconds"], file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
