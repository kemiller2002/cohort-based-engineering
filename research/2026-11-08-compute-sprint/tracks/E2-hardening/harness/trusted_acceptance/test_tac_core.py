import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tac_core as core  # noqa: E402
import tac_keys as keys  # noqa: E402

PLAN = {"requirements": [
    {"id": "R-1", "check_id": "c1", "argv": ["x"], "expect": {"exit_code": 0, "stdout": "5"}},
    {"id": "R-2", "check_id": "c2", "argv": ["y"], "expect": {"exit_code": 2}}]}
PLAN_SHA = core.sha256_hex(core.canonical(PLAN))


class Fixture:
    def __init__(self, outputs):
        self.dir = tempfile.TemporaryDirectory()
        d = Path(self.dir.name)
        public = keys.generate(d / "k.pem", d / "k.pub")
        self.sign, _ = keys.signer(d / "k.pem")
        self.verify, _ = keys.verifier((d / "k.pub").read_text())
        self.kid = core.key_id(public)
        self.files = {f"entries/{r['id']}.json": core.signed_document(
            core.make_entry("run", "job", "sha-a", r["id"], r, code, out, "t0", "t1", self.kid), self.sign)
            for r, (code, out) in zip(PLAN["requirements"], outputs)}
        self.manifest = core.signed_document(core.make_manifest("run", "job", "sha-a", PLAN_SHA, self.kid, self.files), self.sign)

    def decide(self, manifest=None, files=None, sha="sha-a", caller=None):
        files = self.files if files is None else files
        return core.decide(self.manifest if manifest is None else manifest, files.get, self.verify, self.kid, sha,
                           PLAN, PLAN_SHA, caller)


class TacCoreTests(unittest.TestCase):
    def test_judge_uses_expectations_not_candidate_claims(self):
        self.assertEqual(core.judge({"exit_code": 0, "stdout": "5"}, 0, "5\n"), "PASS")
        self.assertEqual(core.judge({"exit_code": 0, "stdout": "5"}, 0, "PASS"), "FAIL")
        self.assertEqual(core.judge({"exit_code": 2}, 0, ""), "FAIL")

    def test_genuine_passing_bundle_is_accepted_and_caller_digest_ignored(self):
        f = Fixture([(0, "5"), (2, "")])
        self.assertEqual(f.decide()["verdict"], "ACCEPTED")
        out = f.decide(caller="00" * 32)
        self.assertEqual(out["verdict"], "ACCEPTED")
        self.assertTrue(out["notes"])

    def test_genuine_failing_bundle_is_failed(self):
        self.assertEqual(Fixture([(0, "6"), (2, "")]).decide()["verdict"], "FAILED")

    def test_unsigned_legacy_manifest_is_refused(self):
        f = Fixture([(0, "5"), (2, "")])
        legacy = json.dumps({"schema": "causa.acceptance-evidence-manifest/1", "entries": []}).encode()
        self.assertEqual(f.decide(manifest=legacy)["verdict"], "REFUSED")

    def test_other_key_wrong_source_tamper_and_missing_are_refused(self):
        f, g = Fixture([(0, "5"), (2, "")]), Fixture([(0, "5"), (2, "")])
        self.assertEqual(f.decide(manifest=g.manifest, files=g.files)["verdict"], "REFUSED")
        self.assertEqual(f.decide(sha="sha-b")["verdict"], "REFUSED")
        tampered = dict(f.files)
        tampered["entries/R-1.json"] = tampered["entries/R-1.json"].replace(b'"FAIL"', b'"PASS"') + b" "
        self.assertEqual(f.decide(files=tampered)["verdict"], "REFUSED")
        missing = {k: v for k, v in f.files.items() if "R-2" not in k}
        self.assertEqual(f.decide(files=missing)["verdict"], "REFUSED")


if __name__ == "__main__":
    unittest.main()
