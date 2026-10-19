#!/usr/bin/env python3
"""REL-001 run-01 Experiment D trial order (preregistered).

Blocked randomization: blocks are (task, replicate); block order is shuffled,
then the arm order inside each block. Seed and algorithm are fixed in
analysis/preregistration.json. Python's random.Random(seed).shuffle is
stable across CPython 3.x for a given seed.
usage: python3 -I randomize.py [SEED]
"""
import json, random, sys

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261019
blocks = [(t, r) for t in ["T1", "T2", "T3"] for r in [1, 2]]
rng = random.Random(seed)
rng.shuffle(blocks)
order = []
for t, r in blocks:
    arms = ["baseline", "treatment"]
    rng.shuffle(arms)
    order += [f"{t}-r{r}-{a}" for a in arms]
print(json.dumps({"seed": seed, "order": order}))
