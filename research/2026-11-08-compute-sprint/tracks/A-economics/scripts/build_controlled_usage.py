#!/usr/bin/env python3
"""Collect per-run provider usage from research-documents controlled experiments.

Usage: python3 build_controlled_usage.py RESEARCH_DOCS PRICE_TABLE OUT_CSV
"""
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import econ  # noqa: E402

EXPERIMENTS = {
    "CONSTRUCT-008": "research/construction-by-design/CONSTRUCT-008/results/*/usage.json",
    "time-entry-expanded-01": "research/construction-by-design/time-entry-expanded-01/results/*/usage.json",
}


def main(argv):
    root, price_path, out = argv[1:4]
    price = json.load(open(price_path))
    rows = [econ.controlled_usage_row(exp, os.path.basename(os.path.dirname(f)), json.load(open(f)), price)
            for exp, pat in EXPERIMENTS.items() for f in sorted(glob.glob(f"{root}/{pat}"))]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
