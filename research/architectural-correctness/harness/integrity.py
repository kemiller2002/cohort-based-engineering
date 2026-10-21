#!/usr/bin/env python3
"""ARCH-001 integrity snapshots (new; X-integrity).

usage: python3 -I integrity.py snapshot RUN_JSON            -> JSON snapshot on stdout
       python3 -I integrity.py compare  BEFORE.json AFTER.json -> JSON diff on stdout (exit 0 always)

A snapshot hashes every target named in run.json .integrityTargets: the harness scripts (harness/: *.sh, *.py,
*.json, briefs/, oracle-template/, pricing/; README/PROVENANCE excluded), the run's workspace-external tools
(submit, ordo, archcheck copy, policy copy), the verifier dist, the policy source, the ordo binary, the sealed
archive or directory and the harness's pristine copies. A target that does not exist hashes as "missing".
trial.sh takes one before and one after each phase; any changed digest flags the trial X-integrity.
"""
import hashlib
import json
import os
import sys

HARNESS_DOCS = {"README.md", "PROVENANCE.md"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def files_under(root, keep):
    return sorted(os.path.relpath(os.path.join(d, f), root)
                  for d, dirs, fs in os.walk(root) if "__pycache__" not in d.split(os.sep)
                  for f in fs if keep(os.path.relpath(os.path.join(d, f), root)))


def tree_digest(root, keep=lambda rel: True):
    rows = "".join(f"{sha256_file(os.path.join(root, r))}  ./{r}\n" for r in files_under(root, keep))
    return hashlib.sha256(rows.encode()).hexdigest()


def harness_keep(rel):
    return rel not in HARNESS_DOCS and not rel.startswith("smoke/out")


def digest(name, path):
    if not path:
        return None
    if os.path.isdir(path):
        return tree_digest(path, harness_keep if name == "harness" else (lambda rel: True))
    if os.path.isfile(path):
        return sha256_file(path)
    return "missing"


def snapshot(run):
    targets = run.get("integrityTargets") or {}
    return {"schema": "arch001.integrity/1", "runId": run["runId"],
            "digests": {k: digest(k, v) for k, v in sorted(targets.items())},
            "paths": dict(sorted(targets.items()))}


def compare(before, after):
    keys = sorted(set(before["digests"]) | set(after["digests"]))
    changed = [k for k in keys if before["digests"].get(k) != after["digests"].get(k)]
    return {"schema": "arch001.integrity-diff/1", "changed": changed, "tampered": bool(changed),
            "before": {k: before["digests"].get(k) for k in changed}, "after": {k: after["digests"].get(k) for k in changed}}


def main(argv):
    if argv[1] == "snapshot":
        out = snapshot(json.load(open(argv[2])))
    elif argv[1] == "compare":
        out = compare(json.load(open(argv[2])), json.load(open(argv[3])))
    else:
        raise SystemExit(__doc__)
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
