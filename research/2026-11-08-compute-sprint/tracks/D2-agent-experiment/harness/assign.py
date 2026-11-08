"""Seeded, balanced arm assignment for SPR-D2-01. Deterministic: python3 -I assign.py > ../assignment.json"""
import json
import random

SEED = 20261108
RUN_IDS = ["r%d" % i for i in range(1, 9)]
WS_ROOT = "/home/user/sprint-scratch/D2/ws"


def assign(seed):
    rng = random.Random(seed)
    order = rng.sample(RUN_IDS, len(RUN_IDS))            # random split into two batches of 4
    batches = [sorted(order[:4], key=RUN_IDS.index), sorted(order[4:], key=RUN_IDS.index)]
    arms = [rng.sample(["M", "M", "G", "G"], 4) for _ in batches]  # 2 M + 2 G inside each batch
    rows = [{"runId": rid, "arm": arm, "batch": b + 1, "workspace": "%s/%s" % (WS_ROOT, rid)}
            for b, (ids, a) in enumerate(zip(batches, arms)) for rid, arm in zip(ids, a)]
    return {"experiment": "SPR-D2-01", "seed": seed, "method": "random.Random(seed): sample(RUN_IDS,8) -> first 4 = "
            "batch 1, rest = batch 2; then per batch sample(['M','M','G','G'],4) in runId order",
            "python": "3.13", "runs": sorted(rows, key=lambda r: RUN_IDS.index(r["runId"]))}


if __name__ == "__main__":
    print(json.dumps(assign(SEED), indent=1))
