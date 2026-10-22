#!/usr/bin/env python3
"""ARCH-001 analysis self-test on SYNTHETIC observations (never real data; nothing here is a result).

usage: python3 -I selftest.py
Builds 96 synthetic arch001.observation/1 documents from harness/order.json (24 blocks x 4 arms) with a fixed
formula, plus 8 pilot and 2 smoke documents, and planted cases: one X4 run (A), one X-integrity run (B), one X5
timeout (D), one run whose S2 commit the verifier could not evaluate (A). Planted effects: arm D costs 30% less per
trial and has more accepted requirements than A; arm B has fewer violations than A; C and D have equal rework.
Checks:
  T1  analyze.py output is byte-identical across two runs (determinism);
  T2  X4 and X-integrity runs are excluded (listed, and their blocks leave the contrasts of their arm);
  T3  the X5 run stays in the main analysis and leaves only the no-X5 sensitivity;
  T4  a missing metric (violations not evaluable) removes the run from H1a only, not from H1b;
  T5  planted effects are recovered: primary D/A Supported, H1a Supported; H4 (no effect) is not Supported;
  T6  pilot and smoke observations are ignored by the confirmatory analysis; --label pilot reads only the pilot.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = json.load(open(os.path.join(HERE, "..", "harness", "order.json")))
PILOT = json.load(open(os.path.join(HERE, "..", "harness", "pilot-order.json")))
CROSS = {f"T{i}": 1 + (i % 4) for i in range(1, 9)}


def synthetic(t, planted, label):
    arm, seq = t["arm"], t["seq"]
    jitter = 1 + 0.1 * (((seq * 7) % 5) - 2) / 2
    cost = round(2.0 * jitter * (0.7 if arm == "D" else 1.0), 6)
    accepted = 2 if arm == "D" else (1 if seq % 3 else 2)
    viol = {"A": 4, "B": 1, "C": 1, "D": 0}[arm] + (seq % 2)
    p = planted.get(t["runId"], set())
    reasons = (["X4 contamination"] if "x4" in p else []) + (["X-integrity tamper"] if "xi" in p else [])
    reqs = [{"id": f"R{k}", "accepted": k <= accepted, "functionalPass": True, "archAccept": k <= accepted} for k in (1, 2)]
    return {"schema": "arch001.observation/1", "runId": t["runId"], "label": label, "arm": arm, "task": t["task"],
            "replicate": t["replicate"], "block": t["block"], "taskMeta": {"crossTierCount": CROSS[t["task"]]},
            "excluded": bool(reasons), "exclusionReasons": reasons,
            "exclusions": {"x5": {"timedOut": "x5" in p}}, "cost": {"totalUsd": cost, "agrees": True},
            "requirements": reqs, "completed": True,
            "architecture": {"p1": {"evaluable": True, "detSeverityWeighted": viol},
                             "p2": {"evaluable": "noarch" not in p, "detSeverityWeighted": None if "noarch" in p else viol}},
            "decisionFidelity": {"decisionTests": {"passed": 3 if arm in "CD" else 2, "total": 4}},
            "diff": {"phase2": {"all": {"rework": 20 + (seq % 3)}}},
            "firstPassCorrect": {"p1": True, "p2": accepted == 2}, "phases": {}}


def run(obs_dir, out, *flags):
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "analyze.py"), obs_dir, out, *flags], check=True, capture_output=True)
    return open(out, "rb").read()


def main():
    trials = ORDER["trials"]
    pick = lambda block, arm: next(t["runId"] for t in trials if t["block"] == block and t["arm"] == arm)
    blocks = ORDER["blocks"]
    planted = {pick(blocks[0], "A"): {"x4"}, pick(blocks[1], "B"): {"xi"}, pick(blocks[2], "D"): {"x5"}, pick(blocks[3], "A"): {"noarch"}}
    with tempfile.TemporaryDirectory() as tmp:
        obs = os.path.join(tmp, "obs")
        os.makedirs(obs)
        for t in trials:
            json.dump(synthetic(t, planted, "confirmatory"), open(os.path.join(obs, t["runId"] + ".json"), "w"))
        for t in PILOT["trials"]:
            json.dump(synthetic(t, {}, "pilot"), open(os.path.join(obs, t["runId"] + ".json"), "w"))
        for i, t in enumerate(trials[:2]):
            json.dump(synthetic({**t, "runId": f"ARCH-001-SMOKE-T0-r1-{t['arm']}-x{i}"}, {}, "smoke"), open(os.path.join(obs, f"smoke{i}.json"), "w"))
        a, b = run(obs, os.path.join(tmp, "a.json")), run(obs, os.path.join(tmp, "b.json"))
        r = json.loads(a)
        pr = json.loads(run(obs, os.path.join(tmp, "p.json"), "--label", "pilot"))
    p, s = r["primary"], r["secondary"]
    sens = r["sensitivity"]["withoutX5Timeouts"]
    checks = [
        ("T1 byte-identical output", a == b),
        ("T2 X4 + X-integrity runs listed as excluded (2)", len(r["excluded"]) == 2),
        ("T2 X4 (A) leaves D-A pairs: 23 of 24", p["pairs"] == 23),
        ("T2 X-integrity (B) and X4 (A) leave B-A rate pairs: 22", s["H1b"]["pairs"] == 22),
        ("T3 X5 (D) kept in main (D-C pairs 24), dropped in no-X5 sensitivity (23)", s["H5a"]["pairs"] == 24 and sens["secondary"]["H5a"]["pairs"] == 23),
        ("T4 missing violations metric: H1a pairs 21 (X4, X-int, not evaluable), H1b pairs 22", s["H1a"]["pairs"] == 21 and s["H1b"]["pairs"] == 22),
        ("T5 primary D/A Supported, estimate < 0", p["classification"] == "Supported" and p["estimate"] < 0),
        ("T5 H1a (B fewer violations) Supported", s["H1a"]["classification"] == "Supported"),
        ("T5 H4 (no planted effect) not Supported", s["H4"]["classification"] != "Supported"),
        ("T6 confirmatory analysed 96, pilot analysed 8", r["input"]["analysed"] == 96 and pr["input"]["analysed"] == 8),
    ]
    for name, ok in checks:
        print(("ok       " if ok else "MISMATCH ") + name)
    print("primary (synthetic):", json.dumps({k: p[k] for k in ("estimate", "ci95", "classification", "pairs")}))
    print("SELFTEST:", "PASS" if all(ok for _, ok in checks) else "FAIL")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
