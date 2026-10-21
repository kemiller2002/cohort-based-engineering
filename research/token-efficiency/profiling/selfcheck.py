#!/usr/bin/env python3
"""Self-check on the tiny fixtures: classification, dedup, findings, estimates, schema, determinism.

usage: python3 selfcheck.py      (exit 0 = all checks pass)
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import phases  # noqa: E402
import records as R  # noqa: E402
import transcripts as T  # noqa: E402

PRICE = {"tableVersion": "fixture", "entries": [{"model": "claude-opus-5-5", "input": 4.0, "output": 20.0, "cacheRead": 0.2, "cacheWrite5m": 5.0, "cacheWrite1h": 8.0}]}
CLASSIFY = [
    ({"name": "Bash", "input": {"command": "source /w/env.sh && praxis work claim --id W --token t"}}, "coordination"),
    ({"name": "Bash", "input": {"command": "git add -A && git commit -m x && praxis work verify --id W --token t"}}, "verification"),
    ({"name": "Bash", "input": {"command": "praxis work validate-run --id W --token t -- dotnet test Ledger.slnx"}}, "verification"),
    ({"name": "Bash", "input": {"command": "praxis work complete-verified --id W --token t"}}, "completion"),
    ({"name": "Bash", "input": {"command": "cd /w && dotnet test Ledger.slnx 2>&1 | tail -5"}}, "testing"),
    ({"name": "Bash", "input": {"command": "git push origin main"}}, "coordination"),
    ({"name": "Bash", "input": {"command": "git commit -am x"}}, "handoff"),
    ({"name": "Bash", "input": {"command": "cat requirements/U4.md"}}, "requirement-ingestion"),
    ({"name": "Bash", "input": {"command": "ls src/Ledger"}}, "repository-discovery"),
    ({"name": "Read", "input": {"file_path": "/w/DIRECTIVES.md"}}, "requirement-ingestion"),
    ({"name": "Read", "input": {"file_path": "/w/src/Ledger/Ledger.fs"}}, "repository-discovery"),
    ({"name": "Edit", "input": {"file_path": "/w/src/Ledger/Ledger.fs"}}, "implementation"),
    ({"name": "WebFetch", "input": {}}, "unattributed"),
]


def checks():
    yield all(phases.classify_call(c)[1] == want for c, want in CLASSIFY), "classification rules"
    with open(os.path.join(HERE, "fixtures/tiny-transcript.jsonl")) as f:
        entries, malformed = T.parse_lines(f.read())
    yield malformed == 1, "malformed line counted, not fatal"
    recs, found = T.profile(entries, "fixtures/tiny-transcript.jsonl", "0" * 64, PRICE, work_item="W-1", execution_id="FIX")
    yield len(recs) == 10, "10 requests after message.id dedup (13 assistant lines)"
    yield [r["phase"] for r in recs] == ["requirement-ingestion", "coordination", "repository-discovery", "implementation", "testing",
                                          "testing", "repository-discovery", "verification", "completion", "reporting"], "request phases"
    yield sum(r["toolCalls"] for r in recs) == 10, "tool calls dedup by id"
    yield recs[0]["flags"] == ["first-request-cache-write"], "cold prefix flagged on first request"
    yield found["testRunsWithoutInterveningEdit"] == [5], "second dotnet test with no edit in between"
    yield [d["request"] for d in found["duplicateToolCalls"]] == [5, 6], "duplicate calls (whitespace-normalized test, re-read)"
    yield found["repeatedReads"] == [{"request": 6, "path": "/w/src/Ledger/Ledger.fs"}], "repeated read"
    yield found["briefReads"][0]["tokensEstimate"] == 500, "brief bytes//4"
    yield recs[0]["estimatedCostUsd"] == round((2 * 4 + 5 * 20 + 40000 * 5.0) / 1e6, 6), "cost from price table"
    schema = R.read_json(os.path.join(HERE, "..", "overhead-schema.json"))
    doc = R.document("fixture", "fixture", [], recs, {})
    yield R.check(schema, doc) == [], "transcript records conform to schema"
    bad = R.document("fixture", "fixture", [], [{**recs[0], "phase": "lunch"}], {})
    yield R.check(schema, bad) != [], "schema checker rejects an unknown phase"
    with tempfile.TemporaryDirectory() as d:
        cmd = lambda out: subprocess.run([sys.executable, os.path.join(HERE, "profile.py"), "observations", "--dataset", "fixture", "--label", "fixture",
                                          "--root", HERE, "--glob", "fixtures/tiny-observation-*.json", "--config", os.path.join(HERE, "config.json"),
                                          "--out", out], check=True)
        a, b = os.path.join(d, "a.json"), os.path.join(d, "b.json")
        cmd(a), cmd(b)
        da = R.read_json(a)
        yield open(a, "rb").read() == open(b, "rb").read(), "deterministic output"
        yield R.check(schema, da) == [], "observation records conform to schema"
        est = {r["recordId"]: r for r in da["records"]}
        yield est["FIX-R2-echelon-optimized:verification"]["tokenEstimate"]["total"] == 53002, "turn-equivalent estimate = 1 x 530020/10"
        yield est["FIX-R2-echelon-optimized:residual"]["elapsedMs"] == 100000 - 20000 - 11000 - 1500, "residual elapsed"
        yield all(r["tokens"] is None for r in da["records"] if r["granularity"] == "run-phase-estimate"), "estimates never fill measured tokens"


def main():
    results = list(checks())
    for ok, name in results:
        print(("PASS " if ok else "FAIL ") + name)
    return 0 if all(ok for ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
