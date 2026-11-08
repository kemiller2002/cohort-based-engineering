import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import merge_conflicts as mc  # noqa: E402


class ParseTests(unittest.TestCase):
    def test_parse_merge_list_keeps_two_parent_commits(self):
        text = "a b c 2026-01-01T00:00:00Z\nd e 2026-01-01T00:00:00Z\nf g h i 2026\n"
        self.assertEqual(mc.parse_merge_list(text),
                         ({"sha": "a", "p1": "b", "p2": "c", "date": "2026-01-01T00:00:00Z"},))

    def test_parse_merge_tree_clean_conflict_error(self):
        self.assertEqual(mc.parse_merge_tree(0, "tree\n"), {"conflicted": False, "paths": ()})
        self.assertEqual(mc.parse_merge_tree(1, "tree\nb.fs\na.fs\na.fs\n"),
                         {"conflicted": True, "paths": ("a.fs", "b.fs")})
        self.assertIsNone(mc.parse_merge_tree(128, "")["conflicted"])

    def test_within_bounds(self):
        self.assertTrue(mc.within("2026-01-02", "2026-01-01", "2026-01-03"))
        self.assertFalse(mc.within("2026-01-04", None, "2026-01-03"))
        # 18:39-04:00 is 22:39Z: inside a window ending 23:00Z, outside one ending 22:00Z
        self.assertTrue(mc.within("2026-10-28T18:39:15-04:00", None, "2026-10-28T23:00:00Z"))
        self.assertFalse(mc.within("2026-10-28T18:39:15-04:00", None, "2026-10-28T22:00:00Z"))

    def test_aggregate_counts_hot_paths(self):
        rs = [{"sha": "1234567890", "date": "d", "conflicted": True, "paths": ("x",)},
              {"sha": "abcdef1234", "date": "d", "conflicted": True, "paths": ("x", "y")},
              {"sha": "0000000000", "date": "d", "conflicted": False, "paths": ()}]
        a = mc.aggregate("R", rs)
        self.assertEqual((a["merges"], a["conflictedMerges"]), (3, 2))
        self.assertEqual(a["hotPaths"], {"x": 2, "y": 1})

    def test_classify_records_vs_source(self):
        self.assertEqual(mc.classify((".ros/events/events.jsonl", "evidence/x.json")), "records-only")
        self.assertEqual(mc.classify((".ros/a", "src/App.fs")), "source")
        self.assertEqual(mc.classify(()), "none")

    def test_parse_arg(self):
        self.assertEqual(mc.parse_arg("R1=/p@2026@2027"), ("R1", "/p", "2026", "2027"))
        self.assertEqual(mc.parse_arg("R1=/p"), ("R1", "/p", None, None))


class ReplayIntegrationTest(unittest.TestCase):
    """Builds a throwaway repo with one clean and one conflicting merge."""

    def test_replay_detects_real_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            def g(*a):
                subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)
            g("init", "-q", "-b", "main")
            g("config", "user.email", "t@t"); g("config", "user.name", "t")
            Path(d, "f.txt").write_text("base\n"); g("add", "."); g("commit", "-qm", "base")
            g("checkout", "-qb", "b1"); Path(d, "f.txt").write_text("one\n"); g("commit", "-qam", "b1")
            g("checkout", "-q", "main"); Path(d, "f.txt").write_text("two\n"); g("commit", "-qam", "m")
            g("checkout", "-qb", "b2"); Path(d, "g.txt").write_text("g\n"); g("add", "."); g("commit", "-qm", "b2")
            g("checkout", "-q", "main"); g("merge", "-q", "--no-ff", "--no-edit", "b2")
            r = subprocess.run(["git", "-C", d, "merge", "-q", "--no-edit", "b1"], capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            Path(d, "f.txt").write_text("resolved\n"); g("commit", "-qam", "resolve")
            a = mc.replay("T", d, None, None)
            self.assertEqual((a["merges"], a["conflictedMerges"]), (2, 1))
            self.assertEqual(a["conflicts"][0]["paths"], ["f.txt"])


if __name__ == "__main__":
    unittest.main()
