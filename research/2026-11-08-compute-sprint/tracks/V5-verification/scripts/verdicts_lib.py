"""Tiny helper to upsert one verdict into verdicts.json (pure merge + IO edge)."""
import json
import os
import sys

FIELDS = ("claimId", "verdict", "claimedValue", "recomputedValue", "independence", "method", "inputs",
          "discrepancies", "notes")


def upsert(verdicts, entry):
    missing = [k for k in FIELDS if k not in entry]
    if missing:
        raise ValueError(f"missing fields {missing}")
    return [v for v in verdicts if v["claimId"] != entry["claimId"]] + [entry]


if __name__ == "__main__":
    path = sys.argv[1]
    cur = json.load(open(path)) if os.path.exists(path) else []
    new = upsert(cur, json.load(sys.stdin))
    with open(path, "w") as f:
        json.dump(new, f, indent=1)
        f.write("\n")
    print(len(new), "verdicts")
