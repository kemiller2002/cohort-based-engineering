#!/usr/bin/env python3
"""E-X10: can a fully fabricated evidence bundle obtain ACCEPTED from Indy-init's
compute-acceptance-verdict.py when the evidence-manifest digest is supplied by the
same party that produced the bundle (as rehearsal-005 tools/acceptance/ci/acceptance.sh does)?

Usage: python3 -I indy_fabricated_acceptance.py INDY_INIT_FULL_CLONE WORKDIR

Uses the REAL Indy-init baseline (BL-CAUSA-INDY-INIT-aab8f80c7743, sha256 621e2f96...)
and the REAL rehearsal-005 approvals file (sha256 3e70dcd2...). The candidate repository
contains one commit with a README and no application. Every evidence artifact is written
by this script; no test is executed. Nothing outside WORKDIR is modified.
Pure builders are unit-tested in tests/test_indy_fabricated_acceptance.py.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

GATES = tuple(f"G{i}" for i in range(10))
BASELINE_PATH = "requirements/causa-requirements-baseline.json"
APPROVALS_PATH = "kickoff/rehearsal-005/approvals.causa.json"
OPERATOR = "kemiller2002"
RUN_ID = "fabricated-run-1"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def jbytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def p0_ids(baseline: dict) -> tuple:
    return tuple(r["id"] for r in baseline.get("requirements", []) if r.get("priority") == "P0")


def evidence_doc(source_sha: str, subject_type: str, subject_id: str, evidence_type: str) -> dict:
    return {"schema": "causa.acceptance-evidence/1", "run_id": RUN_ID, "source_sha": source_sha,
            "subject_type": subject_type, "subject_id": subject_id, "status": "PASS", "exit_code": 0,
            "command": "echo fabricated  # no test was run", "evidence_type": evidence_type}


def gate_evidence_type(gid: str) -> str:
    return {"G8": "ci", "G9": "deployment"}.get(gid, "test")


def fabricate_bundle(source_sha: str, requirement_ids: tuple) -> dict:
    """Return {relative_path: bytes} for every fabricated evidence artifact."""
    gates = {f"gates/{g}.json": jbytes(evidence_doc(source_sha, "gate", g, gate_evidence_type(g))) for g in GATES}
    reqs = {f"requirements/{r}.json": jbytes(evidence_doc(source_sha, "requirement", r, "test")) for r in requirement_ids}
    return {**gates, **reqs}


def manifest_for(bundle: dict, source_sha: str) -> dict:
    return {"schema": "causa.acceptance-evidence-manifest/1", "run_id": RUN_ID, "source_sha": source_sha,
            "entries": [{"path": p, "sha256": sha256(b)} for p, b in sorted(bundle.items())]}


def ledger_for(baseline: dict, baseline_sha: str, approvals_sha: str, manifest_sha: str,
               source_sha: str, requirement_ids: tuple) -> dict:
    return {
        "schema": "causa.acceptance-ledger/2", "run_id": RUN_ID,
        "source_commit_sha": source_sha, "deployed_commit_sha": source_sha,
        "contract_version": "fabricated", "frozen_fixture_digest": "fabricated",
        "dependency_lock_sha": "fabricated", "interface_manifest_sha": "fabricated",
        "requirements_baseline": {"id": baseline["id"], "repository": baseline["source"]["repository"],
                                  "commit": baseline["source"]["commit"], "sha256": baseline_sha},
        "approvals_sha256": approvals_sha, "evidence_manifest_sha256": manifest_sha,
        "scope_changes": [], "accepted": True,
        "requirements": [{"id": r, "priority": "P0", "status": "PASS", "tests": [f"fabricated-{r}"],
                          "evidence_paths": [f"requirements/{r}.json"]} for r in requirement_ids],
        "defect_classes": [],
        "gates": [{"id": g, "status": "PASS", "verified_sha": source_sha, "evidence_paths": [f"gates/{g}.json"]}
                  for g in GATES],
    }


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main(argv):
    indy, work = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    cand = work / "candidate"
    cand.mkdir(exist_ok=True)
    (cand / "README.md").write_text("No application here.\n")
    git("init", "-q", "-b", "main", cwd=cand)
    git("-c", "user.name=x", "-c", "user.email=x@example.invalid", "commit", "-qam", "empty", "--allow-empty", cwd=cand)
    git("add", "-A", cwd=cand)
    git("-c", "user.name=x", "-c", "user.email=x@example.invalid", "commit", "-qm", "readme", cwd=cand)
    source = git("rev-parse", "HEAD", cwd=cand)

    baseline_raw = (indy / BASELINE_PATH).read_bytes()
    approvals_raw = (indy / APPROVALS_PATH).read_bytes()
    baseline = json.loads(baseline_raw)
    reqs = p0_ids(baseline)
    bundle = fabricate_bundle(source, reqs)
    root = work / "bundle"
    for rel, raw in bundle.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(raw)
    manifest_raw = jbytes(manifest_for(bundle, source))
    (root / "evidence-manifest.json").write_bytes(manifest_raw)
    ledger = ledger_for(baseline, sha256(baseline_raw), sha256(approvals_raw), sha256(manifest_raw), source, reqs)
    (work / "ledger.json").write_bytes(jbytes(ledger))
    (work / "approvals.json").write_bytes(approvals_raw)
    cmd = ["python3", "-I", str(indy / "tools/compute-acceptance-verdict.py"), str(work / "ledger.json"),
           "--repo", str(cand), "--baseline", str(indy / BASELINE_PATH), "--baseline-sha256", sha256(baseline_raw),
           "--baseline-source", str(indy), "--approvals", str(work / "approvals.json"),
           "--approvals-sha256", sha256(approvals_raw), "--evidence-manifest", str(root / "evidence-manifest.json"),
           # The manifest digest is computed here, by the producer of the bundle, exactly as acceptance.sh does.
           "--evidence-manifest-sha256", sha256(manifest_raw), "--evidence-root", str(root),
           "--trusted-source-sha", source, "--trusted-operator-id", OPERATOR]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = json.loads(res.stdout) if res.stdout.strip().startswith("{") else {"raw": res.stdout[:500]}
    summary = {"experiment": "E-X10", "indy_init_commit": git("rev-parse", "HEAD", cwd=indy),
               "baseline_sha256": sha256(baseline_raw), "approvals_sha256": sha256(approvals_raw),
               "p0_requirements": len(reqs), "fabricated_artifacts": len(bundle), "candidate_files": ["README.md"],
               "exit": res.returncode, "verdict": out.get("verdict"), "reasons": out.get("reasons", [])[:10],
               "claim_problems": out.get("claim_problems"), "stderr": res.stderr[-400:]}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
