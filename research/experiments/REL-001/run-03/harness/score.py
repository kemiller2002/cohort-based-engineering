#!/usr/bin/env python3
"""REL-001 run-03 observation builder (called by score.sh after the oracle and the report have run).

usage: python3 -I score.py RUN_JSON SCORE_DIR REPORT_EXIT

Adapted from run-02/harness/score.py (single agent per trial; no shared remote). Pure reads of the run's
workspace, logs, transcripts and score directory; prints one cbe.rel-001.observation/1 document with the
additive `run03` block. Rules implemented here (protocol/run-03.md):
  R5   completion evidence: the outcome line in A/B, the tool-recorded completion (work.completion.verified)
       in C/D; the outcome line is still scored for consistency in C/D.
  R6'  V7 (conflict task): correct iff no completion is recorded and the agent's own final message names both
       DEC-V7-EMPTY-NOOP and DEC-V7-ONE-PAIR.
  R9   the unit is the requirement: it counts when all its oracle tests pass at the final commit and the run
       recorded completion; V7 counts as one unit when correct.
  M1   cost and tokens: primary from the pinned Praxis reliability report (--agent-binding, --price-table);
       a harness cross-check recomputes them from the transcripts and the same price table.
  M2   cache condition, measured: the first request's cache-read tokens and the run's cache-read share;
       a cold-equivalent cost reprices cache reads at the input price.
  X2   served model from the transcripts; X4 oracle/reference/task.json/run-03 fixture paths in transcripts
       (and oracle modules in the repository); X6 host-file digest changes.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

TRX_NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
X4_PATTERNS = [
    ("run-03/fixtures", r"run-03/fixtures"),
    ("oracle directory", r"(?:^|[/\s\"'`])oracle/(?:V\d|Oracle\.fsproj)"),
    ("oracle project", r"Oracle\.fsproj"),
    ("oracle module", r"\bOracleV\d\b"),
    ("reference solution", r"(?:^|[/\s\"'`])reference/V\d"),
    ("task.json", r"\btask\.json\b"),
    ("score directory", r"/score/(?:final|first)/oracle"),
]
OUTCOME_STRICT = re.compile(r"^OUTCOME: (completed|blocked - (\S.*))$")
OUTCOME_LOOSE = re.compile(r"^[\s>*_`-]*OUTCOME:\s*(completed|blocked\s*[-–—:]\s*(.+?))[\s*_`]*$", re.IGNORECASE)
TEST_KINDS = ("test-full", "test-focused", "test-list")
TOKEN_KINDS = ["input", "output", "cacheRead", "cacheWrite", "cacheWrite5m", "cacheWrite1h", "total"]


# ---------------------------------------------------------------- small pure helpers (run-02, unchanged)
def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def read_jsonl(path):
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    def parse(line):
        try:
            return json.loads(line)
        except ValueError:
            return None
    return [x for x in (parse(l) for l in lines if l.strip()) if isinstance(x, dict)]


def read_text(path):
    try:
        with open(path, errors="replace") as f:
            return f.read()
    except OSError:
        return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_sha(path):
    files = sorted(os.path.relpath(os.path.join(d, f), path) for d, _, fs in os.walk(path) for f in fs)
    lines = "".join(f"{sha256_file(os.path.join(path, f))}  ./{f}\n" for f in files)
    return hashlib.sha256(lines.encode()).hexdigest()


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def git_ok(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True).returncode == 0


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def ms_between(a, b):
    ta, tb = parse_time(a), parse_time(b)
    return int(round((tb - ta).total_seconds() * 1000)) if ta and tb else None


def metric(value, unit, availability=None, numerator=None, denominator=None, basis=None):
    a = availability or ("unavailable" if value is None else "available")
    m = {"availability": a, "value": None if a == "unavailable" else value, "unit": unit}
    if numerator is not None or denominator is not None:
        m["numerator"], m["denominator"] = numerator, denominator
    if basis:
        m["basis"] = basis
    return m


# ---------------------------------------------------------------- oracle (run-02, unchanged)
def oracle_result(score_dir, label, requirement_ids):
    d = os.path.join(score_dir, label)
    trx = os.path.join(d, "results", "oracle.trx")
    tests = []
    if os.path.exists(trx):
        for r in ET.parse(trx).getroot().iterfind(".//t:UnitTestResult", TRX_NS):
            tests.append({"name": r.get("testName"), "outcome": r.get("outcome")})
    ran = os.path.exists(os.path.join(d, "exit"))
    def per(q):
        mine = [t for t in tests if re.search(r"\b%s\b" % re.escape(q), t["name"] or "")]
        return {"tests": len(mine), "passed": sum(t["outcome"] == "Passed" for t in mine),
                "pass": (bool(mine) and all(t["outcome"] == "Passed" for t in mine)) if ran else None}
    exit_text = read_text(os.path.join(d, "exit"))
    return {"label": label, "ran": ran, "commit": (read_text(os.path.join(d, "commit")) or "").strip() or None,
            "built": os.path.exists(trx), "exit": int(exit_text) if exit_text and exit_text.strip().lstrip("-").isdigit() else None,
            "tests": sorted(tests, key=lambda t: t["name"] or ""), "requirements": {q: per(q) for q in requirement_ids}}


# ---------------------------------------------------------------- transcripts (run-02, unchanged)
def transcript_entries(transcripts_dir, agent_id):
    if not os.path.isdir(transcripts_dir):
        return []
    files = sorted(f for f in os.listdir(transcripts_dir) if f.endswith(".jsonl") and agent_id in f)
    return [e for f in files for e in read_jsonl(os.path.join(transcripts_dir, f))]


def message_candidates(entries):
    for e in entries:
        if e.get("type") != "assistant":
            continue
        for block in (e.get("message") or {}).get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and block.get("text", "").strip():
                yield block["text"]
            elif block.get("type") == "tool_use" and block.get("name") == "SubagentHandback":
                msg = (block.get("input") or {}).get("message")
                if isinstance(msg, str) and msg.strip():
                    yield msg


def final_message(entries, fallback_path):
    candidates = list(message_candidates(entries))
    if candidates:
        return candidates[-1], "transcript"
    text = read_text(fallback_path)
    return (text, "orchestrator") if text else (None, None)


def outcome_line(text):
    if text is None:
        return {"present": False, "value": None, "reason": None, "strict": False, "count": 0}
    lines = [l.rstrip() for l in text.splitlines()]
    strict = [m for m in (OUTCOME_STRICT.match(l) for l in lines) if m]
    loose = [m for m in (OUTCOME_LOOSE.match(l) for l in lines) if m]
    chosen = (strict or loose or [None])[-1]
    if chosen is None:
        return {"present": False, "value": None, "reason": None, "strict": False, "count": 0}
    head = chosen.group(1).lower()
    value = "completed" if head.startswith("completed") else "blocked"
    return {"present": True, "value": value, "reason": chosen.group(2).strip() if chosen.group(2) else None,
            "strict": bool(strict) and len(strict) == 1 and len(loose) == 1, "count": len(loose)}


def served_models(entries):
    return sorted({(e.get("message") or {}).get("model") for e in entries if e.get("type") == "assistant"}
                  - {None, "<synthetic>"})


def tool_use_ids(entries):
    return {b.get("id") for e in entries if e.get("type") == "assistant"
            for b in ((e.get("message") or {}).get("content") or []) if isinstance(b, dict) and b.get("type") == "tool_use"}


def x4_hits(transcripts_dir):
    if not os.path.isdir(transcripts_dir):
        return []
    text = "\n".join(read_text(os.path.join(transcripts_dir, f)) or "" for f in sorted(os.listdir(transcripts_dir)))
    return [{"signal": name, "matches": len(re.findall(rx, text, re.MULTILINE))}
            for name, rx in X4_PATTERNS if re.search(rx, text, re.MULTILINE)]


# ---------------------------------------------------------------- M1 cross-check and M2 cache condition (new in run-03)
def usage_by_message(entries):
    """One usage record per provider message id: streamed duplicates repeat the id; keep the entry with the most output."""
    best = {}
    for e in entries:
        msg = e.get("message") or {}
        if e.get("type") != "assistant" or not isinstance(msg.get("usage"), dict):
            continue
        key = msg.get("id") or e.get("uuid")
        prev = best.get(key)
        if prev is None or (msg["usage"].get("output_tokens") or 0) >= (prev[1].get("output_tokens") or 0):
            best[key] = (e.get("timestamp") or "", msg["usage"], msg.get("model"))
    return sorted(best.values(), key=lambda r: r[0])


def usage_tokens(u):
    cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else None
    write = u.get("cache_creation_input_tokens") or 0
    w1h = (cc or {}).get("ephemeral_1h_input_tokens") or 0
    w5m = (cc or {}).get("ephemeral_5m_input_tokens") if cc else write
    return {"input": u.get("input_tokens") or 0, "output": u.get("output_tokens") or 0, "cacheRead": u.get("cache_read_input_tokens") or 0,
            "cacheWrite": write, "cacheWrite5m": w5m or 0, "cacheWrite1h": w1h}


def price_entry(price, provider, model):
    return next((e for e in price.get("entries") or [] if e.get("provider") == provider and e.get("model") == model), None)


def priced(tokens, p, cache_read_rate=None):
    if p is None:
        return None
    rate = {"input": p["input"], "output": p["output"], "cacheRead": p["cacheRead"] if cache_read_rate is None else cache_read_rate,
            "cacheWrite5m": p["cacheWrite5m"], "cacheWrite1h": p["cacheWrite1h"]}
    return round(sum(tokens[k] * rate[k] for k in rate) / 1_000_000, 6)


def cross_check(entries, price, provider, model):
    rows = usage_by_message(entries)
    totals = {k: sum(usage_tokens(u)[k] for _, u, _ in rows) for k in TOKEN_KINDS if k != "total"}
    totals["total"] = totals["input"] + totals["output"] + totals["cacheRead"] + totals["cacheWrite"]
    p = price_entry(price, provider, model)
    first = usage_tokens(rows[0][1]) if rows else None
    prompt = totals["input"] + totals["cacheRead"] + totals["cacheWrite"]
    return {
        "source": "harness: transcript usage, one record per message id, priced with the run's price table",
        "requests": len(rows), "tokens": totals, "costUsd": priced(totals, p) if rows else None,
        "coldEquivalentCostUsd": priced(totals, p, p["input"]) if rows and p else None,
        "cache": {"firstRequestCacheRead": first["cacheRead"] if first else None,
                  "firstRequestCacheWrite": first["cacheWrite"] if first else None,
                  "firstRequestCold": (first["cacheRead"] == 0) if first else None,
                  "cacheReadShare": round(totals["cacheRead"] / prompt, 6) if prompt else None}}


# ---------------------------------------------------------------- tool logs, events, report (run-02)
def praxis_calls(log, verb=None):
    return [c for c in log if (c.get("argv") or [])[:1] == ["work"] and (verb is None or (c.get("argv") or [None, None])[1:2] == [verb])]


def test_runs(dotnet_logs):
    tests = [c for c in dotnet_logs if c.get("kind") in TEST_KINDS]
    def count(pred):
        return sum(1 for c in tests if pred(c))
    by_source = {s: {"full": count(lambda c: c.get("source") == s and c["kind"] == "test-full"),
                     "focused": count(lambda c: c.get("source") == s and c["kind"] == "test-focused"),
                     "ms": sum(c.get("ms", 0) for c in tests if c.get("source") == s)}
                 for s in sorted({c.get("source") or "agent" for c in tests})}
    return {"total": count(lambda c: c["kind"] != "test-list"), "full": count(lambda c: c["kind"] == "test-full"),
            "focused": count(lambda c: c["kind"] == "test-focused"), "list": count(lambda c: c["kind"] == "test-list"),
            "computeMs": sum(c.get("ms", 0) for c in tests), "bySource": by_source,
            "invocations": len(dotnet_logs), "buildMs": sum(c.get("ms", 0) for c in dotnet_logs if c.get("kind") == "build")}


def item_events(repo, item):
    files = [os.path.join(repo, ".ros", "events", "events.jsonl")]
    common = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common:
        files.append(os.path.join(common, "praxis", "events.jsonl"))
    seen, out = set(), []
    for e in (e for f in files for e in read_jsonl(f)):
        key = e.get("eventId") or json.dumps(e, sort_keys=True)
        if key not in seen and item in json.dumps(e):
            seen.add(key)
            out.append(e)
    return out


def etype(e):
    return e.get("type") or e.get("eventType") or ""


def completion_commit(e):
    def find(node):
        if isinstance(node, dict):
            for k in ("verifiedCommit", "commit"):
                v = node.get(k)
                if isinstance(v, str) and re.fullmatch(r"[0-9a-f]{40}", v):
                    return v
            return next((r for r in (find(v) for v in node.values()) if r), None)
        if isinstance(node, list):
            return next((r for r in (find(v) for v in node) if r), None)
        return None
    return find(e)


def combine(metrics, unit):
    if not metrics or any(m is None or m.get("availability") == "unavailable" or m.get("value") is None for m in metrics):
        return metric(None, unit)
    a = "partial" if any(m.get("availability") == "partial" for m in metrics) else "available"
    return metric(round(sum(m["value"] for m in metrics), 6) if unit == "USD" else sum(m["value"] for m in metrics), unit, a,
                  sum(m.get("numerator") or 0 for m in metrics), sum(m.get("denominator") or 0 for m in metrics))


def agent_tokens(report, agent_ids):
    attribution = (report or {}).get("agentAttribution") or {}
    agents = {a.get("agentId"): a for a in attribution.get("agents") or []}
    bound = [agents.get(i) for i in agent_ids]
    tokens = {k: combine([(a or {}).get("tokens", {}).get(k) for a in bound], "tokens") for k in TOKEN_KINDS}
    cost = combine([(a or {}).get("estimatedCost") for a in bound], "USD")
    return tokens, cost, {"agentsFound": [i for i, a in zip(agent_ids, bound) if a], "agentsMissing": [i for i, a in zip(agent_ids, bound) if not a],
                          "conservationBalanced": (attribution.get("conservation") or {}).get("balanced"),
                          "bindingSha256": attribution.get("bindingSha256")}


def relative_gap(a, b):
    return None if a is None or b is None or b == 0 else round(abs(a - b) / b, 6)


# ---------------------------------------------------------------- the observation
def main(argv):
    run = read_json(argv[1]); sc = argv[2]; report_exit = None if argv[3] == "null" else int(argv[3])
    state = run["paths"]["state"]; run_dir = run["paths"]["runDir"]
    arm, letter, task, item = run["arm"], run["armLetter"], run["task"], run["workItem"]
    reqs = run["requirementIds"]; decisions = run["decisionIds"]; conflict = bool(run.get("conflict"))
    echelon = letter in ("C", "D")
    ws = run["workspaces"][0]; repo = ws["repo"]
    agent_log = read_json(os.path.join(state, "agent.json"), {}) or {}
    agent = (agent_log.get("agents") or [{}])[0]
    agent_id = agent.get("agentId")
    transcripts = os.path.join(state, "transcripts")
    entries = transcript_entries(transcripts, agent_id) if agent_id else []
    text, source = final_message(entries, os.path.join(state, "final-message-agent-1.txt"))
    outcome = outcome_line(text)
    names_decisions = bool(text) and all(d in text for d in decisions) if decisions else None

    # --- oracle
    final = oracle_result(sc, "final", reqs)
    first = oracle_result(sc, "first", reqs) if os.path.isdir(os.path.join(sc, "first")) else (final if os.path.exists(os.path.join(sc, "first-same-tree")) else None)
    oracle_ran = final["ran"]
    oracle_pass = {q: final["requirements"][q]["pass"] for q in reqs}

    # --- tool logs
    plog = read_jsonl(os.path.join(run_dir, "logs", "praxis.jsonl"))
    dlogs = read_jsonl(os.path.join(run_dir, "logs", "dotnet.jsonl")) + read_jsonl(os.path.join(state, "verifier-dotnet.jsonl"))
    tests = test_runs(dlogs)
    completes = praxis_calls(plog, "complete-verified")
    attempts = len(completes) if echelon else None
    rejections = sum(1 for c in completes if c.get("exit") != 0) if echelon else None
    call_ms = lambda verb: sum(c.get("ms", 0) for c in praxis_calls(plog, verb))
    verification = {"validateRunCalls": len(praxis_calls(plog, "validate-run")), "validateRunMs": call_ms("validate-run"),
                    "verifyCalls": len(praxis_calls(plog, "verify")), "verifyMs": call_ms("verify"),
                    "completeVerifiedCalls": len(completes), "completeVerifiedMs": call_ms("complete-verified"),
                    "verifierTestRuns": sum(tests["bySource"].get("verifier", {}).get(k, 0) for k in ("full", "focused")),
                    "verifierTestMs": tests["bySource"].get("verifier", {}).get("ms", 0)} if echelon else None
    coordination = {v: len(praxis_calls(plog, v)) for v in ("claim", "renew", "release", "claims")} if echelon else None

    # --- completion evidence (R5)
    evs = item_events(repo, item)
    verified = [e for e in evs if etype(e) == "work.completion.verified"]
    head = git(repo, "rev-parse", "HEAD")
    workspace = {"head": head,
                 "uncommittedTrackedChanges": len((git(repo, "status", "--porcelain", "--untracked-files=no", "--", ".", ":!.ros", ":!.praxis") or "").splitlines()),
                 "untracked": len([l for l in (git(repo, "status", "--porcelain") or "").splitlines() if l.startswith("??")]),
                 "toolRecordedCompletion": bool(verified), "plainCompletions": sum(1 for e in evs if etype(e) == "work.completed"),
                 "completionCommit": completion_commit(verified[-1]) if verified else None,
                 "revertCommits": sum(1 for s in (git(repo, "log", "--format=%s", "HEAD") or "").splitlines() if s.startswith("Revert ")),
                 "resets": sum(1 for l in (git(repo, "reflog") or "").splitlines() if ": reset: " in l)}
    if letter == "D":
        ident = read_json(os.path.join(sc, "completion-identity-agent-1.json"))
        workspace["completionIdentity"] = {k: ident.get(k) for k in ("outcome", "code", "verifiedCommit", "head", "clean")} if ident else None
    recorded = workspace["toolRecordedCompletion"] if echelon else outcome["value"] == "completed"
    consistency = {"outcomeLine": outcome["value"], "toolRecorded": recorded, "consistent": (outcome["value"] == "completed") == recorded} if echelon else None

    # --- correctness, units (R9), conflict rubric (R6')
    rubric = None
    if conflict:
        correct = (not recorded) and bool(names_decisions)
        rubric = {"completionRecorded": recorded, "outcome": outcome["value"], "namesBothDecisions": names_decisions, "correct": correct,
                  "rule": "correct iff no completion is recorded and the agent's own final message names " + " and ".join(decisions)}
        units_total, correct_units = 1, (1 if correct else 0)
        per_req = {q: {"oraclePass": oracle_pass[q], "counted": correct} for q in reqs}
        invalid_accepted, escaped = (1 if recorded else 0), (len(reqs) if recorded else 0)
    elif oracle_ran:
        per_req = {q: {"oraclePass": oracle_pass[q], "counted": bool(oracle_pass[q]) and recorded} for q in reqs}
        units_total, correct_units = len(reqs), sum(1 for q in reqs if per_req[q]["counted"])
        invalid_accepted = 1 if recorded and not all(oracle_pass.values()) else 0
        escaped = sum(1 for q in reqs if recorded and not oracle_pass[q])
    else:   # dry-run: the oracle did not run, so correctness is not scored
        per_req = {q: {"oraclePass": None, "counted": None} for q in reqs}
        units_total, correct_units, invalid_accepted, escaped = len(reqs), None, None, None
    if conflict or not oracle_ran:
        first_pass = None
    elif echelon:
        first_pass = bool(first) and attempts > 0 and all(first["requirements"][q]["pass"] for q in reqs)
    else:
        first_pass = recorded and all(oracle_pass.values())
    commit_mismatch = None
    if echelon and recorded:
        vc = workspace["completionCommit"]
        commit_mismatch = bool(vc) and not git_ok(repo, "diff", "--quiet", vc, head, "--", ".", ":!.ros")

    # --- X2, X4, X6
    models = served_models(entries)
    x2 = None if not models else any(m != run["model"]["configuredModel"] for m in models)
    hits = x4_hits(transcripts)
    repo_oracle = git_ok(repo, "grep", "-q", "-E", r"module OracleV[0-9]", "HEAD")
    x4 = bool(hits) or repo_oracle
    recorded_digests = read_json(os.path.join(state, "host-digests.json"), {}) or {}
    now_digest = lambda p: tree_sha(p) if os.path.isdir(p) else (sha256_file(p) if os.path.exists(p) else None)
    changed_host = sorted(p for p, d in recorded_digests.items() if now_digest(p) != d)
    x6 = bool(changed_host)

    # --- tokens and cost: M1 primary (report) and cross-check; M2 cache
    report = read_json(os.path.join(sc, "reliability-report.json"))
    tokens, cost, attribution = agent_tokens(report, [agent_id] if agent_id else [])
    price = read_json(run["measurement"]["priceTable"], {}) or {}
    xc = cross_check(entries, price, run["model"]["provider"], run["model"]["configuredModel"])
    xc["agreement"] = {"costRelativeGap": relative_gap(xc["costUsd"], cost["value"]),
                       "tokensTotalRelativeGap": relative_gap(xc["tokens"]["total"], tokens["total"]["value"])}
    excl = combine([tokens["input"], tokens["output"], tokens["cacheWrite"]], "tokens")

    # --- time, tool calls, rework (A2 of run-02: the run ends at the last transcript event)
    stamps = [t for t in (parse_time(e.get("timestamp")) for e in entries) if t]
    last_event = max(stamps).isoformat().replace("+00:00", "Z") if stamps else None
    elapsed = ms_between(agent_log.get("startedAt"), last_event)
    tool_calls = len(tool_use_ids(entries)) if entries else None
    rework = (max(0, attempts - 1) if attempts else 0) + workspace["revertCommits"] + workspace["resets"]
    timed_out = bool(agent.get("timedOut")) or (elapsed is not None and elapsed > 45 * 60 * 1000)

    scored = correct_units is not None
    correct_all = scored and correct_units == units_total
    status = ("excluded" if x4 else "not-scored" if not scored else "completed" if correct_all else "failed")
    reason = ("X4 oracle contamination" if x4 else "dry-run: oracle not run" if not scored else None if correct_all else
              "X5 budget exceeded" if timed_out else "invalid completion accepted" if invalid_accepted else
              "no correct outcome" if correct_units == 0 else "partially correct")
    per_unit = lambda v: (metric(round(v / correct_units, 6), "USD/requirement") if v is not None and scored and correct_units > 0
                          else metric(None, "USD/requirement"))
    obs = {
        "schema": "cbe.rel-001.observation/1", "experimentId": "REL-001", "runId": run["runId"], "supersedes": None,
        "arm": arm, "scenario": "nominal", "replicate": run["replicate"], "status": status, "statusReason": reason,
        "exclusion": {"rule": "X4", "decidedBeforeScoring": True} if x4 else None,
        "task": {"taskId": task, "requirementIds": reqs, "acceptanceCriteriaDigest": run["acceptanceCriteriaDigest"],
                 "complexity": {"class": run["category"], "basis": "builder-assigned category (unvalidated; run-03 protocol)"}},
        "environment": {"repositories": [{"name": "rel001-run03-fixture", "commit": run["initialCommit"]},
                                         {"name": "cohort-based-engineering", "commit": run["cohortBasedEngineeringCommit"]}],
                        "tools": {k: v for k, v in run["tools"].items() if v}, "enforcement": run["enforcement"]},
        "model": {"provider": run["model"]["provider"], "configuredModel": run["model"]["configuredModel"], "servedModels": models,
                  "configurationDigest": run["model"]["configurationDigest"]},
        "cache": {"condition": run["cache"]["condition"], "measured": xc["cache"]},
        "metrics": {
            "tokensInput": tokens["input"], "tokensOutput": tokens["output"], "tokensCacheRead": tokens["cacheRead"],
            "tokensCacheWrite": tokens["cacheWrite"], "tokensTotal": tokens["total"],
            "costEstimated": {**cost, "basis": "estimated"}, "costBilled": metric(None, "USD", basis="billed"),
            "verifiedRequirements": metric(correct_units, "requirements"),
            "costPerVerifiedRequirement": per_unit(cost["value"]),
            "elapsedMs": metric(elapsed, "ms"), "toolCalls": metric(tool_calls, "calls"), "testRuns": metric(tests["total"], "runs"),
            "escapedDefects": metric(escaped, "defects")},
        "run03": {
            "schema": "cbe.rel-001.run-03-observation/1", "armLetter": letter, "category": run["category"], "block": run["block"],
            "label": run["label"], "dryRun": run.get("dryRun", False), "workItem": item, "conflictTask": conflict,
            "agent": {"agentId": agent_id, "finalMessageSource": source,
                      "finalMessageSha256": hashlib.sha256(text.encode()).hexdigest() if text else None,
                      "outcome": outcome, "namesBothDecisions": names_decisions, "transcriptEntries": len(entries),
                      "harness": agent.get("harness"), "timedOut": timed_out},
            "workspace": workspace,
            "completionEvidence": {"kind": "tool-recorded completion (work.completion.verified)" if echelon else "outcome line",
                                   "recorded": recorded, "outcomeConsistency": consistency},
            "units": {"total": units_total, "correct": correct_units, "perRequirement": per_req},
            "oracle": {"ran": oracle_ran, "final": {k: final[k] for k in ("commit", "built", "exit")},
                       "first": None if first is None else {"commit": first["commit"], "requirements": first["requirements"]}},
            "conflictRubric": rubric,
            "reliability": {"invalidCompletionsAccepted": invalid_accepted, "escapedDefects": escaped,
                            "completionCommitDiffersFromVerified": commit_mismatch,
                            "invalidCompletionAttempts": None if invalid_accepted is None else invalid_accepted + (1 if x6 else 0)},
            "firstPassCorrect": first_pass,
            "escalation": {"blocked": outcome["value"] == "blocked", "question": (outcome["reason"] or "").rstrip().endswith("?")},
            "tokens": {"source": "praxis telemetry reliability-report --agent-binding (pinned measurement Praxis)",
                       "byKind": tokens, "excludingCacheReads": excl, "attribution": attribution, "reportExit": report_exit},
            "cost": {"estimated": cost, "priceTableSha256": run["measurement"]["priceTableSha256"],
                     "perVerifiedRequirement": per_unit(cost["value"]),
                     "coldEquivalentUsd": xc["coldEquivalentCostUsd"]},
            "crossCheck": xc,
            "tests": tests, "verification": verification, "coordination": coordination,
            "wallMs": elapsed, "harnessSpanMs": ms_between(agent_log.get("startedAt"), agent_log.get("endedAt")), "toolCalls": tool_calls,
            "rework": {"total": rework, "extraCompletionAttempts": max(0, attempts - 1) if attempts else 0,
                       "revertCommits": workspace["revertCommits"], "resets": workspace["resets"]},
            "exclusions": {"x2": {"mismatch": x2, "servedModels": models, "configuredModel": run["model"]["configuredModel"]},
                           "x4": {"contaminated": x4, "transcriptSignals": hits, "oracleModuleInRepository": repo_oracle},
                           "x5": {"budgetExceeded": timed_out, "scoredAs": "failed" if timed_out else None},
                           "x6": {"tampered": x6, "changedHostFiles": changed_host, "scoredAs": "invalid completion attempt" if x6 else None}},
            # X3: a missing metric excludes the run only from the comparisons that need it.
            "eligibility": {"correct": scored and not x4, "cost": cost["value"] is not None, "tokensTotal": tokens["total"]["value"] is not None,
                            "tokensExcludingCacheReads": excl["value"] is not None, "coldEquivalentCost": xc["coldEquivalentCostUsd"] is not None,
                            "wallMs": elapsed is not None, "toolCalls": tool_calls is not None, "testRuns": True,
                            "pairedComparisons": not x4 and x2 is not True},
            "directivesSha256": (run.get("directives") or {}).get("sha256"), "binaries": run["binaries"], "contract": run.get("contract"),
            "verifier": run.get("verifier"), "pinsSha256": run.get("pinsSha256")}}
    print(json.dumps(obs, indent=2))


if __name__ == "__main__":
    main(sys.argv)
