"""V5 exact stratified permutation test (own code; x02.py/x03.py/V4 stats.py not used).

Statistic: T = sum over strata of (mean(B) - mean(A)), exact Fractions.
Null distribution: all within-stratum relabelings that keep each stratum's group sizes,
enumerated exactly (per-stratum distributions convolved). Two-sided p = P(|T*| >= |T_obs|).
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations
from functools import reduce


def frac(x):
    return x if isinstance(x, Fraction) else Fraction(str(x))


def mean(xs):
    return sum(map(frac, xs), Fraction(0)) / len(xs)


def stat(strata):
    """strata: sequence of (A, B). Returns sum(mean(B) - mean(A))."""
    return sum((mean(b) - mean(a) for a, b in strata), Fraction(0))


def stratum_dist(a, b):
    pool = [frac(x) for x in list(a) + list(b)]
    na, n = len(a), len(a) + len(b)
    total = sum(pool, Fraction(0))
    dist = Counter()
    for idx in combinations(range(n), na):
        sa = sum((pool[i] for i in idx), Fraction(0))
        dist[(total - sa) / (n - na) - sa / na] += 1
    return dist


def convolve(d1, d2):
    out = Counter()
    for v1, c1 in d1.items():
        for v2, c2 in d2.items():
            out[v1 + v2] += c1 * c2
    return out


def perm_test(strata):
    obs = stat(strata)
    dist = reduce(convolve, (stratum_dist(a, b) for a, b in strata), Counter({Fraction(0): 1}))
    n = sum(dist.values())
    k = sum(c for v, c in dist.items() if abs(v) >= abs(obs))
    return {"stat": obs, "p": Fraction(k, n), "count": k, "N": n}


def brute_perm_test(strata):
    """Reference implementation: explicit product of all relabelings (for tests only, small inputs)."""
    obs = stat(strata)
    per = []
    for a, b in strata:
        pool = list(a) + list(b)
        per.append([([pool[i] for i in idx], [pool[i] for i in range(len(pool)) if i not in idx])
                    for idx in combinations(range(len(pool)), len(a))])
    combos = [[]]
    for opts in per:
        combos = [c + [o] for c in combos for o in opts]
    k = sum(1 for c in combos if abs(stat(c)) >= abs(obs))
    return {"stat": obs, "p": Fraction(k, len(combos)), "count": k, "N": len(combos)}


def holm(pvals):
    """pvals: dict name -> Fraction/float. Returns dict name -> Holm-adjusted p (monotone, capped at 1)."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0
    for i, (name, p) in enumerate(items):
        running = max(running, min(1, (m - i) * p))
        out[name] = running
    return out
