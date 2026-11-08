#!/usr/bin/env python3
"""Unit tests for V2 verification scripts (stdlib unittest; run: python3 -m unittest test_v2 -v)."""
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


blob = load("blob_compare")
act = load("actions_count")
flags = load("flag_survey")
inv = load("release_inventory")
cons = load("consumer_pins")
fab = load("fabricate_acceptance")


class BlobCompare(unittest.TestCase):
    A = "100644 blob aaa\tsrc/A.fs\n100644 blob bbb\tsrc/B.fs\n100644 blob ccc\tREADME.md\n040000 tree ddd\tsrc\n"
    B = "100644 blob aaa\tsrc/A.fs\n100644 blob xxx\tsrc/B.fs\n100644 blob ccc\tREADME.md\n100644 blob aaa\tcopy/A.fs\n"

    def test_parse_skips_trees(self):
        self.assertEqual(len(blob.parse_ls_tree(self.A)), 3)

    def test_compare(self):
        r = blob.compare_trees(blob.parse_ls_tree(self.A), blob.parse_ls_tree(self.B), (".fs",))
        self.assertEqual(r["source_files_b"], 3)
        self.assertEqual(r["source_identical_same_path"], 1)
        self.assertEqual(r["source_differing"], ["copy/A.fs", "src/B.fs"])
        self.assertEqual(r["all_identical_same_path"], 2)
        self.assertEqual(r["source_blob_present_anywhere_in_a"], 2)


class ActionsCount(unittest.TestCase):
    RUNS = (
        {"id": 1, "name": "G", "conclusion": "cancelled", "created_at": "2026-11-06T17:00:00Z"},
        {"id": 2, "name": "G", "conclusion": "success", "created_at": "2026-11-06T18:00:00Z"},
        {"id": 3, "name": "G", "conclusion": "cancelled", "created_at": "2026-11-07T07:00:00Z"},
        {"id": 4, "name": "H", "conclusion": "failure", "created_at": "2026-11-06T18:00:00Z"},
        {"id": 5, "name": "G", "conclusion": None, "status": "in_progress", "created_at": "2026-11-06T18:30:00Z"},
    )

    def test_count_all_and_window(self):
        self.assertEqual(act.count(self.RUNS, "G")["cancelled"], 2)
        w = act.count(self.RUNS, "G", "2026-11-06T16:40:13Z", "2026-11-06T23:40:13Z")
        self.assertEqual(dict(w), {"cancelled": 1, "success": 1, "in_progress": 1})

    def test_diff(self):
        other = ({"id": 1, "name": "G", "conclusion": "failure"}, {"id": 9, "name": "G", "conclusion": "success"})
        d = act.diff(self.RUNS, other, "G")
        self.assertEqual(d["outcome_mismatch"], [1])
        self.assertEqual(d["only_in_second"], [9])
        self.assertEqual(d["only_in_first"], [2, 3, 5])


class FlagSurvey(unittest.TestCase):
    def test_flags_and_enabled(self):
        self.assertEqual(flags.flags_in_ros({"workProtocol": {"requireVerifiedCompletion": False}}),
                         {"requireVerifiedCompletion": False})
        self.assertFalse(flags.enabled({"requireVerifiedCompletion": False}))
        self.assertTrue(flags.enabled({"requireAttestedEvidence": True}))
        self.assertTrue(flags.enabled({"trustedVerifierKeyIds": ["k1"]}))
        self.assertFalse(flags.enabled({"trustedVerifierKeyIds": []}))
        self.assertEqual(flags.flags_in_ros({"other": 1}), {})
        self.assertEqual(flags.flags_in_ros([]), {})


