#!/usr/bin/env python3
"""Fetch GitHub Actions workflow runs (read-only GET) for a list of repositories.

Side effects (network, file writes) are confined to `main`; record trimming is a pure
function (`trim_run`) covered by tests. Output: one JSONL file per repository with only
the fields the CI analysis needs, plus a fetch manifest recording when and how.

Usage: python3 fetch_ci_runs.py OUT_DIR OWNER REPO [REPO ...]
"""
import json
import subprocess
import sys
from datetime import datetime, timezone

KEEP = (
    "id", "name", "path", "event", "status", "conclusion", "head_branch", "head_sha",
    "run_number", "run_attempt", "created_at", "run_started_at", "updated_at",
)


def trim_run(run: dict) -> dict:
    """Keep only analysis fields; never copies actor tokens or URLs with credentials."""
    return {k: run.get(k) for k in KEEP}


def fetch_page(owner: str, repo: str, page: int) -> list:
    out = subprocess.run(
        ["gh", "api", "-X", "GET",
         f"repos/{owner}/{repo}/actions/runs?per_page=100&page={page}"],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out).get("workflow_runs", [])


def fetch_all(owner: str, repo: str) -> list:
    pages = []
    page = 1
    while True:
        runs = fetch_page(owner, repo, page)
        if not runs:
            return [trim_run(r) for p in pages for r in p]
        pages.append(runs)
        page += 1
        if page > 60:  # hard stop: >6000 runs is outside this study's scope
            return [trim_run(r) for p in pages for r in p]


def main(argv: list) -> None:
    out_dir, owner, repos = argv[1], argv[2], argv[3:]
    manifest = []
    for repo in repos:
        runs = fetch_all(owner, repo)
        path = f"{out_dir}/ci-runs-{repo}.jsonl"
        with open(path, "w") as fh:
            fh.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in runs))
        manifest.append({"repo": f"{owner}/{repo}", "runs": len(runs), "file": path.split("/")[-1],
                         "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "endpoint": "GET /repos/{owner}/{repo}/actions/runs?per_page=100"})
        print(repo, len(runs), file=sys.stderr)
    with open(f"{out_dir}/ci-fetch-manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv)
