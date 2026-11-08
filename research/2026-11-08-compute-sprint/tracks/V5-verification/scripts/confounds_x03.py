"""Arm-assignment and confound checks for SPR-X-03. Usage: python3 -I -B scripts/confounds_x03.py raw/v5-scores.json OUT.json

Reads workspace files as text only (never imports them). Fixture templates are hashed (SPEC/errors/DECISIONS/NOTES/CHANGELOG
and the D2-03 skeleton); scorer files are not opened.
"""
import ast
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

T = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment"
WS = "/home/user/sprint-scratch/V5/ws"
ORIG = {"D2b": "/home/user/sprint-scratch/D2b/ws", "D2c": "/home/user/sprint-scratch/D2c/ws"}
FIXTURE = {
    "D2b": {f: f"{T}/spr-d2-02/fixture/{f}" for f in ("SPEC.md", "errors.py")},
    "D2c": {f: f"{T}/spr-d2-03/fixture/workspace/{f}" for f in ("SPEC.md", "errors.py", "DECISIONS.md", "NOTES.md", "CHANGELOG.md")},
}
SKELETON = f"{T}/spr-d2-03/fixture/workspace/pricing.py"
PREREG_UTC = datetime(2026, 11, 8, 20, 59, 50, tzinfo=timezone.utc)   # commit 90f85c1
EST = timezone(timedelta(hours=-5))
SUSPECT = re.compile(r"open\(|\bos\.|\bsys\.|subprocess|importlib|__import__|\bexec\(|\beval\(|/home/|/tmp|\.\./|socket|urllib|pathlib|shutil")


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def imports_of(src):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"<syntax error {e}>"]
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods.add((n.module or "").split(".")[0] or ".")
    return sorted(mods)


def arm_from_files(files):
    q, e = "QUESTIONS.md" in files, "EVIDENCE.md" in files
    return "K" if (q and e) else ("C" if not (q or e) else "ambiguous")


def tree_digest(d):
    out = {}
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            p = os.path.join(root, f)
            out[os.path.relpath(p, d)] = sha(p)
    return out


def run_check(r, score):
    rid, fx = r["runId"], r["fixture"]
    ws, orig = os.path.join(WS, rid), os.path.join(ORIG[fx], rid)
    files = sorted(f for f in os.listdir(ws) if f != "__pycache__")
    pyfiles = [f for f in files if f.endswith(".py") and f != "errors.py"]
    srcs = {f: open(os.path.join(ws, f)).read() for f in pyfiles}
    mt = {f: os.stat(os.path.join(orig, f)).st_mtime for f in files}
    pricing_mt = datetime.fromtimestamp(mt["pricing.py"], timezone.utc)
    return {
        "run": rid, "fixture": fx, "assigned_arm": r["arm"], "batch": r["batch"],
        "files": files, "arm_from_workspace": arm_from_files(files),
        "fixture_files_intact": {f: sha(os.path.join(ws, f)) == sha(p) for f, p in FIXTURE[fx].items()},
        "pricing_is_skeleton": fx == "D2c" and sha(os.path.join(ws, "pricing.py")) == sha(SKELETON),
        "unexpected_files": [f for f in files if f not in set(FIXTURE[fx]) | {"pricing.py", "test_pricing.py", "QUESTIONS.md", "EVIDENCE.md"}],
        "imports": {f: imports_of(s) for f, s in srcs.items()},
        "suspect_lines": [f"{f}:{i}: {ln.strip()[:140]}" for f, s in srcs.items()
                          for i, ln in enumerate(s.splitlines(), 1) if SUSPECT.search(ln)],
        "pricing_mtime_est": pricing_mt.astimezone(EST).isoformat(timespec="seconds"),
        "last_write_est": datetime.fromtimestamp(max(mt.values()), timezone.utc).astimezone(EST).isoformat(timespec="seconds"),
        "after_prereg": pricing_mt > PREREG_UTC,
        "copy_equals_original": tree_digest(ws) == tree_digest(orig),
        "violations": score["violations"],
    }


def summarize(checks):
    allowed = {"datetime", "errors", "pricing", "unittest", "copy", "decimal", "math", "fractions", "typing", "itertools", "functools", "numbers"}
    batches = {b: {arm: [c["violations"] for c in checks if c["batch"] == b and c["assigned_arm"] == arm] for arm in ("C", "K")}
               for b in sorted({c["batch"] for c in checks})}
    return {
        "arm_mismatches": [c["run"] for c in checks if c["arm_from_workspace"] != c["assigned_arm"]],
        "QUESTIONS_or_EVIDENCE_in_C": [c["run"] for c in checks if c["assigned_arm"] == "C" and ({"QUESTIONS.md", "EVIDENCE.md"} & set(c["files"]))],
        "K_missing_QUESTIONS_or_EVIDENCE": [c["run"] for c in checks if c["assigned_arm"] == "K" and not {"QUESTIONS.md", "EVIDENCE.md"} <= set(c["files"])],
        "batch_composition": {b: {"C": sum(1 for c in checks if c["batch"] == b and c["assigned_arm"] == "C"),
                                  "K": sum(1 for c in checks if c["batch"] == b and c["assigned_arm"] == "K")} for b in batches},
        "batch_violations": batches,
        "batch_pricing_mtimes_est": {b: sorted(c["pricing_mtime_est"][11:19] for c in checks if c["batch"] == b) for b in batches},
        "all_after_prereg": all(c["after_prereg"] for c in checks),
        "fixture_file_modifications": [(c["run"], f) for c in checks for f, ok in c["fixture_files_intact"].items() if not ok],
        "pricing_left_as_skeleton": [c["run"] for c in checks if c["pricing_is_skeleton"]],
        "unexpected_files": [(c["run"], c["unexpected_files"]) for c in checks if c["unexpected_files"]],
        "non_allowed_imports": [(c["run"], f, [m for m in ms if m not in allowed]) for c in checks for f, ms in c["imports"].items()
                                if [m for m in ms if m not in allowed]],
        "suspect_lines": [(c["run"], c["suspect_lines"]) for c in checks if c["suspect_lines"]],
        "copies_differ_from_original": [c["run"] for c in checks if not c["copy_equals_original"]],
    }


if __name__ == "__main__":
    scores = json.load(open(sys.argv[1]))
    asg = json.load(open(f"{T}/spr-x-03/assignment.json"))["runs"]
    checks = [run_check(r, scores[r["runId"]]) for r in asg]
    res = dict(summarize(checks), per_run=checks)
    json.dump(res, open(sys.argv[2], "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "per_run"}, indent=1))
