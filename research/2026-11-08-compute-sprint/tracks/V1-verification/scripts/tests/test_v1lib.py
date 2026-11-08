"""Run: python3 -I -m unittest discover -s scripts/tests -t scripts  (from the track dir)
or:  python3 -I scripts/tests/test_v1lib.py"""
import os
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import v1lib as L  # noqa: E402

PRICE = {"input": 4.0, "output": 20.0, "cacheRead": 0.2, "cacheWrite5m": 5.0, "cacheWrite1h": 8.0}


class Pricing(unittest.TestCase):
    def test_r3_reported_cost(self):
        # R3 timed buckets from its tokens-final.json; R3 reported $36.01 at list price, 5m cache writes
        b = {"input": 540, "output": 351661, "cacheRead": 115269197, "cacheWrite": 1183427}
        self.assertAlmostEqual(round(L.price_cost(b, PRICE, split_cache_write=False), 2), 36.01)

    def test_split_used_only_when_consistent(self):
        b = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 1_000_000, "cacheWrite5m": 0, "cacheWrite1h": 1_000_000}
        self.assertAlmostEqual(L.price_cost(b, PRICE), 8.0)
        bad = dict(b, cacheWrite1h=5)
        self.assertAlmostEqual(L.price_cost(bad, PRICE), 5.0)

    def test_total4_requires_all(self):
        self.assertIsNone(L.total4({"input": 1, "output": 2, "cacheRead": 3}))
        self.assertEqual(L.total4({"input": 1, "output": 2, "cacheRead": 3, "cacheWrite": 4}), 10)

    def test_metric_buckets(self):
        ms = [{"id": "tokens.input", "value": 3}, {"id": "time.wall_ms", "value": 9}, {"id": "tokens.cache_write_1h", "value": 2}]
        self.assertEqual(L.metric_buckets(ms), {"input": 3, "cacheWrite1h": 2})

    def test_ledger_rows_and_context(self):
        led = {"columns": ["input", "output", "cacheRead", "cacheWrite", "cacheWrite5m", "cacheWrite1h", "reasoning"],
               "rows": [{"key": "m1", "model": "x", "usage": [2, 180, 49007, 18613, 0, 18613, 19]}]}
        rows = L.ledger_rows(led)
        self.assertEqual(L.context_tokens(rows[0]), 2 + 49007 + 18613)


class Stats(unittest.TestCase):
    def test_median(self):
        self.assertEqual(L.median([3, 1, 2]), 2)
        self.assertEqual(L.median([1, 2, 3, 4]), 2.5)

    def test_ceil_minutes(self):
        self.assertEqual(L.ceil_minutes(0), 0)
        self.assertEqual(L.ceil_minutes(1), 1)
        self.assertEqual(L.ceil_minutes(60), 1)
        self.assertEqual(L.ceil_minutes(61), 2)

    def test_quantile(self):
        self.assertEqual(L.quantile_nearest_rank(list(range(1, 11)), 0.9), 9)


class Concurrency(unittest.TestCase):
    def test_samples_and_exact(self):
        t0 = L.parse_ts("2026-01-01T00:00:00Z")
        spans = ((t0, t0 + timedelta(minutes=2)), (t0 + timedelta(minutes=1), t0 + timedelta(minutes=3)))
        self.assertEqual(L.concurrency_samples(spans, t0, 4), (1, 2, 1, 0))
        self.assertAlmostEqual(L.exact_mean_concurrency(spans, t0, t0 + timedelta(minutes=4)), 1.0)
        self.assertAlmostEqual(L.union_minutes(spans), 3.0)


class Merges(unittest.TestCase):
    def test_parse_merge_tree(self):
        out = "abc123\n.ros/context/current.json\n.ros/events/events.jsonl\n\nAuto-merging x\nCONFLICT (content): ...\n"
        self.assertEqual(L.parse_merge_tree_conflicts(out), (".ros/context/current.json", ".ros/events/events.jsonl"))
        self.assertEqual(L.parse_merge_tree_conflicts("abc123\n"), ())

    def test_state_path(self):
        self.assertTrue(L.is_praxis_state(".ros/events/events.jsonl"))
        self.assertFalse(L.is_praxis_state("src/App.fs"))


class CI(unittest.TestCase):
    def test_window(self):
        self.assertTrue(L.in_window("2026-10-23T12:14:13Z", "2026-10-23T12:14:13Z"))
        self.assertFalse(L.in_window("2026-10-23T19:14:13Z", "2026-10-23T12:14:13Z"))
        self.assertTrue(L.in_window("2026-10-23T19:14:12Z", "2026-10-23T12:14:13Z"))

    def test_job_seconds_and_queue(self):
        j = {"created_at": "2026-01-01T00:00:00Z", "started_at": "2026-01-01T00:00:03Z", "completed_at": "2026-01-01T00:01:04Z"}
        self.assertEqual(L.job_seconds(j), 61)
        self.assertEqual(L.queue_seconds(j), 3)
        self.assertEqual(L.job_seconds({"started_at": None}), 0.0)


if __name__ == "__main__":
    unittest.main()
