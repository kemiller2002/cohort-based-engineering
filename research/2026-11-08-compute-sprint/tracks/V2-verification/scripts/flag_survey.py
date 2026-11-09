#!/usr/bin/env python3
"""V2 claim 10 (second half): survey verified-completion flags at each repository's HEAD.

Reads committed content only (git show / git grep), never the working tree.
Usage: flag_survey.py REPO_DIR [REPO_DIR ...]  -> JSON on stdout
"""
import json
import subprocess
import sys

FLAGS = ("requireVerifiedCompletion", "requireAttestedEvidence", "trustedVerifierKeyIds")


def flags_in_ros(doc):
    """Pure: the effective workProtocol flags in a parsed ros.json object."""
    wp = doc.get("workProtocol") if isinstance(doc, dict) else None
    wp = wp if isinstance(wp, dict) else {}
    return {f: wp[f] for f in FLAGS if f in wp}


def enabled(flags):
    """Pure: True when any flag would turn verified/attested completion on."""
    return (flags.get("requireVerifiedCompletion") is True
            or flags.get("requireAttestedEvidence") is True
            or bool(flags.get("trustedVerifierKeyIds")))


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def survey_repo(repo):
    head = (git(repo, "rev-parse", "--short", "HEAD") or "").strip()
    if not head:
        return {"repo": repo, "error": "not a git repository"}
    raw = git(repo, "show", "HEAD:ros.json")
    try:
        root_flags = flags_in_ros(json.loads(raw)) if raw else None
    except ValueError:
        root_flags = "unparseable"
    # Any committed JSON that mentions a flag as a key with a non-default value
    hits = git(repo, "grep", "-n", "-E", "\"(" + "|".join(FLAGS) + ")\"\\s*:", "HEAD", "--", "*.json") or ""
    return {
        "repo": repo,
        "head": head,
        "has_root_ros_json": raw is not None,
        "root_flags": root_flags,
        "enabled": enabled(root_flags) if isinstance(root_flags, dict) else False,
        "json_key_mentions": [l for l in hits.splitlines()][:20],
    }


def main(repos):
    rows = tuple(survey_repo(r) for r in repos)
    ok = tuple(r for r in rows if "error" not in r)
    print(json.dumps({
        "repos_scanned": len(ok),
        "with_root_ros_json": sum(1 for r in ok if r["has_root_ros_json"]),
        "enabled_count": sum(1 for r in ok if r["enabled"]),
        "repos_with_any_flag_key_in_json": [r["repo"] for r in ok if r["json_key_mentions"]],
        "rows": rows,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
