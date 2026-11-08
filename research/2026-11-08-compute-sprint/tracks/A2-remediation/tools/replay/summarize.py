#!/usr/bin/env python3
"""Summarize replay JSONL files (SPR-A2-01). Usage: python3 summarize.py OUT_JSON NAME=FILE.jsonl ..."""
import json
import statistics
import sys


def summarize(rows):
    ros_conf = [r for r in rows if r["rosConflictedWithout"]]
    comps = [c for r in rows for c in r["comparisons"]]
    resolved = [r for r in ros_conf if not r["rosConflictedWith"]]
    newly = [r["label"] for r in rows if set(r["rosConflictedWith"]) - set(r["rosConflictedWithout"])]
    secs = [r["withDriver"]["seconds"] for r in rows]
    by_path = {}
    for c in comps:
        p = by_path.setdefault(c["path"], {"files": 0, "byteIdentical": 0, "idSetEqual": 0, "orderEqual": 0,
                                           "contentEqualAllShared": 0, "metaEqual": 0, "lostRecords": 0,
                                           "duplicateRecords": 0, "metaDiffKeys": {}})
        p["files"] += 1
        p["byteIdentical"] += c["byteIdentical"]
        p["idSetEqual"] += c["idSetEqualToMergeCommit"]
        p["orderEqual"] += c["orderEqualToMergeCommit"]
        p["contentEqualAllShared"] += not c["recordsWithDifferentContent"]
        p["metaEqual"] += not c["metaDifferences"]
        p["lostRecords"] += len(c["lostVsParents"])
        p["duplicateRecords"] += c["duplicatesInResult"]
        for k in c["metaDifferences"]:
            p["metaDiffKeys"][k] = p["metaDiffKeys"].get(k, 0) + 1
    return {
        "mergesReplayed": len(rows),
        "mergesWithRosConflictWithoutDriver": len(ros_conf),
        "rosConflictedPathsWithoutDriver": sum(len(r["rosConflictedWithout"]) for r in rows),
        "rosConflictedPathsWithDriver": sum(len(r["rosConflictedWith"]) for r in rows),
        "mergesFullyResolvedInRos": len(resolved),
        "mergesStillConflictedInRos": [r["label"] for r in ros_conf if r["rosConflictedWith"]],
        "mergesWithNewRosConflictFromDriver": newly,
        "mergesStillNeedingHumanForNonRos": [r["label"] for r in rows if r["nonRosConflictedWith"]],
        "relaxedOrderUses": sum(1 for r in rows for l in r["withDriver"]["driverStderr"] if "RelaxedOrder" in l),
        "refusals": [(r["label"], l) for r in rows for l in r["withDriver"]["driverStderr"] if "REFUSED" in l],
        "mergeWallSecondsWithDriver": {"median": statistics.median(secs) if secs else None, "max": max(secs) if secs else None},
        "comparisonByPath": by_path,
        "recordsInMergeCommitNotInParents": sorted({(r["label"], c["path"], i) for r in rows for c in r["comparisons"] for i in c["inMergeCommitNotInParents"]}),
        "recordsWithDifferentContentVsMergeCommit": sorted({(r["label"], c["path"], i) for r in rows for c in r["comparisons"] for i in c["recordsWithDifferentContent"]}),
    }


def main(argv):
    out = argv[1]
    result = {}
    for spec in argv[2:]:
        name, path = spec.split("=", 1)
        result[name] = summarize([json.loads(l) for l in open(path) if l.strip()])
    json.dump(result, open(out, "w"), indent=1, default=list)
    print(json.dumps(result, indent=1, default=list))


if __name__ == "__main__":
    main(sys.argv)
