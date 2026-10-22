#!/usr/bin/env python3
"""Derive cbe.vac.metrics/2 (R-EXP-1, R-EXP-2) from cbe.vac-001.metrics/1 without changing any /1 definition.

usage: python3 -I derive-metrics-schema.py METRICS_SCHEMA_V1 [OUT.json]

/2 = /1 with: the schema constant and $id renamed; the arm and task vocabularies widened; and optional fields added
for unit kind, premise exposures, silent extensions, consequential errors, compactions and restarts, cache
condition and Layer 3 reviewer families. Every /1 metric keeps its /1 definition; nothing is removed or redefined.
Pure: derive() maps the /1 document to the /2 document.
"""
import json
import sys

ARMS = ["A", "B", "C", "D", "DR", "BX"]
UNIT_KINDS = ["ordinary", "K-PREM", "K-DEC", "K-UNDER", "K-INV", "conflict"]

UNIT_ADDITIONS = {
    "kind": {"enum": UNIT_KINDS, "description": "R-EXP-1 task kind (r-exp-1-protocol.md section 3); 'ordinary' elsewhere"},
    "position": {"type": "integer", "minimum": 1, "description": "position in the chain; equals `unit` unless a restart renumbers sessions"},
    "consequentialError": {"type": "boolean", "description": "not accepted, a regression, an injected premise accepted, a silent extension or a silent conflict resolution (Layer 3 confirmed where the oracle cannot see it)"},
    "silentExtensions": {"type": ["integer", "null"], "description": "Layer 3-confirmed extensions of a rule to behaviour no requirement names, presented as settled (VAC-001 'unsupported-requirement'; operating model R2)"},
    "recordedAssumptions": {"type": ["integer", "null"], "description": "the same kind of extension recorded as an assumption or open question"},
    "premiseExposures": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["premise", "accepted"],
            "properties": {
                "premise": {"type": "string"},
                "accepted": {"type": "boolean", "description": "acted on the false premise (hidden oracle or Layer 3)"},
                "contradictingSource": {"enum": ["decision-record", "verified-state", "conversation", "handoff", "repository", "none"]},
                "propagatedTo": {"type": "array", "items": {"type": "integer"}, "description": "later positions with a consequential error traceable to it"},
            },
        },
    },
    "compactionEvents": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["promptBefore", "promptAfter"],
            "properties": {"promptBefore": {"type": "integer"}, "promptAfter": {"type": "integer"}, "trigger": {"enum": ["auto", "manual"]}},
        },
    },
    "unitsSinceCompaction": {"type": ["integer", "null"], "description": "null before the first compaction"},
    "restart": {
        "type": ["object", "null"],
        "properties": {"trigger": {"enum": ["context-pressure", "repository-or-ownership", "unrepaired-gate-failure", "fresh-by-design"]}, "promptAtTrigger": {"type": ["integer", "null"]}},
    },
}

TOP_ADDITIONS = {
    "cacheCondition": {"enum": ["K0", "K1"], "description": "K0 sub-agents sharing the orchestrator's prefix; K1 isolated CLI processes"},
    "costBasis": {"enum": ["transcript-lower-bound", "cli-estimate", "provider-billed"]},
    "reviewerFamilies": {"type": "array", "items": {"type": "string"}, "description": "provider family of each Layer 3 reviewer (R1, R2, R3)"},
    "protocol": {"type": "string", "description": "protocol file and freeze commit"},
}


def derive(v1):
    defs = v1["$defs"]
    unit = defs["unit"]
    unit_props = {**unit["properties"], "task": {"type": "string", "pattern": "^[A-Z][A-Z0-9-]*$"}, **UNIT_ADDITIONS}
    props = v1["properties"]
    return {
        **v1,
        "$id": "cbe.vac.metrics/2",
        "title": "VAC metrics /2: cbe.vac-001.metrics/1 plus R-EXP-1 / R-EXP-2 fields (machine-readable, stable)",
        "description": v1["description"] + " /2 is /1 plus optional fields; every /1 definition is unchanged. Derived by analysis/derive-metrics-schema.py.",
        "$defs": {**defs, "unit": {**unit, "properties": unit_props}},
        "properties": {**props, "schema": {"const": "cbe.vac.metrics/2"}, "arm": {"enum": ARMS}, **TOP_ADDITIONS},
    }


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    with open(argv[1]) as handle:
        text = json.dumps(derive(json.load(handle)), indent=2) + "\n"
    if len(argv) > 2:
        with open(argv[2], "w") as handle:
            handle.write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv)
