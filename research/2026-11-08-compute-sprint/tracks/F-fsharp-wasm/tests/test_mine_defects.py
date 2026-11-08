import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from mine_defects import classify, file_kinds, parse_log, to_row, SEP


class MineTests(unittest.TestCase):
    def test_classify_compile_and_a11y(self):
        c = classify("Fix FS3261 nullness errors; contrast of save bar")
        self.assertIn("fsharp-compile", c)
        self.assertIn("a11y-contrast", c)
        self.assertIn("fs3261", c["fsharp-compile"])

    def test_classify_none(self):
        self.assertEqual(classify("Update README"), {})

    def test_file_kinds(self):
        self.assertEqual(file_kinds(["a/b.fs", "x.spec.js", "c.css", "Makefile"]),
                         {"fs": 1, "spec": 1, "css": 1, "none": 1})

    def test_parse_and_row(self):
        raw = (SEP + "abc123\x1f2026-10-01T00:00:00Z\x1fFix the site build\x1fbody FS0039\x1f\n\nsrc/A.fs\nweb/x.css\n"
               + SEP + "def456\x1f2026-10-02T00:00:00Z\x1fMerge x\x1f\x1f\n\n")
        cs = parse_log(raw)
        self.assertEqual([c["sha"] for c in cs], ["abc123", "def456"])
        self.assertEqual(cs[0]["files"], ["src/A.fs", "web/x.css"])
        r = to_row("r1", cs[0])
        self.assertTrue(r["isFix"])
        self.assertIn("fsharp-compile", r["categories"])
        self.assertTrue(to_row("r1", cs[1])["isMerge"])


if __name__ == "__main__":
    unittest.main()
