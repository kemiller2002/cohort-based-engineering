"""Seeded assignment for SPR-D3-01. Deterministic: python3 -I assign.py > ../assignment.json

Stage 1 (pilot): c1, arm M, batch 0 (c2 = spare, arm M, used only if c1 is excluded under protocol section 10).
Pilots are excluded from the confirmatory analysis.
Stage 2 (confirmatory): u01..u08 (chains of K = 6 steps). random.Random(SEED): sample(STAGE2_IDS, 8) -> consecutive
groups of 4 are batches 1..2 (each sorted by chain ID); then, per batch in order, sample(['G','G','M','M'], 4)
assigned in chain-ID order.
"""
import json
import random

SEED = 2026110831
STAGE2_IDS = ["u%02d" % i for i in range(1, 9)]
PILOT_IDS = ["c1", "c2"]
WS_ROOT = "/home/user/sprint-scratch/D3/ws"
SNAP_ROOT = "/home/user/sprint-scratch/D3/snap"
K = 6


def ws(rid):
    return "%s/%s" % (WS_ROOT, rid)


def assign(seed):
    rng = random.Random(seed)
    order = rng.sample(STAGE2_IDS, len(STAGE2_IDS))
    batches = [sorted(order[i:i + 4]) for i in range(0, 8, 4)]
    arms = [rng.sample(["G", "G", "M", "M"], 4) for _ in batches]
    stage2 = [{"runId": rid, "stage": 2, "arm": arm, "batch": b + 1, "workspace": ws(rid),
               "snapshots": "%s/%s" % (SNAP_ROOT, rid)}
              for b, (ids, a) in enumerate(zip(batches, arms)) for rid, arm in zip(ids, a)]
    pilots = [{"runId": rid, "stage": 1, "arm": "M", "batch": 0, "workspace": ws(rid),
               "snapshots": "%s/%s" % (SNAP_ROOT, rid), "role": "pilot" if rid == "c1" else "spare"}
              for rid in PILOT_IDS]
    return {"experiment": "SPR-D3-01", "seed": seed, "python": "3.13", "steps_per_chain": K,
            "method": "pilot c1 = M (stage 1, batch 0; c2 spare), excluded from confirmatory analysis; stage 2: "
                      "random.Random(seed).sample(u01..u08,8) -> groups of 4 = batches 1..2; then per batch "
                      "sample(['G','G','M','M'],4) in chain-ID order",
            "runs": pilots + sorted(stage2, key=lambda r: r["runId"])}


if __name__ == "__main__":
    print(json.dumps(assign(SEED), indent=1))
