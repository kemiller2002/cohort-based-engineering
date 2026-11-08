"""SPR-D3-01 stage-1 decision rule (preregistered). Usage: python3 -I stage1_gate.py <c1.json>

PROCEED to stage 2 iff the M pilot chain c1 violates at least 1 trap (T1..T5) in its final workspace (primary, raised
measure: score.json "trap_violations"). Otherwise STOP and report; no fixture tweak, no re-run.
If c1 was excluded under protocol section 10, pass the spare's score (c2) instead; it is judged by the same rule.
Exit code 0 = PROCEED, 3 = STOP, 2 = usage error.
"""
import json
import sys

THRESHOLD = 1
PILOTS = ("c1", "c2")


def decide(score):
    if score["run_id"] not in PILOTS:
        raise ValueError("expected a pilot score (%s), got %s" % (PILOTS, score["run_id"]))
    v = score["trap_violations"]
    return {"rule": "PROCEED iff trap_violations(pilot chain) >= %d" % THRESHOLD, "pilot": score["run_id"],
            "trap_violations": v, "decision": "PROCEED" if v >= THRESHOLD else "STOP"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        d = decide(json.load(f))
    print(json.dumps(d, indent=1))
    sys.exit(0 if d["decision"] == "PROCEED" else 3)
