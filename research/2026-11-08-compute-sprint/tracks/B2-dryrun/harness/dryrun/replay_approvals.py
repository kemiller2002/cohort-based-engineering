"""R4-APPROVALS and R8-APPROVALS (D1): the pinned acceptance verifier on the pinned approvals, with a stub ledger.

The dry run cannot have a real ledger before T0, so it feeds the verifier a stub ledger, an empty evidence manifest and
a throwaway one-commit source repository; only the verifier's approvals-related trust problems are matched."""
import json
import subprocess

from . import checks as c
from . import core

CASES = {
    "R4-APPROVALS": {"rehearsal": "R4", "t0": "2026-10-27T06:04:39Z", "event": "B-E-044",
                     "blocker": "approvals file in Praxis schema; verifier needs causa.requirements-approvals/1 (found T+60)",
                     "pre": "ad2f1af", "approvals": "kickoff/rehearsal-004/approvals.json",
                     "baseline": "requirements/causa-requirements-baseline.json",
                     "fixed": "1ede27f", "fixedApprovals": "kickoff/rehearsal-004/approvals.causa.json",
                     "pattern": r"unsupported schema"},
    "R8-APPROVALS": {"rehearsal": "R8", "t0": "2026-11-01T17:31:24Z", "event": "B-E-099",
                     "blocker": "pinned approvals fail verifier trust checks (no immutable authority source); verdict INVALID",
                     "pre": "1cb27ec", "approvals": "kickoff/rehearsal-007/approvals.causa.json",
                     "baseline": "requirements/causa-requirements-baseline-v4.json",
                     "fixed": "81b5461", "fixedApprovals": "kickoff/acceptance/approvals.causa.json",
                     "pattern": r"immutable authority source|invalid change identity"},
}


def _stub_inputs(work, approvals_sha):
    work.mkdir(parents=True, exist_ok=True)
    src = work / "stub-source"
    if not src.exists():
        src.mkdir()
        (src / "README.md").write_text("dry-run stub implementation\n")
        for args in (["init", "-q"], ["add", "-A"],
                     ["-c", "user.name=dryrun", "-c", "user.email=dryrun@invalid", "commit", "-qm", "stub"]):
            subprocess.run(["git", "-C", str(src), *args], check=True, capture_output=True)
    sha = core.git(src, "rev-parse", "HEAD").decode().strip()
    (work / "evidence").mkdir(exist_ok=True)
    manifest = work / "evidence-manifest.json"
    manifest.write_text(json.dumps({"schema": "causa.acceptance-evidence-manifest/1", "entries": []}))
    ledger = work / "ledger.json"
    import hashlib
    ledger.write_text(json.dumps({"schema": "causa.acceptance-ledger/2", "source_commit_sha": sha, "gates": [],
                                  "requirements": [], "accepted": False, "approvals_sha256": approvals_sha,
                                  "evidence_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}))
    return src, sha, manifest, ledger


def verdict_run(indy_rev, approvals_rel, baseline_rel, approvals_rev=None, label="pre"):
    """Run the verifier of indy_rev on approvals (taken at approvals_rev, default indy_rev)."""
    work = core.SCRATCH / "approvals" / f"{indy_rev}-{label}"
    tools = core.export(core.INDY_FULL, indy_rev, work / "indy", ["tools/compute-acceptance-verdict.py",
                                                                  "tools/validate-acceptance-ledger.py", baseline_rel])
    a_raw = core.show(core.INDY_FULL, approvals_rev or indy_rev, approvals_rel)
    a_path = work / "approvals.json"
    a_path.write_bytes(a_raw)
    import hashlib
    src, sha, manifest, ledger = _stub_inputs(work, hashlib.sha256(a_raw).hexdigest())
    sha256 = lambda p: subprocess.run(["sha256sum", str(p)], capture_output=True, text=True).stdout.split()[0]
    b_path = tools / baseline_rel
    cmd = ["python3", "-I", str(tools / "tools/compute-acceptance-verdict.py"), str(ledger), "--repo", str(src),
           "--baseline", str(b_path), "--baseline-sha256", sha256(b_path), "--baseline-source", str(core.INDY_FULL),
           "--approvals", str(a_path), "--approvals-sha256", sha256(a_path),
           "--evidence-manifest", str(manifest), "--evidence-manifest-sha256", sha256(manifest),
           "--evidence-root", str(work / "evidence"), "--trusted-source-sha", sha, "--trusted-operator-id", "kemiller2002"]
    res = core.run(cmd, work, timeout=300, limit=30000)
    try:
        out = json.loads(res["stdout"])
        reasons = out.get("reasons", [])
        verdict = out.get("verdict")
    except ValueError:
        reasons, verdict = [res["stdout"][-2000:]], None
    approvals_json = json.loads(a_raw)
    return {"verifier": core.commit_info(core.INDY_FULL, indy_rev), "approvalsFile": approvals_rel,
            "approvalsAt": core.commit_info(core.INDY_FULL, approvals_rev or indy_rev),
            "approvalsSha256": sha256(a_path), "approvalsSchema": approvals_json.get("schema"),
            "schemaProblems": c.approvals_schema_problems(approvals_json),
            "exit": res["exit"], "verdict": verdict, "approvalProblems": c.approvals_problems_in(reasons),
            "otherReasonsCount": len(reasons) - len(c.approvals_problems_in(reasons)),
            "seconds": res["seconds"], "cmd": res["cmd"], "stderr": res["stderr"][-1500:]}


def replay():
    import re
    records = []
    for key, k in CASES.items():
        pre = core.commit_info(core.INDY_FULL, k["pre"])
        run = verdict_run(k["pre"], k["approvals"], k["baseline"])
        fixed = verdict_run(k["pre"], k["fixedApprovals"], k["baseline"], approvals_rev=k["fixed"], label="fixed")
        matched = [p for p in run["approvalProblems"] if re.search(k["pattern"], p)]
        records.append({
            "key": key, "rehearsal": k["rehearsal"], "blocker": k["blocker"], "trackBEvent": k["event"], "t0": k["t0"],
            "preT0": pre, "preT0IsBeforeT0": c.is_pre_t0(pre["committerTime"], k["t0"]),
            "toolsRun": [f"tools/compute-acceptance-verdict.py @{k['pre']} (stub ledger, stub evidence)", "harness schema-id check"],
            "check": run,
            "falsePositiveCheck": {"approvalsFixedAt": fixed["approvalsAt"], "approvalProblems": fixed["approvalProblems"],
                                   "schemaProblems": fixed["schemaProblems"], "verdict": fixed["verdict"]},
            "outcome": c.outcome(run["exit"] in (0, 1, 3), bool(matched)),
            "matchEvidence": f"verifier verdict {run['verdict']} (exit {run['exit']}); approvals problems: {run['approvalProblems'][:4]}",
            "dryRunSeconds": run["seconds"]})
    return records
