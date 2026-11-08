"""Run C1..C4 on the preregistered packages, read straight from git objects (read-only), and write raw/*.json.

usage: python3 -m semcheck.run [--repo PATH] [--out DIR]
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from . import carrier, model, partition, rate, slices

REPO = "/home/user/sprint-scratch/B2/indy-init-full"
PACKAGES = (
    # label, role, commit, package dir, slice manifest (optional)
    ("R8-frozen", "target", "1cb27ec", "requirements-compiled/v4.1.1", None),
    ("R8-corrected=R9-frozen", "control", "bc3c381", "requirements-compiled/v4.1.2", None),
    ("R10-frozen", "control", "89f5840", "requirements-compiled/v4.1.5",
     "docs/rehearsal-010-readiness/slice-execution-manifest.json"),
    ("Causa-frozen", "control/C4-target", "dae2347", "requirements-compiled/v4.1.6",
     "docs/competition-readiness/slice-execution-manifest.json"),
)
INVARIANTS = "requirements-compiled/v4/invariants.json"
C1_VARIANTS = (("loop", False), ("loop", True), ("cycle", False), ("cycle", True))


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


def show(repo, rev, path):
    return git(repo, "show", "%s:%s" % (rev, path))


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def run_package(repo, label, role, rev, pkg, manifest):
    full = git(repo, "rev-parse", rev).strip()
    when = git(repo, "show", "-s", "--format=%cI", rev).strip()
    inputs = {}
    t0 = time.perf_counter()
    mtext = show(repo, rev, pkg + "/state-machine-contracts.json")
    itext = show(repo, rev, INVARIANTS)
    inputs[pkg + "/state-machine-contracts.json"] = digest(mtext)
    inputs[INVARIANTS] = digest(itext)
    machines = model.load_machines(json.loads(mtext))
    inv_doc = json.loads(itext)
    bounds = model.load_bounds(inv_doc)
    fs_files = sorted(p for p in git(repo, "ls-tree", "-r", "--name-only", rev, pkg + "/contracts").split()
                      if p.endswith(".fs") and "/negative/" not in p)
    defs = ()
    for p in fs_files:
        src = show(repo, rev, p)
        inputs[p] = digest(src)
        defs += carrier.parse_types(src, p.rsplit("/", 1)[-1])
    t_load = time.perf_counter() - t0

    res, timing = {}, {"loadSeconds": round(t_load, 4)}
    for v in C1_VARIANTS:
        t = time.perf_counter()
        a = rate.check(machines, bounds, v)
        name = "C1-%s%s" % (v[0], "-deleg" if v[1] else "")
        res[name] = a
        timing[name] = round(time.perf_counter() - t, 4)
    for word, name in (("command", "C2"), ("payload", "C2b")):
        t = time.perf_counter()
        a, ex = carrier.check(defs, word, name)
        res[name] = a
        res[name + "-examined"] = ex
        timing[name] = round(time.perf_counter() - t, 4)
    t = time.perf_counter()
    res["C3"] = partition.check(machines)
    timing["C3"] = round(time.perf_counter() - t, 4)
    if manifest:
        stext = show(repo, rev, manifest)
        inputs[manifest] = digest(stext)
        sl = json.loads(stext)["slices"]
        for b in (False, True):
            t = time.perf_counter()
            r = slices.check(sl, inv_doc["invariants"], b)
            res[r["check"]] = r
            timing[r["check"]] = round(time.perf_counter() - t, 4)
    return {"label": label, "role": role, "repo": repo, "rev": full, "committerTime": when, "package": pkg,
            "inputsSha256": inputs,
            "parsed": {"machines": {m.id: len(m.transitions) for m in machines},
                       "bounds": [b._asdict() for b in bounds], "fsTypes": len(defs)},
            "results": res, "timing": timing}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "raw"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t = time.perf_counter()
    for label, role, rev, pkg, manifest in PACKAGES:
        r = run_package(a.repo, label, role, rev, pkg, manifest)
        (out / ("%s.json" % label.split("=")[0])).write_text(json.dumps(r, indent=1) + "\n")
        counts = {k: (len(v) if isinstance(v, list) else len(v["cycles"])) for k, v in r["results"].items()
                  if not k.endswith("-examined")}
        print(label, rev, counts)
    print("total wall seconds %.3f" % (time.perf_counter() - t))


if __name__ == "__main__":
    main()
