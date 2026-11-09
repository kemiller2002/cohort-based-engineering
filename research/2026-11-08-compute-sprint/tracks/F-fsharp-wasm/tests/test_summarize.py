import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from summarize import startup_groups


class SummarizeTests(unittest.TestCase):
    def test_startup_groups_skips_errors_and_missing(self):
        rows = [{"label": "a", "mode": "cold", "throttle": "none", "readyMs": 10, "pageErrors": []},
                {"label": "a", "mode": "cold", "throttle": "none", "readyMs": 30, "pageErrors": []},
                {"label": "a", "mode": "cold", "throttle": "none", "readyMs": None, "pageErrors": []},
                {"label": "a", "mode": "cold", "throttle": "none", "readyMs": 99, "pageErrors": ["x"]}]
        g = startup_groups(rows, "readyMs")
        self.assertEqual(len(g), 1)
        self.assertEqual((g[0]["n"], g[0]["median"], g[0]["server"]), (2, 20, "python-http"))


if __name__ == "__main__":
    unittest.main()
