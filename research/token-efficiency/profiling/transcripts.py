"""Claude Code transcript (JSONL) -> per-request cbe.token-overhead/1 records and findings.

Deduplication mirrors Praxis `SessionTranscript.requestsOf` (praxis
src/Praxis.Domain/Telemetry/SessionTranscript.fs:340-361): one request per
`message.id` (else `requestId`, else `uuid`), first-seen order, last-written usage.
Tool calls are deduplicated by `tool_use` id (SessionTranscript.fs:376-389).
Output tokens from a transcript are a lower bound (ReliabilityReport.fs:240-247).
A request's tokens are attributed to the phase of the tool call(s) it emitted:
the request is the model deciding and issuing that step.
"""
import json
from datetime import datetime
from functools import reduce

import phases
import records as R


def parse_lines(text):
    """(entries, malformed_count); malformed lines are counted, never fatal."""
    def one(line):
        try:
            v = json.loads(line)
            return v if isinstance(v, dict) else None
        except ValueError:
            return None
    parsed = [one(l) for l in text.splitlines() if l.strip()]
    return [p for p in parsed if p is not None], sum(1 for p in parsed if p is None)


def request_key(e):
    return R.get(e, "message", "id") or e.get("requestId") or e.get("uuid")


def blocks(e, kind):
    content = R.get(e, "message", "content")
    return [b for b in content if isinstance(b, dict) and b.get("type") == kind] if isinstance(content, list) else []


def stamp(e):
    try:
        return datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).timestamp() * 1000
    except (KeyError, ValueError, AttributeError):
        return None


def requests_of(entries):
    """Deduplicated requests: [{key, entry(last), first, calls[]}] in first-seen order."""
    assistant = [e for e in entries if e.get("type") == "assistant" and request_key(e) and R.get(e, "message", "usage")]

    def step(acc, e):
        order, by = acc
        k = request_key(e)
        prev = by.get(k, {"key": k, "first": e, "calls": {}})
        calls = {**prev["calls"], **{b.get("id") or f"{k}#{i}": {"name": b.get("name"), "input": b.get("input") or {}, "id": b.get("id")}
                                     for i, b in enumerate(blocks(e, "tool_use"))}}
        return (order if k in by else order + [k], {**by, k: {**prev, "entry": e, "calls": calls}})

    order, by = reduce(step, assistant, ([], {}))
    return [{**by[k], "calls": list(by[k]["calls"].values())} for k in order]


def result_sizes(entries):
    """tool_use_id -> bytes of the tool_result content returned to the model."""
    def size(b):
        c = b.get("content")
        return len((c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)).encode("utf-8")) if c is not None else 0
    return {b.get("tool_use_id"): size(b) for e in entries if e.get("type") == "user" for b in blocks(e, "tool_result")}


def usage_tokens(u):
    cc = u.get("cache_creation") or {}
    return R.tokens(
        u.get("input_tokens"), u.get("output_tokens"), u.get("cache_read_input_tokens"), u.get("cache_creation_input_tokens"),
        cc.get("ephemeral_5m_input_tokens"), cc.get("ephemeral_1h_input_tokens"), lower=True)


def profile(entries, source, sha, price_table, work_item=None, execution_id=None, role="agent"):
    reqs = requests_of(entries)
    sizes = result_sizes(entries)
    starts = [stamp(r["first"]) for r in reqs]
    n = len(reqs)

    def rec(i, r):
        e = r["entry"]
        rule, phase = phases.classify_request(r["calls"], i == n - 1)
        tok = usage_tokens(e["message"]["usage"])
        model = e["message"].get("model")
        nxt = starts[i + 1] if i + 1 < n else None
        flags = (["first-request-cache-write"] if i == 0 and (tok["cacheWrite"] or 0) > (tok["cacheRead"] or 0) else [])
        return R.record(
            recordId=f"{execution_id or source}:req{i:04d}",
            granularity="request",
            phase=phase,
            phaseBasis=f"rule:{rule}",
            measurement="measured",
            tokens=tok,
            providerSession={"provider": "anthropic", "sessionId": e.get("sessionId"), "requestKey": r["key"], "model": model},
            agent={"agentId": e.get("agentId"), "role": role},
            workItem=work_item,
            executionId=execution_id,
            toolCalls=len(r["calls"]),
            toolNames=sorted(c["name"] or "" for c in r["calls"]),
            testRuns=sum(1 for c in r["calls"] if phases.is_test_command(c)),
            toolResultBytes=sum(sizes.get(c["id"], 0) for c in r["calls"]),
            elapsedMs=(nxt - starts[i]) if (nxt is not None and starts[i] is not None) else None,
            estimatedCostUsd=R.cost(tok, R.price_entry(price_table, model)),
            flags=flags,
            provenance={"source": source, "sha256": sha, "locator": f"message.id={r['key']}", "method": "transcript request (dedup by message.id, last-written usage)",
                        "priceTable": {"version": price_table.get("tableVersion")} if price_table else None},
        )

    return [rec(i, r) for i, r in enumerate(reqs)], findings(reqs, sizes)


def findings(reqs, sizes):
    """Duplicate calls, repeated reads, test runs without an intervening edit, brief sizes."""
    calls = [(i, c) for i, r in enumerate(reqs) for c in r["calls"]]
    keys = [phases.canonical_call(c) for _, c in calls]
    duplicates = [{"request": i, "tool": c["name"], "firstAt": next(j for (j, _), k2 in zip(calls, keys) if k2 == k)}
                  for idx, ((i, c), k) in enumerate(zip(calls, keys)) if k in keys[:idx]]
    reads = [(i, c["input"].get("file_path")) for i, c in calls if c["name"] == "Read"]
    repeated_reads = [{"request": i, "path": p} for idx, (i, p) in enumerate(reads) if p in [q for _, q in reads[:idx]]]

    def test_scan(acc, ic):
        state, out = acc
        i, c = ic
        if phases.classify_call(c)[1] == "implementation":
            return ("dirty", out)
        if phases.is_test_command(c):
            return ("tested", out + ([i] if state == "tested" else []))
        return (state, out)

    _, unchanged_tests = reduce(test_scan, calls, ("dirty", []))
    brief_reads = [{"request": i, "tool": c["name"], "bytes": sizes.get(c["id"], 0), "tokensEstimate": sizes.get(c["id"], 0) // 4}
                   for i, c in calls if phases.classify_call(c)[1] == "requirement-ingestion"]
    return {
        "duplicateToolCalls": duplicates,
        "repeatedReads": repeated_reads,
        "testRunsWithoutInterveningEdit": unchanged_tests,
        "briefReads": brief_reads,
        "briefTokensNote": "tokensEstimate = bytes // 4 (estimate, not a tokenizer count)",
    }
