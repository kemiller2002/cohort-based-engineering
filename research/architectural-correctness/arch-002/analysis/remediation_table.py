#!/usr/bin/env python3
"""ARCH-002 remediation-lines table for the lifecycle cost MODEL (INTERFACES §6). Arm-blind: reads only the sealed
references and the public fixtures, never an observation.

usage: python3 -I remediation_table.py SEALED_ROOT FIXTURES_DIR OUT.json [--fixtures F,G]

Per fixture F (every fixtures/<F>/ with a sealed store, or --fixtures):
  * if SEALED_ROOT/F/remediation-lines.json exists (the fixture worker's sealed table: {"rules": {ruleId: lines},
    "*": lines}), it is used as is (basis "sealed table");
  * otherwise, for every task whose sealed task-private/T<n>.json has a trap, the lines that differ between the
    reference `good` and `trap` overlays (phase 1; a file missing from one overlay is compared with the fixture's
    repo copy, or with nothing) are the rework needed to turn the trap into the good solution; that size is credited
    to each DET rule in trap.violatesRules, and a rule's value is the mean over its tasks (basis "good-vs-trap diff").
"default" holds the mean over fixtures of each rule and of "*", for a fixture or rule with no basis of its own.
Output schema arch002.remediation-lines/1. Labelled a model: one remediation is assumed to cost what the reference
diff for that rule's trap costs, whatever the agent's code looked like.
"""
import difflib
import json
import os
import sys


def read_lines(path):
    try:
        with open(path, errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def overlay_files(d):
    return {os.path.relpath(os.path.join(a, f), d) for a, _, fs in os.walk(d) for f in fs if f != ".delete"} if os.path.isdir(d) else set()


def overlay_dir(ref, variant):
    d = os.path.join(ref, variant)
    return os.path.join(d, "phase1") if os.path.isdir(os.path.join(d, "phase1")) else d


def diff_size(good, trap, repo):
    """Lines added + deleted turning the trap overlay into the good overlay."""
    def text(d, rel):
        p = os.path.join(d, rel)
        return read_lines(p) if os.path.exists(p) else read_lines(os.path.join(repo, rel))
    rels = sorted(overlay_files(good) | overlay_files(trap))
    return sum(sum(1 for l in difflib.unified_diff(text(trap, r), text(good, r), lineterm="", n=0)
                   if l[:1] in "+-" and not l.startswith(("+++", "---")))
               for r in rels)


def mean(xs):
    return round(sum(xs) / len(xs), 3) if xs else None


def fixture_table(sealed, repo):
    own = os.path.join(sealed, "remediation-lines.json")
    if os.path.exists(own):
        doc = json.load(open(own))
        return {"rules": doc.get("rules") or {}, "*": doc.get("*"), "basis": "sealed table", "source": own}
    private = os.path.join(sealed, "task-private")
    per_rule, sizes, tasks = {}, [], {}
    for name in sorted(os.listdir(private)) if os.path.isdir(private) else []:
        meta = json.load(open(os.path.join(private, name)))
        trap = meta.get("trap") or {}
        task = name[:-5]
        ref = os.path.join(sealed, "reference", task)
        if not trap.get("exists") or not os.path.isdir(os.path.join(ref, "trap")):
            continue
        size = diff_size(overlay_dir(ref, "good"), overlay_dir(ref, "trap"), repo)
        rules = [r for r in trap.get("violatesRules") or [] if not r.startswith("ARC-HEU") and r != "ARC-TRC-01"]
        tasks[task] = {"lines": size, "rules": rules}
        sizes.append(size)
        for r in rules:
            per_rule.setdefault(r, []).append(size)
    return {"rules": {r: mean(v) for r, v in sorted(per_rule.items())}, "*": mean(sizes), "basis": "good-vs-trap diff", "tasks": tasks}


def main(argv):
    args = [a for a in argv[1:]]
    only = args[args.index("--fixtures") + 1].split(",") if "--fixtures" in args else None
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    sealed_root, fixtures_dir, out = pos[0], pos[1], pos[2]
    names = only or sorted(f for f in os.listdir(fixtures_dir) if os.path.isdir(os.path.join(sealed_root, f)))
    fixtures = {f: fixture_table(os.path.join(sealed_root, f), os.path.join(fixtures_dir, f, "repo")) for f in names}
    rules = sorted({r for t in fixtures.values() for r in t["rules"]})
    default = {"rules": {r: mean([t["rules"][r] for t in fixtures.values() if t["rules"].get(r) is not None]) for r in rules},
               "*": mean([t["*"] for t in fixtures.values() if t["*"] is not None])}
    doc = {"schema": "arch002.remediation-lines/1", "label": "MODEL input (INTERFACES §6)", "fixtures": fixtures, "default": default}
    with open(out, "w") as f:
        f.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": out, "fixtures": {k: {"basis": v["basis"], "*": v["*"], "rules": v["rules"]} for k, v in fixtures.items()}}))


if __name__ == "__main__":
    main(sys.argv)