class ReleaseInventory(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(inv.ros_version({"installedVersion": "3.7.2"}), "3.7.2")
        self.assertEqual(inv.authority_path({}), ".conditor/authority/resolved-release-set.json")
        self.assertEqual(inv.authority_path({"registryAuthority": {"path": "x.json"}}), "x.json")
        self.assertEqual(inv.authority_of({"profile": {"id": "echelon-current", "version": "1.2.0"}}),
                         ("echelon-current", "1.2.0"))

    def test_lock_matches_set(self):
        approved = {"praxis": "3.25.0", "ordo": "1.20.0"}
        self.assertEqual(inv.lock_matches_set({"praxis": "3.25.0", "forma-workflow": "1.2.0"}, approved),
                         (True, ["forma-workflow"]))
        self.assertEqual(inv.lock_matches_set({"praxis": "3.7.2"}, approved), (False, []))
        self.assertEqual(inv.lock_matches_set({"other": "1"}, approved), (False, ["other"]))

    def test_summarize(self):
        facts = ({"repo": "a", "praxisInstalled": "3.7.2", "authoritySet": "1.2.0"},
                 {"repo": "b", "praxisInstalled": "3.25.0", "authoritySet": None,
                  "lockMatchesApproved": {"match": True, "notInSet": []}},
                 {"repo": "c", "praxisInstalled": "3.7.2", "authoritySet": "1.13.0"})
        s = inv.summarize(facts)
        self.assertEqual(s["praxis_3_7_2"], ["a", "c"])
        self.assertEqual(s["authority_1_2_0"], ["a"])
        self.assertEqual(s["authority_1_3_to_1_24"], ["c"])
        self.assertEqual(s["lockMatchesApprovedNoAuthorityFile"], ["b"])


class ConsumerPins(unittest.TestCase):
    def test_nuget(self):
        xml = '<PackageReference Include="EchelonFoundry.Aegis.Core" Version="1.0.0" />' \
              '<PackageVersion Include="echelonfoundry.aegis.core" Version="2.0.0"/>'
        self.assertEqual(cons.nuget_versions(xml, "EchelonFoundry.Aegis.Core"), ("1.0.0", "2.0.0"))

    def test_json(self):
        doc = json.dumps({"components": [{"id": "aegis", "version": "1.0.0"}, {"id": "x", "version": "9"}]})
        self.assertEqual(cons.json_versions(doc, "aegis", "id"), ("1.0.0",))
        self.assertEqual(cons.json_versions("not json", "aegis", "id"), ())

    def test_summarize(self):
        rows = ({"repo": "a", "pins": (("nuget", "f", "1.0.0"),)}, {"repo": "b", "pins": ()})
        self.assertEqual(cons.summarize(rows)["consumers"], 1)


class Fabrication(unittest.TestCase):
    SRC = "a" * 40

    def test_artifact_types(self):
        self.assertEqual(fab.make_artifact("r", self.SRC, "gate", "G8")["evidence_type"], "ci")
        self.assertEqual(fab.make_artifact("r", self.SRC, "gate", "G9")["evidence_type"], "deployment")
        art = fab.make_artifact("r", self.SRC, "requirement", "X-1")
        self.assertEqual((art["status"], art["exit_code"], art["source_sha"]), ("PASS", 0, self.SRC))

    def test_bundle_and_manifest_bind(self):
        bundle = fab.make_bundle("r", self.SRC, ("R1", "R2"))
        self.assertEqual(len(bundle), 12)
        man = fab.make_manifest("r", self.SRC, bundle)
        self.assertEqual({e["path"] for e in man["entries"]}, set(bundle))
        self.assertTrue(all(fab.sha256(bundle[e["path"]]) == e["sha256"] for e in man["entries"]))

    def test_ledger_shape(self):
        base = {"id": "BL", "source": {"repository": "o/r", "commit": "b" * 40}}
        led = fab.make_ledger("r", self.SRC, base, "c" * 64, "d" * 64, "e" * 64, ("R1",))
        self.assertEqual(len(led["gates"]), 10)
        self.assertTrue(led["accepted"])
        self.assertEqual(led["requirements"][0]["evidence_paths"], ["evidence/requirement-R1.json"])


VERIFIER = Path("/home/user/sprint-scratch/V2/indy-dae2347/tools/compute-acceptance-verdict.py")
INDY = Path("/home/user/sprint-scratch/V2/indy-init-full")


@unittest.skipUnless(VERIFIER.exists() and INDY.exists(), "verifier export / Indy-init clone not present")
class FabricationEndToEnd(unittest.TestCase):
    """Runs the real verifier: the fabrication must be ACCEPTED, and a one-byte tamper must not be."""

    def run_probe(self, work):
        out = subprocess.run(["python3", "-I", str(HERE / "fabricate_acceptance.py"), str(INDY), str(VERIFIER), work],
                             capture_output=True, text=True, check=True).stdout
        return json.loads(out)

    def test_accepted_then_tamper_detected(self):
        base = Path("/home/user/sprint-scratch/V2/test-tmp")
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as work:
            r = self.run_probe(work)
            self.assertEqual(r["result"]["verdict"], "ACCEPTED")
            self.assertEqual(r["verifier_exit"], 0)
            self.assertEqual(r["candidate_tracked_files"], ["README.md"])
            # Negative control: alter one evidence artifact after the manifest is pinned.
            victim = Path(work) / "bundle" / "evidence" / "gate-G0.json"
            victim.write_bytes(victim.read_bytes().replace(b'"PASS"', b'"PASs"'))
            r2 = subprocess.run(
                ["python3", "-I", str(VERIFIER), str(Path(work) / "ledger.json"), "--repo", str(Path(work) / "candidate"),
                 "--baseline", str(Path(work) / "baseline.json"), "--baseline-sha256", fab.BASELINE_SHA256,
                 "--baseline-source", str(INDY), "--approvals", str(Path(work) / "approvals.json"),
                 "--approvals-sha256", fab.APPROVALS_SHA256,
                 "--evidence-manifest", str(Path(work) / "bundle" / "evidence-manifest.json"),
                 "--evidence-manifest-sha256", r["manifest_sha256"], "--evidence-root", str(Path(work) / "bundle"),
                 "--trusted-source-sha", r["candidate_sha"], "--trusted-operator-id", fab.OPERATOR],
                capture_output=True, text=True)
            self.assertNotEqual(json.loads(r2.stdout)["verdict"], "ACCEPTED")
            self.assertTrue(any("digest mismatch" in x for x in json.loads(r2.stdout)["reasons"]))


if __name__ == "__main__":
    unittest.main()
