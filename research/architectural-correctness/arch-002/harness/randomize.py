#!/usr/bin/env python3
"""ARCH-002 trial orders (adapted from ARCH-001 harness/randomize.py; see ../PROVENANCE.md).

usage: python3 -I randomize.py [OUT_DIR] [--seed N] [--replicates K] [--fixtures DIR] [--suite F:T1,T2;G:T1]
                               [--pilot F:Tn;G:Tm] [--only calibration|pilot|confirmatory]
  -> OUT_DIR/calibration-order.json, OUT_DIR/pilot-order.json, OUT_DIR/order.json (confirmatory)

The suite is every fixtures/<fixture>/tasks/T<n>/task.json (fixtures and tasks in name order; stand-in fixtures,
task.json .standIn, are skipped) unless --suite names it. Models: opus, sonnet. Arms: A-D.

Confirmatory (INTERFACES §5-6): blocked randomization, the ARCH-001 algorithm with ARCH-002 blocks:
  * a block is (fixture, task, model, replicate) and carries all four arms of that cell;
  * the block list starts in suite order (fixture, task), then model, then replicate; the block order is shuffled,
    then the arm order inside each block (one shuffle per block, in the shuffled block order), all from one
    random.Random(seed) (stable across CPython 3.x for a given integer seed).
Calibration (excluded from every analysis): arm A only, every task x both models x 1 replicate; the (fixture, task,
  model) list in suite order shuffled by random.Random(seed + 1).
Pilot (excluded): the --pilot tasks (default: the first task of F1 lending-brownfield and of F2 summa)
  x 4 arms x 2 models x 1 replicate; blocks (fixture, task, model) in fixed order, arm order shuffled within each block
  by random.Random(seed + 2).
Run ids: ARCH-002-{CAL|PILOT|CONF}-<fixture>-T<n>-<model>-r<k>-<arm>.
"""
import json
import os
import random
import sys

ARMS = ["A", "B", "C", "D"]
MODELS = ["opus", "sonnet"]
DEFAULT_SEED = 20261023
DEFAULT_REPLICATES = 2
LABELS = {"CONF": "confirmatory", "PILOT": "pilot", "CAL": "calibration"}
PILOT_FIXTURES = ("lending-brownfield", "summa")   # F1 and F2 (INTERFACES §4); F3 signal is never a pilot fixture


def run_id(label, fixture, task, model, rep, arm):
    return f"ARCH-002-{label}-{fixture}-{task}-{model}-r{rep}-{arm}"


def trial(seq, label, fixture, task, model, rep, arm):
    return {"seq": seq, "runId": run_id(label, fixture, task, model, rep, arm), "fixture": fixture, "task": task,
            "taskKey": f"{fixture}/{task}", "model": model, "replicate": rep, "arm": arm,
            "block": f"{fixture}/{task}/{model}/r{rep}", "label": LABELS[label]}


def shuffled(rng, xs):
    ys = list(xs)
    rng.shuffle(ys)
    return ys


def task_number(t):
    return int(t[1:]) if t[1:].isdigit() else 0


def discover(fixtures_dir):
    """[(fixture, [task, ...])] from fixtures/<fixture>/tasks/T<n>/task.json, skipping stand-in tasks."""
    out = []
    for f in sorted(os.listdir(fixtures_dir)) if os.path.isdir(fixtures_dir) else []:
        tdir = os.path.join(fixtures_dir, f, "tasks")
        if not os.path.isdir(tdir):
            continue
        def real(t):
            try:
                return not json.load(open(os.path.join(tdir, t, "task.json"))).get("standIn")
            except (OSError, ValueError):
                return False
        tasks = sorted((t for t in os.listdir(tdir) if t.startswith("T") and real(t)), key=task_number)
        if tasks:
            out.append((f, tasks))
    return out


def parse_suite(text):
    """"F:T1,T2;G:T1" -> [(F, [T1, T2]), (G, [T1])]"""
    return [(f, ts.split(",")) for f, ts in (part.split(":", 1) for part in text.split(";") if part)]


def confirmatory(seed, suite, replicates):
    rng = random.Random(seed)
    blocks = shuffled(rng, [(f, t, m, r) for f, ts in suite for t in ts for m in MODELS for r in range(1, replicates + 1)])
    cells = [(f, t, m, r, a) for f, t, m, r in blocks for a in shuffled(rng, ARMS)]
    return blocks, [trial(i + 1, "CONF", *c) for i, c in enumerate(cells)]


