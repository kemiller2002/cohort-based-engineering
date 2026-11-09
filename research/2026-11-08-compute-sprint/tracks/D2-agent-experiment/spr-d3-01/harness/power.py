"""SPR-D3-01 power for the primary test (n=4 chains per arm, exact two-sided permutation test, alpha 0.05), by Monte
Carlo. Model (an assumption, stated in the protocol): each chain's trap_violations ~ Binomial(5, p_arm) (5 traps,
T1..T5), chains independent. Real chains are likely overdispersed (one agent's habits drive all its traps), which
lowers power further; a beta-binomial row (rho = 0.3) is reported alongside.
Usage: python3 -I power.py   (deterministic: SEED, SIMS fixed)
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from perm import min_attainable_p, perm_test  # noqa: E402

SEED, SIMS, N, TRAPS, ALPHA, RHO = 20261108, 4000, 4, 5, 0.05, 0.3
SCENARIOS = [(0.6, 0.6), (0.6, 0.3), (0.6, 0.2), (0.6, 0.0), (0.8, 0.2), (0.8, 0.0), (1.0, 0.0), (0.4, 0.0),
             (1.0, 0.2), (0.4, 0.2)]


def chain(rng, p, rho):
    # beta-binomial with intra-chain correlation rho (rho = 0 -> binomial)
    q = p if rho == 0 or p in (0.0, 1.0) else rng.betavariate(p * (1 - rho) / rho, (1 - p) * (1 - rho) / rho)
    return sum(rng.random() < q for _ in range(TRAPS))


def power(rng, p_m, p_g, rho):
    return sum(perm_test([chain(rng, p_g, rho) for _ in range(N)], [chain(rng, p_m, rho) for _ in range(N)]) <= ALPHA
               for _ in range(SIMS)) / SIMS


if __name__ == "__main__":
    rng = random.Random(SEED)
    out = {"seed": SEED, "sims_per_scenario": SIMS, "n_per_arm": N, "traps": TRAPS, "alpha": ALPHA,
           "min_attainable_two_sided_p": min_attainable_p(N, N),
           "scenarios": [{"p_violation_M": pm, "p_violation_G": pg, "mean_violations_M": pm * TRAPS,
                          "mean_violations_G": pg * TRAPS, "power_binomial": power(rng, pm, pg, 0),
                          "power_betabinomial_rho0.3": power(rng, pm, pg, RHO)} for pm, pg in SCENARIOS]}
    print(json.dumps(out, indent=1))
