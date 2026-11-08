import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dryrun import checks as c  # noqa: E402


class Checks(unittest.TestCase):
    def test_pre_t0(self):
        self.assertTrue(c.is_pre_t0("2026-10-27T02:04:14-04:00", "2026-10-27T06:04:39Z"))
        self.assertFalse(c.is_pre_t0("2026-10-27T02:05:00-04:00", "2026-10-27T06:04:39Z"))

    def test_approvals_schema(self):
        self.assertEqual(c.approvals_schema_problems({"schema": "causa.requirements-approvals/1"}), [])
        self.assertEqual(len(c.approvals_schema_problems({"schema": "praxis.requirements-approvals/1"})), 1)
        self.assertEqual(len(c.approvals_schema_problems([])), 1)

    def test_dotnet_targets(self):
        self.assertEqual(c.dotnet_test_targets("dotnet test a b --filter \"X~Y\""), ["a", "b"])
        self.assertEqual(c.dotnet_test_targets("dotnet test tests/A --filter FullyQualifiedName~A."), ["tests/A"])
        self.assertEqual(c.dotnet_test_targets("npx playwright test"), [])

    def test_playwright_projects(self):
        self.assertEqual(c.playwright_projects("npx playwright test --project=webkit tests/x"), ["webkit"])

    def test_classify(self):
        self.assertEqual(c.classify_suite_run("MSBUILD : error MSB1008: Only one project can be specified.", 1), "MSB1008")
        self.assertEqual(c.classify_suite_run("/scratch/R9-MSB1008/x.dll built", 0), "OK")
        self.assertEqual(c.suite_findings("[xUnit.net] Skipping: A (could not find dependent assembly 'FSharp.Core')\n"
                                          "No test matches the given testcase filter `x`", 0),
                         ["ASSEMBLY_SKIPPED", "NO_TESTS_SELECTED"])
        self.assertEqual(c.classify_suite_run("Error: No tests found.", 1), "NO_TESTS_SELECTED")
        self.assertEqual(c.classify_suite_run('Error: Project(s) "webkit" not found. Available projects: "chromium"', 1),
                         "UNDEFINED_PLAYWRIGHT_PROJECT")
        self.assertEqual(c.classify_suite_run("Total tests: 1", 0), "OK")
        self.assertEqual(c.classify_suite_run("boom", 1), "OTHER_FAILURE")

    def test_scc(self):
        self.assertEqual(c.strongly_connected({"a": {"b"}, "b": {"a"}, "c": {"a"}}), [["a", "b"]])
        self.assertEqual(c.strongly_connected({"a": {"b"}, "b": {"c"}}), [])
        self.assertEqual(c.strongly_connected({"a": {"a"}}), [["a"]])

    def test_slice_edges(self):
        slices = [{"id": "S1", "requirements": ["R1"], "dependsOn": [], "acceptanceTests": ["t1"], "governedAssertions": ["J1"]},
                  {"id": "S2", "requirements": ["R2"], "dependsOn": ["S1"], "acceptanceTests": [], "governedAssertions": []}]
        v1 = c.declared_edges(slices)
        self.assertEqual(c.strongly_connected(v1), [])
        v2 = c.test_owner_edges(slices, {"t1": ["R2-O1"]}, {"R2-O1": "R2"})
        self.assertEqual(c.strongly_connected(c.merge_edges(v1, v2)), [["S1", "S2"]])
        v3 = c.assertion_need_edges(slices, [{"assertions": ["J1"], "needs": ["S2"]}])
        self.assertEqual(c.cycle_containing(c.strongly_connected(c.merge_edges(v1, v3)), ["S1", "S2"]), [["S1", "S2"]])

    def test_rules_binding(self):
        self.assertEqual(c.rules_binding_problems("causa-t0", ["causa", "causa-t0"]), [])
        self.assertEqual(len(c.rules_binding_problems("indy-init-rehearsal-010", ["causa"])), 1)

    def test_budget(self):
        self.assertTrue(c.budget_verdict(20, 29 * 60)["exceedsCap"])
        self.assertFalse(c.budget_verdict(20, 10 * 60)["exceedsCap"])
        rows = [{"step": "a", "seconds": "5"}, {"step": "a", "seconds": "9"}, {"step": "b", "seconds": ""}]
        self.assertEqual(c.max_by_kind(rows, {"a": lambda r: r["step"] == "a", "z": lambda r: False}), {"a": 9.0, "z": 0.0})

    def test_outcome_and_rate(self):
        self.assertEqual(c.outcome(False, True), c.NOT_REPLAYABLE)
        self.assertEqual(c.outcome(True, True), c.CAUGHT)
        r = c.catch_rate([c.CAUGHT, c.NOT_CAUGHT, c.NOT_REPLAYABLE, c.CAUGHT])
        self.assertEqual((r["caught"], r["replayable"], r["rate"]), (2, 3, 0.667))


if __name__ == "__main__":
    unittest.main()
