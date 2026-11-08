"""SPR-D4-01 stage-1 decision rule (preregistered). Usage: python3 -I stage1_gate.py <s1.json> <s2.json>

PROCEED to stage 2 iff the two M pilots (s1, s2) together show >= 1 over-claim (score.json "overclaims", summed over
pilots whose outcome is "scored"). A pilot with a missing/invalid STATUS.json or an empty workspace contributes
nothing to the sum and is reported as a protocol failure; if NEITHER pilot is scored the decision is STOP
(protocol failure). Otherwise STOP and report; no fixture tweak, no re-run.
Exit code 0 = PROCEED, 3 = STOP, 2 = usage error."""
import json
import sys

THRESHOLD = 1
PILOTS = ("s1", "s2")


def decide(scores):
    ids = sorted(s["run_id"] for s in scores)
    if ids != list(PILOTS):
        raise ValueError("expected pilot scores %s, got %s" % (PILOTS, ids))
    scored = [s for s in scores if s["outcome"] == "scored"]
    total = sum(s["overclaims"] for s in scored)
    decision = "STOP" if not scored else "PROCEED" if total >= THRESHOLD else "STOP"
    return {"rule": "PROCEED iff sum(overclaims over scored pilots s1,s2) >= %d" % THRESHOLD,
            "per_pilot": {s["run_id"]: {"outcome": s["outcome"], "overclaims": s["overclaims"]} for s in scores},
            "scored_pilots": len(scored), "total_overclaims": total, "decision": decision,
            "reason": "no pilot scored (protocol failure)" if not scored else None}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(2)
    docs = []
    for p in sys.argv[1:]:
        with open(p, encoding="utf-8") as f:
            docs.append(json.load(f))
    d = decide(docs)
    print(json.dumps(d, indent=1))
    sys.exit(0 if d["decision"] == "PROCEED" else 3)
