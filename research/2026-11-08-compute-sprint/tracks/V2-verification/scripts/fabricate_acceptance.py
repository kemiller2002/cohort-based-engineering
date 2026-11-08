#!/usr/bin/env python3
"""V2 claim 11 (E-F-02): independent fabrication probe of Indy-init's
compute-acceptance-verdict.py. Written from the verifier's source, not from E's script.

Builds, in a scratch directory, a README-only candidate repository and a wholly invented
evidence bundle (no test was run; every artifact's command is a no-op string), then runs the
REAL verifier with the REAL pinned baseline and approvals from rehearsal-005's acceptance.sh,
with the manifest digest computed by the bundle producer (this script) - which is exactly how
acceptance.sh line 66-70/111 derives --evidence-manifest-sha256 from the candidate's own tool.

Usage: fabricate_acceptance.py INDY_FULL_CLONE VERIFIER_PY WORKDIR
Pure functions: make_artifact, make_ledger, make_manifest. I/O lives in main().
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

BASELINE_COMMIT = "cae4102"  # an Indy-init commit whose baseline file hashes to the pinned digest
BASELINE_SHA256 = "621e2f960038dcfb0daa2a9fe18a0c1c350faed297ba2856da1236a0360857b9"
APPROVALS_COMMIT = "295bc6475a17d54d83a1c9e4f7679fab30e43169"
APPROVALS_PATH = "kickoff/rehearsal-005/approvals.causa.json"
APPROVALS_SHA256 = "3e70dcd2e87811c4f3744ee97585855639741c3ba7a63d98f4b842c7e86bace7"
OPERATOR = "kemiller2002"
RUN_ID = "v2-fabricated-run-1"
GATES = tuple(f"G{i}" for i in range(10))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode()


def evidence_type_for(subject_type, subject_id):
    return {("gate", "G8"): "ci", ("gate", "G9"): "deployment"}.get((subject_type, subject_id), "test")


def make_artifact(run_id, source, subject_type, subject_id):
    """An invented evidence record: claims PASS for a command that never ran."""
    return {
        "schema": "causa.acceptance-evidence/1",
        "run_id": run_id, "source_sha": source,
        "subject_type": subject_type, "subject_id": subject_id,
        "status": "PASS", "exit_code": 0,
        "command": "true  # V2 fabricated: nothing was executed",
        "evidence_type": evidence_type_for(subject_type, subject_id),
    }


def artifact_path(subject_type, subject_id):
    return f"evidence/{subject_type}-{subject_id}.json"


def make_bundle(run_id, source, p0_ids):
    """Pure: {relative path: bytes} for every subject the verifier will inspect."""
    subjects = tuple(("gate", g) for g in GATES) + tuple(("requirement", r) for r in p0_ids)
    return {artifact_path(t, i): canonical(make_artifact(run_id, source, t, i)) for t, i in subjects}


def make_manifest(run_id, source, bundle):
    return {
        "schema": "causa.acceptance-evidence-manifest/1",
        "run_id": run_id, "source_sha": source,
        "entries": [{"path": p, "sha256": sha256(b)} for p, b in sorted(bundle.items())],
    }


def make_ledger(run_id, source, baseline, baseline_digest, approvals_digest, manifest_digest, p0_ids):
    src = baseline["source"]
    return {
        "schema": "causa.acceptance-ledger/2",
        "run_id": run_id, "source_commit_sha": source, "deployed_commit_sha": source,
        "contract_version": "fabricated", "frozen_fixture_digest": "fabricated",
        "dependency_lock_sha": "fabricated", "interface_manifest_sha": "fabricated",
        "requirements_baseline": {"id": baseline["id"], "repository": src["repository"],
                                  "commit": src["commit"], "sha256": baseline_digest},
        "approvals_sha256": approvals_digest, "evidence_manifest_sha256": manifest_digest,
        "scope_changes": [],
        "requirements": [{"id": r, "priority": "P0", "status": "PASS", "tests": ["fabricated"],
                          "evidence_paths": [artifact_path("requirement", r)]} for r in p0_ids],
        "defect_classes": [],
        "gates": [{"id": g, "status": "PASS", "verified_sha": source,
                   "evidence_paths": [artifact_path("gate", g)]} for g in GATES],
        "unresolved_decisions": [],
        "accepted": True,
    }


def git(*args, cwd=None, text=False):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True, text=text).stdout


def main(indy, verifier, work):
    work = Path(work)
    assert str(work.resolve()).startswith("/home/user/sprint-scratch/"), "scratch only"
    cand = work / "candidate"
    cand.mkdir(parents=True, exist_ok=True)
    if not (cand / ".git").exists():
        git("init", "-q", "-b", "main", cwd=cand)
        (cand / "README.md").write_text("# README-only candidate (V2 probe)\n")
        git("add", "README.md", cwd=cand)
        git("-c", "user.email=v2@example.invalid", "-c", "user.name=V2", "commit", "-qm", "readme", cwd=cand)
    source = git("rev-parse", "HEAD", cwd=cand, text=True).strip()
    tracked = git("ls-files", cwd=cand, text=True).split()

    baseline_raw = git("-C", indy, "show", f"{BASELINE_COMMIT}:requirements/causa-requirements-baseline.json")
    approvals_raw = git("-C", indy, "show", f"{APPROVALS_COMMIT}:{APPROVALS_PATH}")
    assert sha256(baseline_raw) == BASELINE_SHA256 and sha256(approvals_raw) == APPROVALS_SHA256
    baseline = json.loads(baseline_raw)
    p0_ids = tuple(r["id"] for r in baseline["requirements"] if r.get("priority") == "P0")

    bundle = make_bundle(RUN_ID, source, p0_ids)
    manifest_raw = canonical(make_manifest(RUN_ID, source, bundle))
    manifest_digest = sha256(manifest_raw)  # the "pin" comes from the producer itself
    ledger = make_ledger(RUN_ID, source, baseline, BASELINE_SHA256, APPROVALS_SHA256, manifest_digest, p0_ids)

    out = work / "bundle"
    for rel, raw in bundle.items():
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(raw)
    (out / "evidence-manifest.json").write_bytes(manifest_raw)
    (work / "ledger.json").write_bytes(canonical(ledger))
    (work / "baseline.json").write_bytes(baseline_raw)
    (work / "approvals.json").write_bytes(approvals_raw)

    cmd = ["python3", "-I", verifier, str(work / "ledger.json"), "--repo", str(cand),
           "--baseline", str(work / "baseline.json"), "--baseline-sha256", BASELINE_SHA256,
           "--baseline-source", indy,
           "--approvals", str(work / "approvals.json"), "--approvals-sha256", APPROVALS_SHA256,
           "--evidence-manifest", str(out / "evidence-manifest.json"),
           "--evidence-manifest-sha256", manifest_digest, "--evidence-root", str(out),
           "--trusted-source-sha", source, "--trusted-operator-id", OPERATOR]
    r = subprocess.run(cmd, capture_output=True, text=True)
    result = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"raw": r.stdout, "stderr": r.stderr}
    print(json.dumps({
        "candidate_tracked_files": tracked, "candidate_sha": source,
        "p0_requirements_fabricated": len(p0_ids), "artifacts": len(bundle),
        "manifest_sha256": manifest_digest, "verifier_exit": r.returncode, "result": result,
    }, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:4])
