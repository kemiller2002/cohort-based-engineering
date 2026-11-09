"""Seeded assignment for SPR-D2-03. Deterministic: python3 -I assign.py > ../assignment.json

Stage 1 (calibration): q1, q2, both arm M, batch 0. Excluded from the confirmatory analysis.
Stage 2 (confirmatory): t01..t16. random.Random(SEED): sample(STAGE2_IDS, 16) -> consecutive groups of 4 are batches
1..4 (each sorted by run ID); then, per batch in order, sample(['G','G','M','M'], 4) assigned in run-ID order.
"""
import json
import random

SEED = 2026110803
STAGE2_IDS = ["t%02d" % i for i in range(1, 17)]
PILOT_IDS = ["q1", "q2"]
WS_ROOT = "/home/user/sprint-scratch/D2c/ws"


def ws(rid):
    return "%s/%s" % (WS_ROOT, rid)


def assign(seed):
    rng = random.Random(seed)
    order = rng.sample(STAGE2_IDS, len(STAGE2_IDS))
    batches = [sorted(order[i:i + 4]) for i in range(0, 16, 4)]
    arms = [rng.sample(["G", "G", "M", "M"], 4) for _ in batches]
    stage2 = [{"runId": rid, "stage": 2, "arm": arm, "batch": b + 1, "workspace": ws(rid)}
              for b, (ids, a) in enumerate(zip(batches, arms)) for rid, arm in zip(ids, a)]
    pilots = [{"runId": rid, "stage": 1, "arm": "M", "batch": 0, "workspace": ws(rid)} for rid in PILOT_IDS]
    return {"experiment": "SPR-D2-03", "seed": seed, "python": "3.13",
            "method": "pilots q1,q2 = M (stage 1, batch 0, excluded from confirmatory analysis); stage 2: "
                      "random.Random(seed).sample(t01..t16,16) -> groups of 4 = batches 1..4; then per batch "
                      "sample(['G','G','M','M'],4) in run-ID order",
            "runs": pilots + sorted(stage2, key=lambda r: r["runId"])}


if __name__ == "__main__":
    print(json.dumps(assign(SEED), indent=1))
