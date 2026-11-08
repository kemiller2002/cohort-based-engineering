import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from style_lint import lint


class StyleLintTests(unittest.TestCase):
    def test_rules(self):
        css = """
        :root { --brand: #123456; }
        .a { color: #fff; background: rgb(1,2,3); }
        /* .ignored { color: red; } */
        button:focus { outline: none; }
        button:focus-visible { outline: 0; }
        .card input[type=radio] { opacity: 0; }
        @media (min-width: 1px) { .ef-button { font-size: 14px !important; } }
        h1 { max-inline-size: 14ch; }
        """
        c = lint(css)
        self.assertEqual(c["raw-color"], 2)
        self.assertEqual(c["focus-suppressed"], 1)
        self.assertEqual(c["hidden-control"], 1)
        self.assertEqual(c["px-font-size"], 1)
        self.assertEqual(c["forma-override"], 1)
        self.assertEqual(c["important"], 1)
        self.assertEqual(c["fixed-measure"], 1)


if __name__ == "__main__":
    unittest.main()
