"""SPR-D2-03 power for H2 (n=8 per arm, exact two-sided permutation test, alpha 0.05), by Monte Carlo.

Model (an assumption, stated in the protocol): each run's trap_violations ~ Binomial(3, p_arm) (3 traps: T1, T3, T4), runs independent.
Usage: python3 -I power.py   (deterministic: SEED, SIMS fixed)
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from perm import min_attainable_p, perm_test  # noqa: E402

SEED, SIMS, N, TRAPS, ALPHA = 20261108, 2000, 8, 3, 0.05
SCENARIOS = [(0.6, 0.6), (0.6, 0.4), (0.6, 0.3), (0.6, 0.2), (0.6, 0.0), (0.8, 0.4), (0.8, 0.2), (0.4, 0.2),
             (0.4, 0.1), (0.4, 0.0), (0.33, 0.0), (0.2, 0.0)]


def runs(rng, p):
    return [sum(rng.random() < p for _ in range(TRAPS)) for _ in range(N)]


def power(rng, p_m, p_g):
    return sum(perm_test(runs(rng, p_g), runs(rng, p_m)) <= ALPHA for _ in range(SIMS)) / SIMS


if __name__ == "__main__":
    rng = random.Random(SEED)
    out = {"seed": SEED, "sims_per_scenario": SIMS, "n_per_arm": N, "alpha": ALPHA,
           "min_attainable_two_sided_p": min_attainable_p(N, N),
           "scenarios": [{"p_violation_M": pm, "p_violation_G": pg, "mean_violations_M": pm * TRAPS,
                          "mean_violations_G": pg * TRAPS, "power": power(rng, pm, pg)} for pm, pg in SCENARIOS]}
    print(json.dumps(out, indent=1))
