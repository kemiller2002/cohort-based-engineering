import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import econ  # noqa: E402

PRICE = {"entries": [{"model": "m", "input": 4.0, "output": 20.0, "cacheRead": 0.2,
                      "cacheWrite5m": 5.0, "cacheWrite1h": 8.0}]}


def toks(i=0, o=0, cr=0, cw=0, w5=None, w1=None):
    return {"tokens.input": i, "tokens.output": o, "tokens.cache_read": cr,
            "tokens.cache_write": cw, "tokens.cache_write_5m": w5, "tokens.cache_write_1h": w1}


def test_cost_basic_buckets():
    p = econ.price_entry(PRICE, "m")
    # 1M of each at 4 + 20 + 0.2 + 5 = 29.2
    assert econ.list_price_cost_usd(toks(10**6, 10**6, 10**6, 10**6), p) == 29.2


def test_cost_uses_ttl_partition_when_consistent():
    p = econ.price_entry(PRICE, "m")
    assert econ.list_price_cost_usd(toks(cw=2 * 10**6, w5=10**6, w1=10**6), p) == 13.0


def test_cost_ignores_inconsistent_partition():
    p = econ.price_entry(PRICE, "m")
    assert econ.list_price_cost_usd(toks(cw=10**6, w5=10**6, w1=10**6), p) == 5.0


def test_cost_unavailable_when_bucket_missing_or_no_price():
    p = econ.price_entry(PRICE, "m")
    t = {**toks(1, 1, 1, 1), "tokens.cache_read": None}
    assert econ.list_price_cost_usd(t, p) is None
    assert econ.list_price_cost_usd(toks(1, 1, 1, 1), econ.price_entry(PRICE, "other")) is None


def test_total_tokens_distinguishes_zero_from_missing():
    assert econ.total_tokens(toks()) == 0
    assert econ.total_tokens({"tokens.input": 1}) is None


def test_metric_values_sums_only_sum_aggregation():
    rec = {"metrics": [{"id": "a", "value": 1, "aggregation": "sum"},
                       {"id": "a", "value": 2, "aggregation": "sum"},
                       {"id": "b", "value": 5, "aggregation": "maximum"},
                       {"id": "b", "value": 3, "aggregation": "maximum"}]}
    assert econ.metric_values(rec) == {"a": 3, "b": 3}
    assert econ.duplicate_metric_ids(rec) == ("a", "b")


def test_execution_row_extracts_fields():
    rec = {"executionId": "E1", "workItemId": "WI-R8-T12", "status": "finalized",
           "identity": {"model": "m", "agentId": "claude-code/domain"},
           "repository": {"changeSummary": {"commits": 2, "linesAdded": 10, "counts": {"added": 1}}},
           "metrics": [{"id": "tokens.input", "value": 10**6}, {"id": "tokens.output", "value": 0},
                       {"id": "tokens.cache_read", "value": 0}, {"id": "tokens.cache_write", "value": 0}]}
    row = econ.execution_row("r", "f.json", rec, PRICE)
    assert row["tokens.total4"] == 10**6
    assert row["costUsdListPriceESTIMATE"] == 4.0
    assert row["commits"] == 2 and row["filesAdded"] == 1
    assert econ.role_of(row["agentId"], row["workItemId"]) == "domain"
    assert econ.role_of(None, "WI-R8-COORD") == "coordinator"


