"""SPR-D3-01: create the chain workspaces and the live oracle copy. Idempotent only on a clean slate: refuses to
overwrite an existing workspace (a chain workspace must never be reset after launch).
Usage: python3 -I setup_workspaces.py            -> /home/user/sprint-scratch/D3/ws/{c1,c2,u01..u08}
                                                   + /home/user/sprint-scratch/D3/oracle-5e83/ (score.py,
                                                     oracle_tests.py, workspace/) + empty snapshot root
       python3 -I setup_workspaces.py --report   -> only prints the hashes of what exists (no writes)
Prints the sha256 of every created fixture file so the Director can confirm the start state."""
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(os.path.dirname(HERE), "fixture")
ROOT = "/home/user/sprint-scratch/D3"
ORACLE = os.path.join(ROOT, "oracle-5e83")
IDS = ["c1", "c2"] + ["u%02d" % i for i in range(1, 9)]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tree_sha(d):
    return {os.path.relpath(os.path.join(r, f), d): sha(os.path.join(r, f))
            for r, _, fs in sorted(os.walk(d)) for f in sorted(fs)}


def report():
    return {"workspaces": {i: tree_sha(os.path.join(ROOT, "ws", i)) for i in IDS}, "oracle": tree_sha(ORACLE)}


def setup():
    targets = [os.path.join(ROOT, "ws", i) for i in IDS] + [ORACLE]
    clash = [t for t in targets if os.path.exists(t)]
    if clash:
        sys.exit("refusing to overwrite: %s" % clash)
    for t in targets[:-1]:
        shutil.copytree(os.path.join(FIXTURE, "workspace"), t)
    os.makedirs(ORACLE)
    for f in ("score.py", "oracle_tests.py"):
        shutil.copy(os.path.join(FIXTURE, f), ORACLE)
    shutil.copytree(os.path.join(FIXTURE, "workspace"), os.path.join(ORACLE, "workspace"))
    os.makedirs(os.path.join(ROOT, "snap"), exist_ok=True)
    return report()


if __name__ == "__main__":
    print(json.dumps(report() if sys.argv[1:] == ["--report"] else setup(), indent=1))
