#!/usr/bin/env python3
"""Rehearsal-level token, cost and outcome table (timed windows).

Usage: python3 build_rehearsal_tokens.py HOME_DIR PRICE_TABLE EXECUTIONS_CSV OUT_CSV
Token buckets are read from each rehearsal's own telemetry files; outcome counts are the
rehearsal reports' figures (cited per row). Rehearsals without token telemetry are emitted
with tokens 'unavailable' rather than omitted.
"""
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import econ  # noqa: E402


def r3(home):
    d = json.load(open(f"{home}/indy-init-rehearsal-003/evidence/telemetry/tokens-final.json"))["timed"]["all"]
    return {"input": d["input_tokens"], "output": d["output_tokens"], "cacheRead": d["cache_read_input_tokens"],
            "cacheWrite": d["cache_creation_input_tokens"], "cacheWrite5m": None, "cacheWrite1h": None,
            "messages": d["messages"],
            "tokenSource": "indy-init-rehearsal-003/evidence/telemetry/tokens-final.json (timed.all)"}


def r7(home):
    files = sorted(glob.glob(f"{home}/indy-init-rehearsal-007/evidence/telemetry/*.json"))
    timed = [json.load(open(f))["timed"] for f in files]
    s = lambda k: sum(t[k] for t in timed)  # noqa: E731
    return {"input": s("inputTokens"), "output": s("outputTokens"), "cacheRead": s("cacheReadTokens"),
            "cacheWrite": s("cacheWriteTokens"), "cacheWrite5m": None, "cacheWrite1h": None,
            "messages": s("messages"),
            "tokenSource": "indy-init-rehearsal-007/evidence/telemetry/{main-agent,reviewer-*}.json (timed)"}


def r8(execs_csv):
    rows = [r for r in csv.DictReader(open(execs_csv)) if r["repo"] == "indy-init-rehearsal-008" and r["tokens.total4"]]
    s = lambda k: sum(int(r[k]) for r in rows)  # noqa: E731
    return {"input": s("tokens.input"), "output": s("tokens.output"), "cacheRead": s("tokens.cache_read"),
            "cacheWrite": s("tokens.cache_write"), "cacheWrite5m": s("tokens.cache_write_5m"),
            "cacheWrite1h": s("tokens.cache_write_1h"), "messages": s("model.requests"),
            "tokenSource": "indy-init-rehearsal-008/.ros/telemetry/executions/*.json (48 records with tokens)"}


OUTCOMES = {
    "R1": ("unavailable", "", "", ""),
    "R2": ("66 PASS + 6 NOT_RUN of 72 ledger rows", 66, 72,
           "indy-init-rehearsal-003/docs/REHEARSAL-003-REPORT.md:175 (R2 column); R2 verdict INVALID under Indy-init ledger contract"),
    "R3": ("51 PASS + 5 PARTIAL of 56 criteria (8 requirements); NOT ACCEPTED (blocked)", 51, 56,
           "indy-init-rehearsal-003/docs/REHEARSAL-003-REPORT.md:86,102"),
    "R7": ("73 VERIFIED of 161 P0 (at #24, not re-assessed); NOT ACCEPTED", 73, 161,
           "indy-init-rehearsal-007/evidence/FINAL-REPORT.md:78"),
    "R8": ("51 of 161 P0 requirements fully verified; 266/613 obligations; ledger INVALID", 51, 161,
           "indy-init-rehearsal-008/evidence/T34/T34-ACCEPTANCE-REPORT.md:42,47,136"),
    "R9": ("36/37 content requirements verified; 0/541 frozen-plan obligations; verdict not computed", 36, 37,
           "indy-init-rehearsal-009/evidence/FINAL-REPORT.md:74,93"),
    "R10": ("no governed verdict; implementer-verified only", "", "",
            "indy-init-rehearsal-010/evidence/FINAL-REPORT.md:1"),
}


def main(argv):
    home, price_path, execs_csv, out = argv[1:5]
    price = econ.price_entry(json.load(open(price_path)), "claude-opus-5-5")
    tok = {"R3": r3(home), "R7": r7(home), "R8": r8(execs_csv)}
    rows = []
    for reh in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"):
        t = tok.get(reh)
        outcome = OUTCOMES.get(reh, ("see Track B", "", "", ""))
        base = {"rehearsal": reh, "outcome": outcome[0], "verifiedUnits": outcome[1], "scopeUnits": outcome[2],
                "outcomeSource": outcome[3]}
        if t is None:
            rows.append({**base, "input": "unavailable", "output": "unavailable", "cacheRead": "unavailable",
                         "cacheWrite": "unavailable", "cacheWrite5m": "", "cacheWrite1h": "", "messages": "",
                         "totalTokens": "unavailable", "costUsdListPriceESTIMATE": "unavailable",
                         "tokensPerVerifiedUnit": "unavailable", "costPerVerifiedUnitESTIMATE": "unavailable",
                         "outputShareOfCostESTIMATE": "unavailable",
                         "tokenSource": "no token telemetry found in repository (searched evidence/, .ros/telemetry)"})
            continue
        m = {"tokens.input": t["input"], "tokens.output": t["output"], "tokens.cache_read": t["cacheRead"],
             "tokens.cache_write": t["cacheWrite"], "tokens.cache_write_5m": t["cacheWrite5m"],
             "tokens.cache_write_1h": t["cacheWrite1h"]}
        total = econ.total_tokens(m)
        cost = econ.list_price_cost_usd(m, price)
        v = outcome[1] if isinstance(outcome[1], int) else None
        rows.append({**base, **{k: t[k] for k in ("input", "output", "cacheRead", "cacheWrite", "cacheWrite5m",
                                                  "cacheWrite1h", "messages")},
                     "totalTokens": total, "costUsdListPriceESTIMATE": cost,
                     "tokensPerVerifiedUnit": round(total / v) if v else "",
                     "costPerVerifiedUnitESTIMATE": round(cost / v, 3) if v else "",
                     "outputShareOfCostESTIMATE": round(t["output"] * price["output"] / 1e6 / cost, 3),
                     "tokenSource": t["tokenSource"]})
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["rehearsal"], r["totalTokens"], r["costUsdListPriceESTIMATE"], r["tokensPerVerifiedUnit"],
              r["costPerVerifiedUnitESTIMATE"], r["outputShareOfCostESTIMATE"])


if __name__ == "__main__":
    main(sys.argv)