def test_ci_row_and_summary():
    runs = [
        {"id": 1, "status": "completed", "conclusion": "success", "created_at": "2026-01-01T00:00:00Z",
         "run_started_at": "2026-01-01T00:00:10Z", "updated_at": "2026-01-01T00:01:10Z", "run_attempt": 1},
        {"id": 2, "status": "completed", "conclusion": "failure", "created_at": "2026-01-01T00:00:00Z",
         "run_started_at": "2026-01-01T00:00:30Z", "updated_at": "2026-01-01T00:02:30Z", "run_attempt": 2},
        {"id": 3, "status": "completed", "conclusion": "skipped", "created_at": "2026-01-01T00:00:00Z",
         "run_started_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:01Z", "run_attempt": 1},
    ]
    rows = [econ.ci_row("r", r) for r in runs]
    assert rows[0]["queueSeconds"] == 10 and rows[0]["spanSeconds"] == 60
    s = econ.summarize_ci(rows)
    assert s["executed"] == 2 and s["skipped"] == 1 and s["red"] == 1 and s["reattempts"] == 1
    assert s["spanTotalS"] == 180 and s["redSpanS"] == 120
    assert s["redOrCancelledShareOfSpan"] == round(120 / 180, 3)
    assert s["queueMedianS"] == 20.0


def test_percentile_and_med():
    assert econ.percentile([1, 2, 3, 4], 0.5) == 2.5
    assert econ.percentile([], 0.5) is None
    assert econ.med([None, 3, 1]) == 2


def test_concurrency_profile_and_busy_fraction():
    iv = [("2026-01-01T00:00:00Z", "2026-01-01T00:02:00Z"),
          ("2026-01-01T00:01:00Z", "2026-01-01T00:03:00Z")]
    prof = econ.concurrency_profile(iv, 60)
    assert [c for _, c in prof] == [1, 2, 1, 0]
    assert econ.busy_fraction(prof, 2) == round(4 / 8, 3)


def test_group_by_and_window():
    g = econ.group_by([{"k": 1}, {"k": 2}, {"k": 1}], lambda r: r["k"])
    assert len(g[1]) == 2 and len(g[2]) == 1
    assert econ.in_window("2026-01-01T00:00:05Z", "2026-01-01T00:00:00Z", "2026-01-01T00:00:10Z")
    assert not econ.in_window(None, "2026-01-01T00:00:00Z", "2026-01-01T00:00:10Z")


def test_trim_run_drops_unlisted_fields():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import fetch_ci_runs
    out = fetch_ci_runs.trim_run({"id": 1, "actor": {"login": "x"}, "name": "w"})
    assert "actor" not in out and out["id"] == 1 and out["created_at"] is None


def _rec_with_payload():
    return {"executionId": "E", "workItemId": "W", "rawTelemetry": [{"payload": {
        "schema": "praxis.claude-session-summary/2", "startedAt": "a", "endedAt": "b",
        "distinctFilesRead": 3, "apiErrors": 0, "retries": 1,
        "governanceReads": [{"path": "AGENTS.md", "count": 2}],
        "repeatedReads": [{"path": "AGENTS.md", "count": 2}, {"path": "x.fs", "count": 3}],
        "toolCalls": [{"name": "Bash", "count": 4}],
        "requestLedger": {"columns": ["input", "output", "cacheRead", "cacheWrite", "cacheWrite5m",
                                      "cacheWrite1h", "reasoning"],
                          "rows": [{"key": "k1", "model": "m", "agentId": "a",
                                    "usage": [0, 10**6, 10**6, 0, 0, 0, 5]}]}}}]}


def test_transcript_extractors():
    rec = _rec_with_payload()
    assert econ.agent_span(rec) == ("a", "b", 3, 0, 1)
    assert econ.agent_span({}) == (None, None, None, None, None)
    reqs = econ.request_rows(rec, PRICE)
    assert len(reqs) == 1 and reqs[0]["contextTokens"] == 10**6
    assert reqs[0]["costUsdESTIMATE"] == 20.2
    rr = econ.reread_rows(rec)
    assert [(r["path"], r["governance"]) for r in rr] == [("AGENTS.md", True), ("x.fs", False)]
    assert econ.tool_rows(rec)[0]["calls"] == 4
    split = econ.context_cost_split(reqs, PRICE["entries"][0])
    assert split["output"]["usd"] == 20.0 and split["cacheRead"]["share"] == round(0.2 / 20.2, 3)
