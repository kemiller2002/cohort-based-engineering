import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import summary_tool as s  # noqa: E402


def ev(r, rc="RC-X", et="x", human=False):
    return {"rehearsal": r, "rootCause": rc, "eventType": et, "humanIntervention": human}


class SummaryToolTests(unittest.TestCase):
    def test_missing_inputs_are_unavailable_not_zero(self):
        r = s.row("R9", {}, {}, {}, [])
        self.assertEqual(r["ciRunsWindow"], "unavailable")
        self.assertEqual(r["mergesInWindow"], "unavailable")
        self.assertEqual(r["plannedRequirements"], "unavailable")
        self.assertEqual(r["humanInterventionEvents"], 0)

    def test_counts_derive_from_events_of_that_rehearsal_only(self):
        evs = [ev("R1", "RC-GOV-UNTESTED", "plan-cycle", True), ev("R1", "RC-CONCURRENCY"),
               ev("R2", "RC-GOV-UNTESTED", human=True)]
        r = s.row("R1", {}, {}, {}, evs)
        self.assertEqual((r["governanceFailureEvents"], r["contractIncompatibilityEvents"],
                          r["integrationFailureEvents"], r["humanInterventionEvents"]), (1, 1, 1, 1))

    def test_ci_and_merge_values_pass_through(self):
        ci = {"R1": {"available": True, "windowRuns": 5, "windowFailures": 1, "windowCancelled": 2, "firstGreenBuildMin": None}}
        mg = {"R1": {"merges": 3, "sourceConflicts": 1, "recordsOnlyConflicts": 2}}
        r = s.row("R1", {}, ci, mg, [])
        self.assertEqual((r["ciRunsWindow"], r["ciCancelledWindow"], r["conflictedMerges_recordsOnly"]), (5, 2, 2))
        self.assertEqual(r["firstGreenBuildWorkflowMin_actions"], "unavailable")

    def test_csv_has_all_columns(self):
        text = s.to_csv([s.row("R1", {}, {}, {}, [])])
        header = text.splitlines()[0].split(",")
        self.assertEqual(tuple(header), s.COLUMNS)


if __name__ == "__main__":
    unittest.main()
