"""Run `percepta spec-preflight` on each SPR-B4-01 package and record raw outputs.

Usage: python3 -I run_preflight.py --exe PATH --version-label LABEL --out RAWDIR [--runs 5] [--env K=V ...]
Inputs are extracted read-only from the Indy-init clone with `git show` into /home/user/sprint-scratch/B4/inputs.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

CLONE = "/home/user/sprint-scratch/B2/indy-init-full"
INPUTS = "/home/user/sprint-scratch/B4/inputs"

PACKAGES = (
    ("R8-frozen", "1cb27ec", "v4.1.1", "target"),
    ("R8-corrected", "bc3c381", "v4.1.2", "control"),
    ("R10-frozen", "89f5840", "v4.1.5", "control"),
    ("Causa-frozen", "dae2347", "v4.1.6", "control"),
)


def sources(pkg):
    return {
        "machines": f"requirements-compiled/{pkg}/state-machine-contracts.json",
        "invariants": "requirements-compiled/v4/invariants.json",
        "interfaces": f"requirements-compiled/{pkg}/analysis/interface-specifications.json",
        "catalog": "docs/COMMAND-EVENT-CATALOG.md",
    }


def extract(label, commit, pkg):
    d = os.path.join(INPUTS, label)
    os.makedirs(d, exist_ok=True)
    out = {}
    for flag, path in sources(pkg).items():
        data = subprocess.run(["git", "-C", CLONE, "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
        target = os.path.join(d, os.path.basename(path))
        with open(target, "wb") as fh:
            fh.write(data)
        out[flag] = {"source": f"{commit}:{path}", "file": target, "sha256": hashlib.sha256(data).hexdigest()}
    return out


def command(exe, files, condition, report):
    flags = ("machines", "invariants", "interfaces", "catalog") if condition == "DOC" else ("machines", "invariants", "interfaces")
    return [exe, "spec-preflight"] + [a for f in flags for a in (f"--{f}", files[f]["file"])] + ["--out", report]


def run_once(cmd, env):
    t0 = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return {"exit": p.returncode, "seconds": round(time.perf_counter() - t0, 4), "stdout": p.stdout, "stderr": p.stderr}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--version-label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--env", action="append", default=[])
    a = ap.parse_args(argv)
    env = dict(os.environ, **dict(kv.split("=", 1) for kv in a.env))
    outdir = os.path.join(a.out, a.version_label)
    os.makedirs(outdir, exist_ok=True)
    records = []
    for label, commit, pkg, role in PACKAGES:
        files = extract(label, commit, pkg)
        for condition in ("DOC", "CI"):
            runs, reports = [], []
            for i in range(a.runs):
                rp = os.path.join(INPUTS, f"{a.version_label}.{label}.{condition}.{i}.json")
                if os.path.exists(rp):
                    os.remove(rp)
                cmd = command(a.exe, files, condition, rp)
                r = run_once(cmd, env)
                runs.append(r)
                reports.append(open(rp, encoding="utf-8").read() if os.path.exists(rp) else None)
            keep = os.path.join(outdir, f"{label}.{condition}.json")
            if reports[0] is not None:
                with open(keep, "w", encoding="utf-8") as fh:
                    fh.write(reports[0])
            rec = {"version": a.version_label, "package": label, "commit": commit, "packageDir": pkg, "role": role,
                   "condition": condition, "inputs": files,
                   "command": " ".join(command("percepta", files, condition, f"raw/{a.version_label}/{label}.{condition}.json")),
                   "env": dict(kv.split("=", 1) for kv in a.env),
                   "exits": [r["exit"] for r in runs], "seconds": [r["seconds"] for r in runs],
                   "stdout": runs[0]["stdout"], "stderr": runs[0]["stderr"],
                   "reportsIdentical": len(set(reports)) == 1, "report": keep if reports[0] is not None else None}
            records.append(rec)
            print(label, condition, rec["exits"], rec["seconds"], file=sys.stderr)
    with open(os.path.join(outdir, "runs.json"), "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
