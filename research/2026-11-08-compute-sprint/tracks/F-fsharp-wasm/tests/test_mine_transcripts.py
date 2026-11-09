import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from mine_transcripts import normalise, outcome, builds, distinct_errors, recovery_minutes


def use(i, cmd, t):
    return {"timestamp": t, "message": {"content": [{"type": "tool_use", "name": "Bash", "id": i, "input": {"command": cmd}}]}}


def res(i, text, t):
    return {"timestamp": t, "message": {"content": [{"type": "tool_result", "tool_use_id": i, "content": text}]}}


ERR = "/r/src/A.fs(3,5): error FS0001: The type 'Foo' does not match the type 'Bar' [/r/A.fsproj]"


class TranscriptTests(unittest.TestCase):
    def test_normalise(self):
        self.assertEqual(normalise("The type 'Foo list' does not match 'Bar' at 12"), "The type 'X' does not match 'X' at N")

    def test_outcome(self):
        self.assertEqual(outcome(ERR), "fsharp-compile-error")
        self.assertEqual(outcome("Build succeeded.\n 0 Warning(s)"), "ok")
        self.assertEqual(outcome("error NU1101: x"), "other-build-error")
        self.assertEqual(outcome("hello"), "unknown")

    def test_builds_and_recovery(self):
        rows = [use("1", "dotnet build", "2026-01-01T00:00:00Z"), res("1", ERR, "2026-01-01T00:00:30Z"),
                use("x", "ls", "2026-01-01T00:01:00Z"), res("x", ERR, "2026-01-01T00:01:01Z"),
                use("2", "cd r && dotnet test", "2026-01-01T00:04:00Z"), res("2", "Passed!  - Failed: 0", "2026-01-01T00:05:00Z")]
        bs = builds("t", rows)
        self.assertEqual([b["outcome"] for b in bs], ["fsharp-compile-error", "ok"])
        self.assertEqual(bs[0]["fsCodes"], ["FS0001"])
        self.assertEqual(recovery_minutes(bs), [5.0])
        errs = distinct_errors("t", rows)
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["file"], "A.fs")


if __name__ == "__main__":
    unittest.main()
