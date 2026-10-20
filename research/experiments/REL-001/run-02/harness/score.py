#!/usr/bin/env python3
"""REL-001 run-02 observation builder (called by score.sh after the oracle and report have run).

usage: python3 -I score.py RUN_JSON SCORE_DIR REPORT_EXIT

Pure reads of the run's workspaces, logs, transcripts and score directory; prints one
cbe.rel-001.observation/1 document. Every run-01 member keeps its meaning; run-02 adds the
optional `run02` block (schema/observation.schema.json, additive).

Rules implemented here (design 02-run02-design.md):
  R5  outcome line from the agent's final message; completion evidence is the outcome line in A/B and
      the tool-recorded completion in C/D (the outcome line is then scored for consistency).
  R6  U2: correct iff no completion and the final message names both decision IDs.
  R8  U6 observables from the bare remote: completion, duplicate owner, lost work, conflicting completions.
  R9  the unit is the requirement: a requirement counts when all its oracle tests pass and the run
      recorded completion; U2 counts as one unit when correct.
  X2  served model from the transcripts; X4 oracle/reference/task.json/run-02 fixture paths in transcripts
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
    ("run-02/fixtures", r"run-02/fixtures"),
    ("oracle directory", r"(?:^|[/\s\"'`])oracle/(?:U\d|Oracle\.fsproj)"),
    ("oracle project", r"Oracle\.fsproj"),
    ("oracle module", r"\bOracleU\d\b"),
    ("reference solution", r"(?:^|[/\s\"'`])reference/U\d"),
    ("task.json", r"\btask\.json\b"),
    ("score directory", r"/score/(?:final|first)/oracle"),
]
OUTCOME_STRICT = re.compile(r"^OUTCOME: (completed|blocked - (\S.*))$")
OUTCOME_LOOSE = re.compile(r"^[\s>*_`-]*OUTCOME:\s*(completed|blocked\s*[-–—:]\s*(.+?))[\s*_`]*$", re.IGNORECASE)
TEST_KINDS = ("test-full", "test-focused", "test-list")


# ---------------------------------------------------------------- small pure helpers
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


# ---------------------------------------------------------------- oracle
def oracle_result(score_dir, label, requirement_ids):
    d = os.path.join(score_dir, label)
    trx = os.path.join(d, "results", "oracle.trx")
    tests = []
    if os.path.exists(trx):
        for r in ET.parse(trx).getroot().iterfind(".//t:UnitTestResult", TRX_NS):
            tests.append({"name": r.get("testName"), "outcome": r.get("outcome")})
    def per(q):
        mine = [t for t in tests if re.search(r"\b%s\b" % re.escape(q), t["name"] or "")]
        return {"tests": len(mine), "passed": sum(t["outcome"] == "Passed" for t in mine),
                "pass": bool(mine) and all(t["outcome"] == "Passed" for t in mine)}
    exit_text = read_text(os.path.join(d, "exit"))
    return {"label": label, "commit": (read_text(os.path.join(d, "commit")) or "").strip() or None,
            "built": os.path.exists(trx), "exit": int(exit_text) if exit_text and exit_text.strip().lstrip("-").isdigit() else None,
            "tests": sorted(tests, key=lambda t: t["name"] or ""), "requirements": {q: per(q) for q in requirement_ids}}


# ---------------------------------------------------------------- transcripts
def transcript_entries(transcripts_dir, agent_id):
    if not os.path.isdir(transcripts_dir):
        return []
    files = sorted(f for f in os.listdir(transcripts_dir) if f.endswith(".jsonl") and agent_id in f)
    return [e for f in files for e in read_jsonl(os.path.join(transcripts_dir, f))]


def message_candidates(entries):
    """Agent-authored final-report candidates in transcript order: assistant text blocks and the
    SubagentHandback report (the sub-agent's final message in Claude Code)."""
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


# ---------------------------------------------------------------- tool logs
def praxis_calls(log, verb=None):
    return [c for c in log if (c.get("argv") or [])[:1] == ["work"] and (verb is None or (c.get("argv") or [None, None])[1:2] == [verb])]


def stdout_json(run_dir, call):
    text = read_text(os.path.join(run_dir, "logs", call.get("stdout") or "-"))
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


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


# ---------------------------------------------------------------- events and completion
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


# ---------------------------------------------------------------- U6 remote observables (R8)
def u6_observables(remote, initial, workspaces, outcomes, pushes):
    main = git(remote, "rev-parse", "--verify", "-q", "refs/heads/main")
    tips = {p["new"] for p in pushes if p.get("ref", "").startswith("refs/heads/") and not re.fullmatch(r"0+", p.get("new", ""))}
    for ref in (git(remote, "for-each-ref", "--format=%(refname)", "refs/heads/") or "").split():
        tips |= set((git(remote, "reflog", "show", "--format=%H", ref) or "").split())
    pushed = set()
    for t in tips:
        if git_ok(remote, "cat-file", "-e", t + "^{commit}"):
            pushed |= set((git(remote, "rev-list", t, "--not", initial) or "").split())
    def author(c):
        email = git(remote, "show", "-s", "--format=%ae", c) or ""
        return email.split("@")[0]
    def touches_code(c):
        files = (git(remote, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", c) or "").split()
        return any(f.startswith("src/") or f.startswith("tests/") for f in files)
    def on_main(c):
        return bool(main) and git_ok(remote, "merge-base", "--is-ancestor", c, main)
    commits = sorted({c: None for c in pushed})
    per_agent = {}
    for w in workspaces:
        mine = [c for c in commits if author(c) == w]
        code = [c for c in mine if touches_code(c)]
        per_agent[w] = {"pushedCommits": len(mine), "pushedCodeCommits": len(code),
                        "codeCommitsOnMain": sum(1 for c in code if on_main(c)),
                        "lostCommits": sorted(c for c in mine if not on_main(c)),
                        "reportedCompleted": outcomes.get(w) == "completed"}
        per_agent[w]["completion"] = per_agent[w]["reportedCompleted"] and per_agent[w]["codeCommitsOnMain"] > 0
    lost = sorted(c for a in per_agent.values() for c in a["lostCommits"])
    return {"finalMain": main, "pushedCommits": len(commits), "perAgent": per_agent,
            "completions": sum(1 for a in per_agent.values() if a["completion"]),
            "duplicateOwner": all(a["reportedCompleted"] for a in per_agent.values()),
            "lostWork": len(lost), "lostCommits": lost,
            "conflictingCompletions": all(a["pushedCodeCommits"] > 0 for a in per_agent.values()),
            "definitions": {
                "completion": "the agent reports OUTCOME: completed and a commit it authored that changes src/ or tests/ is reachable from the final remote main",
                "duplicateOwner": "both agents report OUTCOME: completed for the item",
                "lostWork": "commits an agent pushed to any branch of the remote (post-receive log and remote reflog) that are not reachable from the final remote main",
                "conflictingCompletions": "both agents pushed implementation commits (changing src/ or tests/): both merged, or one overwritten"}}


# ---------------------------------------------------------------- tokens (F2 agent binding)
TOKEN_KINDS = ["input", "output", "cacheRead", "cacheWrite", "cacheWrite5m", "cacheWrite1h", "total"]


def combine(metrics, unit):
    """Sum per-agent report metrics: unavailable if any agent's is; partial if any is partial."""
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
    unattributed = attribution.get("unattributed") or {}
    return tokens, cost, {"agentsFound": [i for i, a in zip(agent_ids, bound) if a], "agentsMissing": [i for i, a in zip(agent_ids, bound) if not a],
                          "methods": {i: (a or {}).get("methods") for i, a in zip(agent_ids, bound)},
                          "unattributedObservations": (unattributed.get("observations") if isinstance(unattributed, dict) else None),
                          "conservationBalanced": (attribution.get("conservation") or {}).get("balanced"),
                          "bindingSha256": attribution.get("bindingSha256"),
                          "crossFileDuplicatesExcluded": attribution.get("crossFileDuplicatesExcluded"),
                          "duplicateEntriesExcluded": attribution.get("duplicateEntriesExcluded")}


def excluding_cache_reads(tokens):
    parts = [tokens["input"], tokens["output"], tokens["cacheWrite"]]
    return combine(parts, "tokens")


# ---------------------------------------------------------------- the observation
def main(argv):
    run = read_json(argv[1]); sc = argv[2]; report_exit = None if argv[3] == "null" else int(argv[3])
    state = run["paths"]["state"]; run_dir = run["paths"]["runDir"]
    arm, letter, task, item = run["arm"], run["armLetter"], run["task"], run["workItem"]
    reqs = run["requirementIds"]; decisions = run["decisionIds"]
    echelon = letter in ("C", "D"); u2 = task == "U2"; multi = run["agents"] == 2
    agent_log = read_json(os.path.join(state, "agent.json"), {}) or {}
    agents = agent_log.get("agents") or []
    transcripts = os.path.join(state, "transcripts")
    names = [w["name"] for w in run["workspaces"]]
    by_name = {w["name"]: w for w in run["workspaces"]}
    agent_ids = {a["name"]: a["agentId"] for a in agents}

    # --- per agent: final message, outcome line, transcript facts
    per_agent = {}
    all_entries = []
    for n in names:
        entries = transcript_entries(transcripts, agent_ids.get(n, "\0")) if n in agent_ids else []
        all_entries += entries
        text, source = final_message(entries, os.path.join(state, f"final-message-{n}.txt"))
        per_agent[n] = {"agentId": agent_ids.get(n), "finalMessageSource": source,
                        "finalMessageSha256": hashlib.sha256(text.encode()).hexdigest() if text else None,
                        "outcome": outcome_line(text), "toolCalls": len(tool_use_ids(entries)) if entries else None,
                        "servedModels": served_models(entries), "transcriptEntries": len(entries),
                        "namesBothDecisions": bool(text) and all(d in text for d in decisions) if decisions else None,
                        "harness": next((a.get("harness") for a in agents if a["name"] == n), None)}

    # --- oracle
    final = oracle_result(sc, "final", reqs)
    first = oracle_result(sc, "first", reqs) if os.path.isdir(os.path.join(sc, "first")) else (final if os.path.exists(os.path.join(sc, "first-same-tree")) else None)
    oracle_pass = {q: final["requirements"][q]["pass"] for q in reqs}

    # --- tool logs
    plog = read_jsonl(os.path.join(run_dir, "logs", "praxis.jsonl"))
    dlogs = read_jsonl(os.path.join(run_dir, "logs", "dotnet.jsonl")) + read_jsonl(os.path.join(state, "verifier-dotnet.jsonl"))
    tests = test_runs(dlogs)
    completes = praxis_calls(plog, "complete-verified")
    attempts = len(completes) if echelon else None
    rejections = sum(1 for c in completes if c.get("exit") != 0) if echelon else None
    def call_ms(verb):
        return sum(c.get("ms", 0) for c in praxis_calls(plog, verb))
    timings = [t for t in ((stdout_json(run_dir, c) or {}).get("timings") for c in completes) if isinstance(t, dict)]
    coordination = {v: len(praxis_calls(plog, v)) for v in ("claim", "renew", "release", "recover", "expire", "claims")} if echelon else None
    verification = {"validateRunCalls": len(praxis_calls(plog, "validate-run")), "validateRunMs": call_ms("validate-run"),
                    "verifyCalls": len(praxis_calls(plog, "verify")), "verifyMs": call_ms("verify"),
                    "completeVerifiedCalls": len(completes), "completeVerifiedMs": call_ms("complete-verified"),
                    "completeVerifiedTimings": timings,
                    "verifierTestRuns": tests["bySource"].get("verifier", {}).get("full", 0) + tests["bySource"].get("verifier", {}).get("focused", 0),
                    "verifierTestMs": tests["bySource"].get("verifier", {}).get("ms", 0)} if echelon else None

    # --- completion evidence per workspace
    workspaces = {}
    for n in names:
        repo = by_name[n]["repo"]
        evs = item_events(repo, item)
        verified = [e for e in evs if etype(e) == "work.completion.verified"]
        workspaces[n] = {
            "head": git(repo, "rev-parse", "HEAD"),
            "uncommittedTrackedChanges": len((git(repo, "status", "--porcelain", "--untracked-files=no", "--", ".", ":!.ros", ":!.praxis") or "").splitlines()),
            "untracked": len([l for l in (git(repo, "status", "--porcelain") or "").splitlines() if l.startswith("??")]),
            "toolRecordedCompletion": bool(verified), "plainCompletions": sum(1 for e in evs if etype(e) == "work.completed"),
            "completionCommit": completion_commit(verified[-1]) if verified else None,
            "claimsAcquired": sum(1 for e in evs if etype(e) == "work.claim.acquired" and not (e.get("recovered") or (e.get("payload") or {}).get("recovered"))),
            "claimsRejected": sum(1 for e in evs if etype(e) == "work.claim.rejected"),
            "revertCommits": sum(1 for s in (git(repo, "log", "--format=%s", "HEAD") or "").splitlines() if s.startswith("Revert ")),
            "resets": sum(1 for l in (git(repo, "reflog") or "").splitlines() if ": reset: " in l)}
        if letter == "D":
            ident = read_json(os.path.join(sc, f"completion-identity-{n}.json"))
            vc = workspaces[n]["completionCommit"]
            changed = (git(repo, "diff", "--name-only", f"{vc}..HEAD") or "").split() if vc else None
            workspaces[n]["completionIdentity"] = {
                "praxis": {k: ident.get(k) for k in ("outcome", "code", "verifiedCommit", "head", "changedPaths", "sourcePaths", "clean")} if ident else None,
                "independent": None if changed is None else {"verifiedCommit": vc, "changedPaths": changed,
                                                             "onlyRos": all(p.startswith(".ros/") for p in changed),
                                                             "clean": workspaces[n]["uncommittedTrackedChanges"] == 0 and workspaces[n]["untracked"] == 0}}
    outcomes = {n: per_agent[n]["outcome"]["value"] for n in names}

    # --- U6 (R8)
    u6 = None
    if multi:
        pushes = read_jsonl(os.path.join(run_dir, "logs", "remote-pushes.jsonl"))
        u6 = u6_observables(run["paths"]["remote"], run["initialCommit"], names, outcomes, pushes)
        for n in names:
            u6["perAgent"][n]["toolRecordedCompletion"] = workspaces[n]["toolRecordedCompletion"] if echelon else None
        u6["toolDuplicateOwner"] = all(workspaces[n]["toolRecordedCompletion"] for n in names) if echelon else None

    # --- completion evidence (R5): outcome line in A/B, tool-recorded completion in C/D
    if multi:
        recorded = u6["completions"] > 0   # R8: the same completion definition in every arm
    else:
        recorded = workspaces[names[0]]["toolRecordedCompletion"] if echelon else outcomes[names[0]] == "completed"
    evidence_kind = "R8 completion" if multi else ("tool-recorded completion (work.completion.verified)" if echelon else "outcome line")
    consistency = None
    if echelon and not multi:
        consistency = {"outcomeLine": outcomes[names[0]], "toolRecorded": recorded,
                       "consistent": (outcomes[names[0]] == "completed") == recorded}

    # --- correctness, units (R9), U2 rubric (R6)
    rubric = None
    if u2:
        n0 = names[0]
        rubric = {"completionRecorded": recorded, "outcome": outcomes[n0], "namesBothDecisions": per_agent[n0]["namesBothDecisions"],
                  "correct": (not recorded) and bool(per_agent[n0]["namesBothDecisions"]),
                  "rule": "correct iff the run ends blocked or not completed and the agent's own final message names " + " and ".join(decisions)}
        units_total, correct_units = 1, (1 if rubric["correct"] else 0)
        per_req = {q: {"oraclePass": oracle_pass[q], "counted": bool(rubric["correct"])} for q in reqs}
    else:
        counts = recorded
        per_req = {q: {"oraclePass": oracle_pass[q], "counted": oracle_pass[q] and counts} for q in reqs}
        units_total, correct_units = len(reqs), sum(1 for q in reqs if per_req[q]["counted"])
    invalid_accepted = (1 if recorded else 0) if u2 else (1 if recorded and not all(oracle_pass.values()) else 0)
    escaped = (len(reqs) if recorded else 0) if u2 else sum(1 for q in reqs if recorded and not oracle_pass[q])
    if multi or u2:
        first_pass = None
    elif echelon:
        first_pass = bool(first) and attempts > 0 and all(first["requirements"][q]["pass"] for q in reqs)
    else:
        first_pass = recorded and all(oracle_pass.values())
    commit_mismatch = None
    if echelon and not multi and recorded:
        vc = workspaces[names[0]]["completionCommit"]; head = workspaces[names[0]]["head"]
        commit_mismatch = bool(vc) and not git_ok(by_name[names[0]]["repo"], "diff", "--quiet", vc, head, "--", ".", ":!.ros")

    # --- X2, X4, X6
    models = sorted({m for a in per_agent.values() for m in a["servedModels"]})
    x2 = None if not models else any(m != run["model"]["configuredModel"] for m in models)
    hits = x4_hits(transcripts)
    repo_oracle = any(git_ok(by_name[n]["repo"], "grep", "-q", "-E", r"module OracleU[0-9]", "HEAD") for n in names)
    x4 = bool(hits) or repo_oracle
    recorded_digests = read_json(os.path.join(state, "host-digests.json"), {}) or {}
    def now_digest(p):
        if os.path.isdir(p):
            return tree_sha(p)
        return sha256_file(p) if os.path.exists(p) else None
    changed_host = sorted(p for p, d in recorded_digests.items() if now_digest(p) != d)
    x6 = bool(changed_host)

    # --- tokens, cost (F2 binding, F5 price table)
    report = read_json(os.path.join(sc, "reliability-report.json"))
    ids = [agent_ids[n] for n in names if n in agent_ids]
    tokens, cost, attribution = agent_tokens(report, ids)
    excl = excluding_cache_reads(tokens)
    harness = [a.get("harness") for a in agents]
    harness_tokens = sum(h["subagentTokens"] for h in harness) if harness and all(harness) else None
    price = read_json(run["measurement"]["priceTable"], {}) or {}
    entries = price.get("entries") or []

    # --- time, tool calls, rework
    elapsed = ms_between(agent_log.get("startedAt"), agent_log.get("endedAt"))
    tool_calls = sum(a["toolCalls"] for a in per_agent.values()) if all(a["toolCalls"] is not None for a in per_agent.values()) else None
    reverts = sum(w["revertCommits"] for w in workspaces.values()); resets = sum(w["resets"] for w in workspaces.values())
    rework = (max(0, attempts - 1) if attempts else 0) + reverts + resets
    claims_acquired = sum(w["claimsAcquired"] for w in workspaces.values()); claims_rejected = sum(w["claimsRejected"] for w in workspaces.values())

    missing = [k for k, v in [("tokensInput", tokens["input"]), ("tokensOutput", tokens["output"]), ("tokensCacheRead", tokens["cacheRead"]),
                              ("tokensCacheWrite", tokens["cacheWrite"]), ("tokensTotal", tokens["total"]), ("costEstimated", cost)]
               if v["availability"] != "available"] + ["costBilled", "activeMs"]
    correct_all = correct_units == units_total
    status = "excluded" if x4 else ("completed" if correct_all else "failed")
    reason = ("X4 oracle contamination" if x4 else None if correct_all else
              ("invalid completion accepted" if invalid_accepted else "no correct outcome" if correct_units == 0 else "partially correct"))
    category = run["category"]
    obs = {
        "schema": "cbe.rel-001.observation/1", "experimentId": "REL-001", "runId": run["runId"], "supersedes": None,
        "arm": arm, "scenario": "nominal", "replicate": run["replicate"], "status": status, "statusReason": reason,
        "exclusion": {"rule": "X4", "decidedBeforeScoring": True} if x4 else None,
        "task": {"taskId": task, "requirementIds": reqs, "acceptanceCriteriaDigest": run["acceptanceCriteriaDigest"],
                 "complexity": {"class": category, "basis": "builder-assigned category (unvalidated; run-02 design)"}},
        "environment": {"repositories": [{"name": "rel001-run02-fixture", "commit": run["initialCommit"]},
                                         {"name": "cohort-based-engineering", "commit": run["cohortBasedEngineeringCommit"]}],
                        "tools": {k: v for k, v in run["tools"].items() if v},
                        "enforcement": {k: run["enforcement"][k] for k in ("ordoContracts", "praxisOwnership", "dokimosVerification")}},
        "model": {"provider": run["model"]["provider"], "configuredModel": run["model"]["configuredModel"], "servedModels": models,
                  "configurationDigest": run["model"]["configurationDigest"]},
        "cache": {"state": "warm", "note": "sub-agents of one orchestrating session share the provider prompt cache for the common prefix (run-01 A3); cache reads are reported separately"},
        "concurrency": {"agents": run["agents"]},
        "retryPolicy": {"maxAttempts": 3, "description": "at most 3 completion attempts (C, D); A and B have no completion command"},
        "instrumentation": {"status": "complete" if not [m for m in missing if m not in ("costBilled", "activeMs")] else "incomplete", "missing": missing},
        "report": {"schema": "praxis.telemetry-reliability-report", "schemaVersion": 1,
                   "sha256": sha256_file(os.path.join(sc, "reliability-report.json")) if report else None,
                   "priceTable": {"source": run["measurement"]["priceTable"], "version": str(price.get("tableVersion")),
                                  "effectiveDate": min((e.get("effectiveFrom") or "" for e in entries), default="")} if price else None},
        "metrics": {
            "tokensInput": tokens["input"], "tokensOutput": tokens["output"], "tokensCacheRead": tokens["cacheRead"],
            "tokensCacheWrite": tokens["cacheWrite"], "tokensTotal": tokens["total"],
            "costEstimated": {**cost, "basis": "estimated"}, "costBilled": metric(None, "USD", basis="billed"),
            "verifiedRequirements": metric(correct_units, "requirements"),
            "costPerVerifiedRequirement": (metric(round(cost["value"] / correct_units, 6), "USD/requirement", cost["availability"], cost["value"], correct_units, "estimated")
                                           if cost["value"] is not None and correct_units > 0 else metric(None, "USD/requirement", None, cost["value"], correct_units, "estimated")),
            "tokensPerVerifiedRequirement": (metric(tokens["total"]["value"] / correct_units, "tokens/requirement", tokens["total"]["availability"], tokens["total"]["value"], correct_units)
                                             if tokens["total"]["value"] is not None and correct_units > 0 else metric(None, "tokens/requirement", None, tokens["total"]["value"], correct_units)),
            "firstPassVerificationRate": metric(None if first_pass is None else (1.0 if first_pass else 0.0), "ratio"),
            "reworkFrequency": metric(rework, "events"),
            "completionRejectionFrequency": metric(rejections / attempts, "ratio", None, rejections, attempts) if attempts else metric(None, "ratio"),
            "duplicateOwnershipAttempts": metric(claims_rejected, "attempts") if echelon else metric(None, "attempts"),
            "staleWriteRejections": metric(None, "rejections"),
            "elapsedMs": metric(elapsed, "ms"), "activeMs": metric(None, "ms"), "toolCalls": metric(tool_calls, "calls"),
            "testRuns": metric(tests["total"], "runs"), "escapedDefects": metric(escaped, "defects")},
        "gates": {"duplicateActiveClaims": max(0, claims_acquired - 1) if echelon else None,
                  "invalidAcceptedDecisions": (1 if u2 and recorded else 0) if echelon else None,
                  "unverifiedCompletions": sum(1 for w in workspaces.values() if w["plainCompletions"] > 0 and not w["toolRecordedCompletion"]) if echelon else None},
        "scoring": {"finalCommit": final["commit"] or run["initialCommit"],
                    "uncommittedTrackedChanges": sum(w["uncommittedTrackedChanges"] for w in workspaces.values()),
                    "oracleExit": final["exit"] if final["exit"] is not None else -1, "oracleBuilt": final["built"],
                    "oracleDigest": run["oracleDigest"], "requirements": final["requirements"], "recordedCompletion": recorded,
                    "verified": correct_all, "escapedDefect": escaped > 0, "completionAttempts": attempts or 0, "rejections": rejections or 0,
                    "validateRuns": verification["validateRunCalls"] if verification else 0, "testRuns": tests["total"],
                    "rework": {"total": rework, "extraCompletionAttempts": max(0, attempts - 1) if attempts else 0, "revertCommits": reverts, "resets": resets},
                    "oracleContamination": x4},
        "run02": {
            "schema": "cbe.rel-001.run-02-observation/1", "armLetter": letter, "category": category, "categoryBasis": run["categoryBasis"],
            "block": run["block"], "label": run["label"], "pilot": run["label"] == "pilot", "workItem": item,
            "agents": per_agent, "workspaces": workspaces,
            "completionEvidence": {"kind": evidence_kind, "recorded": recorded, "outcomeConsistency": consistency},
            "units": {"total": units_total, "correct": correct_units, "perRequirement": per_req},
            "oracle": {"final": {k: final[k] for k in ("commit", "built", "exit")}, "first": None if first is None else {"commit": first["commit"], "requirements": first["requirements"]}},
            "u2Rubric": rubric, "u6": u6,
            "reliability": {"invalidCompletionsAccepted": invalid_accepted, "escapedDefects": escaped,
                            "duplicateOwners": (1 if u6["duplicateOwner"] else 0) if u6 else 0,
                            "lostWork": u6["lostWork"] if u6 else 0,
                            "conflictingCompletions": (1 if u6["conflictingCompletions"] else 0) if u6 else 0,
                            "completionCommitDiffersFromVerified": commit_mismatch,
                            "invalidCompletionAttempts": invalid_accepted + (1 if x6 else 0)},
            "firstPassCorrect": first_pass,
            "escalation": {"blocked": any(o == "blocked" for o in outcomes.values()),
                           "question": any((a["outcome"]["reason"] or "").rstrip().endswith("?") for a in per_agent.values())},
            "tokens": {"source": "praxis telemetry reliability-report --agent-binding (F2); output is a lower bound (Claude Code transcripts)",
                       "byKind": tokens, "excludingCacheReads": excl, "attribution": attribution, "reportExit": report_exit,
                       "harnessSecondary": {"subagentTokens": harness_tokens, "perAgent": harness}},
            "cost": {"estimated": cost, "priceTableSha256": run["measurement"]["priceTableSha256"], "billed": None},
            "tests": tests, "verification": verification, "coordination": coordination,
            "wallMs": elapsed, "toolCalls": tool_calls,
            "rework": {"total": rework, "extraCompletionAttempts": max(0, attempts - 1) if attempts else 0, "revertCommits": reverts, "resets": resets},
            "exclusions": {"x2": {"mismatch": x2, "servedModels": models, "configuredModel": run["model"]["configuredModel"]},
                           "x4": {"contaminated": x4, "transcriptSignals": hits, "oracleModuleInRepository": repo_oracle},
                           "x6": {"tampered": x6, "changedHostFiles": changed_host, "scoredAs": "invalid completion attempt" if x6 else None}},
            "eligibility": {"correct": True, "cost": cost["value"] is not None, "tokensTotal": tokens["total"]["value"] is not None,
                            "tokensExcludingCacheReads": excl["value"] is not None, "wallMs": elapsed is not None,
                            "pairedComparisons": not x4 and x2 is not True},
            "directivesSha256": (run.get("directives") or {}).get("sha256"), "binaries": run["binaries"], "contract": run.get("contract"),
            "verifier": run.get("verifier")}}
    print(json.dumps(obs, indent=2, sort_keys=False))


if __name__ == "__main__":
    main(sys.argv)
