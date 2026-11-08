"""unittest suite for release_history.py (SPR-C2-01 H4).

Run: python3 -I -m unittest discover -s harness -p 'test_*.py'   (from the track dir)
The live test reads /home/user/ext/conditor read-only and is skipped if absent.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_history as rh  # noqa: E402

CONDITOR = "/home/user/ext/conditor"


def desc(cid, versions, distribution="npm", rng=None, **extra):
    d = {"id": cid, "distribution": distribution, "qualifiedVersions": versions, **extra}
    return dict(d, qualifiedRange=rng) if rng else d


class RangeTests(unittest.TestCase):
    def test_in_range(self):
        self.assertTrue(rh.in_range(">=0.2.0 <1.0.0", "0.13.0"))
        self.assertFalse(rh.in_range(">=0.2.0 <1.0.0", "1.0.0"))
        self.assertFalse(rh.in_range(">=0.2.0 <1.0.0", "0.1.9"))
        self.assertFalse(rh.in_range(None, "0.5.0"))


class ClassifyTests(unittest.TestCase):
    def test_project_binding_in_range_is_avoidable(self):
        before = {"forma": desc("forma", ["0.12.0"], rng=">=0.2.0 <1.0.0")}
        after = {"forma": desc("forma", ["0.12.0", "0.13.0"], rng=">=0.2.0 <1.0.0")}
        self.assertEqual(rh.classify(rh.component_changes(before, after)), "avoidable")

    def test_host_tool_is_required(self):
        before = {"praxis": desc("praxis", ["3.24.0"], "host-tool")}
        after = {"praxis": desc("praxis", ["3.24.0", "3.25.0"], "host-tool")}
        self.assertEqual(rh.classify(rh.component_changes(before, after)), "required")

    def test_mixed_release_is_required(self):
        before = {"forma": desc("forma", ["0.12.0"], rng=">=0.2.0 <1.0.0"), "ordo": desc("ordo", ["1.19.0"], "host-tool")}
        after = {"forma": desc("forma", ["0.12.0", "0.13.0"], rng=">=0.2.0 <1.0.0"), "ordo": desc("ordo", ["1.19.0", "1.20.0"], "host-tool")}
        self.assertEqual(rh.classify(rh.component_changes(before, after)), "required")

    def test_new_descriptor_is_required(self):
        after = {"forma-workflow": desc("forma-workflow", ["1.2.0"], rng=">=1.2.0 <2.0.0")}
        self.assertEqual(rh.classify(rh.component_changes({}, after)), "required")

    def test_other_descriptor_change_is_required(self):
        before = {"folio": desc("folio", ["0.4.0"], rng=">=0.3.0 <1.0.0")}
        after = {"folio": desc("folio", ["0.4.0"], rng=">=0.3.0 <1.0.0", releaseArtifacts=[{"version": "0.4.0"}])}
        self.assertEqual(rh.classify(rh.component_changes(before, after)), "required")

    def test_no_change(self):
        self.assertEqual(rh.classify([]), "no-catalog")


@unittest.skipUnless(os.path.isdir(os.path.join(CONDITOR, ".git")), "conditor checkout not present")
class LiveHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = rh.analyse(CONDITOR)

    def test_thirteen_releases(self):
        self.assertEqual(len(self.result["releases"]), 13)

    def test_counts_sum(self):
        self.assertEqual(sum(self.result["counts"].values()), 13)


if __name__ == "__main__":
    unittest.main()
