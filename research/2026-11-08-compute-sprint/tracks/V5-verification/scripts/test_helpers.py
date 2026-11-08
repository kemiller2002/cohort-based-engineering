"""unittest for compare_x03 / analyze_x03 / confounds_x03 / verdicts_lib pure functions. Run: python3 -I -B scripts/test_helpers.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_x03 as an  # noqa: E402
import compare_x03 as cmp  # noqa: E402
import confounds_x03 as cf  # noqa: E402
import verdicts_lib as vl  # noqa: E402


def v5(viol_traps, fixture="D2b", planted=None):
    traps = {t: {"violated": t in viol_traps} for t in (["T1", "T2", "T3", "T4", "T5"] if fixture == "D2b" else ["T1", "T3", "T4"])}
    return {"fixture": fixture, "violations": len(viol_traps), "accepted": 12,
            "controls_passed": 2 if fixture == "D2c" else 0, "followed_planted": None if planted is None else sum(planted.values()),
            "followed_planted_detail": planted, "traps": traps}


def committed(viol_traps, fixture="D2b", planted=None):
    traps = {t: {"violated_raised_measure": v["violated"]} for t, v in v5(viol_traps, fixture)["traps"].items()}
    for t, p in (planted or {}).items():
        traps[t]["followed_planted"] = p
    return {"trap_violations": len(viol_traps), "accepted": 12, "controls_passed": 2 if fixture == "D2c" else None,
            "followed_planted": None if planted is None else sum(planted.values()), "traps": traps}


class Compare(unittest.TestCase):
    def test_agree(self):
        r = cmp.compare({"a": v5(["T5"])}, {"a": committed(["T5"])})
        self.assertEqual((r["runs_agree_all_fields"], r["trap_cells_agree"]), (1, 5))

    def test_trap_and_planted_disagreement_detected(self):
        p1, p2 = {"T1": False, "T3": True, "T4": False}, {"T1": False, "T3": False, "T4": False}
        r = cmp.compare({"b": v5(["T3"], "D2c", p1)}, {"b": committed(["T4"], "D2c", p2)})
        fields = {d["field"] for d in r["disagreements"]["b"]}
        self.assertTrue({"trap_violated.T3", "trap_violated.T4", "planted.T3", "fp"} <= fields)


class Documentation(unittest.TestCase):
    def test_topics(self):
        q = "1. **Rounding.** not specified\n\n2. Which day decides the weekend: local offset or UTC?\n"
        self.assertTrue(an.documented(q, "T3"))
        self.assertTrue(an.documented(q, "T5"))
        self.assertFalse(an.documented(q, "T2"))
        self.assertFalse(an.documented(None, "T3"))


class Confounds(unittest.TestCase):
    def test_arm_from_files(self):
        self.assertEqual(cf.arm_from_files(["pricing.py", "QUESTIONS.md", "EVIDENCE.md"]), "K")
        self.assertEqual(cf.arm_from_files(["pricing.py"]), "C")
        self.assertEqual(cf.arm_from_files(["QUESTIONS.md"]), "ambiguous")

    def test_imports(self):
        self.assertEqual(cf.imports_of("import os.path\nfrom datetime import datetime\nfrom . import x\n"), [".", "datetime", "os"])


class Verdicts(unittest.TestCase):
    def test_upsert_replaces_and_validates(self):
        e = {k: k for k in vl.FIELDS}
        e2 = dict(e, verdict="X")
        self.assertEqual(vl.upsert([e], e2), [e2])
        with self.assertRaises(ValueError):
            vl.upsert([], {"claimId": "x"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
