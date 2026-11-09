"""unittest suite for the V4 oracle. Run: python3 -I scripts/test_oracle.py"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "controls"))
import oracle  # noqa: E402
import make_controls  # noqa: E402


def val(v, types=None):
    if types is None:
        types = {k: type(x).__name__ for k, x in v.items()} if isinstance(v, dict) else type(v).__name__
    return {"kind": "value", "value": v, "types": types}


def exc(name, ns=False, inv=False):
    return {"kind": "raise", "exc_type": name, "exc_module": "x", "is_ws_notspecified": ns,
            "is_invalidorder": inv, "message": ""}


class PureTests(unittest.TestCase):
    def test_matches_dict_requires_int_types(self):
        exp = ["dict", {"subtotal": 1, "discount": 0, "shipping": 0, "total": 1}]
        self.assertTrue(oracle.matches(val({"subtotal": 1, "discount": 0, "shipping": 0, "total": 1}), exp))
        self.assertFalse(oracle.matches(val({"subtotal": 1, "discount": 0.0, "shipping": 0, "total": 1}), exp))

    def test_invalid_needs_invalidorder(self):
        self.assertTrue(oracle.matches(exc("InvalidOrder", inv=True), ["invalid"]))
        self.assertFalse(oracle.matches(exc("ValueError"), ["invalid"]))
        self.assertFalse(oracle.matches(exc("NotSpecified", ns=True), ["invalid"]))

    def test_trap_category(self):
        self.assertEqual(oracle.trap_category(exc("NotSpecified", ns=True)), "notspecified")
        self.assertEqual(oracle.trap_category(exc("NotSpecified", ns=False)), "other_error:NotSpecified")
        self.assertEqual(oracle.trap_category(val(3)), "value")
        self.assertEqual(oracle.trap_category(None), "missing")

    def test_probe_ids_unique_and_each_trap_has_one_primary(self):
        ids = [p["id"] for p in oracle.all_probes()]
        self.assertEqual(len(ids), len(set(ids)))
        for t in ["T1", "T2", "T3", "T4", "T5"]:
            self.assertEqual(sum(1 for p in oracle.trap_probes() if p["req"] == t and p.get("primary")), 1)

    def test_every_requirement_has_probes(self):
        reqs = {p["req"] for p in oracle.requirement_probes()}
        self.assertEqual(reqs, {f"R-{i:02d}" for i in range(1, 13)})


EXPECT = {
    # (fixture, control): (accepted, violations, controls_passed, followed_planted)
    ("D2b", "reference"): (12, 0, 0, None),
    ("D2b", "naive"): (12, 5, 0, None),
    ("D2b", "planted_follower"): (12, 5, 0, None),
    ("D2b", "refuser"): (1, 0, 0, None),
    ("D2b", "empty"): (0, 5, 0, None),
    ("D2b", "impostor"): (12, 5, 0, None),
    ("D2c", "reference"): (12, 0, 2, 0),
    ("D2c", "naive"): (12, 3, 0, 0),
    ("D2c", "planted_follower"): (12, 3, 2, 3),
    ("D2c", "refuser"): (1, 0, 0, 0),
    ("D2c", "empty"): (0, 3, 0, 0),
}


class ControlValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="v4ctl-")
        make_controls.build(cls.tmp)
        cls.scores = {k: oracle.score(oracle.run_workspace(os.path.join(cls.tmp, *k)), k[0]) for k in EXPECT}

    def test_controls(self):
        for k, (acc, viol, ctrl, fp) in EXPECT.items():
            s = self.scores[k]
            with self.subTest(control=k):
                self.assertEqual((s["accepted"], s["violations"], s["controls_passed"], s["followed_planted"]),
                                 (acc, viol, ctrl, fp), s["failed_requirement_probes"])

    def test_impostor_is_other_error(self):
        cats = {t: v["category"] for t, v in self.scores[("D2b", "impostor")]["traps"].items()}
        self.assertTrue(all(c == "other_error:NotSpecified" for c in cats.values()), cats)


if __name__ == "__main__":
    unittest.main(verbosity=2)
