"""SPR-D4-01 hidden oracle: run the agent's own tests (discovered exactly as `python3 -m unittest` from the workspace
root would: TestLoader().discover(ws, pattern="test*.py", top_level_dir=ws)) one test at a time, recording which
functions defined in <ws>/invoice.py each test calls (directly or indirectly; sys.setprofile).
  python3 -I trace_tests.py <workspace_copy>
Prints {"discover_error": str|null, "tests": {test_id: {"passed": bool, "called": [names]}}} as the LAST stdout line.
A test is "passed" iff it ran, had no failure/error, was not skipped and was not an expected failure."""
import io
import json
import os
import sys
import unittest


def flatten(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from flatten(t)
        else:
            yield t


def run_one(test, target):
    called = set()
    def prof(frame, event, arg):
        if event == "call" and os.path.realpath(frame.f_code.co_filename) == target:
            called.add(frame.f_code.co_name)
    result = unittest.TestResult()
    sys.setprofile(prof)
    try:
        test(result)
    finally:
        sys.setprofile(None)
    ok = (result.testsRun == 1 and not result.failures and not result.errors and not result.skipped
          and not result.expectedFailures and not result.unexpectedSuccesses)
    return {"passed": ok, "called": sorted(called)}


def main(ws):
    ws = os.path.realpath(ws)
    sys.path.insert(0, ws)
    os.chdir(ws)
    target = os.path.realpath(os.path.join(ws, "invoice.py"))
    real_out = sys.stdout
    sys.stdout = io.StringIO()
    try:
        suite = unittest.TestLoader().discover(ws, pattern="test*.py", top_level_dir=ws)
        tests = {t.id(): run_one(t, target) for t in flatten(suite)}
        err = None
    except BaseException as e:
        tests, err = {}, "%s: %s" % (type(e).__name__, e)
    sys.stdout = real_out
    print(json.dumps({"discover_error": err, "tests": tests}))


if __name__ == "__main__":
    main(sys.argv[1])
