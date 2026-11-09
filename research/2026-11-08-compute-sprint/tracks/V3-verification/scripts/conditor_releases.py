"""C2-F-07 recomputation: classify each Conditor release by its components/ catalog diff.

A release is 'avoidable under signed range qualification' iff its catalog delta
consists solely of qualifiedVersions additions to descriptors that may declare a
range (distribution not host-tool / lifecycle-npm per CON-343), that declare a
qualifiedRange, with every added version inside that range.
"""
import json
import re
import sys
from functools import reduce

import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from v3guard import read_git, require_scratch_cwd

LIFECYCLE = {"host-tool", "lifecycle-npm"}


def parse_ver(v):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
    return tuple(int(x) for x in m.groups()) if m else None


def in_range(rng, v):
    """Range syntax like '>=0.2.0 <1.0.0' (space-separated conjunction)."""
    pv = parse_ver(v)
    ops = {">=": lambda a, b: a >= b, "<": lambda a, b: a < b, ">": lambda a, b: a > b,
           "<=": lambda a, b: a <= b, "=": lambda a, b: a == b}

    def ok(term):
        m = re.match(r"^(>=|<=|>|<|=)?(\d+\.\d+\.\d+)$", term)
        return m is not None and ops[m.group(1) or "="](pv, parse_ver(m.group(2)))
    return pv is not None and all(ok(t) for t in rng.split())


def catalog(repo, tag):
    names = [n for n in read_git(repo, "ls-tree", "--name-only", f"{tag}:components/").split() if n.endswith(".json")]
    return {n.replace(".component.json", ""): json.loads(read_git(repo, "show", f"{tag}:components/{n}")) for n in names}


def descriptor_delta(old, new):
    keys = sorted(set(old or {}) | set(new or {}))
    changed = [k for k in keys if (old or {}).get(k) != (new or {}).get(k)]
    added_q = sorted(set((new or {}).get("qualifiedVersions", [])) - set((old or {}).get("qualifiedVersions", [])), key=parse_ver)
    removed_q = sorted(set((old or {}).get("qualifiedVersions", [])) - set((new or {}).get("qualifiedVersions", [])), key=parse_ver)
    return {"changedKeys": changed, "addedQualified": added_q, "removedQualified": removed_q,
            "isNew": old is None, "isRemoved": new is None,
            "distribution": (new or old).get("distribution"), "qualifiedRange": (new or old).get("qualifiedRange")}


def descriptor_avoidable(d):
    return (not d["isNew"] and not d["isRemoved"] and d["changedKeys"] == ["qualifiedVersions"]
            and not d["removedQualified"] and d["distribution"] not in LIFECYCLE
            and d["qualifiedRange"] is not None
            and all(in_range(d["qualifiedRange"], v) for v in d["addedQualified"]))


def classify(deltas):
    if not deltas:
        return "no-catalog-change"
    return "avoidable" if all(descriptor_avoidable(d) for d in deltas.values()) else "required"


def release_row(repo, prev, tag):
    a, b = catalog(repo, prev), catalog(repo, tag)
    deltas = {k: descriptor_delta(a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}
    drivers = sorted(k for k, d in deltas.items() if not descriptor_avoidable(d))
    return {"tag": tag, "prev": prev, "commit": read_git(repo, "rev-parse", "--short", f"{tag}^{{commit}}").strip(),
            "classification": classify(deltas), "deltas": deltas, "nonAvoidableDescriptors": drivers}


def main(repo, first, last):
    require_scratch_cwd()
    tags = sorted([t for t in read_git(repo, "tag", "-l", "v*").split() if parse_ver(t[1:])], key=lambda t: parse_ver(t[1:]))
    sel = tags[tags.index(first):tags.index(last) + 1]
    rows = [release_row(repo, tags[tags.index(t) - 1], t) for t in sel]
    summary = reduce(lambda acc, r: {**acc, r["classification"]: acc.get(r["classification"], []) + [r["tag"]]}, rows, {})
    print(json.dumps({"repo": repo, "head": read_git(repo, "rev-parse", "HEAD").strip(), "summary": summary, "rows": rows}, indent=1))


if __name__ == "__main__":
    main(*(sys.argv[1:4] if len(sys.argv) >= 4 else ["/home/user/ext/conditor", "v0.10.9", "v0.10.21"]))
