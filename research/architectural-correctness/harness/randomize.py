#!/usr/bin/env python3
"""ARCH-001 trial order (adapted from REL-001 run-03 harness/randomize.py; see PROVENANCE.md).

usage: python3 -I randomize.py [OUT_DIR] [--seed N] [--replicates K] [--tasks T1,T2,...]
  -> OUT_DIR/order.json (confirmatory) and OUT_DIR/pilot-order.json

Blocked randomization, the run-02/run-03 algorithm with ARCH-001 constants:
  * blocks are (task, replicate): REPLICATES replicates of each task T1..T8 (default 3 -> 24 blocks x 4 arms = 96);
  * the block list starts in task order, replicate order; the block order is shuffled, then the arm order inside
    each block (one shuffle per block, in the shuffled block order), all from one random.Random(seed)
    (stable across CPython 3.x for a given seed). Each trial is one process running both phases.
The pilot (excluded from every confirmatory analysis) is fixed, not randomized: T1 then T8, each in arms A, B, C, D,
one replicate, both phases.
Run ids: ARCH-001-CONF-T<n>-r<k>-<arm>, ARCH-001-PILOT-T<n>-r1-<arm>.
"""
import json
import os
import random
import sys

ARMS = ["A", "B", "C", "D"]
TASKS = [f"T{i}" for i in range(1, 9)]
DEFAULT_REPLICATES = 3
DEFAULT_SEED = 20261022
PILOT = [("T1", a) for a in ARMS] + [("T8", a) for a in ARMS]


def run_id(label, task, rep, arm):
    return f"ARCH-001-{label}-{task}-r{rep}-{arm}"


def trial(seq, task, rep, arm, label):
    return {"seq": seq, "runId": run_id(label, task, rep, arm), "task": task, "replicate": rep,
            "block": f"{task}-r{rep}", "arm": arm, "label": "confirmatory" if label == "CONF" else "pilot"}


def shuffled(rng, xs):
    ys = list(xs)
    rng.shuffle(ys)
    return ys


def order(seed, tasks, replicates):
    rng = random.Random(seed)
    blocks = shuffled(rng, [(t, r) for t in tasks for r in range(1, replicates + 1)])
    pairs = [(t, r, a) for t, r in blocks for a in shuffled(rng, ARMS)]
    return blocks, [trial(i + 1, t, r, a, "CONF") for i, (t, r, a) in enumerate(pairs)]


def pilot():
    return [trial(i + 1, t, 1, a, "PILOT") for i, (t, a) in enumerate(PILOT)]


def options(argv):
    args = [a for a in argv[1:]]
    get = lambda k, d: args[args.index(k) + 1] if k in args else d
    positional = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    return {"out": positional[0] if positional else os.path.dirname(os.path.abspath(__file__)),
            "seed": int(get("--seed", DEFAULT_SEED)), "replicates": int(get("--replicates", DEFAULT_REPLICATES)),
            "tasks": get("--tasks", ",".join(TASKS)).split(",")}


def main(argv):
    o = options(argv)
    blocks, trials = order(o["seed"], o["tasks"], o["replicates"])
    assert len(trials) == len(o["tasks"]) * o["replicates"] * len(ARMS)
    assert all(sorted(t["arm"] for t in trials if t["block"] == f"{b}-r{r}") == ARMS for b, r in blocks)
    doc = {"schema": "arch001.order/1", "label": "confirmatory", "seed": o["seed"], "replicates": o["replicates"],
           "tasks": o["tasks"], "arms": ARMS, "algorithm": __doc__.strip().splitlines()[0],
           "blocks": [f"{t}-r{r}" for t, r in blocks], "trials": trials}
    pdoc = {"schema": "arch001.order/1", "label": "pilot", "excludedFromConfirmatoryAnalysis": True,
            "note": "T1 then T8, each in arms A-D, one replicate, both phases; run before the confirmatory order",
            "trials": pilot()}
    for name, d in [("order.json", doc), ("pilot-order.json", pdoc)]:
        with open(os.path.join(o["out"], name), "w") as f:
            f.write(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"seed": o["seed"], "trials": len(trials), "blocks": len(blocks), "pilot": len(pdoc["trials"])}))


if __name__ == "__main__":
    main(sys.argv)
