#!/usr/bin/env python3
"""REL-001 run-03 trial order (protocol/run-03.md, "Trial matrix and order").

Blocked randomization, the run-02 algorithm (run-02/harness/randomize.py) with run-03's tasks and seed:
  * blocks are (task, replicate): 3 replicates for each of V1..V8, giving 24 blocks x 4 arms = 96 trials;
  * the block list starts in task order V1..V8, replicate order; the block order is shuffled, then the arm order
    inside each block (one shuffle per block, in the shuffled block order), all from one random.Random(seed)
    (stable across CPython 3.x for a given seed).
The pilot (excluded from every analysis) is fixed, not randomized: V1 in all four arms, then V7 in arm D.
usage: python3 -I randomize.py [OUT_DIR] [SEED]  -> writes OUT_DIR/order.json and OUT_DIR/pilot-order.json
"""
import json
import os
import random
import sys

ARMS = ["bare", "directives", "echelon-original", "echelon-optimized"]
LETTER = dict(zip(ARMS, "ABCD"))
TASKS = [f"V{i}" for i in range(1, 9)]
REPLICATES = {t: 3 for t in TASKS}
DEFAULT_SEED = 20261021


def run_id(task, tag, arm):
    return f"REL-001-R3-{task}-{tag}-{arm}" if tag.startswith("r") else f"REL-001-R3-{tag}-{task}-{arm}"


def trial(seq, task, replicate, arm, label="trial"):
    tag = f"r{replicate}" if label == "trial" else label.upper()
    return {"seq": seq, "runId": run_id(task, tag, arm), "task": task, "replicate": replicate,
            "block": f"{task}-r{replicate}", "arm": arm, "armLetter": LETTER[arm], "label": label}


def shuffled(rng, xs):
    ys = list(xs)
    rng.shuffle(ys)
    return ys


def order(seed):
    rng = random.Random(seed)
    blocks = shuffled(rng, [(t, r) for t in TASKS for r in range(1, REPLICATES[t] + 1)])
    pairs = [(t, r, a) for t, r in blocks for a in shuffled(rng, ARMS)]
    return blocks, [trial(i + 1, t, r, a) for i, (t, r, a) in enumerate(pairs)]


def pilot():
    runs = [("V1", a) for a in ARMS] + [("V7", "echelon-optimized")]
    return [trial(i + 1, t, 1, a, "pilot") for i, (t, a) in enumerate(runs)]


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    seed = int(argv[2]) if len(argv) > 2 else DEFAULT_SEED
    blocks, trials = order(seed)
    assert len(blocks) == 24 and len(trials) == 96
    assert all(sorted(t["arm"] for t in trials if t["block"] == f"{b}-r{r}") == sorted(ARMS) for b, r in blocks)
    doc = {"schema": "cbe.rel-001.run-03-order/1", "seed": seed, "algorithm": __doc__.strip().splitlines()[0],
           "blocks": [f"{t}-r{r}" for t, r in blocks], "trials": trials}
    pdoc = {"schema": "cbe.rel-001.run-03-order/1", "label": "pilot", "excludedFromAnalysis": True,
            "note": "V1 in all four arms, then V7 in arm D; run before the confirmatory order", "trials": pilot()}
    for name, d in [("order.json", doc), ("pilot-order.json", pdoc)]:
        with open(os.path.join(out, name), "w") as f:
            f.write(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"seed": seed, "trials": len(trials), "blocks": len(blocks), "pilot": len(pdoc["trials"])}))


if __name__ == "__main__":
    main(sys.argv)
