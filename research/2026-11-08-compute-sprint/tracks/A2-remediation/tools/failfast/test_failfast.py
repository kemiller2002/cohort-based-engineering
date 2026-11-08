"""Unit tests for failfast.py (python3 -m unittest test_failfast)."""
import unittest

import failfast as ff


def cat(name):
    return {"b": "build", "w": "browser-test", "s": "runner-setup"}[name[0]]


def step(n, name, concl, start, end):
    return {"number": n, "name": name, "conclusion": concl,
            "started_at": f"2026-01-01T00:{start:02d}:00Z", "completed_at": f"2026-01-01T00:{end:02d}:00Z"}


def job(name, concl, steps, start=0, end=10):
    return {"name": name, "conclusion": concl, "steps": steps,
            "started_at": f"2026-01-01T00:{start:02d}:00Z", "completed_at": f"2026-01-01T00:{end:02d}:00Z"}


class FailFastTests(unittest.TestCase):
    def test_within_job_browser_before_failing_build(self):
        j = job("a", "failure", [step(1, "s", "success", 0, 1), step(2, "w", "success", 1, 5), step(3, "b", "failure", 5, 6)])
        self.assertEqual(ff.within_job_saving(ff.classify_steps(j, cat)), 240.0)

    def test_no_saving_when_browser_step_fails(self):
        j = job("a", "failure", [step(1, "b", "success", 0, 1), step(2, "w", "failure", 1, 5)])
        self.assertEqual(ff.within_job_saving(ff.classify_steps(j, cat)), 0.0)

    def test_across_jobs(self):
        failing = job("build", "failure", [step(1, "b", "failure", 0, 2)], 0, 2)
        browser = job("e2e", "success", [step(1, "s", "success", 0, 1), step(2, "w", "success", 1, 9)], 0, 9)
        s = ff.run_savings([failing, browser], cat)
        self.assertEqual(s["acrossV1"], 480.0)
        self.assertEqual(s["acrossV2"], 540.0)
        self.assertTrue(s["failedRun"])

    def test_cancelled_jobs_excluded(self):
        failing = job("build", "failure", [step(1, "b", "failure", 0, 2)], 0, 2)
        browser = job("e2e", "cancelled", [step(1, "w", "cancelled", 1, 9)], 0, 9)
        self.assertEqual(ff.run_savings([failing, browser], cat)["acrossV2"], 0.0)

    def test_green_run_no_saving(self):
        s = ff.run_savings([job("e2e", "success", [step(1, "w", "success", 0, 5)])], cat)
        self.assertEqual((s["within"], s["acrossV1"], s["failedRunSeconds"]), (0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
