#!/usr/bin/env python3
"""Rehearsal 8 economics: cost by work category, rework share, rereads, context growth,
agent concurrency, verification activity vs task size, merge-conflict overhead.

Usage: python3 analyze_r8.py DATA_DIR PRICE_TABLE MERGES_JSONL OUT_JSON
Reads DATA_DIR/{executions,requests,rereads,r8-workitem-categories}.csv.
Every quantity in the output is MEASURED from those files except keys ending in
ESTIMATE (list-price cost or a stated model).
"""
import csv
import json
import os
import sys
from statistics import mean

sys.path.insert(0, os.path.dirname(__file__))
import econ  # noqa: E402

REPO = "indy-init-rehearsal-008"
T0, FREEZE, END = "2026-11-01T17:31:24Z", "2026-11-01T23:50:28Z", "2026-11-02T00:31:24Z"
VERIFIED_OBLIGATIONS, OBLIGATIONS = 266, 613      # T34-ACCEPTANCE-REPORT.md:42,45
VERIFIED_REQUIREMENTS, REQUIREMENTS = 51, 161     # T34-ACCEPTANCE-REPORT.md:47,136
LANES = 6  # domain, persistence, integration, ui, ui-2, reviewer (FINAL-REPORT.md "By role")


def num(x):
    if x in (None, ""):
        return None
    v = float(x)
    return int(v) if v.is_integer() else v


def read_csv(path):
    with open(path) as fh:
        return tuple({k: v for k, v in r.items()} for r in csv.DictReader(fh))


def nsum(rows, key):
    vals = [num(r[key]) for r in rows if num(r[key]) is not None]
    return sum(vals) if vals else None


def category_table(execs, cats):
    groups = econ.group_by(execs, lambda r: cats.get(r["workItemId"], "uncategorised"))
    tot_tok = nsum(execs, "tokens.total4")
    tot_cost = nsum(execs, "costUsdListPriceESTIMATE")
    return [{
        "category": c,
        "executions": len(rs),
        "executionsWithTokens": sum(1 for r in rs if num(r["tokens.total4"]) is not None),
        "tokensTotal": nsum(rs, "tokens.total4"),
        "tokensOutput": nsum(rs, "tokens.output"),
        "shareOfTokens": round((nsum(rs, "tokens.total4") or 0) / tot_tok, 3),
        "costUsdListPriceESTIMATE": round(nsum(rs, "costUsdListPriceESTIMATE") or 0, 2),
        "shareOfCostESTIMATE": round((nsum(rs, "costUsdListPriceESTIMATE") or 0) / tot_cost, 3),
        "agentWallMinutes": round((nsum(rs, "time.agent_wall_ms") or 0) / 60000, 1),
        "modelRequests": nsum(rs, "model.requests"),
        "repeatedFileReads": nsum(rs, "context.repeated_file_reads"),
        "testExecutions": nsum(rs, "tool.test_executions"),
        "buildExecutions": nsum(rs, "tool.build_executions"),
    } for c, rs in sorted(groups.items())]


def pearson(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pts) < 3:
        return None
    mx, my = mean(p[0] for p in pts), mean(p[1] for p in pts)
    sxy = sum((x - mx) * (y - my) for x, y in pts)
    sx = sum((x - mx) ** 2 for x, _ in pts) ** 0.5
    sy = sum((y - my) ** 2 for _, y in pts) ** 0.5
    return round(sxy / (sx * sy), 3) if sx and sy else None


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def spearman(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pts) < 3:
        return None
    return pearson(ranks([p[0] for p in pts]), ranks([p[1] for p in pts]))


def context_growth(reqs):
    """Mean context per request in deciles of request position within its execution."""
    by_exec = econ.group_by(reqs, lambda r: r["executionId"])
    buckets = {}
    for rs in by_exec.values():
        n = len(rs)
        for r in rs:
            d = min(9, int(10 * int(r["seq"]) / n))
            buckets = {**buckets, d: buckets.get(d, ()) + (num(r["contextTokens"]),)}
    return [{"decile": d, "meanContextTokens": round(mean(v))} for d, v in sorted(buckets.items())]


