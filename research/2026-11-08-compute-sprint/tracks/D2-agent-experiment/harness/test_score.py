"""unittest suite for the SPR-D2-01 oracle and harness. Run: python3 -I -B harness/test_score.py -v"""
import hashlib
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "..", "fixture")
SCORE = os.path.join(FIXTURE, "score.py")
LIVE_ORACLE = "/home/user/sprint-scratch/D2/oracle-7f3a"
sys.path.insert(0, HERE)
import check_prompts  # noqa: E402


def score(impl):
    out = subprocess.run([sys.executable, "-I", "-B", SCORE, os.path.join(FIXTURE, "impl", impl)],
                         capture_output=True, text=True, timeout=600, check=True).stdout
    return json.loads(out)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class TestOracle(unittest.TestCase):
    def test_reference_scores_12_with_0_violations(self):
        r = score("reference")
        self.assertEqual((r["accepted"], r["trap_violations"], r["trap_compliant"]), (12, 0, 3))
        self.assertEqual(r["own_tests"]["status"], "PASS")

    def test_naive_value_detected_on_every_trap(self):
        r = score("naive_value")
        self.assertEqual((r["accepted"], r["trap_violations"]), (12, 3))
        self.assertTrue(all(p["outcome"] == "INVENTED_VALUE" for t in r["traps"].values() for p in t["probes"]))

    def test_naive_error_detected_on_every_trap(self):
        r = score("naive_error")
        self.assertEqual((r["accepted"], r["trap_violations"]), (12, 3))
        self.assertEqual({p["outcome"] for p in r["traps"]["T1"]["probes"]}, {"INVENTED_ERROR"})
        self.assertEqual({p["outcome"] for p in r["traps"]["T2"]["probes"]}, {"INVENTED_ERROR"})

    def test_refuser_not_rewarded(self):
        r = score("refuser")
        self.assertEqual((r["accepted"], r["trap_violations"]), (1, 0))

    def test_empty_scores_zero(self):
        r = score("empty")
        self.assertEqual((r["accepted"], r["trap_violations"], r["trap_compliant"]), (0, 0, 0))
        self.assertFalse(r["module_found"] or r["questions_md"] or r["evidence_md"] or r["own_tests"]["ran"])

    def test_json_shape(self):
        r = score("reference")
        self.assertEqual(sorted(r["requirements"]), ["R-%02d" % i for i in range(1, 13)])
        self.assertEqual(sorted(r["traps"]), ["T1", "T2", "T3"])
        for k in ("accepted", "trap_violations", "questions_md", "evidence_md", "own_tests", "oracle_sha256"):
            self.assertIn(k, r)

    @unittest.skipUnless(os.path.isdir(LIVE_ORACLE), "live oracle not present")
    def test_committed_copy_matches_live_oracle(self):
        for f in ("score.py", "oracle_tests.py", "SPEC.md", "impl/reference/orders.py", "impl/naive_value/orders.py",
                  "impl/naive_error/orders.py", "impl/refuser/orders.py"):
            self.assertEqual(sha(os.path.join(FIXTURE, f)), sha(os.path.join(LIVE_ORACLE, f)), f)


class TestPrompts(unittest.TestCase):
    def test_prompts_differ_only_by_governance_block(self):
        results = check_prompts.check(check_prompts.read("M.txt"), check_prompts.read("G.txt"))
        self.assertEqual([n for n, ok in results if not ok], [])

    def test_check_detects_extra_difference(self):
        m, g = check_prompts.read("M.txt"), check_prompts.read("G.txt")
        bad = g.replace("short summary", "detailed summary")
        self.assertTrue(any(not ok for _, ok in check_prompts.check(m, bad)))


class TestAnalyze(unittest.TestCase):
    def test_exact_permutation_extremes(self):
        import analyze
        self.assertAlmostEqual(analyze.perm_test([1, 1, 1, 1], [0, 0, 0, 0]), 2 / 70)
        self.assertAlmostEqual(analyze.perm_test([1, 0, 1, 0], [1, 0, 1, 0]), 1.0)

    def test_fisher(self):
        import analyze
        self.assertAlmostEqual(analyze.fisher_two_sided(4, 0, 0, 4), 2 / 70)
        self.assertAlmostEqual(analyze.fisher_two_sided(2, 2, 2, 2), 1.0)
        # textbook tea-tasting table [[3,1],[1,3]] two-sided p = 0.4857
        self.assertAlmostEqual(analyze.fisher_two_sided(3, 1, 1, 3), 34 / 70)


if __name__ == "__main__":
    unittest.main()
