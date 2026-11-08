import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from binding_keys import html_keys, fs_keys, compare


class BindingKeyTests(unittest.TestCase):
    def test_roundtrip(self):
        h = html_keys('<p data-text="a.title"></p><b data-text="label"></b><button data-event="a.save"></button><i data-if="a.missing"></i><i data-text="ws.x"></i>')
        self.assertEqual(h, {"view": {"a.title", "a.missing", "ws.x"}, "event": {"a.save"}})
        lits, pre = fs_keys(['Bind.text "a.title" x', 'let k = "ws." + n', 'Bind.flag "a.unused" true', 'on "a.save"'])
        self.assertEqual(pre, {"ws."})
        r = compare(h, lits, pre)
        self.assertEqual(r["boundNotProjected"], ["a.missing"])
        self.assertEqual(r["projectedNotBound"], ["a.unused"])
        self.assertEqual(r["eventsNotInFs"], [])


if __name__ == "__main__":
    unittest.main()
