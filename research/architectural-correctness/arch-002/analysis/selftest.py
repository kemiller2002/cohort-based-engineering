#!/usr/bin/env python3
"""ARCH-002 analysis self-test on SYNTHETIC observations (never real data; nothing here is a result).

usage: python3 -I selftest.py
Builds a synthetic confirmatory order with harness/randomize.py's own functions (suite lending-brownfield T1-T6 and
summa T1-T3, 2 models, 2 replicates: 36 blocks x 4 arms = 144 trials), plus pilot and calibration documents, then
arch002.observation/1 documents from a fixed formula with planted cases: one X4 run, one X-integrity run, one X5
timeout, one run whose S2 commit the verifier could not evaluate. Planted effects: D costs 30% less and is always
accepted; NEW violations at S2 are opus A 3, B 1, C 1, D 0 and sonnet 1 in every arm (so D-A differs by model: H8);
C and D have equal rework. Brownfield deltas that must NOT move any violation metric: pre-existing findings grow with
the arm (A 0 ... D 60) and every trial "fixes" a different number of start-commit findings; the all-findings totals
(detSeverityWeighted) are therefore dominated by pre-existing ones.
Checks:
  T1  analyze.py output is byte-identical across two runs (determinism);
  T2  X4 and X-integrity runs are excluded and leave the contrasts of their arm;
  T3  the X5 run stays in the main analysis and leaves only the no-X5 sensitivity;
  T4  a missing metric (S2 not evaluable) removes the run from H1a only, not from H1b;
  T5  planted effects are recovered: primary D/A Supported; H1a Supported; H4 (no effect) not Supported;
      H8 Supported with estimate < 0 (opus effect larger); per-model D-A: opus < 0, sonnet ~ 0;
  T6  brownfield: per-arm new-violation means equal the planted NEW values (not the pre-existing-dominated totals);
  T7  pilot, calibration and smoke observations are ignored by the confirmatory analysis; --label pilot reads the pilot;
  T8  lifecycle model: remediation lines = new violations x table lines; arm A's remediation exceeds arm D's.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location("randomize", os.path.join(HERE, "..", "harness", "randomize.py"))
RZ = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RZ)

SUITE = [("lending-brownfield", [f"T{i}" for i in range(1, 7)]), ("summa", ["T1", "T2", "T3"])]
CROSS = lambda fixture, task: 1 + (int(task[1:]) % 4) + (1 if fixture == "summa" else 0)
NEW = {"opus": {"A": 3, "B": 1, "C": 1, "D": 0}, "sonnet": {"A": 1, "B": 1, "C": 1, "D": 1}}
PRE = {"A": 0, "B": 20, "C": 40, "D": 60}
TABLE = {"schema": "arch002.remediation-lines/1", "default": {"rules": {"ARC-SYM-02": 12}, "*": 10},
         "fixtures": {"summa": {"rules": {"ARC-SYM-02": 30}}}}


def synthetic(t, planted, label):
    arm, seq, model = t["arm"], t["seq"], t["model"]
    jitter = 1 + 0.1 * (((seq * 7) % 5) - 2) / 2
    cost = round(2.0 * jitter * (0.7 if arm == "D" else 1.0) * (0.5 if model == "sonnet" else 1.0), 6)
    new = NEW[model][arm] + (seq % 2 if NEW[model][arm] else 0)   # new findings, severity 2 each
    accepted = 2 if new == 0 else 1
    p = planted.get(t["runId"], set())
    reasons = (["X4 contamination"] if "x4" in p else []) + (["X-integrity tamper"] if "xi" in p else [])
    reqs = [{"id": f"R{k}", "accepted": k <= accepted, "functionalPass": True, "archAccept": k <= accepted} for k in (1, 2)]
    def arch(evaluable):
        pre, fixed = PRE[arm], seq % 4
        if not evaluable:
            return {"evaluable": False}
        return {"evaluable": True, "detNew": new, "detNewSev2plus": new, "detNewSeverityWeighted": 2 * new,
                "newByRule": {"ARC-SYM-02": new} if new else {}, "detPreexisting": pre, "detFixed": fixed,
                "det": new + pre, "detSeverityWeighted": 2 * new + 3 * pre}
    rework = 20 + (seq % 3)
    return {"schema": "arch002.observation/1", "runId": t["runId"], "label": label, "fixture": t["fixture"], "arm": arm,
            "task": t["task"], "taskKey": t["taskKey"], "modelKey": model, "replicate": t["replicate"], "block": t["block"],
            "taskMeta": {"crossTierCount": CROSS(t["fixture"], t["task"])},
            "excluded": bool(reasons), "exclusionReasons": reasons,
            "exclusions": {"x5": {"timedOut": "x5" in p}},
            "cost": {"totalUsd": cost, "byPhase": {"1": round(cost * 0.6, 6), "2": round(cost * 0.4, 6)}, "agrees": True},
            "requirements": reqs, "completed": True,
            "architecture": {"p1": arch(True), "p2": arch("noarch" not in p)},
            "decisionFidelity": {"decisionTests": {"passed": 3 if arm in "CD" else 2, "total": 4}},
            "diff": {"phase2": {"all": {"rework": rework}}},
            "firstPassCorrect": {"p1": True, "p2": accepted == 2}, "phases": {}}


def run(obs_dir, out, *flags):
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "analyze.py"), obs_dir, out, *flags], check=True, capture_output=True)
    return open(out, "rb").read()


def main():
    o = {"seed": RZ.DEFAULT_SEED, "suite": SUITE, "replicates": 2, "pilot": [(f, ts[:1]) for f, ts in SUITE]}
    docs = RZ.documents(o)
    order, pilot, cal = docs["order.json"], docs["pilot-order.json"], docs["calibration-order.json"]
    trials, blocks = order["trials"], order["blocks"]
    pick = lambda block, arm: next(t["runId"] for t in trials if t["block"] == block and t["arm"] == arm)
    planted = {pick(blocks[0], "A"): {"x4"}, pick(blocks[1], "B"): {"xi"}, pick(blocks[2], "D"): {"x5"}, pick(blocks[3], "A"): {"noarch"}}
    nb = len(blocks)
    with tempfile.TemporaryDirectory() as tmp:
        obs = os.path.join(tmp, "obs")
        os.makedirs(obs)
        for t in trials:
            json.dump(synthetic(t, planted, "confirmatory"), open(os.path.join(obs, t["runId"] + ".json"), "w"))
        for t in pilot["trials"]:
            json.dump(synthetic(t, {}, "pilot"), open(os.path.join(obs, t["runId"] + ".json"), "w"))
        for t in cal["trials"]:
            json.dump(synthetic(t, {}, "calibration"), open(os.path.join(obs, t["runId"] + ".json"), "w"))
        for i, t in enumerate(trials[:2]):
            sid = f"ARCH-002-SMOKE-lending-smoke-T0-opus-r1-{t['arm']}-x{i}"
            json.dump(synthetic({**t, "runId": sid}, {}, "smoke"), open(os.path.join(obs, f"smoke{i}.json"), "w"))
        table = os.path.join(tmp, "remediation.json")
        json.dump(TABLE, open(table, "w"))
        a = run(obs, os.path.join(tmp, "a.json"), "--remediation", table)
        b = run(obs, os.path.join(tmp, "b.json"), "--remediation", table)
        r = json.loads(a)
        pr = json.loads(run(obs, os.path.join(tmp, "p.json"), "--label", "pilot", "--remediation", table))
    p, s = r["primary"], r["secondary"]
    sens = r["sensitivity"]["withoutX5Timeouts"]
    included = [t for t in trials if not (planted.get(t["runId"], set()) & {"x4", "xi"})]
    def planted_mean(arm, model):
        xs = [2 * (NEW[model][arm] + (t["seq"] % 2 if NEW[model][arm] else 0)) for t in included
              if t["arm"] == arm and t["model"] == model and "noarch" not in planted.get(t["runId"], set())]
        return round(sum(xs) / len(xs), 6)
    bm = r["byModel"]
    lc = r["lifecycle"]["byArm"]
    def lines(arm):
        return sum((NEW[t["model"]][arm] + (t["seq"] % 2 if NEW[t["model"]][arm] else 0)) * (30 if t["fixture"] == "summa" else 12)
                   for t in included if t["arm"] == arm and "noarch" not in planted.get(t["runId"], set()))
    a_lines = lines("A")
    checks = [
        ("T1 byte-identical output", a == b),
        ("T2 X4 + X-integrity runs listed as excluded (2)", len(r["excluded"]) == 2),
        (f"T2 X4 (A) leaves D-A pairs: {nb - 1} of {nb}", p["pairs"] == nb - 1),
        (f"T2 X-integrity (B) and X4 (A) leave B-A rate pairs: {nb - 2}", s["H1b"]["pairs"] == nb - 2),
        (f"T3 X5 (D) kept in main (D-C pairs {nb}), dropped in no-X5 sensitivity ({nb - 1})",
         s["H5a"]["pairs"] == nb and sens["secondary"]["H5a"]["pairs"] == nb - 1),
        (f"T4 missing violations metric: H1a pairs {nb - 3}, H1b pairs {nb - 2}", s["H1a"]["pairs"] == nb - 3 and s["H1b"]["pairs"] == nb - 2),
        ("T5 primary D/A Supported, estimate < 0", p["classification"] == "Supported" and p["estimate"] < 0),
        ("T5 H1a (B fewer new violations, pooled) Supported", s["H1a"]["classification"] == "Supported"),
        ("T5 H4 (no planted effect) not Supported", s["H4"]["classification"] != "Supported"),
        ("T5 H8 (D-A differs by model) Supported, estimate < 0", s["H8"]["classification"] == "Supported" and s["H8"]["estimate"] < 0),
        ("T5 H3 per model: opus D-C < -1, |sonnet D-C| < 0.5", s["H3"]["byModel"]["opus"]["estimate"] < -1 and abs(s["H3"]["byModel"]["sonnet"]["estimate"]) < 0.5),
        ("T6 new-violation means per arm and model equal the planted NEW values",
         all(bm[m][x]["newViolationsPerTrialS2"] == planted_mean(x, m) for m in ("opus", "sonnet") for x in "ABCD")),
        ("T6 pre-existing/fixed findings do not enter: D opus mean is 0 despite 60 pre-existing", bm["opus"]["D"]["newViolationsPerTrialS2"] == 0),
        ("T7 confirmatory analysed 144 (pilot, calibration, smoke ignored); pilot analysed 16",
         r["input"]["analysed"] == len(trials) == 144 and pr["input"]["analysed"] == len(pilot["trials"]) == 16),
        ("T8 lifecycle: remediation lines = new x table lines (A and D); A's remediation exceeds D's",
         lc["A"]["remediationLines"] == a_lines and lc["D"]["remediationLines"] == lines("D") and lc["A"]["remediationUsd"] > lc["D"]["remediationUsd"]),
    ]
    for name, ok in checks:
        print(("ok       " if ok else "MISMATCH ") + name)
    print("primary (synthetic):", json.dumps({k: p[k] for k in ("estimate", "ci95", "classification", "pairs")}))
    print("H8 (synthetic):", json.dumps({k: s["H8"][k] for k in ("estimate", "ci95", "pHolm", "classification")}))
    print("lifecycle (synthetic):", json.dumps({x: {k: lc[x][k] for k in ("remediationLines", "remediationUsd", "withLifecycle")} for x in "AD"}), "expected A lines", a_lines)
    print("SELFTEST:", "PASS" if all(ok for _, ok in checks) else "FAIL")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
