"""Build results.csv from raw/*.json (one row per blocker) and print the catch rate."""
import csv
import json
import sys
from pathlib import Path

from . import checks as c

TRACK = Path(__file__).resolve().parents[2]
ORDER = ["R4-APPROVALS", "R8-CMDBODY", "R8-INV04", "R8-APPROVALS", "R8-MSB1008", "R9-MSB1008",
         "R10-AUTH", "R10-GATE", "R10-JOBCAP", "CAUSA-CYCLE", "CAUSA-RULES"]
BRIEF = {"R8-CMDBODY", "R8-INV04", "R9-MSB1008", "R10-AUTH", "R10-GATE", "R10-JOBCAP", "CAUSA-CYCLE", "CAUSA-RULES"}


def rows(records):
    for r in records:
        pre = r["preT0"]
        yield {"rehearsal": r["rehearsal"], "blocker": f"{r['key']}: {r['blocker']}",
               "preT0Commit": f"{Path(pre['repo']).name}@{pre['sha'][:12]} ({pre['committerTime']})",
               "toolsRun": " + ".join(r["toolsRun"]), "outcome": r["outcome"],
               "matchEvidence": str(r["matchEvidence"]).replace("\n", " ")[:900],
               "dryRunSeconds": r["dryRunSeconds"]}


def cost(records):
    """Dry-run tool seconds per rehearsal (pre-T0 runs only; fixed-version reruns excluded) and build seconds."""
    out = {}
    for r in records:
        e = out.setdefault(r["rehearsal"], {"dryRunSeconds": 0.0, "buildSeconds": 0.0, "blockers": 0})
        e["dryRunSeconds"] = round(e["dryRunSeconds"] + float(r["dryRunSeconds"] or 0), 2)
        e["buildSeconds"] = round(e["buildSeconds"] + float(r.get("buildSeconds", 0) or 0), 2)
        e["blockers"] += 1
    return out


def main():
    recs = {p.stem: json.loads(p.read_text()) for p in (TRACK / "raw").glob("*.json")}
    ordered = [recs[k] for k in ORDER if k in recs]
    with open(TRACK / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rehearsal", "blocker", "preT0Commit", "toolsRun", "outcome",
                                          "matchEvidence", "dryRunSeconds"])
        w.writeheader()
        w.writerows(rows(ordered))
    summary = {"extended": c.catch_rate([r["outcome"] for r in ordered]),
               "briefList": c.catch_rate([r["outcome"] for r in ordered if r["key"] in BRIEF]),
               "briefPlusR4": c.catch_rate([r["outcome"] for r in ordered if r["key"] in BRIEF | {"R4-APPROVALS"}]),
               "missing": [k for k in ORDER if k not in recs],
               "dryRunSecondsByRehearsal": cost(ordered)}
    json.dump(summary, sys.stdout, indent=2)
    print()
    return summary


if __name__ == "__main__":
    main()
