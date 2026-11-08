import unittest
from x02 import assign, stratified_exact_p
class T(unittest.TestCase):
    def test_assign_balance(self):
        a = assign()
        self.assertEqual(len(a), 24)
        for fx in ("D2b", "D2c"):
            self.assertEqual(sum(1 for r in a if r["fixture"] == fx and r["arm"] == "G"), 6)
            self.assertEqual(sum(1 for r in a if r["fixture"] == fx and r["arm"] == "M"), 6)
        for b in range(1, 5):
            rows = [r for r in a if r["batch"] == b]
            self.assertEqual(len(rows), 6); self.assertEqual(sum(r["arm"] == "G" for r in rows), 3)
        self.assertEqual(len({r["runId"] for r in a}), 24)
    def test_assign_deterministic(self):
        self.assertEqual(assign(), assign())
    def test_null_p_is_one(self):
        v = {"A": [("G", 1), ("M", 1), ("G", 1), ("M", 1)], "B": [("G", 0), ("M", 0)]}
        self.assertEqual(stratified_exact_p(v)[1], 1.0)
    def test_complete_separation_small(self):
        v = {"A": [("G", 0), ("G", 0), ("M", 1), ("M", 1)]}
        obs, p = stratified_exact_p(v)
        self.assertEqual(obs, 1.0); self.assertAlmostEqual(p, 2 / 6)
    def test_min_p_full_design(self):
        v = {fx: [("G", 0)] * 6 + [("M", 3)] * 6 for fx in ("D2b", "D2c")}
        self.assertAlmostEqual(stratified_exact_p(v)[1], 2 / (924 * 924))
if __name__ == "__main__":
    unittest.main()
