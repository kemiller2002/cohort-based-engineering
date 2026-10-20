"""Sizes of the context an agent is handed (brief templates, directives, task files).

Sizes are bytes; token figures are bytes // 4 and are labelled estimates (no tokenizer).
Placeholders ({{NAME}}) are left unexpanded, so a rendered brief differs by the length of
the substituted paths and tokens (typically +300..600 bytes).
"""
import glob
import os

import records as R

# run-02 harness/setup.sh:154-159 template composition per arm (agent count 1; U6 adds shared-remote.md)
RUN02_COMPOSITION = {
    "echelon-original": ["core.md", "directives.md", "workflow-c.md", "outcome.md"],
    "echelon-optimized": ["core.md", "directives.md", "workflow-d.md", "outcome.md"],
}


def size(path):
    return os.path.getsize(path)


def item(root, rel):
    p = os.path.join(root, rel)
    b = size(p)
    return {"path": rel, "bytes": b, "tokensEstimate": b // 4, "sha256": R.sha256_file(p)}


def run02(root):
    h = "research/experiments/REL-001/run-02/harness/briefs"
    compositions = {
        arm: {"templates": [item(root, f"{h}/{t}") for t in ts],
              "bytes": sum(size(os.path.join(root, h, t)) for t in ts)}
        for arm, ts in RUN02_COMPOSITION.items()
    }
    compositions = {a: {**c, "tokensEstimate": c["bytes"] // 4} for a, c in compositions.items()}
    tasks = sorted(glob.glob(os.path.join(root, "research/experiments/REL-001/run-02/fixtures/tasks/*/")))
    task_files = [item(root, os.path.relpath(os.path.join(t, f), root)) for t in tasks for f in ("requirement.md", "contract.json")]
    return {
        "briefTemplates": compositions,
        "directives": item(root, "research/experiments/REL-001/run-02/directives/DIRECTIVES.md"),
        "workflowSectionDelta": {
            "workflow-c.md": item(root, f"{h}/workflow-c.md"),
            "workflow-d.md": item(root, f"{h}/workflow-d.md"),
        },
        "taskFiles": task_files,
        "note": "tokensEstimate = bytes // 4 (estimate). Placeholders unexpanded. The agent sees contract.json only if it opens it; D passes it via PRAXIS_ORDO_CONTRACT.",
    }


def carry(item_tokens, requests_after_read):
    """Cache-read tokens spent re-reading an item that stays in the context for later requests."""
    return item_tokens * max(0, requests_after_read)
