#!/usr/bin/env python3
"""V2 claim 8 (C-F-08): which repositories consume a component, at which version, at HEAD.

A repo consumes the component when any of these committed files names it with a version:
  *.fsproj / Directory.Packages.props PackageReference/PackageVersion  (NuGet id)
  conditor.json components[] / .conditor/lock.json components[]       (component id)
  .conditor/authority/resolved-release-set.json components[]          (systemId)
Usage: consumer_pins.py COMPONENT_ID NUGET_ID REPO_DIR [REPO_DIR ...]
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def nuget_versions(text, nuget_id):
    """Pure: versions of nuget_id in MSBuild XML text."""
    pat = re.compile(r'<Package(?:Reference|Version)\s+[^>]*Include="' + re.escape(nuget_id)
                     + r'"[^>]*Version="([^"]+)"', re.IGNORECASE)
    return tuple(pat.findall(text))


def json_versions(text, component_id, key):
    """Pure: versions of component_id in components[] of a JSON document."""
    try:
        doc = json.loads(text) if text else {}
    except ValueError:
        return ()
    comps = doc.get("components", []) if isinstance(doc, dict) else []
    return tuple(c.get("version") for c in comps if isinstance(c, dict) and c.get(key) == component_id)


def repo_versions(repo, component_id, nuget_id):
    files = git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    msb = tuple(f for f in files if f.endswith((".fsproj", ".csproj", "Directory.Packages.props")))
    found = []
    for f in msb:
        found += [("nuget", f, v) for v in nuget_versions(git(repo, "show", f"HEAD:{f}"), nuget_id)]
    for f, key in (("conditor.json", "id"), (".conditor/lock.json", "id"),
                   (".conditor/authority/resolved-release-set.json", "systemId")):
        if f in files:
            found += [("component", f, v) for v in json_versions(git(repo, "show", f"HEAD:{f}"), component_id, key)]
    return tuple(found)


def summarize(rows):
    consumers = tuple(r for r in rows if r["pins"])
    return {
        "consumers": len(consumers),
        "byVersionSet": dict(Counter(",".join(sorted({p[2] for p in r["pins"]})) for r in consumers)),
        "repos": [r["repo"] for r in consumers],
    }


def main(argv):
    component_id, nuget_id, repos = argv[0], argv[1], argv[2:]
    rows = tuple({"repo": Path(r).name, "pins": repo_versions(r, component_id, nuget_id)}
                 for r in repos if Path(r).name != component_id)
    print(json.dumps({"summary": summarize(rows), "rows": [r for r in rows if r["pins"]]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
