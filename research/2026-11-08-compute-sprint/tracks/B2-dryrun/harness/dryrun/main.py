"""Run replays and write raw/<key>.json. Usage: python3 -m dryrun.main causa r4 ..."""
import json
import sys
from pathlib import Path

TRACK = Path(__file__).resolve().parents[2]


def write(records):
    for r in records:
        (TRACK / "raw" / f"{r['key']}.json").write_text(json.dumps(r, indent=2, default=str) + "\n")
        print(r["key"], "->", r["outcome"], "|", str(r["matchEvidence"])[:300])


def main(names):
    import importlib
    for n in names:
        write(importlib.import_module(f"dryrun.replay_{n}").replay())


if __name__ == "__main__":
    main(sys.argv[1:])
