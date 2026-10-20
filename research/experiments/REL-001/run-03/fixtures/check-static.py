#!/usr/bin/env python3
"""REL-001 run-03 static fixture check: everything that can be proved without the .NET SDK.

usage: python3 -I check-static.py FIXTURE_DIR [RUN02_FIXTURE_DIR]

Checks (each prints one line, ok or MISMATCH; exit 0 only when all hold):
  S1  every task has requirement.md, visible tests, oracle and task.json, and task.json's digests match;
  S2  every visible and oracle test name starts with one of the task's requirement IDs, and every requirement
      has at least one visible and one oracle test (the scoring unit is the requirement);
  S3  isolation: nothing given to an agent (repo/, tasks/*/requirement.md, visible tests) names the oracle,
      the reference solutions or task.json;
  S4  independence from run-02: no run-03 oracle test name, oracle module or task id matches run-02's
      (only when RUN02_FIXTURE_DIR is given);
  S5  make-references.py and make-contracts.py reproduce the committed reference/ tree and contracts;
  S6  every wrong variant differs from its reference; V7 has exactly the two forced variants and no reference;
  S7  F# hygiene: no tabs, balanced (), [] and {} outside strings and comments, a module line per test file;
  S8  new modules named by the prose are added to Ledger.fsproj in the reference.
It also prints the fixture-tree and oracle digests, computed exactly as run-02's check.sh does
(sha256 of `sha256sum` lines over the sorted file list).
"""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

FIX = pathlib.Path(sys.argv[1]).resolve()
RUN02 = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
TASKS = [f"V{i}" for i in range(1, 9)]
TEST_NAME = re.compile(r"^let ``([^`]+)`` \(\) =", re.MULTILINE)


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def tree_digest(root, dirs):
    files = sorted((str(p.relative_to(root)) for d in dirs for p in (root / d).rglob("*") if p.is_file()), key=lambda s: s.encode())
    return hashlib.sha256("".join(f"{sha(root / f)}  {f}\n" for f in files).encode()).hexdigest()


def tests_of(path):
    return TEST_NAME.findall(pathlib.Path(path).read_text())


def strip_fsharp(text):
    """Remove string literals, char literals, // comments and (* *) comments, keeping brackets that matter."""
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"\(\*.*?\*\)", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return re.sub(r"``[^`]*``", "``x``", text)


def balanced(text):
    pairs = {")": "(", "]": "[", "}": "{"}
    def step(stack, ch):
        if stack is None:
            return None
        if ch in "([{":
            return stack + [ch]
        if ch in pairs:
            return stack[:-1] if stack and stack[-1] == pairs[ch] else None
        return stack
    from functools import reduce
    return reduce(step, strip_fsharp(text), []) == []


def check(label, ok, detail=""):
    print(f"{'ok      ' if ok else 'MISMATCH'} {label}{(' — ' + detail) if detail else ''}")
    return bool(ok)


def task_checks(t):
    tdir = FIX / "tasks" / t
    tj = json.loads((tdir / "task.json").read_text())
    files = tj["files"]
    reqs = tj["requirementIds"]
    visible, oracle = tests_of(tdir / f"{t}AcceptanceTests.fs"), tests_of(FIX / "oracle" / t / "OracleTests.fs")
    def tagged(names):
        return all(any(n.startswith(r + " ") for r in reqs) for n in names)
    def covered(names):
        return all(any(n.startswith(r + " ") for n in names) for r in reqs)
    return [
        check(f"S1 {t} files and digests",
              files["requirement"]["sha256"] == sha(tdir / "requirement.md")
              and files["visibleTests"]["sha256"] == sha(tdir / f"{t}AcceptanceTests.fs")
              and files["oracleSha256"] == sha(FIX / "oracle" / t / "OracleTests.fs")
              and tj["contract"]["sha256"] == sha(tdir / "contract.json")),
        check(f"S2 {t} tests tagged and every requirement covered",
              tagged(visible) and tagged(oracle) and covered(visible) and covered(oracle),
              f"{len(reqs)} requirement(s), {len(visible)} visible / {len(oracle)} oracle tests"),
    ]


def isolation():
    given = [p for p in (FIX / "repo").rglob("*") if p.is_file()] + \
            [FIX / "tasks" / t / n for t in TASKS for n in ("requirement.md", f"{t}AcceptanceTests.fs")]
    pattern = re.compile(r"OracleV\d|oracle/|reference/|task\.json|run-03/fixtures|Oracle\.fsproj")
    hits = [str(p.relative_to(FIX)) for p in given if pattern.search(p.read_text(errors="replace"))]
    return [check("S3 nothing given to an agent names the oracle, references or task.json", not hits, ", ".join(hits))]


