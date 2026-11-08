#!/usr/bin/env python3
"""Builds inventory.json from computed graph data plus hand-authored qualitative fields.

Pure functions (`consumers_of`, `dependencies_of`, `usage_evidence`, `pin_summary`, `test_coverage`,
`build_entry`, `build_inventory`) take parsed data and return data; `main` does the IO.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Mapping

REQUIRED_FIELDS = ("intendedResponsibility", "actualResponsibility", "currentRelease", "consumers", "dependencies",
                   "usageEvidence", "missingFunctionality", "duplicatedFunctionality", "unusedOrBypassed",
                   "integrationFriction", "testCoverage", "securityCoverage", "docAccuracy",
                   "highestValueNextImprovement", "evidence")
CONCRETE = ("package-ref", "CLI-invocation", "contract/schema")


def consumers_of(system: str, edges: list) -> list:
    """Repositories with a concrete (non doc-only) edge to `system`, with the edge types they use."""
    by: dict = {}
    for e in edges:
        if e["to"] == system and e["type"] in CONCRETE:
            by.setdefault(e["from"], set()).add(e["type"])
    return [{"repository": k, "edgeTypes": sorted(v)} for k, v in sorted(by.items())]


def dependencies_of(system: str, edges: list) -> list:
    by: dict = {}
    for e in edges:
        if e["from"] == system:
            d = by.setdefault(e["to"], {"types": set(), "versions": set()})
            d["types"].add(e["type"])
            d["versions"].update(e.get("versions") or [])
    return [{"system": k, "edgeTypes": sorted(v["types"]), "versions": sorted(v["versions"])}
            for k, v in sorted(by.items())]


def pin_summary(system: str, skew_rows: list) -> dict:
    """Distribution of versions consumers pin for `system` (all registry ids that map to it)."""
    rows = [r for r in skew_rows if r["consumer"] != system and
            (r["component"] == system or r["component"].startswith(system + "-"))]
    consumers_by_skew: dict = {}
    for r in rows:
        consumers_by_skew.setdefault(r["skew"], set()).add(r["consumer"])
    return {"pins": len(rows),
            "versions": dict(sorted(Counter(r["pinned"] for r in rows).items())),
            "consumersBySkew": {k: sorted(v) for k, v in sorted(consumers_by_skew.items())},
            "approved": sorted({r["approved"] for r in rows if r["approved"]})}


def usage_evidence(system: str, edges: list, skew_rows: list) -> list:
    cli = sorted({f'{e["from"]}: {v}' for e in edges if e["to"] == system and e["type"] == "CLI-invocation"
                  for v in e["vias"]})
    s = pin_summary(system, skew_rows)
    out = [f"CLI/workflow invocations: {len(cli)}"] + cli[:15]
    if s["pins"]:
        out.append(f"version pins by consumers: {s['versions']} (approved {s['approved'] or 'n/a'})")
    return out


def test_coverage(counts: Mapping) -> str:
    if not counts:
        return "NOT TESTED"
    src, tst = counts.get("sourceFiles", 0), counts.get("testFiles", 0)
    ratio = f"{tst}/{src} test/source files" if src else "no source files"
    return (f"{ratio}; {counts.get('workflows', 0)} workflows; line coverage not measured (NOT TESTED); "
            f"last commit {counts.get('lastCommit')}")


def build_entry(system: str, qual: Mapping, edges: list, skew_rows: list, latest: Mapping, counts: Mapping) -> dict:
    rel = latest.get(system) or {"version": None, "source": "no release or tag found", "date": None}
    entry = {
        "intendedResponsibility": qual.get("intendedResponsibility", "NOT ASSESSED"),
        "actualResponsibility": qual.get("actualResponsibility", "NOT ASSESSED"),
        "currentRelease": {"version": rel.get("version"), "source": rel.get("source"), "date": rel.get("date"),
                           "basis": rel.get("basis")},
        "consumers": consumers_of(system, edges),
        "dependencies": dependencies_of(system, edges),
        "usageEvidence": usage_evidence(system, edges, skew_rows),
        "pinSummary": pin_summary(system, skew_rows),
        "missingFunctionality": list(qual.get("missingFunctionality", [])),
        "duplicatedFunctionality": list(qual.get("duplicatedFunctionality", [])),
        "unusedOrBypassed": list(qual.get("unusedOrBypassed", [])),
        "integrationFriction": list(qual.get("integrationFriction", [])),
        "testCoverage": test_coverage(counts),
        "securityCoverage": qual.get("securityCoverage", "NOT ASSESSED") + (
            f" Workflow signals: {counts.get('securityWorkflowSignals')}; dependabot: {counts.get('dependabot')}."
            if counts else ""),
        "docAccuracy": qual.get("docAccuracy", "NOT ASSESSED"),
        "highestValueNextImprovement": qual.get("highestValueNextImprovement", "NOT ASSESSED"),
        "evidence": list(qual.get("evidence", [])),
    }
    return entry


def build_inventory(qual: Mapping, graph: Mapping, skew_rows: list, latest: Mapping, counts: Mapping) -> dict:
    systems = sorted(k for k in qual if not k.startswith("_"))
    return {"schema": "track-c.inventory/1", "approvedSet": graph.get("approvedSet"),
            "systems": {s: build_entry(s, qual[s], graph["edges"], skew_rows, latest, counts.get(s, {}))
                        for s in systems}}


def missing_fields(inventory: Mapping) -> list:
    return [(s, f) for s, e in inventory["systems"].items() for f in REQUIRED_FIELDS if f not in e]


def main(track: Path) -> None:
    load = lambda p: json.loads((track / p).read_text())
    inv = build_inventory(load("data/qualitative.json"), load("dependency-graph.json"), load("data/pin-skew.json"),
                          load("data/latest-releases.json"), load("data/code-counts.json"))
    assert not missing_fields(inv), missing_fields(inv)
    (track / "inventory.json").write_text(json.dumps(inv, indent=1) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
