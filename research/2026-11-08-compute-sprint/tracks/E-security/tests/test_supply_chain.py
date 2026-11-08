import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import supply_chain as S  # noqa: E402


class T(unittest.TestCase):
    def test_floating(self):
        self.assertTrue(S.is_floating_nuget("1.*"))
        self.assertTrue(S.is_floating_nuget("[1.0,2.0)"))
        self.assertFalse(S.is_floating_nuget("1.2.3"))
        self.assertFalse(S.is_floating_nuget("[1.2.3]"))

    def test_npm_range(self):
        self.assertTrue(S.is_range_npm("^1.2.0"))
        self.assertTrue(S.is_range_npm("~1.2.0"))
        self.assertTrue(S.is_range_npm("*"))
        self.assertFalse(S.is_range_npm("1.2.0"))

    def test_audit_repo(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.fsproj").write_text('<PackageReference Include="X" Version="2.*" /><PackageReference Include="Y" Version="1.0.0" />')
            (root / "package.json").write_text('{"dependencies":{"a":"^1.0.0","b":"1.0.0"}}')
            (root / "obj").mkdir()
            (root / "obj" / "b.fsproj").write_text('<PackageReference Include="Z" Version="*" />')
            a = S.audit_repo(root)
            self.assertEqual([f["package"] for f in a["floating_nuget"]], ["X"])
            self.assertEqual(a["npm"][0]["ranged"], ["a"])
            self.assertFalse(a["npm"][0]["lockfile"])
            self.assertFalse(a["nuget_lock_enabled"])


if __name__ == "__main__":
    unittest.main()
