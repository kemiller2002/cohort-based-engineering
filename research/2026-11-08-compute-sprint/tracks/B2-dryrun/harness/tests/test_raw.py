"""Consistency tests over the committed raw replay records (skipped when a record is absent)."""
import json
import unittest
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "raw"
OUTCOMES = {"CAUGHT", "NOT CAUGHT", "NOT REPLAYABLE"}
FIELDS = {"key", "rehearsal", "blocker", "trackBEvent", "t0", "preT0", "toolsRun", "check", "outcome",
          "matchEvidence", "dryRunSeconds"}


def load(key):
    p = RAW / f"{key}.json"
    return json.loads(p.read_text()) if p.exists() else None


class Raw(unittest.TestCase):
    def test_every_record_well_formed(self):
        for p in RAW.glob("*.json"):
            r = json.loads(p.read_text())
            self.assertTrue(FIELDS <= set(r), (p.name, FIELDS - set(r)))
            self.assertIn(r["outcome"], OUTCOMES, p.name)
            self.assertEqual(r["key"], p.stem)

    def test_indy_init_inputs_precede_t0(self):
        for key in ("R4-APPROVALS", "R8-APPROVALS", "R8-CMDBODY", "R8-INV04", "R8-MSB1008", "R9-MSB1008",
                    "R10-AUTH", "CAUSA-CYCLE", "CAUSA-RULES"):
            r = load(key)
            if r:
                self.assertTrue(r["preT0IsBeforeT0"], key)

    def test_r10_auth_reproduces_historical_causes(self):
        r = load("R10-AUTH")
        if r is None:
            self.skipTest("no record")
        self.assertEqual(r["check"]["causeCount"], 55)
        self.assertTrue(r["historical"]["identicalCauseSet"])
        self.assertEqual(r["falsePositiveCheck"]["exit"], 0)

    def test_approvals_fixed_versions_clean(self):
        for key in ("R4-APPROVALS", "R8-APPROVALS"):
            r = load(key)
            if r:
                self.assertEqual(r["falsePositiveCheck"]["approvalProblems"], [], key)
                self.assertTrue(r["check"]["approvalProblems"], key)


if __name__ == "__main__":
    unittest.main()
