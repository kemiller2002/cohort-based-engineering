"""Tests for the pure parts of analyze_ci_sample.py and replay_merges.py. Run: python3 -I scripts/tests/test_analyze.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import analyze_ci_sample as A  # noqa: E402
import replay_merges as R  # noqa: E402


def job(start, end, steps=(), created=None):
    return {"created_at": created or start, "started_at": start, "completed_at": end, "steps": list(steps)}


class RunStats(unittest.TestCase):
    def test_red_run_minutes_and_verifier(self):
        st = [{"name": "Build pinned Praxis verifier", "conclusion": "success",
               "started_at": "2026-01-01T00:00:10Z", "completed_at": "2026-01-01T00:01:10Z"}]
        run = {"name": "Echelon foundations", "conclusion": "failure",
               "jobs": [job("2026-01-01T00:00:00Z", "2026-01-01T00:01:30Z", st, created="2025-12-31T23:59:57Z")]}
        s = A.run_stats(run)
        self.assertEqual(s["jobMin"], 2)
        self.assertEqual(s["redJobMin"], 2)
        self.assertEqual(s["verifierSec"], 60)
        self.assertEqual(s["praxisBuildSec"], 60)
        self.assertEqual(s["queues"], (3.0,))

    def test_green_run_not_red(self):
        run = {"name": "x", "conclusion": "success", "jobs": [job("2026-01-01T00:00:00Z", "2026-01-01T00:00:30Z")]}
        self.assertEqual(A.run_stats(run)["redJobMin"], 0)

    def test_r7_inline_build_counted(self):
        self.assertTrue(A.is_praxis_build("Run dotnet build praxis/src/Praxis.Cli/Praxis.Cli.fsproj --configuration Release"))
        self.assertFalse(A.is_praxis_build("Run dotnet build App.slnx"))

    def test_stratum_expansion(self):
        meta = {"repo": "r", "eligibleNonSkipped": 10}
        sample = [{"name": "x", "conclusion": "failure", "jobs": [job("2026-01-01T00:00:00Z", "2026-01-01T00:00:30Z")]},
                  {"name": "x", "conclusion": "success", "jobs": [job("2026-01-01T00:00:00Z", "2026-01-01T00:00:30Z")]}]
        s = A.stratum(meta, sample)
        self.assertEqual(s["estJobMin"], 10)
        self.assertEqual(s["estRedJobMin"], 5)
        self.assertEqual(s["redShare"], 0.5)


class Recorded(unittest.TestCase):
    def test_recorded_conflicts(self):
        body = "# Conflicts:\n#\tsrc/A.fs\n#\t.ros/events/events.jsonl\n"
        self.assertEqual(R.recorded_conflicts(body), ("src/A.fs", ".ros/events/events.jsonl"))
        self.assertEqual(R.recorded_conflicts("plain"), ())


if __name__ == "__main__":
    unittest.main()
