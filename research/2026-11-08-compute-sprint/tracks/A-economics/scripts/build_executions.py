#!/usr/bin/env python3
"""Build data/executions.csv from Praxis/ROS execution records (.ros/telemetry/executions).

Usage: python3 build_executions.py HOME_DIR PRICE_TABLE OUT_CSV REPO [REPO ...]
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


def rows_for(home, repo, price):
    files = sorted(glob.glob(f"{home}/{repo}/.ros/telemetry/executions/*.json"))
    return tuple(econ.execution_row(repo, os.path.basename(f), load(f), price) for f in files)


def main(argv):
    home, price_path, out = argv[1], argv[2], argv[3]
    price = load(price_path)
    rows = tuple(r for repo in argv[4:] for r in rows_for(home, repo, price))
    cols = list(rows[0].keys())
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
