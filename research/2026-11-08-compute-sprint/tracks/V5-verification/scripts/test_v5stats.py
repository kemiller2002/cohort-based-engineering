"""unittest for v5stats. Run: python3 -I -B scripts/test_v5stats.py"""
import os
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v5stats as s  # noqa: E402


class T(unittest.TestCase):
    def test_matches_bruteforce(self):
        cases = [
            [([1, 1, 1], [2, 4, 5])],
            [([1, 1, 1], [2, 4, 5]), ([0, 0], [1, 2, 0])],
            [([3, 1], [1, 3]), ([0, 0, 1], [1, 0])],
        ]
        for c in cases:
            self.assertEqual(s.perm_test(c), s.brute_perm_test(c))

    def test_extreme_single_stratum(self):
        r = s.perm_test([([0, 0, 0], [1, 1, 1])])
        self.assertEqual(r["N"], 20)
        self.assertEqual(r["p"], Fraction(2, 20))

    def test_null_identical(self):
        self.assertEqual(s.perm_test([([1, 2], [1, 2])])["p"], 1)

    def test_constant_shift_invariance(self):
        a = [([1, 1, 1], [2, 4, 5]), ([0, 0, 0], [1, 2, 0])]
        b = [([0, 0, 0], [1, 3, 4]), ([0, 0, 0], [1, 2, 0])]
        self.assertEqual(s.perm_test(a)["p"], s.perm_test(b)["p"])

    def test_holm(self):
        h = s.holm({"a": Fraction(1, 100), "b": Fraction(4, 100), "c": Fraction(3, 100)})
        self.assertEqual(h, {"a": Fraction(3, 100), "c": Fraction(6, 100), "b": Fraction(6, 100)})
        self.assertEqual(s.holm({"x": Fraction(9, 10), "y": Fraction(8, 10)})["x"], 1)

    def test_decimal_inputs_exact(self):
        self.assertEqual(s.mean([0.1, 0.2]), Fraction(3, 20))


if __name__ == "__main__":
    unittest.main(verbosity=2)
