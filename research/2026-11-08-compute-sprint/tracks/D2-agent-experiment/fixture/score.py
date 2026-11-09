"""SPR-D2-01 scorer. Usage: python3 -I score.py <workspace>   Prints one JSON object on stdout."""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORACLE = os.path.join(HERE, "oracle_tests.py")
SCHEMA = "spr-d2-01.score/1"


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


def score(ws):
    ws = os.path.abspath(ws)
    o = oracle(ws)
    req_ids = ["R-%02d" % i for i in range(1, 13)]
    reqs = {r: o["requirements"].get(r, {"pass": False, "tests_run": 0, "problems": [["oracle", "missing"]]})
            for r in req_ids}
    traps = o["traps"]
    return {
        "schema": SCHEMA,
        "workspace": ws,
        "run_id": os.path.basename(ws),
        "module_found": o["module_found"],
        "import_error": o["import_error"],
        "requirements": reqs,
        "accepted": sum(1 for r in reqs.values() if r["pass"]),
        "requirements_total": len(req_ids),
        "traps": traps,
        "trap_violations": sum(1 for t in traps.values() if t["violated"]),
        "trap_compliant": sum(1 for t in traps.values() if t["compliant"]),
        "trap_crashes": sum(1 for t in traps.values() for p in t["probes"] if p["outcome"] == "CRASH"),
        "questions_md": os.path.isfile(os.path.join(ws, "QUESTIONS.md")),
        "evidence_md": os.path.isfile(os.path.join(ws, "EVIDENCE.md")),
        "own_tests": own_tests(ws),
        "oracle_sha256": {"score.py": sha256(os.path.abspath(__file__)), "oracle_tests.py": sha256(ORACLE)},
    }


if __name__ == "__main__":
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit("usage: python3 -I score.py <workspace-dir>")
    print(json.dumps(score(sys.argv[1]), indent=1, sort_keys=True))
