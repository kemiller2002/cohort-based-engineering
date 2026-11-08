"""Pure statistical helpers for the SPR-D re-analysis (stdlib only, no I/O).

Every function is deterministic given its inputs (random draws take an explicit seed).
"""
from __future__ import annotations

import math
import random
from typing import Callable, Iterable, Sequence, Tuple

Block = Tuple[float, int, float, int]  # (cost_x, accepted_x, cost_y, accepted_y)


def ratio_of_cpa(blocks: Sequence[Block]) -> float | None:
    """(sum cost_x / sum accepted_x) / (sum cost_y / sum accepted_y) - 1, None if undefined."""
    cx = sum(b[0] for b in blocks)
    ax = sum(b[1] for b in blocks)
    cy = sum(b[2] for b in blocks)
    ay = sum(b[3] for b in blocks)
    if ax == 0 or ay == 0 or cy == 0:
        return None
    return (cx / ax) / (cy / ay) - 1.0


def geometric_mean_ratio(blocks: Sequence[Block]) -> float | None:
    """exp(mean log(cost_x/cost_y)) - 1 over blocks where both arms accepted (robustness statistic)."""
    logs = [math.log(b[0] / b[2]) for b in blocks if b[1] and b[3] and b[0] > 0 and b[2] > 0]
    return math.exp(sum(logs) / len(logs)) - 1.0 if logs else None


def percentile(sorted_xs: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile of an already-sorted sequence."""
    if not sorted_xs:
        return float("nan")
    k = (len(sorted_xs) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (k - lo)


def bootstrap(items: Sequence, stat: Callable[[Sequence], float | None], n: int, seed: int) -> dict:
    """Percentile bootstrap resampling whole items with replacement."""
    rng = random.Random(seed)
    m = len(items)
    draws = (stat([items[rng.randrange(m)] for _ in range(m)]) for _ in range(n))
    samples = sorted(s for s in draws if s is not None)
    return {
        "point": stat(items),
        "ci95": [percentile(samples, 0.025), percentile(samples, 0.975)],
        "validResamples": len(samples),
        "resamples": n,
        "seed": seed,
    }


def sign_flip_p(diffs: Sequence[float]) -> float:
    """Exact two-sided paired permutation (sign-flip) p-value for the mean of diffs.

    Enumerates all 2^n sign assignments; intended for n <= 20.
    """
    n = len(diffs)
    if n == 0:
        return 1.0
    observed = abs(sum(diffs))
    hits = 0
    for mask in range(1 << n):
        s = sum(d if (mask >> i) & 1 else -d for i, d in enumerate(diffs))
        if abs(s) >= observed - 1e-12:
            hits += 1
    return hits / (1 << n)


def binom_pmf(k: int, n: int, p: float = 0.5) -> float:
    return math.comb(n, k) * p ** k * (1 - p) ** (n - k)


def exact_sign_p(k: int, n: int) -> float:
    """Two-sided exact binomial (sign / conditional McNemar) test, p0 = 0.5, 'minimum likelihood' convention."""
    if n == 0:
        return 1.0
    obs = binom_pmf(k, n)
    return min(1.0, sum(binom_pmf(i, n) for i in range(n + 1) if binom_pmf(i, n) <= obs + 1e-12))


def _beta_cdf_binom(x: int, n: int, p: float) -> float:
    """P(Bin(n,p) <= x)."""
    return sum(binom_pmf(i, n, p) for i in range(0, x + 1))


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Exact binomial CI by bisection on the binomial CDF."""
    def solve(f: Callable[[float], float], target: float) -> float:
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if f(mid) > target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else _invert_upper_tail(k, n, alpha / 2)
    upper = 1.0 if k == n else solve(lambda p: _beta_cdf_binom(k, n, p), alpha / 2)
    return lower, upper


def _invert_upper_tail(k: int, n: int, a: float) -> float:
    """Smallest p with P(Bin(n,p) >= k) >= a."""
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if 1 - _beta_cdf_binom(k - 1, n, mid) < a:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def mcnemar_power(p_a: float, p_b: float, blocks: int, sims: int, seed: int,
                  rho: float = 0.0, alpha: float = 0.05) -> float:
    """Simulated power of the two-sided exact sign test for paired binary outcomes.

    Arms are independent within a block when rho = 0; rho > 0 adds positive within-block
    concordance by copying arm A's outcome to arm B with probability rho (then drawing B
    at a rate adjusted to keep its marginal ~p_b when feasible).
    """
    rng = random.Random(seed)
    hits = 0
    for _ in range(sims):
        a_only = b_only = 0
        for _ in range(blocks):
            a = rng.random() < p_a
            if rng.random() < rho:
                b = a and (rng.random() < min(1.0, p_b / p_a if p_a else 0.0))
            else:
                b = rng.random() < p_b
            a_only += a and not b
            b_only += b and not a
        d = a_only + b_only
        if d and exact_sign_p(b_only, d) < alpha and a_only > b_only:
            hits += 1
    return hits / sims


def smallest_n(power_at: Callable[[int], float], ns: Iterable[int], target: float = 0.8) -> Tuple[int | None, list]:
    """First n in ns whose power reaches target, plus the evaluated table."""
    table = []
    for n in ns:
        pw = power_at(n)
        table.append((n, pw))
        if pw >= target:
            return n, table
    return None, table


def paired_t_n(mean_diff: float, sd_diff: float, alpha_z: float = 1.959964, power_z: float = 0.841621) -> int:
    """Normal-approximation sample size for a paired mean difference (two-sided alpha .05, power .80)."""
    if mean_diff == 0:
        raise ValueError("zero effect")
    return math.ceil(((alpha_z + power_z) * sd_diff / mean_diff) ** 2)


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def sd(xs: Sequence[float]) -> float:
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def t_cdf(x: float, df: int, steps: int = 4000) -> float:
    """Student t CDF by Simpson integration of the density from 0 to |x| (adequate for df >= 1, |x| < 50)."""
    c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
    f = lambda t: c * (1 + t * t / df) ** (-(df + 1) / 2)
    a, b = 0.0, abs(x)
    h = (b - a) / steps
    area = f(a) + f(b) + sum((4 if i % 2 else 2) * f(a + i * h) for i in range(1, steps))
    half = area * h / 3
    return 0.5 + half if x >= 0 else 0.5 - half


def t_quantile(p: float, df: int) -> float:
    lo, hi = -50.0, 50.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def paired_t_n_exact(mean_diff: float, sd_diff: float, alpha: float = 0.05, power: float = 0.8, n_max: int = 10000) -> int:
    """Smallest n (>= 2) with n >= ((t_{1-a/2,n-1} + t_{power,n-1}) * sd / d)^2 (standard t-iteration)."""
    for n in range(2, n_max):
        df = n - 1
        need = ((t_quantile(1 - alpha / 2, df) + t_quantile(power, df)) * sd_diff / mean_diff) ** 2
        if n >= need:
            return n
    return n_max
