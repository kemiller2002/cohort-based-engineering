import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import indy_fabricated_acceptance as F  # noqa: E402

SHA = "a" * 40
BASE = {"id": "BL", "source": {"repository": "r", "commit": "b" * 40},
        "requirements": [{"id": "R1", "priority": "P0"}, {"id": "R2", "priority": "P1"}, {"id": "R3", "priority": "P0"}]}


class T(unittest.TestCase):
    def test_p0_ids(self):
        self.assertEqual(F.p0_ids(BASE), ("R1", "R3"))

    def test_bundle_paths_and_types(self):
        b = F.fabricate_bundle(SHA, ("R1",))
        self.assertEqual(len(b), 11)
        self.assertEqual(json.loads(b["gates/G8.json"])["evidence_type"], "ci")
        self.assertEqual(json.loads(b["gates/G9.json"])["evidence_type"], "deployment")
        self.assertEqual(json.loads(b["requirements/R1.json"])["source_sha"], SHA)

    def test_manifest_digests_match(self):
        b = F.fabricate_bundle(SHA, ("R1",))
        m = F.manifest_for(b, SHA)
        self.assertTrue(all(F.sha256(b[e["path"]]) == e["sha256"] for e in m["entries"]))

    def test_ledger_shape(self):
        led = F.ledger_for(BASE, "1" * 64, "2" * 64, "3" * 64, SHA, ("R1", "R3"))
        self.assertTrue(led["accepted"])
        self.assertEqual([g["id"] for g in led["gates"]], list(F.GATES))
        self.assertEqual(len(led["requirements"]), 2)
        self.assertEqual(led["evidence_manifest_sha256"], "3" * 64)


if __name__ == "__main__":
    unittest.main()
