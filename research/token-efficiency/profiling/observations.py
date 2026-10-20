"""REL-001 observation files (cbe.rel-001.observation/1) -> cbe.token-overhead/1 records.

Observations carry run-level token sums (Praxis `telemetry reliability-report`), not
per-request usage, so measured tokens are never phase-attributed: each run yields one
`run-total` record (phase `unattributed`, measured) plus `run-phase-estimate` records
whose tokens are a turn-equivalent model (tokenEstimate), with elapsed time measured
where the observation records it (run-02 only).

Turn-equivalent model: a workflow command issued as its own tool call costs one provider
request, and a request re-reads the whole context; so a phase with k such commands is
estimated at k x (mean context per request). Late-run commands (verify, complete) see a
larger-than-mean context, so the estimate is conservative for them; chaining commands in
one call makes it an over-estimate. Both are stated in every estimate's assumptions.
"""
import records as R

TURN_ASSUMPTIONS = [
    "one provider request per workflow command (not transcript-verified; chained commands share a request)",
    "request cost = mean context per request = (input + cacheRead + cacheWrite) / requests",
]


def fmt(obs):
    return "run-02" if "run02" in obs else "run-01"


def measured(obs):
    """Normalized run-level facts from either observation format."""
    m = obs.get("metrics", {})
    val = lambda k: R.get(m, k, "value")
    if fmt(obs) == "run-02":
        r = obs["run02"]
        kind = lambda k: R.get(r, "tokens", "byKind", k, "value")
        tests = R.get(r, "tests", "bySource") or {}
        agent_tests = (R.get(tests, "agent", "full") or 0) + (R.get(tests, "agent", "focused") or 0)
        boundary = {k: v for k, v in tests.items() if k != "agent"}
        v = r.get("verification") or {}
        c = r.get("coordination") or {}
        return {
            "tokens": R.tokens(kind("input"), kind("output"), kind("cacheRead"), kind("cacheWrite"), kind("cacheWrite5m"), kind("cacheWrite1h"), lower=True),
            "requests": R.get(r, "tokens", "byKind", "cacheRead", "numerator"),
            "agents": len(R.get(r, "tokens", "attribution", "agentsFound") or []) or 1,
            "harnessSubagentTokens": [a.get("subagentTokens") for a in R.get(r, "tokens", "harnessSecondary", "perAgent") or []],
            "toolCalls": r.get("toolCalls"),
            "wallMs": r.get("wallMs"),
            "agentTestRuns": agent_tests,
            "agentTestMs": R.get(tests, "agent", "ms"),
            "boundaryTestRuns": sum((b.get("full") or 0) + (b.get("focused") or 0) for b in boundary.values()),
            "boundaryTestMs": sum(b.get("ms") or 0 for b in boundary.values()),
            "claims": sum(c.get(k) or 0 for k in ("claim", "renew", "release", "recover", "expire", "claims")),
            "claimsBasis": "field:/run02/coordination",
            "verifications": (v.get("verifyCalls") or 0) + (v.get("validateRunCalls") or 0),
            "verificationMs": (v.get("verifyMs") or 0) + (v.get("validateRunMs") or 0),
            "completions": v.get("completeVerifiedCalls") or 0,
            "completionMs": v.get("completeVerifiedMs"),
            "completionTimings": v.get("completeVerifiedTimings") or [],
            "model": (R.get(obs, "model", "servedModels") or [None])[0] or R.get(obs, "model", "configuredModel"),
        }
    s = obs.get("scoring", {})
    validate = s.get("validateRuns") or 0
    return {
        "tokens": R.tokens(val("tokensInput"), val("tokensOutput"), val("tokensCacheRead"), val("tokensCacheWrite"), lower=True),
        "requests": R.get(m, "tokensCacheRead", "numerator"),
        "agents": 1,
        "harnessSubagentTokens": [],
        "toolCalls": val("toolCalls"),
        "wallMs": val("elapsedMs"),
        "agentTestRuns": max(0, (val("testRuns") or 0) - validate),
        "agentTestMs": None,
        "boundaryTestRuns": validate,
        "boundaryTestMs": None,
        "claims": 1,
        "claimsBasis": "brief-mandated (claim / work start step 1); not observed in run-01 observations",
        "verifications": validate,
        "verificationMs": None,
        "completions": s.get("completionAttempts") or 0,
        "completionMs": None,
        "completionTimings": [],
        "model": R.get(obs, "model", "configuredModel"),
    }


