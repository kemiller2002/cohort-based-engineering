import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import d2_stats as s  # noqa: E402


class StatsTests(unittest.TestCase):
    def test_complete_separation_n4_4(self):
        vals = {f"g{i}": 10 + i for i in range(4)} | {f"m{i}": i for i in range(4)}
        p, hits, n, d = s.exact_perm_p(vals, {f"g{i}" for i in range(4)})
        self.assertEqual((hits, n), (2, 70))
        self.assertAlmostEqual(p, 2 / 70)

    def test_all_equal(self):
        vals = {f"r{i}": 12 for i in range(8)}
        self.assertEqual(s.exact_perm_p(vals, {"r0", "r1", "r2", "r3"})[0], 1.0)

    def test_holm(self):
        adj = s.holm({"a": 2 / 70, "b": 1.0, "c": 1.0})
        self.assertAlmostEqual(adj["a"], 6 / 70)
        self.assertEqual(adj["b"], 1.0)
        adj2 = s.holm({"a": 0.01, "b": 0.02, "c": 0.04})
        self.assertAlmostEqual(adj2["a"], 0.03)
        self.assertAlmostEqual(adj2["b"], 0.04)
        self.assertAlmostEqual(adj2["c"], 0.04)


if __name__ == "__main__":
    unittest.main()
