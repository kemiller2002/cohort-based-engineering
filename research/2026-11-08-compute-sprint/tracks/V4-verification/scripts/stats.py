"""V4 independent statistics (not harness/x02.py).

Exact two-sided permutation tests, labels permuted within fixture strata, enumerated exactly
with Fractions. Statistic: sum over strata of mean(M) - mean(G).
Two-sided p = #{relabelings : |S| >= |S_obs|} / N.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations
from math import comb


def stratum_distribution(values, n_g):
    """Counter of mean(M)-mean(G) (exact Fractions) over all choices of n_g G labels."""
    n = len(values)
    total = sum(values)
    n_m = n - n_g
    return Counter(Fraction(total - sum(c), n_m) - Fraction(sum(c), n_g)
                   for c in combinations(values, n_g))


def observed(strata):
    return sum(Fraction(sum(m), len(m)) - Fraction(sum(g), len(g)) for g, m in strata)


def convolve(dists):
    acc = Counter({Fraction(0): 1})
    for dist in dists:
        nxt = Counter()
        for a, ca in acc.items():
            for b, cb in dist.items():
                nxt[a + b] += ca * cb
        acc = nxt
    return acc


def stratified_perm_test(strata):
    """strata: list of (g_values, m_values). Returns dict with exact stat, p (Fraction) and N."""
    dists = [stratum_distribution(list(g) + list(m), len(g)) for g, m in strata]
    full = convolve(dists)
    obs = observed(strata)
    n_total = sum(full.values())
    expected_n = 1
    for g, m in strata:
        expected_n *= comb(len(g) + len(m), len(g))
    assert n_total == expected_n
    extreme = sum(c for s, c in full.items() if abs(s) >= abs(obs))
    return {"stat": obs, "p": Fraction(extreme, n_total), "n_extreme": extreme, "N": n_total}


def holm(pvals):
    """pvals: dict name -> p. Returns dict name -> Holm-adjusted p (monotone, capped at 1)."""
    order = sorted(pvals, key=lambda k: pvals[k])
    m = len(order)
    out, running = {}, 0
    for i, k in enumerate(order):
        running = max(running, min(1, (m - i) * pvals[k]))
        out[k] = running
    return out
