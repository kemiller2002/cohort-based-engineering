#!/usr/bin/env python3
"""REL-001 run-02 trial order (design 02-run02-design.md, "Trial matrix and order" and "Replicates").

Blocked randomization with seed 20261020, as run-01 (harness/d/randomize.py):
  * blocks are (task, replicate): 3 replicates for U2, U3, U7 and U9, 2 for U1, U4, U5, U6 and U8,
    giving 22 blocks x 4 arms = 88 trials;
  * the block list starts in task order U1..U9, replicate order; the block order is shuffled, then the
    arm order inside each block (one shuffle per block, in the shuffled block order), all from one
    random.Random(seed) (stable across CPython 3.x for a given seed).
The pilot (excluded from every analysis) is fixed, not randomized: U1 in all four arms, then one U6 in
arm D.
usage: python3 -I randomize.py [OUT_DIR] [SEED]  -> writes OUT_DIR/order.json and OUT_DIR/pilot-order.json
"""
import json
import os
import random
import sys

ARMS = ["bare", "directives", "echelon-original", "echelon-optimized"]
LETTER = dict(zip(ARMS, "ABCD"))
REPLICATES = {"U1": 2, "U2": 3, "U3": 3, "U4": 2, "U5": 2, "U6": 2, "U7": 3, "U8": 2, "U9": 3}


def run_id(task, label, arm):
    return f"REL-001-R2-{task}-{label}-{arm}" if label.startswith("r") else f"REL-001-R2-{label}-{task}-{arm}"


def trial(seq, task, replicate, arm, label="trial"):
    tag = f"r{replicate}" if label == "trial" else label.upper()
    return {"seq": seq, "runId": run_id(task, tag, arm), "task": task, "replicate": replicate,
            "block": f"{task}-r{replicate}", "arm": arm, "armLetter": LETTER[arm], "label": label}


def order(seed):
    rng = random.Random(seed)
    blocks = [(t, r) for t in sorted(REPLICATES) for r in range(1, REPLICATES[t] + 1)]
    rng.shuffle(blocks)
    def arms_for_block():
        arms = list(ARMS)
        rng.shuffle(arms)
        return arms
    pairs = [(t, r, a) for t, r in blocks for a in arms_for_block()]
    return blocks, [trial(i + 1, t, r, a) for i, (t, r, a) in enumerate(pairs)]


def pilot():
    runs = [(t, a) for t, a in [("U1", a) for a in ARMS] + [("U6", "echelon-optimized")]]
    return [trial(i + 1, t, 1, a, "pilot") for i, (t, a) in enumerate(runs)]


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    seed = int(argv[2]) if len(argv) > 2 else 20261020
    blocks, trials = order(seed)
    assert len(blocks) == 22 and len(trials) == 88
    doc = {"schema": "cbe.rel-001.run-02-order/1", "seed": seed, "algorithm": __doc__.strip().splitlines()[0],
           "blocks": [f"{t}-r{r}" for t, r in blocks], "trials": trials}
    pdoc = {"schema": "cbe.rel-001.run-02-order/1", "label": "pilot", "excludedFromAnalysis": True,
            "note": "U1 in all four arms, then one U6 in arm D; run before the confirmatory order", "trials": pilot()}
    for name, d in [("order.json", doc), ("pilot-order.json", pdoc)]:
        with open(os.path.join(out, name), "w") as f:
            f.write(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"seed": seed, "trials": len(trials), "blocks": len(blocks), "pilot": len(pdoc["trials"])}))


if __name__ == "__main__":
    main(sys.argv)
