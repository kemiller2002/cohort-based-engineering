"""Unit tests for bench.py. Run: python3 -m unittest -v test_bench"""
import unittest

import bench


class ScheduleTests(unittest.TestCase):
    def test_abba_balanced_and_alternating(self):
        order = bench.schedule(["X", "Y"], 4, seed=3)
        self.assertEqual(len(order), 8)
        self.assertEqual(order.count("X"), 4)
        self.assertEqual(order[0:2], order[2:4][::-1])

    def test_seed_reproducible(self):
        self.assertEqual(bench.schedule(["A", "B", "C"], 3, 9, "random"), bench.schedule(["A", "B", "C"], 3, 9, "random"))

    def test_random_blocks_are_permutations(self):
        order = bench.schedule(["A", "B", "C"], 2, 1, "random")
        self.assertEqual(sorted(order[:3]), ["A", "B", "C"])
        self.assertEqual(sorted(order[3:]), ["A", "B", "C"])


class ParseTests(unittest.TestCase):
    def test_parse_two_assemblies(self):
        text = ("Passed!  - Failed:     0, Passed:    12, Skipped:     0, Total:    12, Duration: 1 s - A.dll\n"
                "Failed!  - Failed:     1, Passed:     3, Skipped:     1, Total:     5, Duration: 1 s - B.dll\n")
        self.assertEqual(bench.parse_test_counts(text),
                         {"failed": 1, "passed": 15, "skipped": 1, "total": 17, "assemblies": 2})

    def test_parse_none(self):
        self.assertEqual(bench.parse_test_counts("nothing")["assemblies"], 0)


class SummaryTests(unittest.TestCase):
    def test_median(self):
        self.assertEqual(bench.median([3, 1, 2]), 2)
        self.assertEqual(bench.median([4, 1, 2, 3]), 2.5)

    def test_summarize_excludes_failures(self):
        recs = [{"arm": "A", "exit": 0, "wallS": 1.0}, {"arm": "A", "exit": 1, "wallS": 99.0},
                {"arm": "B", "exit": 0, "wallS": 2.0}]
        s = bench.summarize(recs)
        self.assertEqual(s["A"]["n"], 1)
        self.assertEqual(s["B"]["median"], 2.0)


if __name__ == "__main__":
    unittest.main()
