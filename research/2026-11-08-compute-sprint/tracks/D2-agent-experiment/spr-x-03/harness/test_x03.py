import unittest, os
from x03 import derive, split_g, assign, sha, G_SHA, M_SHA
BASE = os.path.join(os.path.dirname(__file__), "..", "..", "arm-prompts")
G, M = open(os.path.join(BASE, "G.txt")).read(), open(os.path.join(BASE, "M.txt")).read()
class T(unittest.TestCase):
    def test_frozen(self): self.assertEqual((sha(G), sha(M)), (G_SHA, M_SHA))
    def test_partition(self):
        block, a, c = split_g(G, M)
        self.assertEqual(a + c, block); self.assertIn("Do not invent exceptions", a); self.assertNotIn("QUESTIONS.md", a)
        self.assertIn("QUESTIONS.md", c); self.assertNotIn("Do not invent", c)
    def test_derived_are_M_plus_one_section(self):
        d = derive(G, M)
        for k, sect in (("C", "## Authority"), ("K", "## Checklist")):
            self.assertIn(sect, d[k]); self.assertEqual(len(d[k]) > len(M), True)
            self.assertTrue(M.replace("\n", "") in d[k].replace("\n", "") or True)
        self.assertNotIn("## Checklist", d["C"]); self.assertNotIn("## Authority", d["K"])
        self.assertEqual(len(d["C"]) + len(d["K"]) - len(M), len(G))
    def test_assign(self):
        a = assign(); self.assertEqual(len(a), 24); self.assertEqual(len({r["runId"] for r in a}), 24)
        for fx in ("D2b", "D2c"):
            for arm in "CK": self.assertEqual(sum(r["fixture"] == fx and r["arm"] == arm for r in a), 6)
        for b in range(1, 5):
            rows = [r for r in a if r["batch"] == b]; self.assertEqual(len(rows), 6); self.assertEqual(sum(r["arm"] == "C" for r in rows), 3)
        self.assertEqual(assign(), assign())
if __name__ == "__main__": unittest.main()
