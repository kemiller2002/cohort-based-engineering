import sys, pathlib, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from measure_build import build_dirs, plan, mode_spec


class MeasureBuildTests(unittest.TestCase):
    def test_plan_order(self):
        self.assertEqual(plan(["a", "b"], 2), [("a", 1), ("a", 2), ("b", 1), ("b", 2)])

    def test_mode_spec(self):
        s = mode_spec("publish-cold", "src/H", "X.slnx", "/o")
        self.assertEqual(s["clean"], ("src",))
        self.assertIn("publish", s["cmd"])
        self.assertTrue(mode_spec("sln-incr", "p", "X.slnx", "/o")["touch"])
        with self.assertRaises(KeyError):
            mode_spec("nope", "p", "s", "o")

    def test_build_dirs_skips_node_modules_and_other_roots(self):
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            for p in ["src/A/bin", "src/A/obj", "src/node_modules/x/bin", "tests/T/obj", "src/A/binx"]:
                (root / p).mkdir(parents=True)
            found = [str(p.relative_to(root)) for p in build_dirs(root, ("src",))]
            self.assertEqual(found, ["src/A/bin", "src/A/obj"])


if __name__ == "__main__":
    unittest.main()
