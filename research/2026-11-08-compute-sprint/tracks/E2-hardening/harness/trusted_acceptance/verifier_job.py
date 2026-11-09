#!/usr/bin/env python3
"""SPR-E2-03 verifier job (runs as the verifier identity, root in the local simulation).

usage: verifier_job.py VERIFIER_DIR CANDIDATE_REPO PINNED_SOURCE_SHA RUN_ID OUT_DIR

1. Clones the candidate at the operator-pinned commit into a verifier-owned workspace (not writable by the candidate).
2. Runs every black-box check of the verifier's own plan by invoking the candidate program as uid/gid 65534 through
   setpriv, with a cleared environment and a timeout; the candidate never sees the key or the output directory.
3. Judges each result in this process, writes one signed entry per requirement, computes the manifest digest itself
   and signs the manifest. Prints {"manifest_sha256": ...} computed here.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tac_core as core  # noqa: E402
import tac_keys as keys  # noqa: E402

CANDIDATE_UID = 65534


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def run_as_candidate(argv, workspace, timeout=10):
    cmd = ["setpriv", f"--reuid={CANDIDATE_UID}", f"--regid={CANDIDATE_UID}", "--clear-groups", "--", *argv]
    try:
        p = subprocess.run(cmd, cwd=workspace, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired:
        return 124, ""


def main(verifier_dir, candidate, pinned_sha, run_id, out_dir):
    verifier_dir, out = Path(verifier_dir), Path(out_dir)
    assert os.geteuid() == 0, "the verifier job runs as the verifier identity (root in this simulation)"
    sign, public_raw = keys.signer(verifier_dir / "keys" / "signing.pem")
    kid = core.key_id(public_raw)
    plan_raw = (verifier_dir / "plan.json").read_bytes()
    plan = json.loads(plan_raw)
    job_id = str(uuid.uuid4())

    work_parent = verifier_dir / "work"
    work_parent.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="ws-", dir=work_parent))
    workspace.chmod(0o755)
    try:
        # file:// transport: the verifier reads the candidate's objects through upload-pack and never trusts the
        # candidate-owned repository's config or hooks (it is owned by another uid).
        git("clone", "-q", "-u", "git -c safe.directory=* upload-pack", "file://" + str(Path(candidate).resolve()),
            str(workspace / "src"))
        git("checkout", "-q", "--detach", pinned_sha, cwd=workspace / "src")
        head = git("rev-parse", "HEAD", cwd=workspace / "src")
        assert head == pinned_sha, f"workspace HEAD {head} is not the pinned {pinned_sha}"
        files = {}
        for req in plan["requirements"]:
            started = now()
            argv = [a.replace("{src}", str(workspace / "src")) for a in req["argv"]]
            code, stdout = run_as_candidate(argv, workspace / "src")
            entry = core.make_entry(run_id, job_id, pinned_sha, req["id"], req, code, stdout, started, now(), kid)
            files[f"entries/{req['id']}.json"] = core.signed_document(entry, sign)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

    manifest = core.make_manifest(run_id, job_id, pinned_sha, core.sha256_hex(plan_raw), kid, files)
    manifest_doc = core.signed_document(manifest, sign)
    out.mkdir(parents=True, exist_ok=True)
    out.chmod(0o755)
    for rel, raw in files.items():
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(raw)
    (out / "manifest.json").write_bytes(manifest_doc)
    print(json.dumps({"job_id": job_id, "source_sha": pinned_sha, "entries": len(files),
                      "manifest_sha256": core.sha256_hex(manifest_doc),
                      "statuses": {json.loads(b)["body"]["requirement"]: json.loads(b)["body"]["status"] for b in files.values()}}))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
