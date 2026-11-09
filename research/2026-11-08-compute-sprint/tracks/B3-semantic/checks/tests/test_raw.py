"""Raw records are reproducible: re-running the checks on the R8 frozen package from git objects gives the committed
alarm subjects (skipped when the read-only clone is absent)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from semcheck import run  # noqa: E402

RAW = Path(__file__).resolve().parents[2] / "raw"


@unittest.skipUnless(Path(run.REPO).is_dir(), "read-only Indy-init clone not present")
class Reproduce(unittest.TestCase):
    def test_r8_and_control_alarm_subjects(self):
        for label, role, rev, pkg, manifest in run.PACKAGES:
            fresh = run.run_package(run.REPO, label, role, rev, pkg, manifest)["results"]
            stored = json.loads((RAW / (label.split("=")[0] + ".json")).read_text())["results"]
            for k in ("C1-loop", "C1-cycle", "C2", "C2b", "C3"):
                self.assertEqual(json.dumps(fresh[k], sort_keys=True), json.dumps(stored[k], sort_keys=True), (label, k))

    def test_primary_outcomes(self):
        r8 = json.loads((RAW / "R8-frozen.json").read_text())["results"]
        self.assertTrue({"T-S31", "T-S32"} <= {a["transition"] for a in r8["C1-loop"] if a["invariant"] == "INV-04"})
        self.assertIn("type CommandEnvelope", {a["candidate"] for a in r8["C2"]})
        for f in ("R8-corrected", "R10-frozen", "Causa-frozen"):
            res = json.loads((RAW / (f + ".json")).read_text())["results"]
            self.assertEqual((len(res["C1-loop"]), len(res["C2"])), (0, 0), f)


if __name__ == "__main__":
    unittest.main()
