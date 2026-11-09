import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ci_metrics as m  # noqa: E402

META = {"id": "RX", "repo": "r", "t0": "2026-01-01T10:00:00Z", "ceilingMinutes": 60,
        "buildWorkflows": ["Build"], "deployWorkflows": ["Deploy"]}


def run(name, concl, created, updated):
    return {"name": name, "conclusion": concl, "created_at": created, "updated_at": updated}


RUNS = (
    run("Build", "success", "2026-01-01T09:50:00Z", "2026-01-01T09:55:00Z"),  # before t0
    run("Build", "failure", "2026-01-01T10:05:00Z", "2026-01-01T10:10:00Z"),
    run("Build", "success", "2026-01-01T10:20:00Z", "2026-01-01T10:30:00Z"),
    run("Build", "success", "2026-01-01T10:15:00Z", "2026-01-01T10:40:00Z"),
    run("Deploy", "cancelled", "2026-01-01T10:31:00Z", "2026-01-01T10:32:00Z"),
    run("Deploy", "success", "2026-01-01T11:30:00Z", "2026-01-01T11:35:00Z"),  # after window
)


class CiMetricsTests(unittest.TestCase):
    def test_window_excludes_runs_outside(self):
        s = m.summarize(META, RUNS)
        self.assertEqual(s["totalRuns"], 6)
        self.assertEqual(s["windowRuns"], 4)
        self.assertEqual(s["windowFailures"], 1)
        self.assertEqual(s["windowCancelled"], 1)

    def test_first_green_ignores_pre_t0_and_uses_earliest_finish(self):
        self.assertEqual(m.summarize(META, RUNS)["firstGreenBuildMin"], 30.0)

    def test_first_deploy_may_fall_outside_window(self):
        self.assertEqual(m.summarize(META, RUNS)["firstDeployMin"], 95.0)

    def test_missing_workflow_is_none_not_zero(self):
        meta = {**META, "deployWorkflows": []}
        self.assertIsNone(m.summarize(meta, RUNS)["firstDeployMin"])

    def test_no_runs_is_unavailable(self):
        self.assertEqual(m.summarize(META, ()), {"id": "RX", "repo": "r", "available": False})

    def test_per_workflow_counts_are_immutable_accumulation(self):
        self.assertEqual(m.per_workflow(RUNS[:3]), {"Build": {"success": 2, "failure": 1}})


if __name__ == "__main__":
    unittest.main()
