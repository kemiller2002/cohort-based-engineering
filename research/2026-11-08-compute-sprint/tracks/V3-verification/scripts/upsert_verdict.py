"""Upsert one verdict entry (JSON on stdin) into verdicts.json, keyed by claimId."""
import json
import os
import sys

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "verdicts.json")
FIELDS = ["claimId", "verdict", "claimedValue", "recomputedValue", "independence", "method", "inputs", "discrepancies", "notes"]
VERDICTS = {"VERIFIED", "PARTIALLY VERIFIED", "CONTRADICTED", "UNVERIFIABLE"}


def upsert(doc, entry):
    missing = [f for f in FIELDS if f not in entry]
    if missing or entry["verdict"] not in VERDICTS:
        raise ValueError(f"bad entry: missing={missing} verdict={entry.get('verdict')}")
    others = [v for v in doc["verdicts"] if v["claimId"] != entry["claimId"]]
    return {**doc, "verdicts": others + [{f: entry[f] for f in FIELDS}]}


if __name__ == "__main__":
    doc = json.load(open(PATH)) if os.path.exists(PATH) else {"schema": "v3-verdicts/1", "worker": "V3-001", "date": "2026-11-08", "verdicts": []}
    json.dump(upsert(doc, json.load(sys.stdin)), open(PATH, "w"), indent=1)
    print("ok")
