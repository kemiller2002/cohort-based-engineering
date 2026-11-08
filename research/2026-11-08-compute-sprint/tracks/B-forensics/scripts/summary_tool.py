"""Build rehearsal-summary.csv from reported facts, measured CI metrics, merge replay
and curated event counts. Pure row construction is unit-tested.

  python3 -I summary_tool.py ROOT
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence

U = "unavailable"
CONTRACT_EVENT_TYPES = frozenset({
    "contract-mismatch", "contract-defect", "contract-gap", "format-mismatch", "plan-cycle",
    "gate-cannot-run", "process-rules-misbound", "tool-catalog-mismatch", "gate-env-incomplete",
    "gate-refuses-valid-plan", "self-reference-paradox",
})
INTEGRATION_CODES = frozenset({"RC-PROVIDER-MODEL", "RC-CONCURRENCY"})

COLUMNS = (
    "rehearsal", "scope", "plannedRequirements", "completedRequirements", "completedBasis",
    "indyInitVerdict", "selfReported", "acceptedUnderIndyInit",
    "firstGreenAppCiMin", "firstGreenBuildWorkflowMin_actions", "firstDeployedAppMin", "firstVerifiedE2eMin",
    "ciRunsWindow", "ciFailuresWindow", "ciCancelledWindow",
    "governanceFailureEvents", "contractIncompatibilityEvents", "integrationFailureEvents",
    "mergesInWindow", "conflictedMerges_source", "conflictedMerges_recordsOnly",
    "humanInterventionEvents", "topology", "sources",
)


def count(events: Iterable[Mapping], rid: str, pred) -> int:
    return sum(1 for e in events if e["rehearsal"] == rid and pred(e))


def row(rid: str, facts: Mapping, ci: Mapping, merges: Mapping, events: Sequence[Mapping]) -> dict:
    f = facts.get(rid, {})
    c = ci.get(rid, {"available": False})
    m = merges.get(rid)
    ok = c.get("available", False)
    return {
        "rehearsal": rid,
        "scope": f.get("scope", U),
        "plannedRequirements": f.get("planned", U),
        "completedRequirements": f.get("completed", U),
        "completedBasis": f.get("completedBasis", U),
        "indyInitVerdict": f.get("indyInitVerdict", U),
        "selfReported": f.get("selfReported", U),
        "acceptedUnderIndyInit": f.get("acceptedUnderIndyInit", U),
        "firstGreenAppCiMin": f.get("firstGreenAppCiMin", U),
        "firstGreenBuildWorkflowMin_actions": (c.get("firstGreenBuildMin") if ok and c.get("firstGreenBuildMin") is not None else U),
        "firstDeployedAppMin": f.get("firstDeployedAppMin", U),
        "firstVerifiedE2eMin": f.get("firstVerifiedE2eMin", U),
        "ciRunsWindow": c["windowRuns"] if ok else U,
        "ciFailuresWindow": c["windowFailures"] if ok else U,
        "ciCancelledWindow": c["windowCancelled"] if ok else U,
        "governanceFailureEvents": count(events, rid, lambda e: e["rootCause"] == "RC-GOV-UNTESTED"),
        "contractIncompatibilityEvents": count(events, rid, lambda e: e["eventType"] in CONTRACT_EVENT_TYPES),
        "integrationFailureEvents": count(events, rid, lambda e: e["rootCause"] in INTEGRATION_CODES),
        "mergesInWindow": m["merges"] if m else U,
        "conflictedMerges_source": m["sourceConflicts"] if m else U,
        "conflictedMerges_recordsOnly": m["recordsOnlyConflicts"] if m else U,
        "humanInterventionEvents": count(events, rid, lambda e: e["humanIntervention"]),
        "topology": f.get("topology", U),
        "sources": f.get("source", U),
    }


def to_csv(rows: Sequence[Mapping]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def main(root: Path) -> str:
    facts = json.loads((root / "data" / "rehearsal_facts.json").read_text())
    ci = {c["id"]: c for c in json.loads((root / "data" / "ci-metrics.json").read_text())}
    merges = {m["id"]: m for m in json.loads((root / "data" / "merge-conflicts.json").read_text())}
    events = [json.loads(l) for l in (root / "events.jsonl").read_text().splitlines() if l.strip()]
    ids = [k for k in facts if not k.startswith("_")]
    text = to_csv([row(r, facts, ci, merges, events) for r in ids])
    (root / "rehearsal-summary.csv").write_text(text)
    return text


if __name__ == "__main__":
    print(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent))
