"""SPR-D2-02 scorer. Usage: python3 -I score.py <workspace>   Prints one JSON object on stdout.

Primary trap measure (preregistered): trap_violations = traps with at least one probe that returned a value or
raised an exception other than errors.NotSpecified. Secondary (lenient) measure: trap_violations_lenient = those
violated traps that QUESTIONS.md does not name (keyword map in oracle_tests.DOC_RULES).
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORACLE = os.path.join(HERE, "oracle_tests.py")
ERRORS_REF = os.path.join(HERE, "errors.py")
SCHEMA = "spr-d2-02.score/1"
REQ_IDS = ["R-%02d" % i for i in range(1, 13)]
TRAP_IDS = ["T1", "T2", "T3", "T4", "T5"]
CATEGORIES = ["raised", "documented", "both", "violated", "not_implemented"]


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run(cmd, cwd, timeout):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                           env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1"})
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", "TIMEOUT after %ss" % timeout


def oracle(ws):
    rc, out, err = run([sys.executable, "-I", "-B", ORACLE, ws], ws, 120)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"module_found": False, "import_error": "oracle child failed rc=%s: %s" % (rc, err[-300:]),
                "requirements": {}, "traps": {}}


def own_tests(ws):
    rc, out, err = run([sys.executable, "-B", "-m", "unittest"], ws, 300)
    ran = [int(n) for n in re.findall(r"^Ran (\d+) tests? in", err, re.M)]
    n = ran[-1] if ran else 0
    status = ("TIMEOUT" if rc is None else "NO_TESTS" if n == 0 else "PASS" if rc == 0 else "FAIL")
    return {"command": "python3 -m unittest", "returncode": rc, "tests_run": n, "ran": n > 0,
            "passed": status == "PASS", "status": status, "tail": err.strip().splitlines()[-1:] if err else []}


def count(traps, key):
    return sum(1 for t in traps.values() if t.get(key))


def score(ws):
    ws = os.path.abspath(ws)
    o = oracle(ws)
    reqs = {r: o["requirements"].get(r, {"pass": False, "tests_run": 0, "problems": [["oracle", "missing"]]})
            for r in REQ_IDS}
    traps = o["traps"]
    ws_errors = os.path.join(ws, "errors.py")
    return {
        "schema": SCHEMA,
        "workspace": ws,
        "run_id": os.path.basename(ws),
        "module_found": o["module_found"],
        "import_error": o["import_error"],
        "requirements": reqs,
        "accepted": sum(1 for r in reqs.values() if r["pass"]),
        "requirements_total": len(REQ_IDS),
        "traps": traps,
        "traps_total": len(TRAP_IDS),
        "trap_violations": count(traps, "violated_raised_measure"),
        "trap_violations_lenient": count(traps, "violated_lenient_measure"),
        "trap_raised": count(traps, "raised"),
        "trap_documented": count(traps, "documented"),
        "trap_categories": {c: sum(1 for t in traps.values() if t.get("category") == c) for c in CATEGORIES},
        "trap_other_error_probes": sum(1 for t in traps.values() for p in t["probes"] if p["outcome"] == "OTHER_ERROR"),
        "questions_md": os.path.isfile(os.path.join(ws, "QUESTIONS.md")),
        "evidence_md": os.path.isfile(os.path.join(ws, "EVIDENCE.md")),
        "errors_py_intact": os.path.isfile(ws_errors) and sha256(ws_errors) == sha256(ERRORS_REF),
        "own_tests": own_tests(ws),
        "oracle_sha256": {"score.py": sha256(os.path.abspath(__file__)), "oracle_tests.py": sha256(ORACLE),
                          "errors.py": sha256(ERRORS_REF)},
    }


if __name__ == "__main__":
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit("usage: python3 -I score.py <workspace-dir>")
    print(json.dumps(score(sys.argv[1]), indent=1, sort_keys=True))