def context_tokens(tok):
    return sum((tok.get(k) or 0) for k in ("input", "cacheRead", "cacheWrite"))


def run_records(obs, f, source, sha, price_table):
    x = measured(obs)
    tok, n = x["tokens"], x["requests"] or 0
    mean_ctx = context_tokens(tok) / n if n else None
    entry = R.price_entry(price_table, x["model"])
    base = dict(
        providerSession={"provider": R.get(obs, "model", "provider"), "sessionId": None, "requestKey": None, "model": x["model"]},
        agent={"agentId": ",".join(R.get(obs, "run02", "tokens", "attribution", "agentsFound") or []) or None, "role": "trial-agent"},
        workItem=R.get(obs, "task", "taskId"),
        executionId=obs.get("runId"),
    )
    prov = lambda loc, method: {"source": source, "sha256": sha, "locator": loc, "method": method,
                                "priceTable": {"version": price_table.get("tableVersion")} if price_table else None}
    total_rec = R.record(
        recordId=f"{obs['runId']}:total", granularity="run-total", phase="unattributed", phaseBasis="none",
        measurement="measured", tokens=tok, toolCalls=x["toolCalls"], testRuns=x["agentTestRuns"] + x["boundaryTestRuns"],
        elapsedMs=x["wallMs"], estimatedCostUsd=R.cost(tok, entry),
        flags=["output-lower-bound"] + (["cost-lower-bound"] if entry else ["no-price"]),
        provenance=prov("/run02/tokens/byKind" if fmt(obs) == "run-02" else "/metrics/tokens*", "Praxis telemetry reliability-report sums as scored by the harness"),
        **base)

    def est(phase, count, basis, ms=None, extra=()):
        return R.record(
            recordId=f"{obs['runId']}:{phase}", granularity="run-phase-estimate", phase=phase, phaseBasis=basis,
            measurement="estimated", toolCalls=count,
            tokenEstimate=None if mean_ctx is None else {"total": round(count * mean_ctx), "method": "turn-equivalent", "assumptions": TURN_ASSUMPTIONS + list(extra)},
            testRuns=count if phase == "testing" else None, elapsedMs=ms,
            provenance=prov(basis, "turn-equivalent estimate; elapsed measured when present"), **base)

    phase_counts = [
        ("coordination", x["claims"], x["claimsBasis"], None, ()),
        ("testing", x["agentTestRuns"], "field:/run02/tests/bySource/agent" if fmt(obs) == "run-02" else "field:/metrics/testRuns - /scoring/validateRuns", x["agentTestMs"], ("agent-run test commands only; boundary runs are in verification",)),
        ("verification", x["verifications"], "field:/run02/verification/{verifyCalls,validateRunCalls}" if fmt(obs) == "run-02" else "field:/scoring/validateRuns", x["verificationMs"] or None, ()),
        ("completion", x["completions"], "field:/run02/verification/completeVerifiedCalls" if fmt(obs) == "run-02" else "field:/scoring/completionAttempts", x["completionMs"], ()),
    ]
    attributed = sum(c for _, c, _, _, _ in phase_counts)
    known_ms = sum(ms or 0 for *_, ms, _ in phase_counts)
    residual = R.record(
        recordId=f"{obs['runId']}:residual", granularity="run-phase-estimate", phase="unattributed",
        phaseBasis="residual: requests minus workflow commands (ingestion, discovery, implementation, reporting; not separable without transcripts)",
        measurement="estimated", toolCalls=max(0, (x["toolCalls"] or 0) - attributed),
        tokenEstimate=None if mean_ctx is None else {"total": round(max(0, n - attributed) * mean_ctx), "method": "turn-equivalent residual", "assumptions": TURN_ASSUMPTIONS},
        elapsedMs=(x["wallMs"] - known_ms) if (x["wallMs"] is not None and fmt(obs) == "run-02") else None,
        provenance=prov("derived", "residual"), **base)
    return [total_rec] + [est(*p) for p in phase_counts] + [residual], x, mean_ctx
