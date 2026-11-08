"""Exact two-sided permutation test on the difference in means (G - M), by subset-sum counting.

For fixed group sizes, mean(G) - mean(M) is a strictly increasing function of sum(G), so enumerating all
C(n_G + n_M, n_G) relabelings reduces to counting subsets of size n_G by their sum. Integer-valued outcomes use an
exact dynamic programme; others fall back to explicit enumeration (itertools.combinations). Both give the exact
p-value: the share of relabelings whose |mean diff| >= the observed |mean diff|.
"""
import itertools
import math
from collections import Counter
from functools import reduce

EPS = 1e-9


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def subset_sum_counts(values, k):
    """Counter{(sum): number of size-k subsets} for integer values."""
    def step(table, v):
        nxt = [Counter(c) for c in table]
        for j in range(len(table) - 1):
            for s, n in table[j].items():
                nxt[j + 1][s + v] += n
        return nxt
    return reduce(step, values, [Counter({0: 1})] + [Counter() for _ in range(k)])[k]


def abs_diff(sum_g, k, total, n):
    return abs(sum_g / k - (total - sum_g) / (n - k))


def perm_test(g, m):
    pooled, k, n = list(g) + list(m), len(g), len(g) + len(m)
    total, obs = sum(pooled), abs(mean(g) - mean(m))
    if all(float(v).is_integer() for v in pooled):
        counts = subset_sum_counts([int(v) for v in pooled], k)
        hits = sum(c for s, c in counts.items() if abs_diff(s, k, total, n) >= obs - EPS)
        return hits / math.comb(n, k)
    diffs = [abs_diff(sum(c), k, total, n) for c in itertools.combinations(pooled, k)]
    return sum(1 for d in diffs if d >= obs - EPS) / len(diffs)


def perm_test_bruteforce(g, m):
    pooled, k = list(g) + list(m), len(g)
    obs, idx = abs(mean(g) - mean(m)), range(len(pooled))
    diffs = [abs(mean([pooled[i] for i in c]) - mean([pooled[i] for i in idx if i not in c]))
             for c in itertools.combinations(idx, k)]
    return sum(1 for d in diffs if d >= obs - EPS) / len(diffs)


def min_attainable_p(n_g, n_m):
    return 2 / math.comb(n_g + n_m, n_g)
