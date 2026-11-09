"""A-F-11: bootstrap CI for estimated queued job-minutes in one repository stratum.
Usage: python3 -I queue_ci.py SAMPLE_DIR REPO [BOOT=2000] [SEED=20261108]"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1lib as L  # noqa: E402
import analyze_ci_sample as A  # noqa: E402


def main(d, repo, reps="2000", seed="20261108"):
    man = {m["repo"]: m for m in json.load(open(os.path.join(d, "manifest.json")))["repos"]}[repo]
    q = tuple(A.run_stats(r)["queueSec"] / 60 for r in json.load(open(os.path.join(d, f"sample-{repo}.json"))))
    w = man["eligibleNonSkipped"] / len(q)
    rng = random.Random(int(seed))
    b = sorted(w * sum(q[rng.randrange(len(q))] for _ in q) for _ in range(int(reps)))
    print(json.dumps({"repo": repo, "estQueuedJobMin": w * sum(q), "ci95": [L.quantile_nearest_rank(b, .025), L.quantile_nearest_rank(b, .975)]}))


if __name__ == "__main__":
    main(*sys.argv[1:])
