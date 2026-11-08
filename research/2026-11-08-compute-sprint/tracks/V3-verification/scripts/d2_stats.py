"""SPR-D2-01: agreement of V3 scores with D2's results/scores, and exact permutation tests
(two-sided, difference in means, all C(8,4) splits) with Holm adjustment over H1-H3."""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3guard import require_scratch_cwd, require_scratch_path  # noqa: E402


def mean(xs):
    return sum(xs) / len(xs)


def exact_perm_p(values, group_a):
    """values: run->number; group_a: set of runs. Two-sided: |diff| >= |observed| (1e-9 tolerance)."""
    runs = sorted(values)
    diff = lambda a: mean([values[r] for r in a]) - mean([values[r] for r in runs if r not in a])
    obs = abs(diff(group_a))
    splits = list(itertools.combinations(runs, len(group_a)))
    hits = sum(abs(diff(set(s))) >= obs - 1e-9 for s in splits)
    return hits / len(splits), hits, len(splits), diff(group_a)


def holm(pvals):
    order = sorted(pvals, key=pvals.get)
    m, running, out = len(order), 0.0, {}
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvals[k]))
        out[k] = running
    return out


def agreement(v3, d2, fields):
    return {r: {f"{a}": {"v3": v3[r][a], "d2": d2[r].get(b), "agree": v3[r][a] == d2[r].get(b)} for a, b in fields} for r in sorted(v3)}


def main(d2_dir, v3_scores_path, out_path):
    require_scratch_cwd()
    require_scratch_path(out_path)
    v3 = json.load(open(v3_scores_path))
    d2 = {r: json.load(open(os.path.join(d2_dir, "results", "scores", f"{r}.json"))) for r in v3}
    assignment = json.load(open(os.path.join(d2_dir, "assignment.json")))
    usage = json.load(open(os.path.join(d2_dir, "results", "usage.json")))
    arm = {row["runId"]: row["arm"] for row in assignment["runs"]}
    G = {r for r, a in arm.items() if a == "G"}
    agree = agreement(v3, d2, [("accepted", "accepted"), ("trapViolations", "trap_violations"), ("trapCompliant", "trap_compliant")])
    tokens = {r: usage[r]["total_tokens"] for r in sorted(arm) if not usage[r].get("excluded")}
    tests = {
        "H1_accepted_v3": exact_perm_p({r: v3[r]["accepted"] for r in arm}, G),
        "H2_trapViolations_v3": exact_perm_p({r: v3[r]["trapViolations"] for r in arm}, G),
        "H3_tokens": exact_perm_p(tokens, G),
        "wall_ms": exact_perm_p({r: usage[r]["duration_ms"] for r in arm}, G),
        "tool_uses": exact_perm_p({r: usage[r]["tool_uses"] for r in arm}, G),
    }
    adj = holm({k: tests[k][0] for k in ("H1_accepted_v3", "H2_trapViolations_v3", "H3_tokens")})
    res = {"arms": arm, "tokens": tokens,
           "meanTokens": {"G": mean([tokens[r] for r in G]), "M": mean([tokens[r] for r in tokens if r not in G])},
           "agreement": agree, "allAgree": all(x["agree"] for r in agree.values() for x in r.values()),
           "tests": {k: {"p": v[0], "hits": v[1], "splits": v[2], "diffGminusM": v[3]} for k, v in tests.items()},
           "holm": adj}
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("arms", "meanTokens", "allAgree", "tests", "holm")}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
