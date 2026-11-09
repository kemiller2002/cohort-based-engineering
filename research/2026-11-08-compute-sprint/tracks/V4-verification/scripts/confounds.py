"""Arm-assignment check and confound checks. Usage: confounds.py V4SCORES OUT"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats  # noqa: E402

T = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment"
WS = "/home/user/sprint-scratch/V4/ws"
ORIG = {"D2b": "/home/user/sprint-scratch/D2b/ws", "D2c": "/home/user/sprint-scratch/D2c/ws"}
FIXTURE_SHA = {
    "D2b": {"errors.py": T + "/spr-d2-02/fixture/errors.py", "SPEC.md": T + "/spr-d2-02/fixture/SPEC.md"},
    "D2c": {f: T + "/spr-d2-03/fixture/workspace/" + f for f in ["errors.py", "SPEC.md", "DECISIONS.md", "NOTES.md", "CHANGELOG.md"]},
}
IMPORT_RE = re.compile(r"^\s*(?:from\s+(\S+)\s+import|import\s+(\S+))", re.M)
ALLOWED_MODULES = {"datetime", "errors", "pricing", "unittest", "copy", "decimal", "math", "fractions"}
SUSPECT_RE = re.compile(r"open\(|os\.|sys\.|subprocess|importlib|__import__|exec\(|eval\(|/home/|/tmp|\.\./")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def run_checks(rid, fx, arm):
    ws = os.path.join(WS, rid)
    files = sorted(os.listdir(ws))
    pyfiles = [f for f in files if f.endswith(".py") and f != "errors.py"]
    imports = sorted({(m.group(1) or m.group(2)).split(".")[0].rstrip(",")
                      for f in pyfiles for m in IMPORT_RE.finditer(open(os.path.join(ws, f)).read())})
    suspect = [f"{f}:{i}: {ln.strip()[:120]}" for f in pyfiles
               for i, ln in enumerate(open(os.path.join(ws, f)).read().splitlines(), 1) if SUSPECT_RE.search(ln)]
    return {
        "run": rid, "fixture": fx, "assigned_arm": arm,
        "has_QUESTIONS": "QUESTIONS.md" in files, "has_EVIDENCE": "EVIDENCE.md" in files,
        "arm_from_workspace": "G" if ("QUESTIONS.md" in files and "EVIDENCE.md" in files) else
                              ("M" if not ("QUESTIONS.md" in files or "EVIDENCE.md" in files) else "ambiguous"),
        "files": files,
        "fixture_files_intact": {f: sha(os.path.join(ws, f)) == sha(p) for f, p in FIXTURE_SHA[fx].items()},
        "imports": imports, "non_allowed_imports": [m for m in imports if m not in ALLOWED_MODULES],
        "suspect_lines": suspect,
        "orig_pricing_mtime_utc": os.stat(os.path.join(ORIG[fx], rid, "pricing.py")).st_mtime,
    }


def main(v4path, out):
    sc = json.load(open(v4path))
    asg = json.load(open(f"{T}/spr-x-02/assignment.json"))["runs"]
    checks = [dict(run_checks(r["runId"], r["fixture"], r["arm"]), batch=r["batch"],
                   violations=sc[r["runId"]]["violations"]) for r in asg]
    x01 = [run_checks(r, fx, "M") for r, fx in [("s01", "D2b"), ("s02", "D2b"), ("t01", "D2c"), ("t02", "D2c")]]
    batches = {b: {"G": [c["violations"] for c in checks if c["batch"] == b and c["assigned_arm"] == "G"],
                   "M": [c["violations"] for c in checks if c["batch"] == b and c["assigned_arm"] == "M"]}
               for b in range(1, 5)}
    bt = stats.stratified_perm_test([(v["G"], v["M"]) for v in batches.values()])
    result = {
        "arm_mismatches": [c["run"] for c in checks if c["arm_from_workspace"] != c["assigned_arm"]],
        "fixture_file_modifications": [(c["run"], f) for c in checks + x01 for f, ok in c["fixture_files_intact"].items() if not ok],
        "non_allowed_imports": [(c["run"], c["non_allowed_imports"]) for c in checks + x01 if c["non_allowed_imports"]],
        "suspect_lines": [(c["run"], c["suspect_lines"]) for c in checks + x01 if c["suspect_lines"]],
        "batches": batches,
        "batch_stratified_test": {"stat": float(bt["stat"]), "p": float(bt["p"]), "p_exact": str(bt["p"]), "N": bt["N"]},
        "per_run": checks, "x01": x01,
    }
    json.dump(result, open(out, "w"), indent=1)
    return result


if __name__ == "__main__":
    r = main(sys.argv[1], sys.argv[2])
    print(json.dumps({k: v for k, v in r.items() if k not in ("per_run", "x01")}, indent=1))
