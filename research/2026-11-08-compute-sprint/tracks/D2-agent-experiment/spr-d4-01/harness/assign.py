"""Seeded assignment for SPR-D4-01. Deterministic: python3 -I assign.py > ../assignment.json

Stage 1 (pilots): s1, s2, both arm M, batch 0. Excluded from the confirmatory analysis.
Stage 2 (confirmatory): w01..w16. random.Random(SEED): sample(STAGE2_IDS, 16) -> consecutive groups of 4 are
batches 1..4 (each sorted by run ID); then, per batch in order, sample(['G','G','M','M'], 4) assigned in run-ID order.
Each batch is therefore 2 G + 2 M (counterbalanced), 8 per arm in total.
"""
import json
import random

SEED = 2026110841
STAGE2_IDS = ["w%02d" % i for i in range(1, 17)]
PILOT_IDS = ["s1", "s2"]
WS_ROOT = "/home/user/sprint-scratch/D4/ws"


def ws(rid):
    return "%s/%s" % (WS_ROOT, rid)


def assign(seed):
    rng = random.Random(seed)
    order = rng.sample(STAGE2_IDS, len(STAGE2_IDS))
    batches = [sorted(order[i:i + 4]) for i in range(0, 16, 4)]
    arms = [rng.sample(["G", "G", "M", "M"], 4) for _ in batches]
    stage2 = [{"runId": rid, "stage": 2, "arm": arm, "batch": b + 1, "workspace": ws(rid)}
              for b, (ids, a) in enumerate(zip(batches, arms)) for rid, arm in zip(ids, a)]
    pilots = [{"runId": rid, "stage": 1, "arm": "M", "batch": 0, "workspace": ws(rid), "role": "pilot"}
              for rid in PILOT_IDS]
    return {"experiment": "SPR-D4-01", "seed": seed, "python": "3.13",
            "method": "pilots s1,s2 = M (stage 1, batch 0), excluded from confirmatory analysis; stage 2: "
                      "random.Random(seed).sample(w01..w16,16) -> groups of 4 = batches 1..4; then per batch "
                      "sample(['G','G','M','M'],4) in run-ID order",
            "runs": pilots + sorted(stage2, key=lambda r: r["runId"])}


if __name__ == "__main__":
    print(json.dumps(assign(SEED), indent=1))
