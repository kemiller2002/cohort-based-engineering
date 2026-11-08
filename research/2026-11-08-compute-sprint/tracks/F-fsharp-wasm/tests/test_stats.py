import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from stats import median, quantile, summarize, group_summaries


class StatsTests(unittest.TestCase):
    def test_median_odd_even(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([4, 1, 2, 3]), 2.5)

    def test_quantile_bounds(self):
        self.assertEqual(quantile([1, 2, 3], 0), 1)
        self.assertEqual(quantile([1, 2, 3], 1), 3)
        with self.assertRaises(ValueError):
            quantile([1], 2)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            median([])

    def test_summarize(self):
        s = summarize([10, 12, 11, 30, 11])
        self.assertEqual(s["n"], 5)
        self.assertEqual(s["median"], 11)
        self.assertEqual(s["min"], 10)
        self.assertEqual(s["max"], 30)
        self.assertAlmostEqual(s["relSpread"], 20 / 11, places=3)

    def test_group_summaries(self):
        rows = [{"a": "x", "v": 1}, {"a": "x", "v": 3}, {"a": "y", "v": 5}]
        out = group_summaries(rows, ["a"], "v")
        self.assertEqual([(r["a"], r["median"], r["n"]) for r in out], [("x", 2, 2), ("y", 5, 1)])


if __name__ == "__main__":
    unittest.main()
