#!/usr/bin/env python3
"""V2 claim 6 (C-F-01): recount Praxis installs and Conditor authority sets at each repo HEAD.

Reads committed content only. Pure helpers: ros_version, authority_of, summarize.
Usage: release_inventory.py [--approved=SET.json] REPO_DIR [REPO_DIR ...]
"""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def show(repo, path):
    r = subprocess.run(["git", "-C", repo, "show", f"HEAD:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def parse(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def ros_version(doc):
    """Pure: installed Praxis version from a .echelon/ros.json document."""
    return doc.get("installedVersion") if isinstance(doc, dict) else None


def authority_path(conditor):
    """Pure: where conditor.json says its registry authority lives (default location otherwise)."""
    ra = conditor.get("registryAuthority") if isinstance(conditor, dict) else None
    return ra.get("path") if isinstance(ra, dict) and ra.get("path") else ".conditor/authority/resolved-release-set.json"


def authority_of(rrs):
    """Pure: (profile id, version) of a resolved-release-set document."""
    p = rrs.get("profile") if isinstance(rrs, dict) else None
    return (p.get("id"), p.get("version")) if isinstance(p, dict) else None


def component_version(rrs, system_id):
    comps = rrs.get("components", []) if isinstance(rrs, dict) else []
    return next((c.get("version") for c in comps if c.get("systemId") == system_id), None)


def lock_versions(lock):
    """Pure: {component id: version} from a .conditor/lock.json (schema 4)."""
    comps = lock.get("components", []) if isinstance(lock, dict) else []
    return {c.get("id"): c.get("version") for c in comps if isinstance(c, dict)}


def set_versions(release_set):
    comps = release_set.get("components", []) if isinstance(release_set, dict) else []
    return {c.get("systemId") or c.get("id"): c.get("version") for c in comps}


def lock_matches_set(locked, approved):
    """Pure: every locked component that the set names is at the set's version."""
    shared = {k: v for k, v in locked.items() if k in approved}
    return bool(shared) and all(approved[k] == v for k, v in shared.items()), sorted(set(locked) - set(approved))


def fact(repo, approved_set=None):
    conditor = parse(show(repo, "conditor.json"))
    rrs = parse(show(repo, authority_path(conditor))) if conditor is not None else parse(
        show(repo, ".conditor/authority/resolved-release-set.json"))
    auth = authority_of(rrs)
    return {
        "repo": Path(repo).name,
        "praxisInstalled": ros_version(parse(show(repo, ".echelon/ros.json"))),
        "hasConditorJson": conditor is not None,
        "authoritySet": auth[1] if auth else None,
        "authorityProfile": auth[0] if auth else None,
        "authorityPraxis": component_version(rrs, "praxis"),
        "authorityOrdo": component_version(rrs, "ordo"),
        "lockMatchesApproved": (lambda m: {"match": m[0], "notInSet": m[1]})(
            lock_matches_set(lock_versions(parse(show(repo, ".conditor/lock.json"))), approved_set))
            if approved_set and show(repo, ".conditor/lock.json") else None,
    }


def summarize(facts, approved="1.37.0"):
    return {
        "repos": len(facts),
        "praxisInstalled": dict(Counter(f["praxisInstalled"] for f in facts)),
        "authoritySet": dict(Counter(f["authoritySet"] for f in facts)),
        "matchApproved": sorted(f["repo"] for f in facts if f["authoritySet"] == approved),
        "lockMatchesApprovedNoAuthorityFile": sorted(f["repo"] for f in facts if f["authoritySet"] is None
                                                     and (f.get("lockMatchesApproved") or {}).get("match")),
        "authority_1_3_to_1_24": sorted(f["repo"] for f in facts if f["authoritySet"] not in (None, "1.2.0", approved)),
        "praxis_3_7_2": sorted(f["repo"] for f in facts if f["praxisInstalled"] == "3.7.2"),
        "authority_1_2_0": sorted(f["repo"] for f in facts if f["authoritySet"] == "1.2.0"),
    }


def main(repos):
    approved_set = None
    if repos and repos[0].startswith("--approved="):
        with open(repos[0].split("=", 1)[1]) as fh:
            approved_set = set_versions(json.load(fh))
        repos = repos[1:]
    facts = tuple(fact(r, approved_set) for r in repos)
    print(json.dumps({"summary": summarize(facts), "facts": facts}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
