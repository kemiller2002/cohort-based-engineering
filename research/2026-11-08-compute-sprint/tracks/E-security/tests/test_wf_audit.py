import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import wf_audit as W  # noqa: E402

WF = """
name: t
on:
  pull_request_target:
    types: [opened]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: foo/bar@0123456789abcdef0123456789abcdef01234567
      - uses: ./local
      - run: echo "${{ github.event.pull_request.title }} ${{ github.sha }}"
      - run: echo ok
"""


class T(unittest.TestCase):
    def setUp(self):
        self.r = W.audit_doc(yaml.safe_load(WF), "x.yml")

    def test_triggers(self):
        self.assertEqual(self.r["risky_triggers"], ["pull_request_target"])

    def test_missing_permissions(self):
        self.assertTrue(self.r["missing_permissions"])

    def test_pinning(self):
        self.assertEqual([u["uses"] for u in self.r["unpinned_uses"]], ["actions/checkout@v4"])
        self.assertEqual(self.r["pinned_uses"], ["foo/bar@0123456789abcdef0123456789abcdef01234567"])

    def test_injection_only_untrusted(self):
        self.assertEqual(len(self.r["untrusted_in_run"]), 1)
        self.assertEqual(self.r["untrusted_in_run"][0]["expressions"], ["github.event.pull_request.title"])

    def test_permissions_present(self):
        d = yaml.safe_load(WF)
        d["permissions"] = {"contents": "write", "pages": "read"}
        r = W.audit_doc(d, "y")
        self.assertFalse(r["missing_permissions"])
        self.assertEqual(r["write_scopes"], ["contents"])

    def test_classify(self):
        self.assertEqual(W.classify_uses("kemiller2002/x/.github/workflows/a.yml@v1"), ("echelon", False))
        self.assertEqual(W.classify_uses("docker://alpine"), ("docker", True))
        self.assertEqual(W.classify_uses("evil/act@main"), ("third-party", False))

    def test_string_and_list_triggers(self):
        self.assertEqual(W.triggers({True: "push"}), ["push"])
        self.assertEqual(W.triggers({"on": ["push", "workflow_run"]}), ["push", "workflow_run"])


if __name__ == "__main__":
    unittest.main()
