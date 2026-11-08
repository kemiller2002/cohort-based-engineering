import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import secret_scan as S  # noqa: E402

# Synthetic values assembled at runtime so this file itself never contains a token-shaped literal.
GH = b"gh" + b"p_" + b"Q7wZ3kLmN9pR2sT5vX8yB1cD4fG6hJ0aE3iU"
AWS = b"AK" + b"IA" + b"QWERTYUIOPLKJHGF"


class T(unittest.TestCase):
    def test_detects_github_and_aws(self):
        rules = {r for r, _ in S.scan_bytes(b"x " + GH + b" y " + AWS)}
        self.assertEqual(rules, {"github-token", "aws-access-key-id"})

    def test_fingerprint_redacts(self):
        fp = S.fingerprint(GH)
        self.assertNotIn(GH.decode(), fp)
        self.assertTrue(fp.startswith("ghp_"))
        self.assertIn("len=40", fp)

    def test_placeholder_not_live(self):
        self.assertFalse(S.live_looking("generic-assignment", b"your_api_key_goes_here_123"))
        self.assertFalse(S.live_looking("github-token", b"ghp_" + b"x" * 36))
        self.assertTrue(S.live_looking("github-token", GH))

    def test_generic_assignment_group(self):
        hits = list(S.scan_bytes(b'api_key = "Zq8Rk2Lm7Np4Ws9Tx3Vb6Yc1"'))
        self.assertEqual(hits[0][0], "generic-assignment")
        self.assertEqual(hits[0][1], b"Zq8Rk2Lm7Np4Ws9Tx3Vb6Yc1")

    def test_private_key_header(self):
        self.assertEqual([r for r, _ in S.scan_bytes(b"-----BEGIN OPENSSH PRIVATE KEY-----")], ["private-key-block"])


if __name__ == "__main__":
    unittest.main()
