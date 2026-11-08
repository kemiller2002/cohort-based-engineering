#!/usr/bin/env python3
"""Build request-, reread- and tool-level CSVs from transcript summaries embedded in
execution records (rawTelemetry payload schema praxis.claude-session-summary/2).

Usage: python3 build_transcript_detail.py HOME_DIR PRICE_TABLE OUT_DIR REPO [REPO ...]
Writes OUT_DIR/requests.csv, rereads.csv, tool-calls.csv (each row carries `repo`).
"""
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import econ  # noqa: E402


def load(path):
    with open(path) as fh:
        return json.load(fh)


def write(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {path}", file=sys.stderr)


def main(argv):
    home, price_path, out_dir = argv[1], argv[2], argv[3]
    price = load(price_path)
    recs = tuple((repo, load(f)) for repo in argv[4:]
                 for f in sorted(glob.glob(f"{home}/{repo}/.ros/telemetry/executions/*.json")))
    tag = lambda repo, rows: tuple({"repo": repo, **r} for r in rows)  # noqa: E731
    write(f"{out_dir}/requests.csv", [r for repo, d in recs for r in tag(repo, econ.request_rows(d, price))])
    write(f"{out_dir}/rereads.csv", [r for repo, d in recs for r in tag(repo, econ.reread_rows(d))])
    write(f"{out_dir}/tool-calls.csv", [r for repo, d in recs for r in tag(repo, econ.tool_rows(d))])


if __name__ == "__main__":
    main(sys.argv)
