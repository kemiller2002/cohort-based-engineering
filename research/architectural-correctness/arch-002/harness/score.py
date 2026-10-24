#!/usr/bin/env python3
"""ARCH-002 observation builder (adapted from ARCH-001 harness/score.py; see ../PROVENANCE.md).

usage: python3 -I score.py RUN_JSON SCORE_DIR   -> one arch002.observation/1 document on stdout

ARCH-002 changes: fixture, model and the (fixture, task, model, replicate) block; brownfield baseline-delta
architecture (INTERFACES §3): a finding is NEW when the verifier did not mark it `preexisting` against the scoring
baseline (the base commit, same policy and probes); FIXED baseline keys are reported descriptively; architectural
acceptance = zero NEW DET findings of severity >= 2 (ARC-TRC-01 excluded); A3 superseded tests keyed by fixture/task.

Pure reads of the run's harness state (score directory, phase streams, ledger, integrity and contamination files)
and of the workspace's git object store (diff metrics). Copied unchanged from run-03 in substance: usage_by_message
(one usage record per message id, keeping the maximum output), usage_tokens (cache write split 5m/1h), priced,
the first-request cache measurement and the TRX reader. New: two requirements per trial (initial at S1, follow-up
at S2), architectural acceptance from the verifier report, diff/rework metrics, the submit ledger, the
cost cross-check against the stream's `result` event (total_cost_usd, modelUsage), X4/X5/X-integrity flags.

Definitions (preregistration draft):
  functional pass, R1: every InitialOracle test passes at S1 (the oracle built and ran >= 1 test).
  functional pass, R2: every FollowupOracle test passes at S2 AND every regression-subset InitialOracle test at S2.
  architectural acceptance at S_k: the verifier evaluated the commit (exit 0/1) and reported zero NEW DET findings
      of severity >= 2, ARC-TRC-01 excluded (full policy + probes + scoring baseline).
  requirement accepted = functional pass AND architectural acceptance.
  regression subset: oracle.json .regression (test names or name prefixes) when present, else tests whose name
      contains "Regression", else (no labels) every InitialOracle test.
  decision tests: oracle tests whose name contains a DEC- id (or oracle.json .decisionTests regex).
  conflict tests: tests whose name contains "CONFLICT" (or oracle.json .conflictTests regex); task.json .conflict.
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
TOKEN_KINDS = ["input", "output", "cacheRead", "cacheWrite", "cacheWrite5m", "cacheWrite1h"]
DONE_LINE = re.compile(r"^\s*`?ARCH002-DONE\s+([0-9a-fA-F]{7,40})`?\s*$")
DEC_ID = re.compile(r"DEC-[A-Za-z0-9][A-Za-z0-9-]*")


# ---------------------------------------------------------------- small pure helpers (run-03)
def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def read_jsonl(path):
    try:
        with open(path, errors="replace") as f:
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


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def parse_time(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
    except ValueError:
        return None


def ms_between(a, b):
    ta, tb = parse_time(a), parse_time(b)
    return int(round((tb - ta).total_seconds() * 1000)) if ta and tb else None


def rel_gap(a, b):
    return None if a is None or b is None or b == 0 else round(abs(a - b) / abs(b), 6)


# ---------------------------------------------------------------- oracle and visible tests
def trx_tests(path):
    if not os.path.exists(path):
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    return sorted(({"name": r.get("testName"), "outcome": r.get("outcome")} for r in root.iterfind(".//t:UnitTestResult", TRX_NS)),
                  key=lambda t: t["name"] or "")


def find_trx(d):
    hits = sorted(os.path.join(a, f) for a, _, fs in os.walk(d) for f in fs if f.endswith(".trx")) if os.path.isdir(d) else []
    return hits[0] if hits else None


def summarize(tests, ran):
    if tests is None:
        return {"ran": ran, "built": False, "total": 0, "passed": 0, "failed": 0, "allPass": False if ran else None}
    passed = sum(t["outcome"] == "Passed" for t in tests)
    return {"ran": ran, "built": True, "total": len(tests), "passed": passed, "failed": len(tests) - passed,
            "allPass": bool(tests) and passed == len(tests)}


def oracle_run(score_dir, label):
    d = os.path.join(score_dir, f"oracle-{label}")
    if not os.path.isdir(d):
        return None
    exit_text = (read_text(os.path.join(d, "exit")) or "").strip()
    tests = trx_tests(find_trx(os.path.join(d, "results")) or "")
    return {"label": label, "commit": (read_text(os.path.join(d, "commit")) or "").strip() or None,
            "kind": (read_text(os.path.join(d, "kind")) or "").strip() or None,
            "exit": int(exit_text) if exit_text.lstrip("-").isdigit() else exit_text or None,
            "missingOracle": exit_text == "missing", "tests": tests or [], **summarize(tests, exit_text not in ("", "missing"))}


def short_name(name):
    """The test name without its module/namespace qualification (TRX names are "Module.test name")."""
    m = re.match(r"^([\w.]+)\.(\S.*)$", name or "")
    return m.group(2) if m else (name or "")


def subset(run, names_or_prefixes=None, pattern=None):
    """A summary of the tests of an oracle run selected by explicit names/prefixes or a regex."""
    if run is None:
        return None
    if names_or_prefixes:
        pick = [t for t in run["tests"] if any(x.startswith(n) for n in names_or_prefixes for x in (t["name"] or "", short_name(t["name"])))]
    elif pattern:
        pick = [t for t in run["tests"] if re.search(pattern, t["name"] or "")]
    else:
        pick = list(run["tests"])
    s = summarize(pick if run["built"] else None, run["ran"])
    return {**s, "tests": [t["name"] for t in pick]}


# ARCH-001 Amendment A3, built in: an initial-oracle test that a task's follow-up deliberately supersedes is not a
# regression test. "Superseded" = the InitialOracle tests that FAIL on the sealed follow-up-good reference
# (harness/superseded.sh writes harness/superseded.json keyed "<fixture>/<task>"). Removed from the phase-2
# regression set (labelled or fallback).
def superseded(task_key):
    path = os.environ.get("ARCH002_SUPERSEDED", os.path.join(os.path.dirname(os.path.abspath(__file__)), "superseded.json"))
    doc = read_json(path, {}) or {}
    return tuple((doc.get(task_key) or {}).get("superseded") or ())


def regression_subset(run, manifest, task_key=None):
    if run is None:
        return None
    drop = set(superseded(task_key)) if task_key else set()
    if drop:
        run = {**run, "tests": [t for t in run["tests"] if (t["name"] or "") not in drop and short_name(t["name"]) not in drop]}
    if manifest.get("regression"):
        return {**subset(run, names_or_prefixes=manifest["regression"]), "basis": "oracle.json regression list"}
    if any("regression" in (t["name"] or "").lower() for t in run["tests"]):
        return {**subset(run, pattern=r"(?i)regression"), "basis": "test names containing 'Regression'"}
    return {**subset(run), "basis": "no labels: every InitialOracle test" + (" not superseded by the follow-up (amendment A3)" if drop else "")}


def visible_run(score_dir, label):
    d = os.path.join(score_dir, f"visible-{label}")
    if not os.path.isdir(d):
        return None
    tests = trx_tests(find_trx(os.path.join(d, "results")) or "")
    return {"commit": (read_text(os.path.join(d, "commit")) or "").strip(), "exit": (read_text(os.path.join(d, "exit")) or "").strip(),
            "tests": tests or [], **summarize(tests, True)}


def broken_visible(p1, p2):
    """Visible tests that passed at S1 and do not pass (or no longer exist) at S2."""
    if not p1 or not p2:
        return None
    before = {t["name"] for t in p1["tests"] if t["outcome"] == "Passed"}
    after = {t["name"]: t["outcome"] for t in p2["tests"]}
    broken = sorted(n for n in before if after.get(n) != "Passed")
    return {"count": len(broken), "names": broken, "missingAtS2": sorted(n for n in broken if n not in after)}


# ---------------------------------------------------------------- architecture (verifier reports)
def fkey(f):
    """The baseline key (INTERFACES §3): rule, file, symbol, enclosing module; line ignored."""
    return (f.get("ruleId") or "", f.get("file") or "", f.get("symbol") or "", f.get("scope") or "")


def sev_weighted(fs):
    return sum(f.get("severity") or 0 for f in fs)


def by_rule(fs):
    return {r: sum(1 for f in fs if f.get("ruleId") == r) for r in sorted({f.get("ruleId") for f in fs})}


def arch_run(score_dir, label):
    d = os.path.join(score_dir, f"arch-{label}")
    if not os.path.isdir(d):
        return None
    exit_text = (read_text(os.path.join(d, "exit")) or "").strip()
    report = read_json(os.path.join(d, "report.json"))
    findings = (report or {}).get("findings") or []
    det = [f for f in findings if f.get("class") == "DET" and f.get("ruleId") != "ARC-TRC-01"]
    trc = [f for f in findings if f.get("ruleId") == "ARC-TRC-01"]
    heu = [f for f in findings if f.get("class") == "HEU"]
    baseline = (report or {}).get("baseline")
    evaluable = exit_text in ("0", "1") and report is not None and baseline is not None
    new = [f for f in det if not f.get("preexisting")]
    pre = [f for f in det if f.get("preexisting")]
    new2 = [f for f in new if (f.get("severity") or 0) >= 2]
    fixed = [k for k in ((baseline or {}).get("fixed") or []) if k.get("ruleId") != "ARC-TRC-01" and not str(k.get("ruleId", "")).startswith("ARC-HEU")]
    ev = lambda v: v if evaluable else None
    return {"label": label, "commit": (read_text(os.path.join(d, "commit")) or "").strip() or None,
            "exit": exit_text or None, "evaluable": evaluable, "probesApplied": (read_text(os.path.join(d, "probes")) or "").strip() == "true",
            "baselineApplied": baseline is not None, "baseline": None if baseline is None else {k: baseline.get(k) for k in ("id", "sha256", "findings", "matched")},
            "verifier": (report or {}).get("verifier"), "policy": (report or {}).get("policy"),
            "errors": (report or {}).get("errors") or [],
            # all DET findings (brownfield total, descriptive)
            "det": ev(len(det)), "detSev2plus": ev(sum(1 for f in det if (f.get("severity") or 0) >= 2)),
            "detSeverityWeighted": ev(sev_weighted(det)),
            # baseline-delta (the ARCH-002 measures)
            "detNew": ev(len(new)), "detNewSev2plus": ev(len(new2)), "detNewSeverityWeighted": ev(sev_weighted(new)),
            "newByRule": ev(by_rule(new)), "detPreexisting": ev(len(pre)), "detFixed": ev(len(fixed)), "fixedByRule": ev(by_rule(fixed)),
            "byRule": by_rule(det),
            "heu": ev(len(heu)), "heuNew": ev(sum(1 for f in heu if not f.get("preexisting"))), "trc": ev(len(trc)),
            "accept": (len(new2) == 0) if evaluable else False,
            "newFindings": [{k: f.get(k) for k in ("ruleId", "class", "severity", "project", "file", "line", "symbol", "scope")} for f in new],
            "fixedKeys": fixed,
            "findings": [{k: f.get(k) for k in ("ruleId", "class", "severity", "project", "file", "line", "symbol", "scope", "preexisting")} for f in det + trc]}


def multiset_minus(xs, ys):
    """Elements of xs not matched by ys (multiset difference, order of xs kept)."""
    left = {}
    for y in ys:
        left[y] = left.get(y, 0) + 1
    out = []
    for x in xs:
        if left.get(x, 0) > 0:
            left[x] -= 1
        else:
            out.append(x)
    return out


def new_since_s1(a1, a2):
    """DET findings at S2 whose key is not at S1 (multiset; line ignored), ARC-TRC-01 excluded (descriptive)."""
    if not a1 or not a2 or not a1["evaluable"] or not a2["evaluable"]:
        return None
    keys = lambda a: [fkey(f) for f in a["findings"] if f["ruleId"] != "ARC-TRC-01"]
    new = multiset_minus(keys(a2), keys(a1))
    return {"count": len(new), "keys": [{"ruleId": r, "file": f, "symbol": s, "scope": sc} for r, f, s, sc in new]}


# ---------------------------------------------------------------- diffs (phase 1: base -> S1; phase 2: follow-up commit -> S2)
def numstat(repo, a, b, pathspec=()):
    out = git(repo, "diff", "--no-renames", "--numstat", a, b, "--", *pathspec) or ""
    rows = []
    for line in out.splitlines():
        add, dele, path = line.split("\t", 2)
        rows.append((path, int(add) if add.isdigit() else 0, int(dele) if dele.isdigit() else 0))
    return rows


def name_status(repo, a, b):
    out = git(repo, "diff", "--no-renames", "--name-status", a, b) or ""
    return {p: s for s, p in (l.split("\t", 1) for l in out.splitlines() if "\t" in l)}


def line_count(repo, commit, path):
    text = git(repo, "show", f"{commit}:{path}")
    return len(text.splitlines()) if text is not None else 0


def diff_metrics(repo, a, b):
    if not a or not b or git(repo, "cat-file", "-e", f"{a}^{{commit}}") is None or git(repo, "cat-file", "-e", f"{b}^{{commit}}") is None:
        return None
    rows = numstat(repo, a, b)
    status = name_status(repo, a, b)
    pre = set((git(repo, "ls-tree", "-r", "--name-only", a) or "").splitlines())
    def part(prefix):
        sel = [(p, ad, de) for p, ad, de in rows if p.startswith(prefix)]
        pre_rows = [(p, ad, de) for p, ad, de in sel if p in pre]
        rewritten = sorted(p for p, ad, de in pre_rows if status.get(p) == "M" and de > 0.5 * max(1, line_count(repo, a, p)))
        return {"filesModified": sum(1 for p, _, _ in sel if status.get(p) == "M"),
                "filesAdded": sum(1 for p, _, _ in sel if status.get(p) == "A"),
                "filesDeleted": sum(1 for p, _, _ in sel if status.get(p) == "D"),
                "linesAdded": sum(ad for _, ad, _ in sel), "linesDeleted": sum(de for _, _, de in sel),
                "preexistingRewritten": len(rewritten), "preexistingRewrittenFiles": rewritten,
                "rework": sum(ad + de for _, ad, de in pre_rows)}
    return {"from": a, "to": b, "all": part(""), "src": part("src/"), "tests": part("tests/")}


# ---------------------------------------------------------------- tokens and cost (run-03 M1/M2, adapted to the stream)
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
            best[key] = (e.get("timestamp") or "", msg["usage"], msg.get("model"), prev[3] if prev else len(best))
    return [r[:3] for r in sorted(best.values(), key=lambda r: r[3])]


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


def phase_cost(events, price, model, transcript=()):
    """Usage comes from the session transcript (final per-message usage) when present: the stream's assistant events
    carry the message-start output count only (a lower bound, verified in the live smoke). The result event (cost,
    modelUsage) always comes from the stream."""
    usage_events = list(transcript) if any(e.get("type") == "assistant" for e in transcript) else events
    rows = [r for r in usage_by_message(usage_events)]
    main = [r for r in rows if r[2] == model]
    totals = {k: sum(usage_tokens(u)[k] for _, u, _ in main) for k in TOKEN_KINDS}
    totals["total"] = totals["input"] + totals["output"] + totals["cacheRead"] + totals["cacheWrite"]
    p = price_entry(price, "anthropic", model)
    recomputed = priced(totals, p) if main else 0.0
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    mu = (result or {}).get("modelUsage") or {}
    mu_main = mu.get(model) or {}
    others = {m: {"costUsd": v.get("costUSD"), "input": v.get("inputTokens"), "output": v.get("outputTokens")} for m, v in sorted(mu.items()) if m != model}
    reported_total = (result or {}).get("total_cost_usd")
    mu_tokens = None
    if mu_main:
        mu_tokens = {"input": mu_main.get("inputTokens") or 0, "output": mu_main.get("outputTokens") or 0,
                     "cacheRead": mu_main.get("cacheReadInputTokens") or 0, "cacheWrite": mu_main.get("cacheCreationInputTokens") or 0}
        mu_tokens["total"] = sum(mu_tokens.values())
    first = usage_tokens(main[0][1]) if main else None
    prompt = totals["input"] + totals["cacheRead"] + totals["cacheWrite"]
    cost = reported_total if reported_total is not None else (round(recomputed + sum((o["costUsd"] or 0) for o in others.values()), 6) if main else None)
    return {
        "costUsd": cost,
        "costSource": "result.total_cost_usd" if reported_total is not None else ("recomputed from stream (no result event)" if main else None),
        "recomputedMainModelUsd": recomputed if main else None,
        "reportedMainModelUsd": mu_main.get("costUSD"),
        "otherModels": others,
        "tokens": totals, "requests": len(main), "requestsOtherModels": len(rows) - len(main),
        "usageSource": "session transcript" if usage_events is not events else "stream (output tokens are a lower bound)",
        "streamOutputTokensLowerBound": sum(usage_tokens(u)["output"] for _, u, m in usage_by_message(events) if m == model),
        "crossCheck": {"mainModelCostRelativeGap": rel_gap(recomputed if main else None, mu_main.get("costUSD")),
                       "totalCostVsModelUsageSumGap": rel_gap(reported_total, sum((v.get("costUSD") or 0) for v in mu.values()) if mu else None),
                       "tokensTotalRelativeGap": rel_gap(totals["total"], (mu_tokens or {}).get("total")),
                       "agrees": (lambda g: g is not None and g <= 0.01)(rel_gap(recomputed if main else None, mu_main.get("costUSD"))),
                       "basis": "stream usage deduplicated by message id, priced with the harness price table, vs the result event's modelUsage"},
        "coldEquivalentUsd": priced(totals, p, p["input"]) if main and p else None,
        "cache": {"firstRequestCacheRead": first["cacheRead"] if first else None, "firstRequestCacheWrite": first["cacheWrite"] if first else None,
                  "firstRequestCold": (first["cacheRead"] == 0) if first else None,
                  "cacheReadShare": round(totals["cacheRead"] / prompt, 6) if prompt else None},
        "resultEvent": None if result is None else {k: result.get(k) for k in ("subtype", "is_error", "num_turns", "duration_ms", "duration_api_ms", "stop_reason", "terminal_reason")}}


def tool_activity(events):
    seen, uses = set(), []
    for e in events:
        if e.get("type") != "assistant":
            continue
        for b in (e.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") not in seen:
                seen.add(b.get("id"))
                uses.append((b.get("name"), b.get("input") or {}))
    commands = [u.get("command") or "" for n, u in uses if n == "Bash"]
    word = lambda w: re.compile(r"(?:^|[\s;&|()`$])" + w + r"(?=$|[\s;&|()`])", re.M)
    count = lambda rx: sum(1 for c in commands if rx.search(c))
    by = {}
    for n, _ in uses:
        by[n] = by.get(n, 0) + 1
    return {"toolCalls": len(uses), "byTool": dict(sorted(by.items())),
            "testExecutions": sum(1 for c in commands if re.search(r"\bdotnet\s+test\b", c)),
            "buildExecutions": sum(1 for c in commands if re.search(r"\bdotnet\s+build\b", c)),
            "verificationExecutions": {"ordo": count(word("ordo")), "archcheck": count(word("archcheck")), "submit": count(word("submit"))}}


def final_line(text):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    m = DONE_LINE.match(lines[-1]) if lines else None
    anywhere = [DONE_LINE.match(l) for l in lines]
    return {"present": bool(m), "gitHead": m.group(1) if m else None,
            "presentNotLast": (not m) and any(anywhere)}


def transcript_events(phase_dir):
    d = os.path.join(phase_dir, "transcripts")
    return [e for f in (sorted(os.listdir(d)) if os.path.isdir(d) else []) if f.endswith(".jsonl") for e in read_jsonl(os.path.join(d, f))]


# ---------------------------------------------------------------- per phase
def phase_block(run, k, state, price, ledger):
    p = os.path.join(state, f"phase{k}")
    if not os.path.isdir(p):
        return None
    events = read_jsonl(os.path.join(p, "stream.jsonl"))
    launch = read_json(os.path.join(p, "launch.json"), {}) or {}
    stamps = [t for t in (parse_time(e.get("timestamp")) for e in events) if t]
    last = max(stamps).isoformat().replace("+00:00", "Z") if stamps else None
    ph = (run.get("phases") or {}).get(str(k)) or {}
    subs = [r for r in ledger if r.get("phase") == k and r.get("verdict") in ("PASS", "FAIL")]
    integ = read_json(os.path.join(p, "integrity.json"), {}) or {}
    cont = read_json(os.path.join(p, "contamination.json"), {}) or {}
    text = read_text(os.path.join(p, "final-message.txt"))
    timed_out = bool(launch.get("timedOut")) or bool(ph.get("timedOut"))
    return {"sessionId": launch.get("sessionId"), "nonce": launch.get("nonce"), "exit": launch.get("exit", ph.get("runnerExit")),
            "timedOut": timed_out, "brief": ph.get("brief"), "startCommit": ph.get("startCommit"), "endHead": ph.get("endHead"),
            "startedAt": launch.get("startedAt") or ph.get("startedAt"), "lastEventAt": last,
            "wallMs": ms_between(launch.get("startedAt") or ph.get("startedAt"), last or launch.get("endedAt") or ph.get("endedAt")),
            **phase_cost(events, price, run["model"], transcript_events(p)), **tool_activity(events),
            "finalLine": final_line(text), "finalMessageSha256": hashlib.sha256(text.encode()).hexdigest() if text else None,
            "submit": {"attempts": len(subs), "verdicts": [r["verdict"] for r in subs], "passed": any(r["verdict"] == "PASS" for r in subs),
                       "firstVerdict": subs[0]["verdict"] if subs else None, "firstCommit": subs[0]["gitHead"] if subs else None,
                       "lastCommit": subs[-1]["gitHead"] if subs else None,
                       "refused": sum(1 for r in ledger if r.get("phase") == k and r.get("verdict") == "REFUSED"),
                       "records": subs},
            "integrity": {"tampered": bool(integ.get("tampered")), "changed": integ.get("changed") or []},
            "contamination": {"contaminated": bool((cont.get("x4") or {}).get("contaminated")), "hits": (cont.get("x4") or {}).get("hits") or [],
                              "advisory": cont.get("advisory") or []}}


# ---------------------------------------------------------------- the observation
def main(argv):
    run = read_json(argv[1]); sc = argv[2]
    state, repo = run["paths"]["state"], run["paths"]["repo"]
    sealed = os.environ.get("ARCH002_SEALED_DIR") or os.path.join("/home/user/arch002-sealed", run["fixture"])
    manifest = read_json(os.path.join(sealed, "oracle", run["task"], "oracle.json"), {}) or {}
    price = read_json(os.path.join(state, "pristine", "price-table.json"), {}) or {}
    ledger = read_jsonl(os.path.join(state, "submit-ledger.jsonl"))
    commits = read_json(os.path.join(sc, "commits.json"), {}) or {}
    tj = run.get("task_json") or {}
    arm = run["arm"]

    phases = {str(k): phase_block(run, k, state, price, ledger) for k in (1, 2)}
    o = {lab: oracle_run(sc, lab) for lab in ("p1", "p1-first", "p2", "p2-regression", "p2-first")}
    reg = regression_subset(o["p2-regression"], manifest, run["taskKey"])
    private = read_json(os.path.join(sealed, "task-private", run["task"] + ".json"), {}) or {}
    a = {lab: arch_run(sc, lab) for lab in ("p1", "p2", "p2-initial-contract")}
    vis = {lab: visible_run(sc, lab) for lab in ("p1", "p2")}

    def functional(k):
        if k == 1:
            return bool(o["p1"] and o["p1"]["allPass"])
        return bool(o["p2"] and o["p2"]["allPass"] and reg and reg["allPass"])
    def arch_accept(k):
        r = a[f"p{k}"]
        return bool(r and r["accept"])
    reqs = [{"id": f"R{k}", "phase": k, "commit": commits.get(f"S{k}"), "functionalPass": functional(k),
             "archAccept": arch_accept(k), "archEvaluable": bool(a[f"p{k}"] and a[f"p{k}"]["evaluable"]),
             "accepted": functional(k) and arch_accept(k)} for k in (1, 2)]

    def first_pass(k):
        ph = phases[str(k)]
        if not ph or not ph["submit"]["attempts"]:
            return False
        if ph["submit"]["firstVerdict"] != "PASS":
            return False
        if k == 1:
            orc = o["p1-first"] or o["p1"]
            return bool(orc and orc["allPass"])
        if o["p2-first"] is not None:   # F2 differs from S2: follow-up oracle at F2 (regression is scored at S2 only)
            return bool(o["p2-first"]["allPass"])
        return functional(2)

    dec_rx = manifest.get("decisionTests") or DEC_ID.pattern
    con_rx = manifest.get("conflictTests") or r"CONFLICT"
    # Amendment A3: the phase-2 regression run counts only its regression subset (superseded tests are not decision
    # failures), and conflict tests are scored where the conflict exists, at S1.
    reg_run = (None if not o["p2-regression"] or reg is None else
               {**o["p2-regression"], "tests": [t for t in o["p2-regression"]["tests"] if t["name"] in set(reg["tests"])]})
    scored_runs = [r for r in (o["p1"], o["p2"], reg_run) if r]
    dec = [subset(r, pattern=dec_rx) for r in scored_runs]
    con = [subset(r, pattern=con_rx) for r in ([o["p1"]] if o["p1"] else [])]
    dsum = lambda xs, key: sum(x[key] for x in xs if x)
    conflict_applicable = bool(tj.get("conflict")) or dsum(con, "total") > 0

    x4 = any(ph and ph["contamination"]["contaminated"] for ph in phases.values())
    xi = any(ph and ph["integrity"]["tampered"] for ph in phases.values())
    x5 = {k: bool(ph and ph["timedOut"]) for k, ph in phases.items()}
    reasons = (["X4 contamination"] if x4 else []) + (["X-integrity tamper"] if xi else [])
    cost_parts = [ph["costUsd"] for ph in phases.values() if ph]
    total_cost = round(sum(c for c in cost_parts if c is not None), 6) if cost_parts else None
    review = read_json(os.path.join(state, "review", "result.json"))

    obs = {
        "schema": "arch002.observation/1", "experimentId": "ARCH-002", "runId": run["runId"], "label": run["label"],
        "fixture": run["fixture"], "arm": arm, "task": run["task"], "taskKey": run["taskKey"], "replicate": run["replicate"],
        "modelKey": run["modelKey"], "block": run["block"],
        "taskMeta": {"crossTierCount": run.get("crossTierCount"), "categories": tj.get("categories"), "conflict": bool(tj.get("conflict")),
                     "control": bool(tj.get("control")), "trap": (private.get("trap") or {}).get("exists"),
                     "trapRules": (private.get("trap") or {}).get("violatesRules"), "standIn": bool(tj.get("standIn"))},
        "status": "excluded" if reasons else "scored", "excluded": bool(reasons), "exclusionReasons": reasons,
        "exclusions": {"x4": {"contaminated": x4}, "xIntegrity": {"tampered": xi},
                       "x5": {"timedOut": any(x5.values()), "phases": x5, "scoredAs": "as is (not excluded)"}},
        "model": {"key": run["modelKey"], "configured": run["model"], "budgetMinutes": run["budgetMinutes"], "maxSubmits": run["maxSubmits"]},
        "commits": {"base": run.get("baseCommit"), "start": run.get("startCommit"), "S1": commits.get("S1"), "F1": commits.get("F1"),
                    "followup": run.get("followupCommit"), "S2": commits.get("S2"), "F2": commits.get("F2")},
        "requirements": reqs,
        "acceptedRequirements": sum(r["accepted"] for r in reqs),
        "completed": bool(phases["2"] and phases["2"]["submit"]["passed"]),
        "firstPassCorrect": {"p1": first_pass(1), "p2": first_pass(2) if phases["2"] else None},
        "cost": {"totalUsd": total_cost, "byPhase": {k: (ph["costUsd"] if ph else None) for k, ph in phases.items()},
                 "agrees": all(ph["crossCheck"]["agrees"] for ph in phases.values() if ph and ph["requests"]),
                 "priceTableSha256": run["digests"]["priceTable"]},
        "phases": phases,
        "oracle": {k: (None if v is None else {kk: vv for kk, vv in v.items() if kk != "tests"} | {"perTest": v["tests"]}) for k, v in o.items()},
        "regression": reg,
        "visibleTests": {"p1": None if not vis["p1"] else {k: vis["p1"][k] for k in ("total", "passed", "failed", "allPass")},
                         "p2": None if not vis["p2"] else {k: vis["p2"][k] for k in ("total", "passed", "failed", "allPass")},
                         "preexistingBroken": broken_visible(vis["p1"], vis["p2"])},
        "architecture": {**a, "baseline": run.get("baseline"), "newSinceS1": new_since_s1(a["p1"], a["p2"]),
                         "measure": "baseline-delta: new = DET finding (ARC-TRC-01 excluded) whose (ruleId, file, symbol, scope) the base commit's scoring report does not hold (multiset)"},
        "diff": {"phase1": diff_metrics(repo, run.get("baseCommit"), commits.get("S1")),
                 "phase2": diff_metrics(repo, run.get("followupCommit"), commits.get("S2"))},
        "decisionFidelity": {"decisionTests": {"total": dsum(dec, "total"), "passed": dsum(dec, "passed")},
                             "conflict": {"applicable": conflict_applicable, "tests": dsum(con, "total"), "passed": dsum(con, "passed"),
                                          "correct": (dsum(con, "total") > 0 and dsum(con, "passed") == dsum(con, "total")) if conflict_applicable else None},
                             "trc": {"definedForArm": arm in ("C", "D"),
                                     "p1": a["p1"]["trc"] if a["p1"] and arm in ("C", "D") else None,
                                     "p2": a["p2"]["trc"] if a["p2"] and arm in ("C", "D") else None,
                                     "p2InitialContract": a["p2-initial-contract"]["trc"] if a["p2-initial-contract"] else None}},
        "review": review,
        "provenance": {"digests": run.get("digests"), "tools": run.get("tools"), "cohortCommit": run.get("cohortCommit"),
                       "integritySetup": (read_json(os.path.join(state, "integrity-setup.json"), {}) or {}).get("digests")}}
    print(json.dumps(obs, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
