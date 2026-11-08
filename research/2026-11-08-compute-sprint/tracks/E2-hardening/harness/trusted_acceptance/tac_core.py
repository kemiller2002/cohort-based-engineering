"""SPR-E2-03 trusted acceptance: pure core (no I/O). EXPERIMENTAL prototype for E-F-02.

Evidence is trusted only if it was produced and signed by the verifier job: every entry and the manifest carry an
Ed25519 signature by the pinned verifier key, and the manifest digest is computed here from the bytes, never taken
from the caller. Signing and verification are passed in as functions so this module stays pure and testable.
"""
import hashlib
import json

ENTRY_SCHEMA = "e2.trusted-evidence/1"
MANIFEST_SCHEMA = "e2.trusted-manifest/1"


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def key_id(public_raw: bytes) -> str:
    return "ed25519:" + sha256_hex(public_raw)[:32]


def judge(expect: dict, exit_code: int, stdout: str) -> str:
    """The verifier's own judgement of one black-box check; the candidate's output is data, never a verdict."""
    ok = exit_code == expect.get("exit_code", 0) and ("stdout" not in expect or stdout.strip() == expect["stdout"])
    return "PASS" if ok else "FAIL"


def make_entry(run_id, job_id, source_sha, requirement, check, exit_code, stdout, started, finished, kid) -> dict:
    return {"schema": ENTRY_SCHEMA, "run_id": run_id, "job_id": job_id, "source_sha": source_sha,
            "requirement": requirement, "check_id": check["check_id"], "command": check["argv"],
            "exit_code": exit_code, "status": judge(check["expect"], exit_code, stdout),
            "stdout_sha256": sha256_hex(stdout.encode()), "started_at": started, "finished_at": finished,
            "verifier_key_id": kid}


def signed_document(body: dict, sign) -> bytes:
    return canonical({"body": body, "signature": sign(canonical(body)).hex()})


def make_manifest(run_id, job_id, source_sha, plan_sha, kid, entry_files: dict) -> dict:
    return {"schema": MANIFEST_SCHEMA, "run_id": run_id, "job_id": job_id, "source_sha": source_sha,
            "plan_sha256": plan_sha, "verifier_key_id": kid,
            "entries": [{"path": p, "sha256": sha256_hex(b)} for p, b in sorted(entry_files.items())]}


def _open_signed(raw: bytes, verify, label: str):
    """(body, reasons) for a signed document; body is None when it cannot be trusted."""
    try:
        doc = json.loads(raw)
    except ValueError as ex:
        return None, [f"{label} is not JSON: {ex}"]
    if not isinstance(doc, dict) or not isinstance(doc.get("body"), dict) or not isinstance(doc.get("signature"), str):
        return None, [f"{label} carries no verifier signature (not produced by the trusted verifier job)"]
    try:
        signature = bytes.fromhex(doc["signature"])
    except ValueError:
        return None, [f"{label} signature is not hex"]
    if not verify(signature, canonical(doc["body"])):
        return None, [f"{label} signature does not verify under the pinned verifier key"]
    return doc["body"], []


def decide(manifest_raw: bytes, read_entry, verify, pinned_kid: str, pinned_source_sha: str, plan: dict,
           plan_sha: str, caller_manifest_sha=None) -> dict:
    """The trusted verdict. read_entry(path) -> bytes | None. Returns {verdict, reasons, manifest_sha256, ...}.

    REFUSED: evidence that is not verifiably the verifier job's own output for the pinned commit and plan.
    FAILED: trusted evidence in which some requirement did not pass. ACCEPTED: trusted, complete, all PASS.
    """
    computed = sha256_hex(manifest_raw)
    notes = []
    if caller_manifest_sha is not None and caller_manifest_sha != computed:
        notes.append("caller-supplied manifest digest ignored (differs from the digest computed by the verifier)")
    result = lambda verdict, reasons: {"verdict": verdict, "reasons": reasons, "manifest_sha256": computed, "notes": notes}

    manifest, reasons = _open_signed(manifest_raw, verify, "manifest")
    if manifest is None:
        return result("REFUSED", reasons)
    checks = [
        (manifest.get("schema") == MANIFEST_SCHEMA, "manifest schema is not " + MANIFEST_SCHEMA),
        (manifest.get("verifier_key_id") == pinned_kid, "manifest names a different verifier key"),
        (manifest.get("source_sha") == pinned_source_sha,
         f"manifest is for source {manifest.get('source_sha')}, not the pinned {pinned_source_sha}"),
        (manifest.get("plan_sha256") == plan_sha, "manifest was produced for a different acceptance plan"),
    ]
    reasons = [message for ok, message in checks if not ok]
    if reasons:
        return result("REFUSED", reasons)

    required = {r["id"] for r in plan["requirements"]}
    statuses = {}
    for item in manifest.get("entries", []):
        raw = read_entry(item.get("path", ""))
        if raw is None:
            reasons.append(f"evidence entry {item.get('path')} is missing")
            continue
        if sha256_hex(raw) != item.get("sha256"):
            reasons.append(f"evidence entry {item['path']} does not match the signed manifest digest")
            continue
        entry, problems = _open_signed(raw, verify, f"evidence entry {item['path']}")
        reasons.extend(problems)
        if entry is None:
            continue
        for field in ("run_id", "job_id", "source_sha"):
            if entry.get(field) != manifest.get(field):
                reasons.append(f"evidence entry {item['path']} {field} differs from the manifest")
        if entry.get("schema") != ENTRY_SCHEMA or entry.get("verifier_key_id") != pinned_kid:
            reasons.append(f"evidence entry {item['path']} is not a trusted-evidence entry of the pinned key")
        if entry.get("requirement") in statuses:
            reasons.append(f"requirement {entry.get('requirement')} has more than one entry")
        statuses[entry.get("requirement")] = entry.get("status")
    missing = sorted(required - set(statuses))
    unknown = sorted(set(statuses) - required)
    reasons += [f"requirement {r} has no trusted evidence" for r in missing]
    reasons += [f"evidence names requirement {r}, which is not in the plan" for r in unknown]
    if reasons:
        return result("REFUSED", reasons)
    failed = sorted(r for r, s in statuses.items() if s != "PASS")
    return result("FAILED", [f"requirement {r} did not pass" for r in failed]) if failed else result("ACCEPTED", [])
