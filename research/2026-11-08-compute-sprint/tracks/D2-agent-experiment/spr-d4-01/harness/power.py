"""SPR-D4-01 power for the primary test (n=8 runs per arm, exact two-sided permutation test, alpha 0.05), by Monte
Carlo. Model (an assumption, stated in the protocol): each run's over-claims ~ Binomial(K=4, p_arm), K = the four
structural opportunities R5 (broken fixture), R6, R7, R8 (infeasible); runs independent. Real runs are likely
overdispersed (one agent's reporting habit drives all its claims), which lowers power; a beta-binomial row
(rho = 0.3) is reported alongside.
Usage: python3 -I power.py   (deterministic: SEED, SIMS fixed)"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from perm import min_attainable_p, perm_test  # noqa: E402

SEED, SIMS, N, K, ALPHA, RHO = 20261108, 2000, 8, 4, 0.05, 0.3
SCENARIOS = [(0.5, 0.5), (0.5, 0.25), (0.5, 0.1), (0.5, 0.0), (0.75, 0.25), (0.75, 0.0), (1.0, 0.5),
             (1.0, 0.25), (0.25, 0.0), (0.25, 0.1)]


def run(rng, p, rho):
    q = p if rho == 0 or p in (0.0, 1.0) else rng.betavariate(p * (1 - rho) / rho, (1 - p) * (1 - rho) / rho)
    return sum(rng.random() < q for _ in range(K))


def power(rng, p_m, p_g, rho):
    return sum(perm_test([run(rng, p_g, rho) for _ in range(N)], [run(rng, p_m, rho) for _ in range(N)]) <= ALPHA
               for _ in range(SIMS)) / SIMS


if __name__ == "__main__":
    rng = random.Random(SEED)
    out = {"seed": SEED, "sims_per_scenario": SIMS, "n_per_arm": N, "opportunities_K": K, "alpha": ALPHA,
           "min_attainable_two_sided_p": min_attainable_p(N, N),
           "scenarios": [{"p_M": pm, "p_G": pg, "mean_overclaims_M": pm * K, "mean_overclaims_G": pg * K,
                          "power_binomial": power(rng, pm, pg, 0),
                          "power_betabinomial_rho0.3": power(rng, pm, pg, RHO)} for pm, pg in SCENARIOS]}
    print(json.dumps(out, indent=1))
