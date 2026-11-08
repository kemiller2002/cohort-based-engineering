"""Consistency of committed artifacts with raw/ and with the read-only Indy-init clone (no percepta run needed)."""
import hashlib
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
import classify  # noqa: E402
import summarize  # noqa: E402

CLONE = "/home/user/sprint-scratch/B2/indy-init-full"


def runs(version):
    return json.load(open(os.path.join(TRACK, "raw", version, "runs.json"), encoding="utf-8"))


class RawTests(unittest.TestCase):
    def test_results_csv_regenerates_from_raw(self):
        committed = open(os.path.join(TRACK, "results.csv"), encoding="utf-8").read()
        self.assertEqual(summarize.csv_text(summarize.rows(TRACK)), committed)

    def test_comparison_regenerates(self):
        committed = json.load(open(os.path.join(TRACK, "comparison.json"), encoding="utf-8"))
        self.assertEqual(summarize.comparison(summarize.rows(TRACK), summarize.b3_rows()), committed)

    def test_input_hashes_match_git_objects(self):
        for r in runs("v0.4.0-4a53688"):
            for flag, meta in r["inputs"].items():
                blob = subprocess.run(["git", "-C", CLONE, "show", meta["source"]], check=True, capture_output=True).stdout
                self.assertEqual(hashlib.sha256(blob).hexdigest(), meta["sha256"], (r["package"], flag))

    def test_preregistered_expectations(self):
        rs = {(r["package"], r["condition"]): r for r in summarize.rows(TRACK) if r["version"] == "v0.4.0-4a53688"}
        r8 = rs[("R8-frozen", "DOC")]
        self.assertEqual(r8["exits"], "3/3/3/3/3")
        self.assertTrue(r8["R8-INV04"] and r8["R8-CMDBODY"] and r8["DEV-R8-12"])
        for p in ("R8-corrected", "R10-frozen", "Causa-frozen"):
            self.assertEqual(rs[(p, "DOC")]["exits"], "0/0/0/0/0")
            self.assertEqual(rs[(p, "DOC")]["findings"], "")
        self.assertFalse(rs[("R8-frozen", "CI")]["R8-CMDBODY"])  # no --catalog: carrier rule cannot fire

    def test_every_run_reproduced_its_report(self):
        for v in summarize.VERSIONS:
            self.assertTrue(all(r["reportsIdentical"] for r in runs(v)), v)

    def test_probe_identity_matches_baseline(self):
        probe = json.load(open(os.path.join(TRACK, "raw", "probe.json"), encoding="utf-8"))
        base = json.load(open(os.path.join(TRACK, "raw", "v0.4.0-4a53688", "R8-frozen.DOC.json"), encoding="utf-8"))
        p0 = next(p for p in probe if p["probe"] == "P0-identity")
        self.assertEqual(p0["perceptaFindings"], [classify.label(f) for f in classify.findings(base)])


if __name__ == "__main__":
    unittest.main()
