import unittest

import analyze_bench as ab


def rec(seq, arm, c, exit=0):
    return {"seq": seq, "arm": arm, "cpuUserS": c, "cpuSysS": 0.0, "wallS": c, "exit": exit, "loadavg1Before": 1.0}


class AnalyzeTests(unittest.TestCase):
    def test_decide(self):
        self.assertEqual(ab.decide([0.1, 0.15], 0.2, "below"), "SUPPORTED")
        self.assertEqual(ab.decide([0.1, 0.3], 0.2, "below"), "INCONCLUSIVE")
        self.assertEqual(ab.decide([0.3, 0.4], 0.2, "below"), "CONTRADICTED")
        self.assertEqual(ab.decide([1.6, 2.0], 1.5, "above"), "SUPPORTED")
        self.assertEqual(ab.decide([0.9, 1.1], 1.5, "above"), "CONTRADICTED")

    def test_permutation_extreme(self):
        self.assertAlmostEqual(ab.permutation_p([10, 11, 12], [1, 2, 3]), 2 / 20)

    def test_analyze_excludes_failed(self):
        recs = [rec(0, "t", 1), rec(1, "r", 10), rec(2, "t", 2, exit=1), rec(3, "r", 10), rec(4, "t", 1)]
        out = ab.analyze(recs, "t", "r", 0.2, "below")
        self.assertEqual(out["excludedSeq"], [2])
        self.assertAlmostEqual(out["cpuS"]["ratioOfMedians"], 0.1)
        self.assertEqual(out["decisionPrimaryCpu"], "SUPPORTED")


if __name__ == "__main__":
    unittest.main()