def calibration(seed, suite):
    rng = random.Random(seed + 1)
    cells = shuffled(rng, [(f, t, m) for f, ts in suite for t in ts for m in MODELS])
    return [trial(i + 1, "CAL", f, t, m, 1, "A") for i, (f, t, m) in enumerate(cells)]


def pilot(seed, pilot_tasks):
    rng = random.Random(seed + 2)
    cells = [(f, t, m, a) for f, ts in pilot_tasks for t in ts for m in MODELS for a in shuffled(rng, ARMS)]
    return [trial(i + 1, "PILOT", f, t, m, 1, a) for i, (f, t, m, a) in enumerate(cells)]


def options(argv):
    args = list(argv[1:])
    get = lambda k, d: args[args.index(k) + 1] if k in args else d
    positional = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    here = os.path.dirname(os.path.abspath(__file__))
    fixtures = get("--fixtures", os.path.join(here, "..", "fixtures"))
    suite = parse_suite(get("--suite", "")) if "--suite" in args else discover(fixtures)
    preferred = [x for x in suite if x[0] in PILOT_FIXTURES] or suite[:2]
    pilot_tasks = parse_suite(get("--pilot", "")) if "--pilot" in args else [(f, ts[:1]) for f, ts in preferred]
    return {"out": positional[0] if positional else here, "seed": int(get("--seed", DEFAULT_SEED)),
            "replicates": int(get("--replicates", DEFAULT_REPLICATES)), "suite": suite, "pilot": pilot_tasks,
            "only": get("--only", None)}


def documents(o):
    seed, suite = o["seed"], o["suite"]
    blocks, trials = confirmatory(seed, suite, o["replicates"])
    n_tasks = sum(len(ts) for _, ts in suite)
    assert len(trials) == n_tasks * len(MODELS) * o["replicates"] * len(ARMS)
    assert all(sorted(t["arm"] for t in trials if t["block"] == f"{f}/{t_}/{m}/r{r}") == ARMS for f, t_, m, r in blocks)
    meta = {"seed": seed, "suite": {f: ts for f, ts in suite}, "models": MODELS, "algorithm": __doc__.strip().splitlines()[0]}
    cal = calibration(seed, suite)
    pil = pilot(seed, o["pilot"])
    return {
        "calibration-order.json": {"schema": "arch002.order/1", "label": "calibration", "excludedFromAnalysis": True, **meta,
                                   "arms": ["A"], "replicates": 1,
                                   "note": "arm A only; every task x both models x 1; arm-blind revision allowed (INTERFACES §5)",
                                   "trials": cal},
        "pilot-order.json": {"schema": "arch002.order/1", "label": "pilot", "excludedFromConfirmatoryAnalysis": True, **meta,
                             "arms": ARMS, "replicates": 1, "pilotTasks": {f: ts for f, ts in o["pilot"]},
                             "note": "pilot tasks x 4 arms x 2 models x 1 replicate, both phases; before the confirmatory order",
                             "trials": pil},
        "order.json": {"schema": "arch002.order/1", "label": "confirmatory", **meta, "arms": ARMS, "replicates": o["replicates"],
                       "blocks": [f"{f}/{t}/{m}/r{r}" for f, t, m, r in blocks], "trials": trials},
    }


def main(argv):
    o = options(argv)
    if not o["suite"]:
        raise SystemExit("no tasks: pass --suite F:T1,T2;G:T1 or populate fixtures/<fixture>/tasks/")
    docs = documents(o)
    keep = {"calibration": "calibration-order.json", "pilot": "pilot-order.json", "confirmatory": "order.json"}
    for name, d in docs.items():
        if o["only"] and keep[o["only"]] != name:
            continue
        with open(os.path.join(o["out"], name), "w") as f:
            f.write(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"seed": o["seed"], "suite": {f: ts for f, ts in o["suite"]}, "confirmatory": len(docs["order.json"]["trials"]),
                      "calibration": len(docs["calibration-order.json"]["trials"]), "pilot": len(docs["pilot-order.json"]["trials"])}))


if __name__ == "__main__":
    main(sys.argv)
