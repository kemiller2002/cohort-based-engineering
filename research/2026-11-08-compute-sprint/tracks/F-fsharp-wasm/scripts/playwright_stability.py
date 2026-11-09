"""Summarise repeated Playwright JSON-reporter runs into per-test stability (pass / fail / flaky / skipped).

Usage: python3 playwright_stability.py LABEL [--project chromium] RUN1.json RUN2.json ... > summary.json
A test is 'stable-pass' if it passed in every run, 'stable-fail' if it failed in every run, 'flaky' if outcomes differ
across runs (or Playwright itself marked it flaky), 'skipped' if skipped in every run.
"""
from __future__ import annotations

import json
import sys
from collections import Counter


def walk(suite: dict, prefix: str = ""):
    """Yield (testId, status, durationMs) from a Playwright JSON report suite tree (pure)."""
    title = f"{prefix} > {suite['title']}" if prefix and suite.get("title") else suite.get("title", prefix)
    for spec in suite.get("specs", []):
        for t in spec.get("tests", []):
            results = t.get("results", [])
            status = t.get("status") or (results[-1]["status"] if results else "skipped")
            # Playwright test-level status: expected | unexpected | flaky | skipped
            yield f"{spec.get('file', '')}::{title} > {spec['title']} [{t.get('projectName', '')}]", status, sum(r.get("duration", 0) for r in results)
    for child in suite.get("suites", []):
        yield from walk(child, title)


def per_run(report: dict) -> dict[str, tuple[str, int]]:
    return {tid: (st, d) for s in report.get("suites", []) for tid, st, d in walk(s)}


def classify(outcomes: list[str]) -> str:
    kinds = set(outcomes)
    if kinds == {"skipped"}:
        return "skipped"
    if "flaky" in kinds or len(kinds - {"skipped"}) > 1:
        return "flaky"
    return "stable-pass" if kinds - {"skipped"} == {"expected"} else "stable-fail"


def summarise(label: str, reports: list[dict], project: str | None = None) -> dict:
    runs = [{t: v for t, v in per_run(r).items() if project is None or t.endswith(f"[{project}]")} for r in reports]
    ids = sorted(set().union(*runs))
    tests = {t: [r.get(t, ("missing", 0))[0] for r in runs] for t in ids}
    verdicts = {t: classify([o for o in os if o != "missing"] or ["skipped"]) for t, os in tests.items()}
    wall = [r.get("stats", {}).get("duration") for r in reports]
    return {"label": label, "project": project or "all", "runs": len(reports), "tests": len(ids), "verdicts": dict(Counter(verdicts.values())),
            "runWallMs": wall, "perRunCounts": [dict(Counter(s for s, _ in r.values())) for r in runs],
            "nonPassing": {t: tests[t] for t, v in verdicts.items() if v not in ("stable-pass", "skipped")}}


if __name__ == "__main__":
    args = sys.argv[1:]
    project = args[args.index("--project") + 1] if "--project" in args else None
    files = [a for i, a in enumerate(args[1:], 1) if a != "--project" and (i == 0 or args[i - 1] != "--project")]
    print(json.dumps(summarise(args[0], [json.load(open(f)) for f in files], project), indent=1))
