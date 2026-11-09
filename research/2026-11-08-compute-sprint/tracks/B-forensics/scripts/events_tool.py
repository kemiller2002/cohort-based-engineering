"""Validate the curated event dataset and derive the normalized outputs.

  python3 -I events_tool.py ROOT   -> writes events.jsonl and data/event-analysis.json

Pure functions (validate, tally, recurrence) are unit-tested. Nothing here invents
values: counts are derived only from the curated records.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence

REQUIRED = ("rehearsal", "timestamp", "eventType", "description", "source", "rootCause",
            "contributingFactors", "requirementIds", "humanIntervention")
REHEARSALS = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "CAUSA")


def validate(events: Sequence[Mapping], codes: Iterable[str]) -> tuple:
    """Return a tuple of problem strings (empty when valid)."""
    known = set(codes)
    problems = []
    for i, ev in enumerate(events):
        missing = [k for k in REQUIRED if k not in ev]
        if missing:
            problems.append(f"{i}: missing {missing}")
            continue
        if ev["rehearsal"] not in REHEARSALS:
            problems.append(f"{i}: unknown rehearsal {ev['rehearsal']}")
        if ev["rootCause"] not in known:
            problems.append(f"{i}: unknown rootCause {ev['rootCause']}")
        for c in ev["contributingFactors"]:
            if c not in known:
                problems.append(f"{i}: unknown contributing factor {c}")
        if not str(ev["source"]).strip():
            problems.append(f"{i}: empty source")
        if not isinstance(ev["humanIntervention"], bool):
            problems.append(f"{i}: humanIntervention not bool")
        if ev.get("measuredOrEstimate") not in (None, "MEASURED", "ESTIMATE"):
            problems.append(f"{i}: bad measuredOrEstimate")
    return tuple(problems)


def with_ids(events: Sequence[Mapping]) -> tuple:
    return tuple({"id": f"B-E-{i + 1:03d}", **ev} for i, ev in enumerate(events))


def failures(events: Iterable[Mapping]) -> tuple:
    return tuple(ev for ev in events if ev["rootCause"] != "NONE")


def tally_primary(events: Iterable[Mapping]) -> dict:
    out: dict = {}
    for ev in failures(events):
        out = {**out, ev["rootCause"]: out.get(ev["rootCause"], 0) + 1}
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def recurrence(events: Iterable[Mapping]) -> dict:
    """code -> sorted rehearsals where it appears as primary or contributing cause."""
    out: dict = {}
    for ev in failures(events):
        for code in (ev["rootCause"], *ev["contributingFactors"]):
            if code != "NONE":
                out = {**out, code: out.get(code, frozenset()) | {ev["rehearsal"]}}
    order = {r: i for i, r in enumerate(REHEARSALS)}
    return dict(sorted(((k, sorted(v, key=order.get)) for k, v in out.items()),
                       key=lambda kv: (-len(kv[1]), kv[0])))


def human_by_rehearsal(events: Iterable[Mapping]) -> dict:
    out = {r: 0 for r in REHEARSALS}
    for ev in events:
        if ev["humanIntervention"]:
            out = {**out, ev["rehearsal"]: out[ev["rehearsal"]] + 1}
    return out


def count_by_rehearsal(events: Iterable[Mapping], code: str) -> dict:
    out = {r: 0 for r in REHEARSALS}
    for ev in events:
        if ev["rootCause"] == code:
            out = {**out, ev["rehearsal"]: out[ev["rehearsal"]] + 1}
    return out


def analyse(events: Sequence[Mapping]) -> dict:
    return {
        "events": len(events),
        "failureEvents": len(failures(events)),
        "primaryRootCauseCounts": tally_primary(events),
        "recurrenceAcrossRehearsals": recurrence(events),
        "humanInterventionEvents": human_by_rehearsal(events),
    }


def main(root: Path) -> None:
    sys.path.insert(0, str(root / "data"))
    from events_source import EVENTS  # noqa: E402  (curated data module)
    codes = json.loads((root / "taxonomy.json").read_text())["codes"].keys()
    problems = validate(EVENTS, codes)
    if problems:
        raise SystemExit("invalid events:\n" + "\n".join(problems))
    evs = with_ids(EVENTS)
    (root / "events.jsonl").write_text("".join(json.dumps(ev, ensure_ascii=False) + "\n" for ev in evs))
    (root / "data" / "event-analysis.json").write_text(json.dumps(analyse(evs), indent=1) + "\n")
    print(json.dumps(analyse(evs), indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
