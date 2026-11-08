#!/usr/bin/env python3
"""Build CI datasets from fetched run JSONL.

Usage: python3 build_ci.py RAW_DIR WINDOWS_CSV OUT_DIR
Writes OUT_DIR/ci-runs.csv, ci-summary-by-repo.csv (scope=all|timed-window),
ci-summary-timed-by-workflow.csv.
"""
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import econ  # noqa: E402


def read_jsonl(path):
    with open(path) as fh:
        return tuple(json.loads(line) for line in fh if line.strip())


def write(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {path}", file=sys.stderr)


def main(argv):
    raw, win_path, out = argv[1], argv[2], argv[3]
    with open(win_path) as fh:
        windows = {r["repo"]: r for r in csv.DictReader(fh)}
    rows = tuple(
        {**econ.ci_row(repo, run),
         "inTimedWindow": (econ.in_window(run.get("created_at"), windows[repo]["t0"], windows[repo]["windowEnd"])
                           if repo in windows else None)}
        for path in sorted(glob.glob(f"{raw}/ci-runs-*.jsonl"))
        for repo in [os.path.basename(path)[len("ci-runs-"):-len(".jsonl")]]
        for run in read_jsonl(path))
    write(f"{out}/ci-runs.csv", list(rows))
    by_repo = econ.group_by(rows, lambda r: r["repo"])
    summary = [{"repo": repo, "scope": scope, **econ.summarize_ci(sel)}
               for repo, rs in sorted(by_repo.items())
               for scope, sel in (("all", rs), ("timed-window", tuple(r for r in rs if r["inTimedWindow"])))
               if sel]
    write(f"{out}/ci-summary-by-repo.csv", summary)
    timed = tuple(r for r in rows if r["inTimedWindow"])
    by_wf = econ.group_by(timed, lambda r: (r["repo"], r["workflow"]))
    write(f"{out}/ci-summary-timed-by-workflow.csv",
          [{"repo": k[0], "workflow": k[1], **econ.summarize_ci(v)} for k, v in sorted(by_wf.items())])


if __name__ == "__main__":
    main(sys.argv)
