#!/usr/bin/env python3
"""REL-001 run-03 analysis self-test on SYNTHETIC observations (never real data; nothing here is a result).

usage: python3 -I selftest.py
Builds 96 synthetic observations (24 blocks x 4 arms, the order.json design) from a fixed formula, with planted
cases: one X4 run, one X2 run, one run whose cost is unavailable and one with tokens unavailable. It then checks:
  T1  analyze.py output is byte-identical across two runs (determinism);
  T2  X4 removes the run from every comparison; X2 removes the block from comparisons involving that arm;
  T3  X3: the run without cost leaves only the cost comparisons (its block stays in the token comparison);
  T4  a planted 30% cost reduction in arm D is recovered by H1 with an interval excluding 0;
  T5  pilot and smoke observations are ignored unless --include-smoke.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = json.load(open(os.path.join(HERE, "..", "harness", "order.json")))
CATEGORY = {"V1": "simple", "V2": "simple", "V3": "moderate", "V4": "moderate", "V5": "complex", "V6": "complex", "V7": "adversarial", "V8": "adversarial"}
UNITS = {"V1": 1, "V2": 1, "V3": 2, "V4": 2, "V5": 3, "V6": 3, "V7": 1, "V8": 2}
FACTOR = {"A": 1.0, "B": 1.05, "C": 1.3, "D": 0.7}


def avail(v, unit):
    return {"availability": "unavailable" if v is None else "available", "value": v, "unit": unit}


def synthetic(t, planted):
    task, arm, rep = t["task"], t["armLetter"], t["replicate"]
    base = 0.2 * UNITS[task] * (1 + 0.1 * ((t["seq"] * 7) % 5 - 2) / 2)
    cost = round(base * FACTOR[arm], 6)
    correct = UNITS[task] if (t["seq"] % 11) or arm == "D" else UNITS[task] - 1
    tokens = int(cost * 2_000_000)
    p = planted.get(t["runId"], set())
    eligible = {"correct": "x4" not in p, "cost": "nocost" not in p, "tokensTotal": "notokens" not in p,
                "tokensExcludingCacheReads": True, "coldEquivalentCost": True, "wallMs": True, "toolCalls": True,
                "testRuns": True, "pairedComparisons": not ({"x4", "x2"} & p)}
    return {"schema": "cbe.rel-001.observation/1", "runId": t["runId"], "supersedes": None, "status": "excluded" if "x4" in p else "completed",
            "task": {"taskId": task}, "cache": {"condition": "K1 isolated-cli (synthetic)", "measured": {"firstRequestCold": True, "cacheReadShare": 0.5}},
            "metrics": {"costEstimated": avail(None if "nocost" in p else cost, "USD"), "tokensTotal": avail(None if "notokens" in p else tokens, "tokens")},
            "run03": {"armLetter": arm, "category": CATEGORY[task], "block": t["block"], "label": t.get("label", "trial"),
                      "units": {"total": UNITS[task], "correct": correct}, "completionEvidence": {"recorded": True},
                      "tokens": {"excludingCacheReads": avail(tokens // 10, "tokens")}, "cost": {"coldEquivalentUsd": cost * 3},
                      "wallMs": 60000, "toolCalls": 10, "tests": {"total": 2, "computeMs": 5000},
                      "reliability": {"invalidCompletionsAccepted": 0, "escapedDefects": UNITS[task] - correct},
                      "firstPassCorrect": correct == UNITS[task],
                      "exclusions": {"x4": {"contaminated": "x4" in p}, "x5": {"budgetExceeded": False}, "x6": {"tampered": False}},
                      "eligibility": eligible}}


def run(obs_dir, out, *flags):
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "analyze.py"), obs_dir, out, *flags], check=True, capture_output=True)
    return open(out, "rb").read()


def main():
    trials = ORDER["trials"]
    pick = lambda block, arm: next(t["runId"] for t in trials if t["block"] == block and t["armLetter"] == arm)
    planted = {pick("V2-r1", "A"): {"x4"}, pick("V3-r1", "C"): {"x2"}, pick("V4-r1", "D"): {"nocost"}, pick("V5-r1", "B"): {"notokens"}}
    with tempfile.TemporaryDirectory() as tmp:
        obs = os.path.join(tmp, "obs"); os.makedirs(obs)
        for t in trials:
            json.dump(synthetic(t, planted), open(os.path.join(obs, t["runId"] + ".json"), "w"))
        json.dump(synthetic({**trials[0], "runId": "REL-001-R3-SMOKE-x", "label": "smoke"}, {}), open(os.path.join(obs, "smoke.json"), "w"))
        a, b = run(obs, os.path.join(tmp, "a.json")), run(obs, os.path.join(tmp, "b.json"))
        r = json.loads(a)
        smoke = json.loads(run(obs, os.path.join(tmp, "c.json"), "--include-smoke"))
    h1, h2, h3 = r["primary"]["H1"], r["secondary"]["H2"], r["secondary"]["H3"]
    tok = r["sensitivity"]["tokensTotal"]
    checks = [
        ("T1 byte-identical output", a == b),
        ("T2 X4: D vs A drops the X4 block and the no-cost block (22 of 24); X4 run counted as excluded", h1["blocks"] == 22 and r["arms"]["A"]["excludedX4"] == 1),
        ("T2 X2: D vs C drops the X2 block and the no-cost block (22)", h2["blocks"] == 22),
        ("T3 X3: no-cost block leaves cost but stays in tokens (D vs A tokens: 23)", tok["D vs A"]["blocks"] == 23),
        ("T3 X3: no-token run leaves only token comparisons (B vs A cost 23, tokens 22)", h3["blocks"] == 23 and tok["B vs A"]["blocks"] == 22),
        ("T4 planted D cost reduction recovered, interval excludes 0", h1["ci95"] is not None and h1["ci95"][1] < 0 and h1["decision"] == "first arm lower"),
        ("T5 smoke ignored by default, included with --include-smoke", r["input"]["analysed"] == 96 and smoke["input"]["analysed"] == 96
                                                                         and smoke["input"]["duplicateBlockArm"] != []),
    ]
    for name, ok in checks:
        print(("ok       " if ok else "MISMATCH ") + name)
    print("H1 (synthetic):", json.dumps({k: h1[k] for k in ("estimate", "ci95", "blocks", "decision")}))
    print("SELFTEST:", "PASS" if all(ok for _, ok in checks) else "FAIL")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
