import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from playwright_stability import classify, summarise


def report(statuses, duration=1000):
    return {"stats": {"duration": duration}, "suites": [{"title": "a.spec.js", "specs": [
        {"title": f"t{i}", "file": "a.spec.js", "tests": [{"projectName": "chromium", "status": s, "results": [{"status": "passed", "duration": 5}]}]}
        for i, s in enumerate(statuses)], "suites": []}]}


class StabilityTests(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify(["expected"] * 3), "stable-pass")
        self.assertEqual(classify(["unexpected"] * 3), "stable-fail")
        self.assertEqual(classify(["expected", "unexpected", "expected"]), "flaky")
        self.assertEqual(classify(["flaky", "expected"]), "flaky")
        self.assertEqual(classify(["skipped", "skipped"]), "skipped")

    def test_summarise(self):
        s = summarise("x", [report(["expected", "expected", "skipped"]), report(["expected", "unexpected", "skipped"])])
        self.assertEqual(s["tests"], 3)
        self.assertEqual(s["verdicts"], {"stable-pass": 1, "flaky": 1, "skipped": 1})
        self.assertEqual(len(s["nonPassing"]), 1)


if __name__ == "__main__":
    unittest.main()
