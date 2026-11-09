"""Unit tests for stats.py. Run: python3 -m unittest -v test_stats (from this directory)."""
import math
import unittest

import stats


class RatioTests(unittest.TestCase):
    def test_ratio_of_cpa_halves(self):
        self.assertAlmostEqual(stats.ratio_of_cpa([(1.0, 1, 2.0, 1), (1.0, 1, 2.0, 1)]), -0.5)

    def test_ratio_of_cpa_counts_acceptance(self):
        # x accepted only one of two units -> cost per accepted doubles
        self.assertAlmostEqual(stats.ratio_of_cpa([(1.0, 1, 1.0, 1), (1.0, 0, 1.0, 1)]), 1.0)

    def test_ratio_undefined(self):
        self.assertIsNone(stats.ratio_of_cpa([(1.0, 0, 1.0, 1)]))

    def test_geometric_mean_ratio(self):
        self.assertAlmostEqual(stats.geometric_mean_ratio([(1, 1, 2, 1), (4, 1, 2, 1)]), 0.0)


class TestTests(unittest.TestCase):
    def test_sign_p_0_of_4(self):
        self.assertAlmostEqual(stats.exact_sign_p(0, 4), 0.125)

    def test_sign_p_balanced(self):
        self.assertAlmostEqual(stats.exact_sign_p(2, 4), 1.0)

    def test_sign_p_empty(self):
        self.assertEqual(stats.exact_sign_p(0, 0), 1.0)

    def test_sign_flip_all_same_sign(self):
        self.assertAlmostEqual(stats.sign_flip_p([1, 1, 1, 1]), 2 / 16)

    def test_clopper_pearson_known(self):
        lo, hi = stats.clopper_pearson(7, 18)
        self.assertAlmostEqual(lo, 0.172986, places=4)
        self.assertAlmostEqual(hi, 0.642549, places=4)

    def test_clopper_pearson_zero(self):
        lo, hi = stats.clopper_pearson(0, 24)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.1425, places=3)


class BootstrapTests(unittest.TestCase):
    def test_deterministic_with_seed(self):
        items = [(1.0, 1, 2.0, 1), (1.5, 1, 2.0, 1), (0.8, 1, 1.0, 1)]
        a = stats.bootstrap(items, stats.ratio_of_cpa, 500, 7)
        b = stats.bootstrap(items, stats.ratio_of_cpa, 500, 7)
        self.assertEqual(a, b)
        self.assertLessEqual(a["ci95"][0], a["point"])
        self.assertGreaterEqual(a["ci95"][1], a["point"])

    def test_percentile(self):
        self.assertAlmostEqual(stats.percentile([0, 1, 2, 3, 4], 0.5), 2)
        self.assertTrue(math.isnan(stats.percentile([], 0.5)))


class PowerTests(unittest.TestCase):
    def test_power_increases_with_n(self):
        small = stats.mcnemar_power(0.4, 0.1, 10, 400, 1)
        large = stats.mcnemar_power(0.4, 0.1, 60, 400, 1)
        self.assertLess(small, large)

    def test_null_power_below_alpha(self):
        self.assertLess(stats.mcnemar_power(0.3, 0.3, 40, 1000, 2), 0.06)

    def test_paired_t_n(self):
        self.assertEqual(stats.paired_t_n(1.0, 1.0), 8)

    def test_t_quantile(self):
        self.assertAlmostEqual(stats.t_quantile(0.975, 2), 4.303, places=2)
        self.assertAlmostEqual(stats.t_quantile(0.975, 30), 2.042, places=2)

    def test_paired_t_n_exact_exceeds_normal(self):
        self.assertGreaterEqual(stats.paired_t_n_exact(1.0, 1.0), stats.paired_t_n(1.0, 1.0))
        self.assertEqual(stats.paired_t_n_exact(1.0, 1.0), 10)

    def test_smallest_n(self):
        n, table = stats.smallest_n(lambda k: k / 10, range(1, 11))
        self.assertEqual(n, 8)
        self.assertEqual(len(table), 8)


if __name__ == "__main__":
    unittest.main()
