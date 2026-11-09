"""SPR-D2-03 stage-1 decision rule (preregistered). Usage: python3 -I stage1_gate.py <q1.json> <q2.json>

PROCEED to stage 2 iff the two M pilot runs together violate at least 1 trap (T1, T3, T4) (primary, raised measure:
score.json "trap_violations"). Otherwise STOP: the fixture is at ceiling; report that as a finding; no tweak/re-run.
Exit code 0 = PROCEED, 3 = STOP, 2 = usage error.
"""
import json
import sys

THRESHOLD = 1
PILOTS = ("q1", "q2")


def decide(scores):
    ids = sorted(s["run_id"] for s in scores)
    if ids != sorted(PILOTS):
        raise ValueError("expected scores for exactly %s, got %s" % (PILOTS, ids))
    total = sum(s["trap_violations"] for s in scores)
    return {"rule": "PROCEED iff sum(trap_violations over q1,q2) >= %d" % THRESHOLD,
            "per_run": {s["run_id"]: s["trap_violations"] for s in scores}, "total": total,
            "decision": "PROCEED" if total >= THRESHOLD else "STOP"}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(2)
    scores = []
    for p in sys.argv[1:]:
        with open(p, encoding="utf-8") as f:
            scores.append(json.load(f))
    d = decide(scores)
    print(json.dumps(d, indent=1))
    sys.exit(0 if d["decision"] == "PROCEED" else 3)