def main(argv):
    data, price_path, merges_path, out = argv[1:5]
    price = econ.price_entry(json.load(open(price_path)), "claude-opus-5-5")
    execs = tuple(r for r in read_csv(f"{data}/executions.csv") if r["repo"] == REPO)
    reqs = tuple(r for r in read_csv(f"{data}/requests.csv") if r["repo"] == REPO)
    rereads = tuple(r for r in read_csv(f"{data}/rereads.csv") if r["repo"] == REPO)
    cats = {r["workItemId"]: r["category"] for r in read_csv(f"{data}/r8-workitem-categories.csv")}
    merges = tuple(json.loads(l) for l in open(merges_path) if l.strip())

    tot_tok = nsum(execs, "tokens.total4")
    tot_cost = round(nsum(execs, "costUsdListPriceESTIMATE"), 2)
    table = category_table(execs, cats)
    with open(f"{data}/r8-by-category.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)
    cat = {r["category"]: r for r in table}
    rework_cats = ("defect-rework",)
    corrective_cats = ("defect-rework", "cross-lane-CR", "test-backfill")

    task = tuple(r for r in execs if cats.get(r["workItemId"]) != "coordinator"
                 and num(r["tokens.total4"]) is not None)
    coord = next(r for r in execs if cats.get(r["workItemId"]) == "coordinator")
    coord_reqs = tuple(r for r in reqs if r["workItemId"] == "WI-R8-COORD")
    task_reqs = tuple(r for r in reqs if r["workItemId"] != "WI-R8-COORD")

    intervals = tuple((r["agentStartedAt"], r["agentEndedAt"]) for r in task if r["agentStartedAt"])
    prof = econ.concurrency_profile(intervals, 60)
    prof_window = tuple(p for p in prof if econ.in_window(p[0].replace("+00:00", "Z"), T0, FREEZE))
    ros_vs_agent = [(num(r["time.wall_ms"]), num(r["time.agent_wall_ms"])) for r in task]

    feature = tuple(r for r in task if cats[r["workItemId"]] == "feature")
    conflicts = tuple(m for m in merges if m.get("conflict"))
    ros_only = tuple(m for m in conflicts
                     if all(f.startswith(".ros/") for f in m.get("conflictFiles", "").split()))
    gov = tuple(r for r in rereads if r["governance"] == "True")
    path_counts = econ.group_by(rereads, lambda r: r["path"])
    top_paths = sorted(((p, sum(int(r["reads"]) for r in rs), len(rs)) for p, rs in path_counts.items()),
                       key=lambda t: -t[2])[:10]

    result = {
        "source": {"repo": f"kemiller2002/{REPO}", "executionRecords": len(execs),
                   "window": [T0, END], "mergeFreeze": FREEZE},
        "totals": {
            "tokensTotalMEASURED": tot_tok,
            "reportedInFinalReport": 533823102,
            "reproduced": tot_tok == 533823102,
            "executionsWithTokens": sum(1 for r in execs if num(r["tokens.total4"]) is not None),
            "modelRequestsMEASURED": nsum(execs, "model.requests"),
            "costUsdListPriceESTIMATE": tot_cost,
            "costSplitByBucketESTIMATE": econ.context_cost_split(reqs, price),
            "cacheReadShareOfTokensMEASURED": round(nsum(execs, "tokens.cache_read") / tot_tok, 4),
        },
        "outcome": {
            "verifiedObligations": VERIFIED_OBLIGATIONS, "obligations": OBLIGATIONS,
            "fullyVerifiedRequirements": VERIFIED_REQUIREMENTS, "requirements": REQUIREMENTS,
            "ledgerVerdict": "INVALID (T34-ACCEPTANCE-REPORT.md)",
            "mergedPRs": len([m for m in merges if m.get("merged")]),
            "tokensPerVerifiedObligation": round(tot_tok / VERIFIED_OBLIGATIONS),
            "tokensPerFullyVerifiedRequirement": round(tot_tok / VERIFIED_REQUIREMENTS),
            "costPerVerifiedObligationESTIMATE": round(tot_cost / VERIFIED_OBLIGATIONS, 3),
            "costPerFullyVerifiedRequirementESTIMATE": round(tot_cost / VERIFIED_REQUIREMENTS, 2),
            "costPerMergedPRESTIMATE": round(tot_cost / len([m for m in merges if m.get("merged")]), 2),
        },
        "byCategory": table,
        "rework": {
            "definition": "defect-rework = work items whose stated purpose is fixing a defect found by CI, review or acceptance (r8-workitem-categories.csv)",
            "defectReworkShareOfTokens": round(sum(cat[c]["tokensTotal"] or 0 for c in rework_cats) / tot_tok, 3),
            "defectReworkShareOfTaskTokens": round(sum(cat[c]["tokensTotal"] or 0 for c in rework_cats)
                                                   / nsum(task, "tokens.total4"), 3),
            "correctiveShareOfTaskTokens": round(sum(cat[c]["tokensTotal"] or 0 for c in corrective_cats if c in cat)
                                                 / nsum(task, "tokens.total4"), 3),
            "defectReworkItems": cat["defect-rework"]["executions"],
            "taskItemsWithTokens": len(task),
        },
        "coordinator": {
            "tokens": num(coord["tokens.total4"]), "shareOfTokens": round(num(coord["tokens.total4"]) / tot_tok, 3),
            "costUsdListPriceESTIMATE": num(coord["costUsdListPriceESTIMATE"]),
            "requests": len(coord_reqs),
            "meanContextTokensPerRequest": round(mean(num(r["contextTokens"]) for r in coord_reqs)),
            "taskAgentMeanContextTokensPerRequest": round(mean(num(r["contextTokens"]) for r in task_reqs)),
            "costPerRequestUsdESTIMATE": round(num(coord["costUsdListPriceESTIMATE"]) / len(coord_reqs), 4),
            "taskCostPerRequestUsdESTIMATE": round(sum(num(r["costUsdESTIMATE"]) for r in task_reqs) / len(task_reqs), 4),
            "peakContextTokens": num(coord["context.peak_tokens"]),
            "compactions": num(coord["context.compactions"]),
        },
        "fixedPrefix": {"allExecutions": econ.prefix_share(reqs), "taskAgents": econ.prefix_share(task_reqs),
                        "outputTokensPerRequest": round(nsum(execs, "tokens.output") / len(reqs), 1)},
        "contextGrowthByRequestDecile": {"task": context_growth(task_reqs), "coordinator": context_growth(coord_reqs)},
        "rereads": {
            "repeatedFileReadsTotal": nsum(execs, "context.repeated_file_reads"),
            "fileReadsTotal": nsum(execs, "tool.file_reads"),
            "repeatedShareOfFileReads": round(nsum(execs, "context.repeated_file_reads") / nsum(execs, "tool.file_reads"), 3),
            "executionsWithAnyReread": sum(1 for r in task if (num(r["context.repeated_file_reads"]) or 0) > 0),
            "governanceReadsTotal": nsum(execs, "context.governance_reads"),
            "governanceRepeatedPaths": len(gov),
            "topRereadPaths": [{"path": p, "reads": n, "executions": e} for p, n, e in top_paths],
            "note": "repeatedReads lists only files read more than once in one session; cross-session rereads of the same file are visible as one path appearing in many executions",
        },
        "concurrency": {
            "basis": "task-agent transcript spans (agentStartedAt..agentEndedAt), 60 s samples, T0..merge freeze",
            "peakActiveAgents": max(c for _, c in prof_window),
            "meanActiveAgents": round(mean(c for _, c in prof_window), 2),
            "minutesWithZeroTaskAgents": sum(1 for _, c in prof_window if c == 0),
            "samples": len(prof_window),
            "laneSlotUtilisationVs6": econ.busy_fraction(prof_window, LANES),
            "agentMinutesTotal": round(nsum(task, "time.agent_wall_ms") / 60000, 1),
        },
        "rosWallVsAgentWall": {
            "executions": len(ros_vs_agent),
            "rosWallShorterThanHalfAgentWall": sum(1 for a, b in ros_vs_agent if a is not None and b and a < 0.5 * b),
            "rosWallSumMin": round(sum(a for a, _ in ros_vs_agent if a) / 60000, 1),
            "agentWallSumMin": round(sum(b for _, b in ros_vs_agent if b) / 60000, 1),
            "note": "time.wall_ms starts at `praxis work start`, which agents often ran minutes after starting; it understates task duration",
        },
        "verificationVsSize": {
            "basis": "feature executions with tokens",
            "n": len(feature),
            "spearman_linesAdded_testExecutions": spearman([num(r["linesAdded"]) for r in feature], [num(r["tool.test_executions"]) for r in feature]),
            "spearman_linesAdded_tokens": spearman([num(r["linesAdded"]) for r in feature], [num(r["tokens.total4"]) for r in feature]),
            "spearman_testExecutions_tokens": spearman([num(r["tool.test_executions"]) for r in feature], [num(r["tokens.total4"]) for r in feature]),
            "spearman_buildExecutions_agentWall": spearman([num(r["tool.build_executions"]) for r in feature], [num(r["time.agent_wall_ms"]) for r in feature]),
            "testExecutionsTotalTask": nsum(task, "tool.test_executions"),
            "buildExecutionsTotalTask": nsum(task, "tool.build_executions"),
            "shellCommandsTotalTask": nsum(task, "tool.shell_commands"),
            "toolCallsTotalTask": nsum(task, "tool.calls"),
            "toolFailuresTotalTask": nsum(task, "tool.failures"),
        },
        "merges": {
            "merges": len(merges), "conflicts": len(conflicts),
            "conflictsOnlyInRosState": len(ros_only),
            "resolutionSecondsTotal": sum(m.get("resolutionSeconds") or 0 for m in merges),
            "resolutionSecondsConflicted": sum(m.get("resolutionSeconds") or 0 for m in conflicts),
            "medianResolutionSeconds": econ.med([m.get("resolutionSeconds") for m in merges]),
        },
    }
    with open(out, "w") as fh:
        json.dump(result, fh, indent=1)
    print(json.dumps({k: result[k] for k in ("totals", "outcome", "rework", "coordinator", "concurrency")}, indent=1))


if __name__ == "__main__":
    main(sys.argv)
