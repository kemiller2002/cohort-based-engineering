"""SPR-D4-01: create the run workspaces and the live oracle copy. Refuses to overwrite anything that exists (a run
workspace must never be reset after launch).
Usage: python3 -I setup_workspaces.py            -> /home/user/sprint-scratch/D4/ws/{s1,s2,w01..w16}
                                                   + /home/user/sprint-scratch/D4/oracle-a62d/ (score.py, probes.py,
                                                     trace_tests.py, workspace/)
       python3 -I setup_workspaces.py --report   -> only prints the hashes of what exists (no writes)"""
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(os.path.dirname(HERE), "fixture")
ROOT = "/home/user/sprint-scratch/D4"
ORACLE = os.path.join(ROOT, "oracle-a62d")
IDS = ["s1", "s2"] + ["w%02d" % i for i in range(1, 17)]
ORACLE_FILES = ("score.py", "probes.py", "trace_tests.py")


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
    for f in ORACLE_FILES:
        shutil.copy(os.path.join(FIXTURE, f), ORACLE)
    shutil.copytree(os.path.join(FIXTURE, "workspace"), os.path.join(ORACLE, "workspace"))
    return report()


if __name__ == "__main__":
    print(json.dumps(report() if sys.argv[1:] == ["--report"] else setup(), indent=1))
