"""Claims A-F-11/12/13: estimate from V1's own stratified random sample (fetch_ci_sample.py output).
Usage: python3 -I analyze_ci_sample.py SAMPLE_DIR OUT_JSON [BOOT=2000] [SEED=20261108]"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1lib as L  # noqa: E402

VERIFIER_STEP = "Build pinned Praxis verifier"


def is_praxis_build(name):
    """Any from-source Praxis CLI build step: the named verifier step, or R7's inline `dotnet build praxis/...`."""
    return name == VERIFIER_STEP or "dotnet build praxis/" in (name or "")


def step_seconds(s):
    if not s.get("started_at") or not s.get("completed_at"):
        return 0.0
    return max(0.0, (L.parse_ts(s["completed_at"]) - L.parse_ts(s["started_at"])).total_seconds())


def run_stats(run):
    """Per-run tuple of measures (pure)."""
    jobs = run["jobs"]
    jm = sum(L.ceil_minutes(L.job_seconds(j)) for j in jobs)
    red = run["conclusion"] in L.RED
    steps = [s for j in jobs for s in j["steps"]]
    ver = [s for s in steps if s["name"] == VERIFIER_STEP]
    q = [L.queue_seconds(j) for j in jobs if j.get("started_at") and L.job_seconds(j) > 0]
    own = sum(L.ceil_minutes(L.job_seconds(j)) for j in jobs if j.get("conclusion") in L.RED)
    secs = sum(L.job_seconds(j) for j in jobs)
    return {"jobMin": jm, "redJobMin": jm if red else 0, "red": red, "redOwnJobMin": own,
            "redJobSecRaw": secs if red else 0.0,
            "jobSec": sum(L.job_seconds(j) for j in jobs),
            "stepSec": sum(step_seconds(s) for s in steps),
            "verifierSec": sum(step_seconds(s) for s in ver),
            "praxisBuildSec": sum(step_seconds(s) for s in steps if is_praxis_build(s["name"])),
            "verifierSteps": len(ver), "verifierStepsRan": sum(1 for s in ver if s.get("conclusion") not in ("skipped", None)),
            "queues": tuple(x for x in q if x is not None), "queueSec": sum(max(0, x) for x in q if x is not None),
            "jobs": len(jobs), "workflow": run["name"]}


def stratum(meta, sample):
    rs = tuple(run_stats(r) for r in sample)
    n, N = len(rs), meta["eligibleNonSkipped"]
    w = N / n if n else 0
    tot = lambda k: sum(r[k] for r in rs)
    qs = [x for r in rs for x in r["queues"]]
    return {"repo": meta["repo"], "N": N, "n": n, "weight": w, "rows": rs,
            "estJobMin": w * tot("jobMin"), "estRedJobMin": w * tot("redJobMin"),
            "redShare": tot("redJobMin") / tot("jobMin") if tot("jobMin") else None,
            "estRedOwnJobMin": w * tot("redOwnJobMin"), "estJobSecRaw": w * tot("jobSec"), "estRedJobSecRaw": w * tot("redJobSecRaw"),
            "estStepMin": w * tot("stepSec") / 60, "estVerifierMin": w * tot("verifierSec") / 60, "estPraxisBuildAnyMin": w * tot("praxisBuildSec") / 60,
            "verifierShareOfStep": tot("verifierSec") / tot("stepSec") if tot("stepSec") else None,
            "sampledRunsWithVerifierStep": sum(1 for r in rs if r["verifierSteps"]),
            "verifierStepsRan": tot("verifierStepsRan"), "verifierStepsTotal": tot("verifierSteps"),
            "foundationsRunsSampled": sum(1 for r in rs if "foundation" in (r["workflow"] or "").lower()),
            "jobsSampled": len(qs), "queueMedian": L.median(qs) if qs else None,
            "queueP90": L.quantile_nearest_rank(qs, 0.9) if qs else None,
            "estQueuedJobMin": w * tot("queueSec") / 60}


def combined(strata):
    tj = sum(s["estJobMin"] for s in strata)
    tr = sum(s["estRedJobMin"] for s in strata)
    ts = sum(s["estStepMin"] for s in strata)
    tv = sum(s["estVerifierMin"] for s in strata)
    tp = sum(s.get("estPraxisBuildAnyMin", 0) for s in strata)
    ro = sum(s.get("estRedOwnJobMin", 0) for s in strata)
    rs, rr = sum(s.get("estJobSecRaw", 0) for s in strata), sum(s.get("estRedJobSecRaw", 0) for s in strata)
    return {"redShareJobOwnConclusion": ro / tj if tj else None, "redShareUnroundedSeconds": rr / rs if rs else None,
            "estPraxisBuildAnyMin": tp, "estJobMin": tj, "estRedJobMin": tr, "redShare": tr / tj if tj else None,
            "estStepMin": ts, "estVerifierMin": tv, "verifierShare": tv / ts if ts else None}


def bootstrap(strata, reps, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        res = []
        for s in strata:
            rows = s["rows"]
            pick = [rows[rng.randrange(len(rows))] for _ in rows] if rows else []
            w = s["weight"]
            res.append({"estJobMin": w * sum(r["jobMin"] for r in pick), "estRedJobMin": w * sum(r["redJobMin"] for r in pick),
                        "estStepMin": w * sum(r["stepSec"] for r in pick) / 60, "estVerifierMin": w * sum(r["verifierSec"] for r in pick) / 60})
        out.append(combined(res))
    ci = lambda k: (L.quantile_nearest_rank([o[k] for o in out], 0.025), L.quantile_nearest_rank([o[k] for o in out], 0.975))
    return {k: ci(k) for k in ("redShare", "estJobMin", "estRedJobMin", "estVerifierMin", "verifierShare")}


def main(sample_dir, out, reps="2000", seed="20261108"):
    man = json.load(open(os.path.join(sample_dir, "manifest.json")))
    strata = tuple(stratum(m, json.load(open(os.path.join(sample_dir, f"sample-{m['repo']}.json")))) for m in man["repos"])
    allc = combined(strata)
    ex = [s for s in strata if s["repo"][-3:] not in ("006", "010")]
    result = {"seed": man["seed"], "perRepo": man["perRepo"], "fetchedAt": [man["fetchedAtStart"], man.get("fetchedAtEnd")],
              "combined": allc, "combinedCI95": bootstrap(strata, int(reps), int(seed)),
              "combinedExclR6R10": combined(ex),
              "strata": [{k: v for k, v in s.items() if k != "rows"} for s in strata]}
    json.dump(result, open(out, "w"), indent=1)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:])
