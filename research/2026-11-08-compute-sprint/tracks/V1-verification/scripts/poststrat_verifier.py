"""A-F-13 refinement: post-stratified estimate of 'Build pinned Praxis verifier' step minutes.
Verifier minutes = sum over repos of N_foundations_runs(population) x mean verifier minutes per sampled foundations run.
Usage: python3 -I poststrat_verifier.py SAMPLE_DIR [BOOT=2000] [SEED=20261108]"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1lib as L  # noqa: E402
import analyze_ci_sample as A  # noqa: E402

WF = "Echelon foundations"


def per_repo(sample_dir, repo):
    runs = json.load(open(os.path.join(sample_dir, f"runs-{repo}.json")))
    n_pop = sum(1 for r in runs if r["conclusion"] != "skipped" and r["name"] == WF)
    smp = json.load(open(os.path.join(sample_dir, f"sample-{repo}.json")))
    mins = tuple(A.run_stats(r)["verifierSec"] / 60 for r in smp if r["name"] == WF)
    return repo, n_pop, mins


def estimate(rows):
    return sum(n * (sum(m) / len(m)) for _, n, m in rows if m)


def main(sample_dir, reps="2000", seed="20261108"):
    man = json.load(open(os.path.join(sample_dir, "manifest.json")))
    rows = tuple(per_repo(sample_dir, m["repo"]) for m in man["repos"])
    rng = random.Random(int(seed))
    boots = sorted(estimate(tuple((r, n, [m[rng.randrange(len(m))] for _ in m]) for r, n, m in rows if m)) for _ in range(int(reps)))
    out = {"estVerifierMin": estimate(rows), "ci95": (L.quantile_nearest_rank(boots, .025), L.quantile_nearest_rank(boots, .975)),
           "byRepo": {r: {"foundationsRuns": n, "sampled": len(m), "meanVerifierMin": (sum(m) / len(m)) if m else None,
                          "estMin": n * sum(m) / len(m) if m else 0} for r, n, m in rows}}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:])
