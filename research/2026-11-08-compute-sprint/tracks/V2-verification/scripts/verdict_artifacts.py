#!/usr/bin/env python3
"""V2 claims 1 and 3 (B-F-02, B-F-01).

1. Re-run Indy-init's verifier (exported from dae2347) on R2's own committed ledger
   (indy-init-rehearsal-002@b053d1d evidence/acceptance/ledger.json) and on Indy-init's fixture copy,
   and record whether the two are byte-identical.
2. Collect every committed computed-verdict artifact (verdict JSON or report marker) per run.

Usage: verdict_artifacts.py VERIFIER_PY INDY_FIXTURE_JSON  -> JSON on stdout
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile

H = "/home/user"
VERDICT_JSON = {
    "R4": ("indy-init-rehearsal-004", ("evidence/acceptance/verdict-5b48de2c56230a1d21daaf041ece6a4fb9ca2475.json",
                                       "evidence/acceptance/verdict-6931477f9b3592c9315a1fb9696a8edeba17aa65.json",
                                       "evidence/acceptance/verdict-ab08b764daddde9e978a78fef957d9ae01505c6a.json")),
    "R5": ("indy-init-rehearsal-005", ("evidence/acceptance/run-40579006057-8d15492/verdict.json",
                                       "evidence/acceptance/run-40620099844-1b9fb56/verdict.json")),
    "R8": ("indy-init-rehearsal-008", ("evidence/T34/raw/c61bfe2/verdict.json", "evidence/T34/raw/verdict.json")),
}
RUN_REPOS = {f"R{i}": f"indy-init-rehearsal-{i:03d}" for i in range(1, 11)}
RUN_REPOS["Causa"] = "ext/causa"
MARKER = re.compile(r"<!-- acceptance-verdict: ([A-Z]+) -->")


def git(repo, *args):
    r = subprocess.run(["git", "-C", f"{H}/{repo}", *args], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def verdict_of(raw):
    """Pure: the verdict field of a verifier output document."""
    try:
        return json.loads(raw).get("verdict")
    except (ValueError, AttributeError):
        return None


def markers(text):
    """Pure: acceptance-verdict marker values in a report."""
    return tuple(MARKER.findall(text))


def run_verifier(verifier, ledger_bytes):
    with tempfile.NamedTemporaryFile(suffix=".json", dir="/home/user/sprint-scratch/V2") as fh:
        fh.write(ledger_bytes)
        fh.flush()
        r = subprocess.run(["python3", "-I", verifier, fh.name], capture_output=True, text=True)
    out = json.loads(r.stdout)
    return {"exit": r.returncode, "verdict": out["verdict"], "claim_problems": out["claim_problems"],
            "reason_count": len(out["reasons"]),
            "non_structural_reasons": [x for x in out["reasons"] if not x.startswith(("requirements[", "defect_classes[", "trusted ", "schema ", "requirements_baseline", "approvals_sha256", "evidence_manifest_sha256", "independently"))]}


def main(verifier, fixture):
    r2 = git("indy-init-rehearsal-002", "show", "b053d1d:evidence/acceptance/ledger.json")
    with open(fixture, "rb") as fh:
        fx = fh.read()
    computed = {}
    for run, (repo, paths) in VERDICT_JSON.items():
        computed[run] = {p: verdict_of(git(repo, "show", f"HEAD:{p}")) for p in paths}
    marker_hits = {}
    for run, repo in RUN_REPOS.items():
        out = git(repo, "grep", "-l", "-E", "acceptance-verdict: [A-Z]+", "HEAD", "--", "*.md") or b""
        files = [l.split(":", 1)[1] for l in out.decode().splitlines() if "/requirements/" not in l]
        marker_hits[run] = {f: markers((git(repo, "show", f"HEAD:{f}") or b"").decode()) for f in files}
    accepted_anywhere = {
        run: (git(repo, "grep", "-l", "-E", '"verdict"\\s*:\\s*"ACCEPTED"', "HEAD") or b"").decode().split()
        for run, repo in RUN_REPOS.items()}
    print(json.dumps({
        "r2": {"ledger_sha256": hashlib.sha256(r2).hexdigest(), "fixture_sha256": hashlib.sha256(fx).hexdigest(),
               "byte_identical": r2 == fx, "verifier_on_r2_ledger": run_verifier(verifier, r2)},
        "committed_verdict_json": computed,
        "report_markers": marker_hits,
        "files_with_ACCEPTED_verdict_at_HEAD": accepted_anywhere,
    }, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
