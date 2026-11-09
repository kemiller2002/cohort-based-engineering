#!/usr/bin/env python3
"""SPR-D benchmark runner: timed, counterbalanced execution of shell steps with JSONL output.

Pure planning/summary functions are separated from the one impure `run_step` / `main`.

Usage:
  bench.py run --plan PLAN.json --out RAW.jsonl
PLAN.json: {"experiment": "SPR-D-03", "seed": 1, "replicates": 5, "cwd": "...", "env": {...},
            "arms": {"ARM": {"prepare": ["cmd", ...], "measure": "cmd"}}, "design": "abba"|"random"}
`prepare` commands run untimed before each measured command (e.g. clean or touch a file).
"""
from __future__ import annotations

import json
import os
import random
import re
import resource
import subprocess
import sys
import time
from typing import Dict, List, Sequence


# ---------- pure ----------

def schedule(arms: Sequence[str], replicates: int, seed: int, design: str = "abba") -> List[str]:
    """Order of arm executions.

    abba: for two arms, blocks alternate AB, BA, ... with the first block's order drawn from seed.
    random: each block is an independent seeded permutation of all arms.
    """
    rng = random.Random(seed)
    arms = list(arms)
    if design == "abba" and len(arms) == 2:
        first = arms[:] if rng.random() < 0.5 else arms[::-1]
        return [a for i in range(replicates) for a in (first if i % 2 == 0 else first[::-1])]
    out = []
    for _ in range(replicates):
        block = arms[:]
        rng.shuffle(block)
        out.extend(block)
    return out


def parse_test_counts(text: str) -> Dict[str, int]:
    """Sum 'Passed!  - Failed: 0, Passed: 12, Skipped: 0, Total: 12' lines from dotnet test output."""
    pat = re.compile(r"Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+)")
    rows = [tuple(int(g) for g in m.groups()) for m in pat.finditer(text)]
    keys = ("failed", "passed", "skipped", "total")
    return {k: sum(r[i] for r in rows) for i, k in enumerate(keys)} | {"assemblies": len(rows)}


def median(xs: Sequence[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def summarize(records: Sequence[dict], metric: str = "wallS") -> Dict[str, dict]:
    arms = sorted({r["arm"] for r in records})
    return {a: {"n": len(v), "median": median(v), "min": min(v), "max": max(v)}
            for a in arms for v in [[r[metric] for r in records if r["arm"] == a and r["exit"] == 0]] if v}


# ---------- impure ----------

def loadavg() -> float:
    with open("/proc/loadavg") as f:
        return float(f.read().split()[0])


def run_step(cmd: str, cwd: str, env: dict) -> dict:
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.monotonic()
    p = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, capture_output=True, text=True)
    wall = time.monotonic() - t0
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"exit": p.returncode, "wallS": round(wall, 3),
            "cpuUserS": round(after.ru_utime - before.ru_utime, 3),
            "cpuSysS": round(after.ru_stime - before.ru_stime, 3),
            "stdoutTail": p.stdout[-4000:], "stderrTail": p.stderr[-2000:]}


def main(argv: List[str]) -> int:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return 2
    args = dict(zip(argv[2::2], argv[3::2]))
    plan = json.load(open(args["--plan"]))
    env = os.environ | plan.get("env", {})
    order = schedule(list(plan["arms"]), plan["replicates"], plan["seed"], plan.get("design", "abba"))
    with open(args["--out"], "a") as out:
        for i, arm in enumerate(order):
            spec = plan["arms"][arm]
            prep = [run_step(c, plan["cwd"], env) for c in spec.get("prepare", [])]
            la0 = loadavg()
            r = run_step(spec["measure"], plan["cwd"], env)
            rec = {"experiment": plan["experiment"], "seq": i, "arm": arm, "seed": plan["seed"],
                   "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "measure": spec["measure"],
                   "prepareExits": [p["exit"] for p in prep], "loadavg1Before": la0, "loadavg1After": loadavg(),
                   "testCounts": parse_test_counts(r["stdoutTail"]) if "test" in spec["measure"] else None,
                   **{k: v for k, v in r.items() if k not in ("stdoutTail", "stderrTail")},
                   "outputTail": (r["stdoutTail"] + r["stderrTail"])[-600:]}
            out.write(json.dumps(rec) + "\n")
            out.flush()
            print(f"[{i + 1}/{len(order)}] {arm} exit={r['exit']} wall={r['wallS']}s cpu={r['cpuUserS'] + r['cpuSysS']:.1f}s load={la0}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
