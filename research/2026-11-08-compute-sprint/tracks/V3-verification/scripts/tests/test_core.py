import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import conditor_releases as cr  # noqa: E402
import merge_replay as mr  # noqa: E402
import percepta_preflight as pp  # noqa: E402
import upsert_verdict as uv  # noqa: E402
import v3guard  # noqa: E402


def wi(*items):
    return json.dumps({"workItems": [{"id": i, "state": s} for i, s in items]})


class GuardTests(unittest.TestCase):
    def test_paths(self):
        self.assertTrue(v3guard.is_under("/home/user/sprint-scratch/V3/clones/r008"))
        self.assertFalse(v3guard.is_under("/home/user/sprint-scratch/V30"))
        self.assertFalse(v3guard.is_under("/home/user/sprint-scratch/A2/r8"))
        with self.assertRaises(SystemExit):
            v3guard.require_scratch_path("/home/user/sprint-wt/A2-remediation")

    def test_refuses_cwd_outside(self):
        old = os.getcwd()
        try:
            os.chdir("/tmp")
            with self.assertRaises(SystemExit):
                v3guard.require_scratch_cwd()
        finally:
            os.chdir(old)

    def test_mutating_git_refuses_foreign_repo(self):
        with self.assertRaises(SystemExit):
            v3guard.mutating_git("/home/user/ext/conditor", "status")


class MergeCompareTests(unittest.TestCase):
    def test_clean_union(self):
        b, p1, p2 = mr.work_items(wi(("A", "x"))), mr.work_items(wi(("A", "x"), ("B", "y"))), mr.work_items(wi(("A", "x"), ("C", "z")))
        res = mr.work_items(wi(("A", "x"), ("B", "y"), ("C", "z")))
        c = mr.compare(b, p1, p2, res, res)
        self.assertEqual((c["lost"], c["duplicates"], c["extra"]), ([], [], []))
        self.assertTrue(c["idsEqualTeam"])

    def test_one_side_drop_detected(self):
        """The d8447ed1 shape: item added on P2 only, team keeps P1."""
        b, p1, p2 = mr.work_items(wi(("A", "x"))), mr.work_items(wi(("A", "x"), ("W9", "a"))), mr.work_items(wi(("A", "x"), ("W3", "a")))
        team = p1
        c = mr.compare(b, p1, p2, mr.work_items(wi(("A", "x"), ("W9", "a"), ("W3", "a"))), team)
        self.assertEqual(c["teamLostVsParents"], ["W3"])
        self.assertEqual(c["onlyInResult"], ["W3"])
        self.assertEqual(c["lost"], [])

    def test_legit_deletion_not_lost(self):
        b, p1, p2 = mr.work_items(wi(("A", "x"), ("D", "q"))), mr.work_items(wi(("A", "x"))), mr.work_items(wi(("A", "x"), ("D", "q")))
        c = mr.compare(b, p1, p2, mr.work_items(wi(("A", "x"))), mr.work_items(wi(("A", "x"))))
        self.assertEqual(c["lost"], [])

    def test_duplicate_events(self):
        e = '{"eventId":"e1","t":1}\n{"eventId":"e1","t":1}\n{"eventId":"e2"}\n'
        c = mr.compare({}, mr.events('{"eventId":"e1","t":1}'), mr.events('{"eventId":"e2"}'), mr.events(e), mr.events(e))
        self.assertEqual(c["duplicates"], ["e1"])

    def test_content_diff(self):
        p = mr.work_items(wi(("A", "x")))
        c = mr.compare({}, p, p, mr.work_items(wi(("A", "y"))), p)
        self.assertEqual(c["contentDiffVsTeam"], ["A"])

    def test_sample_seeded(self):
        pop = [f"m{i}" for i in range(58)]
        self.assertEqual(mr.sample(pop, 18, 20261108), mr.sample(pop, 18, 20261108))
        self.assertEqual(len(set(mr.sample(pop, 18, 1))), 18)


class ConditorTests(unittest.TestCase):
    def test_range(self):
        self.assertTrue(cr.in_range(">=0.2.0 <1.0.0", "0.13.0"))
        self.assertFalse(cr.in_range(">=0.2.0 <1.0.0", "1.0.0"))
        self.assertFalse(cr.in_range(">=0.6.1 <1.0.0", "0.6.0"))

    def base(self, **kw):
        d = {"changedKeys": ["qualifiedVersions"], "addedQualified": ["0.11.0"], "removedQualified": [], "isNew": False,
             "isRemoved": False, "distribution": "npm", "qualifiedRange": ">=0.2.0 <1.0.0"}
        return {**d, **kw}

    def test_avoidable_rules(self):
        self.assertTrue(cr.descriptor_avoidable(self.base()))
        self.assertFalse(cr.descriptor_avoidable(self.base(distribution="host-tool")))
        self.assertFalse(cr.descriptor_avoidable(self.base(qualifiedRange=None)))
        self.assertFalse(cr.descriptor_avoidable(self.base(changedKeys=["qualifiedVersions", "releaseArtifacts"])))
        self.assertFalse(cr.descriptor_avoidable(self.base(isNew=True)))
        self.assertFalse(cr.descriptor_avoidable(self.base(addedQualified=["1.2.0"])))

    def test_classify(self):
        self.assertEqual(cr.classify({}), "no-catalog-change")
        self.assertEqual(cr.classify({"forma": self.base()}), "avoidable")
        self.assertEqual(cr.classify({"forma": self.base(), "praxis": self.base(distribution="host-tool")}), "required")


class PerceptaTests(unittest.TestCase):
    def test_ci_args_drop_catalog(self):
        a = pp.r9_args("/r", "requirements-compiled/v4.1.1")
        self.assertIn("--catalog", a)
        self.assertNotIn("--catalog", pp.ci_args("/r", "requirements-compiled/v4.1.1"))
        self.assertTrue(a[3].endswith("requirements-compiled/v4/invariants.json"))

    def test_ci_gate(self):
        self.assertTrue(pp.ci_jq_gate({"blocked": False, "blockingContradictions": [], "analysed": {"transitions": 3}}))
        self.assertFalse(pp.ci_jq_gate({"blocked": False, "blockingContradictions": [], "analysed": {"transitions": 0}}))
        self.assertTrue(pp.ci_jq_gate({"blocked": False, "blockingContradictions": [], "missingInterfaces": [{"blocking": True}],
                                       "analysed": {"transitions": 3}}), "gate ignores missingInterfaces")


class UpsertTests(unittest.TestCase):
    def test_upsert_replaces(self):
        e = {f: "x" for f in uv.FIELDS}
        e["verdict"] = "VERIFIED"
        doc = uv.upsert(uv.upsert({"verdicts": []}, {**e, "claimId": "A"}), {**e, "claimId": "A", "notes": "y"})
        self.assertEqual(len(doc["verdicts"]), 1)
        self.assertEqual(doc["verdicts"][0]["notes"], "y")
        with self.assertRaises(ValueError):
            uv.upsert(doc, {**e, "verdict": "MAYBE"})


if __name__ == "__main__":
    unittest.main()
