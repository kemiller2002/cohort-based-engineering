"""SPR-C2-01 H4: which Conditor releases v0.10.9..v0.10.21 could CR-01 have avoided?

Reads the conditor repository read-only (git show / git diff). For each release,
it lists the versions added to each component's qualifiedVersions and whether
other descriptor content changed, then classifies the release:

  avoidable   every catalog change is a version added to a component whose
              descriptor (at the later tag) declares a qualifiedRange that
              contains the version, and nothing else in components/ changed;
  required    at least one added version belongs to a component with no
              qualifiedRange (host-tool / lifecycle; CON-343), or a version
              outside the range, or a new or otherwise changed descriptor;
  no-catalog  nothing in components/ changed (the release had other reasons).

Usage: python3 -I release_history.py /home/user/ext/conditor > out.json
"""

import json
import re
import subprocess
import sys

RELEASES = [f"v0.10.{n}" for n in range(8, 22)]


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


def descriptors_at(repo, tag):
    names = [line for line in git(repo, "ls-tree", "--name-only", tag, "components/").splitlines() if line.endswith(".component.json")]
    return {json.loads(git(repo, "show", f"{tag}:{n}"))["id"]: json.loads(git(repo, "show", f"{tag}:{n}")) for n in names}


def parse_version(text):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(x) for x in m.groups()) if m else None


def in_range(range_text, version):
    """Conditor-style '>=a.b.c <x.y.z' range (only the forms used in components/)."""
    v = parse_version(version)
    if v is None or not range_text:
        return False
    checks = {">=": lambda a, b: a >= b, ">": lambda a, b: a > b, "<=": lambda a, b: a <= b, "<": lambda a, b: a < b}
    terms = re.findall(r"(>=|<=|>|<)\s*(\d+\.\d+\.\d+)", range_text)
    return bool(terms) and all(checks[op](v, parse_version(bound)) for op, bound in terms)


def strip_versions(descriptor):
    return {k: v for k, v in descriptor.items() if k not in ("qualifiedVersions",)}


def component_changes(before, after):
    """Pure: per-component change records between two descriptor maps."""
    ids = sorted(set(before) | set(after))
    return [
        {
            "id": cid,
            "new": cid not in before,
            "removed": cid not in after,
            "addedVersions": sorted(set(after.get(cid, {}).get("qualifiedVersions", [])) - set(before.get(cid, {}).get("qualifiedVersions", []))),
            "otherChange": cid in before and cid in after and strip_versions(before[cid]) != strip_versions(after[cid]),
            "distribution": after.get(cid, before.get(cid, {})).get("distribution"),
            "qualifiedRange": after.get(cid, {}).get("qualifiedRange"),
        }
        for cid in ids
        if before.get(cid) != after.get(cid)
    ]


def avoidable_change(change):
    return (
        not change["new"]
        and not change["removed"]
        and not change["otherChange"]
        and bool(change["qualifiedRange"])
        and all(in_range(change["qualifiedRange"], v) for v in change["addedVersions"])
    )


def classify(changes):
    if not changes:
        return "no-catalog"
    return "avoidable" if all(avoidable_change(c) for c in changes) else "required"


def analyse(repo):
    snapshots = {tag: descriptors_at(repo, tag) for tag in RELEASES}
    rows = [
        {
            "release": later,
            "date": git(repo, "log", "-1", "--format=%cs", later).strip(),
            "changes": component_changes(snapshots[earlier], snapshots[later]),
        }
        for earlier, later in zip(RELEASES, RELEASES[1:])
    ]
    rows = [dict(row, classification=classify(row["changes"])) for row in rows]
    counts = {k: sum(1 for r in rows if r["classification"] == k) for k in ("avoidable", "required", "no-catalog")}
    return {"experiment": "SPR-C2-01/H4", "repository": repo, "head": git(repo, "rev-parse", "--short", "HEAD").strip(), "releases": rows, "counts": counts}


if __name__ == "__main__":
    json.dump(analyse(sys.argv[1]), sys.stdout, indent=2)
    sys.stdout.write("\n")
