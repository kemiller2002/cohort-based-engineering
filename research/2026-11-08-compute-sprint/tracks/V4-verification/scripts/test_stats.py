"""unittest for stats.py: compare exact enumeration against brute-force relabeling."""
import itertools
import os
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats  # noqa: E402


def brute(strata):
    def labelings(n, k):
        return list(itertools.combinations(range(n), k))
    obs = stats.observed(strata)
    pools = [(list(g) + list(m), len(g)) for g, m in strata]
    count = ext = 0
    for choice in itertools.product(*[labelings(len(p), k) for p, k in pools]):
        s = Fraction(0)
        for (vals, k), gidx in zip(pools, choice):
            g = [vals[i] for i in gidx]
            m = [vals[i] for i in range(len(vals)) if i not in gidx]
            s += Fraction(sum(m), len(m)) - Fraction(sum(g), len(g))
        count += 1
        ext += abs(s) >= abs(obs)
    return Fraction(ext, count), count


class StatsTests(unittest.TestCase):
    def test_matches_bruteforce_two_strata(self):
        strata = [([1, 0, 1], [3, 2, 2]), ([0, 1, 0], [2, 1, 2])]
        r = stats.stratified_perm_test(strata)
        p, n = brute(strata)
        self.assertEqual((r["p"], r["N"]), (p, n))

    def test_matches_bruteforce_unequal(self):
        strata = [([5, 1], [3, 9, 2]), ([0, 0, 1, 4], [7, 1])]
        r = stats.stratified_perm_test(strata)
        self.assertEqual((r["p"], r["N"]), brute(strata))

    def test_extreme_separation_min_p(self):
        r = stats.stratified_perm_test([([0] * 6, [1] * 6), ([0] * 6, [1] * 6)])
        self.assertEqual(r["p"], Fraction(2, 924 ** 2))
        self.assertEqual(r["stat"], 2)

    def test_all_equal_p_one(self):
        r = stats.stratified_perm_test([([12] * 6, [12] * 6)])
        self.assertEqual(r["p"], 1)

    def test_holm(self):
        h = stats.holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(h["a"], 0.03)
        self.assertAlmostEqual(h["c"], 0.06)
        self.assertAlmostEqual(h["b"], 0.06)
        self.assertEqual(stats.holm({"a": 0.9, "b": 0.8})["a"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
