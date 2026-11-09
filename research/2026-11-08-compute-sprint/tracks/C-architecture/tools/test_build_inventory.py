"""Unit tests for build_inventory.py (run: python3 -I tools/test_build_inventory.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_inventory as bi  # noqa: E402

EDGES = [
    {"from": "app", "to": "limen", "type": "package-ref", "vias": ["npm:@echelon-foundry/limen"], "versions": ["0.9.0"]},
    {"from": "app", "to": "praxis", "type": "CLI-invocation", "vias": ["praxis validate"], "versions": []},
    {"from": "app", "to": "tutela", "type": "doc-only-claim", "vias": ["README"], "versions": []},
    {"from": "limen", "to": "praxis", "type": "contract/schema", "vias": ["ros-pin"], "versions": ["3.7.2"]},
]
SKEW = [
    {"consumer": "app", "component": "limen", "pinned": "0.9.0", "approved": "0.9.1", "skew": "patch-behind"},
    {"consumer": "lib", "component": "limen-fsharp", "pinned": "0.9.0", "approved": "0.9.0", "skew": "current"},
    {"consumer": "limen", "component": "limen", "pinned": "0.9.1", "approved": "0.9.1", "skew": "current"},
]


class Tests(unittest.TestCase):
    def test_consumers_exclude_doc_only(self):
        self.assertEqual(bi.consumers_of("tutela", EDGES), [])
        self.assertEqual(bi.consumers_of("praxis", EDGES),
                         [{"repository": "app", "edgeTypes": ["CLI-invocation"]},
                          {"repository": "limen", "edgeTypes": ["contract/schema"]}])

    def test_dependencies(self):
        deps = bi.dependencies_of("app", EDGES)
        self.assertEqual([d["system"] for d in deps], ["limen", "praxis", "tutela"])
        self.assertEqual(deps[0]["versions"], ["0.9.0"])

    def test_pin_summary_includes_sub_ids_and_skips_self(self):
        s = bi.pin_summary("limen", SKEW)
        self.assertEqual(s["pins"], 2)
        self.assertEqual(s["consumersBySkew"], {"current": ["lib"], "patch-behind": ["app"]})

    def test_test_coverage(self):
        self.assertEqual(bi.test_coverage({}), "NOT TESTED")
        self.assertIn("3/10 test/source files", bi.test_coverage({"sourceFiles": 10, "testFiles": 3}))

    def test_build_inventory_has_all_fields(self):
        inv = bi.build_inventory({"_note": "x", "limen": {"intendedResponsibility": "boundary"}},
                                 {"approvedSet": "s", "edges": EDGES}, SKEW, {}, {})
        self.assertEqual(list(inv["systems"]), ["limen"])
        self.assertEqual(bi.missing_fields(inv), [])
        self.assertEqual(inv["systems"]["limen"]["currentRelease"]["version"], None)


if __name__ == "__main__":
    unittest.main()
