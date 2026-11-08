import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import classify  # noqa: E402


def f(rule, subjects, blocking=True, detail="", kind="x"):
    return {"rule": rule, "subjects": subjects, "blocking": blocking, "detail": detail, "kind": kind}


INV = f("rate-bound-vs-unbounded-loop", ["INV-04", "SM-SAVE", "T-S31"])
CMD = f("carrier-cannot-discriminate", ["CommandEnvelope", "IF41-X.Decide"])
GAP = f("counter-guard-without-complement", ["SM-SAVE", "T-S29"], False,
        "SM-SAVE (UnknownOutcome, ReconcileReadFailed) is specified only when ...")


class ClassifyTests(unittest.TestCase):
    def test_all_three_r8_defects_match(self):
        r = classify.classify({"blocked": True, "blockingContradictions": [INV], "missingInterfaces": [CMD],
                               "missingDecisions": [GAP]})
        self.assertTrue(all(r["defects"][d]["caught"] for d in ("R8-INV04", "R8-CMDBODY", "DEV-R8-12")))
        self.assertFalse(r["defects"]["CAUSA-T18-T20"]["caught"])
        self.assertEqual(r["unmatched"], [])

    def test_non_blocking_or_wrong_subject_does_not_match(self):
        self.assertFalse(classify.is_inv04(dict(INV, blocking=False)))
        self.assertFalse(classify.is_inv04(f("rate-bound-vs-unbounded-loop", ["INV-04", "SM-SAVE", "T-S47"])))
        self.assertFalse(classify.is_cmdbody(f("carrier-cannot-discriminate", ["RefusedCommand"])))
        self.assertFalse(classify.is_dev_r8_12(dict(GAP, detail="SM-SAVE (UnknownOutcome, CheckAgain)")))

    def test_duplicates_across_sections_count_once_and_extras_are_split(self):
        extra = f("counter-guard-without-complement", ["SM-SAVE", "T-S31"], False, "(UnknownOutcome, CheckAgain)")
        r = classify.classify({"blockingContradictions": [INV], "warnings": [INV], "missingDecisions": [extra]})
        self.assertEqual(r["defects"]["R8-INV04"]["by"], ["rate-bound-vs-unbounded-loop:INV-04/SM-SAVE/T-S31"])
        self.assertEqual((r["unmatchedBlocking"], r["unmatchedNonBlocking"]), (0, 1))

    def test_empty_report(self):
        r = classify.classify({"blocked": False})
        self.assertFalse(any(v["caught"] for v in r["defects"].values()))
        self.assertEqual(r["unmatchedBlocking"], 0)

    def test_t18_t20(self):
        self.assertTrue(classify.mentions_t18_t20(f("r", ["SL-T18", "SL-T20"])))
        self.assertFalse(classify.mentions_t18_t20(f("r", ["SL-T18"])))

    def test_median(self):
        self.assertEqual(classify.median([3, 1, 2]), 2)
        self.assertEqual(classify.median([4, 1, 2, 3]), 2.5)
        self.assertIsNone(classify.median([]))


if __name__ == "__main__":
    unittest.main()
