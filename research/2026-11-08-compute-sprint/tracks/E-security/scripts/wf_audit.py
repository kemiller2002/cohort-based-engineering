#!/usr/bin/env python3
"""Static GitHub Actions workflow auditor (read-only, functional style).

Usage: python3 -I wf_audit.py OUT.json REPO_DIR [REPO_DIR ...]

For every .github/workflows/*.yml in each repo it reports:
  - trigger set (flags pull_request_target / workflow_run / issue_comment)
  - top-level and per-job `permissions:` (missing => token defaults apply)
  - `${{ github.event.* }}` / `github.head_ref` interpolated directly in `run:`
  - third-party `uses:` not pinned to a 40-hex commit SHA
Pure functions do the analysis; only main() touches the filesystem.
"""
import json
import re
import sys
from pathlib import Path

import yaml

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPR_RE = re.compile(r"\$\{\{\s*([^}]*?)\s*\}\}")
# Contexts an external actor can influence (subset of GitHub's documented list).
UNTRUSTED_RE = re.compile(
    r"github\.event\.(issue\.(title|body)|pull_request\.(title|body|head\.ref|head\.label)"
    r"|comment\.body|review\.body|review_comment\.body|pages\.[^ ]*page_name"
    r"|commits\.[^ ]*message|head_commit\.(message|author)|workflow_run\.(head_branch|display_title|head_commit))"
    r"|github\.head_ref|inputs\.[A-Za-z_-]+"
)
RISKY_TRIGGERS = {"pull_request_target", "workflow_run", "issue_comment"}


def triggers(doc):
    # PyYAML parses the bare key `on` as boolean True.
    on = doc.get("on", doc.get(True, {}))
    if isinstance(on, str):
        return [on]
    if isinstance(on, list):
        return list(on)
    if isinstance(on, dict):
        return list(on.keys())
    return []


def classify_uses(ref):
    """Return (kind, pinned) for a `uses:` reference."""
    if ref.startswith("./") or ref.startswith("docker://"):
        return ("local" if ref.startswith("./") else "docker", True)
    if "@" not in ref:
        return ("unversioned", False)
    target, version = ref.rsplit("@", 1)
    owner = target.split("/", 1)[0]
    kind = "first-party-github" if owner in ("actions", "github") else (
        "echelon" if owner == "kemiller2002" else "third-party")
    return (kind, bool(SHA_RE.match(version)))


def iter_steps(doc):
    for job_id, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        if "uses" in job:  # reusable workflow call
            yield job_id, None, {"uses": job["uses"]}
        for idx, step in enumerate(job.get("steps") or []):
            if isinstance(step, dict):
                yield job_id, idx, step


def untrusted_interpolations(run_text):
    return sorted({e for e in EXPR_RE.findall(run_text or "") if UNTRUSTED_RE.search(e)})


def audit_doc(doc, path):
    trig = triggers(doc)
    jobs = doc.get("jobs") or {}
    job_perms = {j: v.get("permissions") for j, v in jobs.items() if isinstance(v, dict)}
    steps = list(iter_steps(doc))
    uses = [(j, i, s["uses"], *classify_uses(str(s["uses"]))) for j, i, s in steps if "uses" in s]
    inj = [
        {"job": j, "step": i, "name": s.get("name"), "expressions": untrusted_interpolations(str(s.get("run")))}
        for j, i, s in steps if "run" in s and untrusted_interpolations(str(s.get("run")))
    ]
    return {
        "path": path,
        "triggers": trig,
        "risky_triggers": sorted(RISKY_TRIGGERS & set(map(str, trig))),
        "top_permissions": doc.get("permissions"),
        "job_permissions": job_perms,
        "missing_permissions": doc.get("permissions") is None and any(v is None for v in job_perms.values()),
        "write_scopes": sorted(write_scopes(doc.get("permissions")) | {
            s for v in job_perms.values() for s in write_scopes(v)}),
        "unpinned_uses": [
            {"job": j, "step": i, "uses": u, "kind": k} for j, i, u, k, p in uses if not p],
        "pinned_uses": [u for j, i, u, k, p in uses if p and k not in ("local", "docker")],
        "untrusted_in_run": inj,
    }


def write_scopes(perms):
    if perms in ("write-all",):
        return {"ALL"}
    if isinstance(perms, dict):
        return {k for k, v in perms.items() if v == "write"}
    return set()


def summarize(results):
    all_uses = [u for r in results for u in r["unpinned_uses"]]
    return {
        "workflows": len(results),
        "missing_permissions": sum(r["missing_permissions"] for r in results),
        "risky_trigger_workflows": [r["path"] for r in results if r["risky_triggers"]],
        "unpinned_refs": len(all_uses),
        "pinned_refs": sum(len(r["pinned_uses"]) for r in results),
        "unpinned_by_kind": {k: sum(1 for u in all_uses if u["kind"] == k)
                             for k in sorted({u["kind"] for u in all_uses})},
        "untrusted_in_run": [(r["path"], x) for r in results for x in r["untrusted_in_run"]],
        "write_scope_workflows": {r["path"]: r["write_scopes"] for r in results if r["write_scopes"]},
    }


def main(argv):
    out, repos = argv[1], argv[2:]
    results = []
    for repo in repos:
        for wf in sorted(Path(repo).glob(".github/workflows/*.y*ml")):
            try:
                doc = yaml.safe_load(wf.read_text()) or {}
            except yaml.YAMLError as exc:
                results.append({"path": str(wf), "error": str(exc)})
                continue
            results.append(audit_doc(doc, str(wf)))
    ok = [r for r in results if "error" not in r]
    Path(out).write_text(json.dumps({"summary": summarize(ok), "results": results}, indent=1, default=str))
    print(json.dumps(summarize(ok), indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv)