def independence():
    if RUN02 is None:
        return [check("S4 independence from run-02 (skipped: no RUN02_FIXTURE_DIR)", True)]
    def names(root, glob):
        return {n.split(" ", 1)[1] for p in root.glob(glob) for n in tests_of(p)}
    mine, theirs = names(FIX, "oracle/V*/OracleTests.fs"), names(RUN02, "oracle/U*/OracleTests.fs")
    shared = sorted(mine & theirs)
    ids = {p.name for p in (RUN02 / "tasks").iterdir()} & set(TASKS)
    return [check("S4 no oracle test name or task id shared with run-02", not shared and not ids,
                  f"{len(mine)} run-03 vs {len(theirs)} run-02 oracle tests; shared: {shared or 'none'}")]


def reproducible():
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp) / "fx"
        shutil.copytree(FIX, t, ignore=shutil.ignore_patterns("reference"))
        r1 = subprocess.run([sys.executable, "-I", str(FIX / "make-references.py"), str(t)], capture_output=True, text=True)
        r2 = subprocess.run([sys.executable, "-I", str(FIX / "make-contracts.py"), str(t)], capture_output=True, text=True)
        same_refs = r1.returncode == 0 and tree_digest(t, ["reference"]) == tree_digest(FIX, ["reference"])
        same_contracts = r2.returncode == 0 and all(sha(t / "tasks" / x / "contract.json") == sha(FIX / "tasks" / x / "contract.json") for x in TASKS)
        # task.json is reproduced too, except the Ordo verdict when the committed one was made with a binary
        same_tasks = all(json.loads((t / "tasks" / x / "task.json").read_text())["files"] == json.loads((FIX / "tasks" / x / "task.json").read_text())["files"]
                         for x in TASKS)
    return [check("S5 make-references.py reproduces reference/", same_refs, r1.stderr.strip()[-200:]),
            check("S5 make-contracts.py reproduces contract.json and task.json files", same_contracts and same_tasks, r2.stderr.strip()[-200:])]


def variants():
    def differs(t, v):
        vdir = FIX / "reference" / f"{t}-{v}"
        return all(not (FIX / "reference" / t / p.relative_to(vdir)).exists() or sha(p) != sha(FIX / "reference" / t / p.relative_to(vdir))
                   for p in vdir.rglob("*") if p.is_file())
    pairs = [(t, v) for t in TASKS for v in json.loads((FIX / "tasks" / t / "task.json").read_text())["files"]["wrongVariants"]]
    v7 = sorted(p.name for p in (FIX / "reference" / "V7").iterdir())
    return [check("S6 every wrong variant differs from its reference", all(differs(t, v) for t, v in pairs),
                  f"{len(pairs)} variants: " + ", ".join(f"{t}-{v}" for t, v in pairs)),
            check("S6 V7 has only the two forced variants", v7 == ["forced-noop", "forced-refuse"], ", ".join(v7))]


def hygiene():
    fs = sorted(p for d in ("repo", "tasks", "oracle", "reference") for p in (FIX / d).rglob("*.fs"))
    bad = [str(p.relative_to(FIX)) for p in fs if "\t" in p.read_text() or not balanced(p.read_text())]
    tests = [p for p in fs if p.name.endswith("Tests.fs")]
    nomod = [str(p.relative_to(FIX)) for p in tests if not re.match(r"^module \w+", p.read_text())]
    return [check("S7 F# hygiene (tabs, bracket balance, module line)", not bad and not nomod, ", ".join(bad + nomod) or f"{len(fs)} files")]


def projects():
    def has(t, module):
        proj = FIX / "reference" / t / "src/Ledger/Ledger.fsproj"
        text = proj.read_text() if proj.exists() else ""
        order = re.findall(r'Include="([^"]+)"', text)
        return module in order and order.index(module) == order.index("Ledger.fs") + 1 and (FIX / "reference" / t / "src/Ledger" / module).exists()
    return [check("S8 new modules are in Ledger.fsproj right after Ledger.fs", has("V5", "StandingOrders.fs") and has("V6", "Reconciliation.fs"))]


def main():
    print(f"fixture tree digest: {tree_digest(FIX, ['repo', 'tasks', 'oracle', 'reference'])}")
    print(f"oracle digest:       {tree_digest(FIX, ['oracle'])}")
    results = [r for t in TASKS for r in task_checks(t)] + isolation() + independence() + reproducible() + variants() + hygiene() + projects()
    print(f"STATIC RESULT: {'PASS' if all(results) else 'FAIL'} ({sum(results)}/{len(results)} checks)")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
