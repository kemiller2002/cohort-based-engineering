#!/usr/bin/env python3
"""Redacting secret-pattern scanner over every blob reachable in a repository's history.

Usage: python3 -I secret_scan.py OUT.json REPO_DIR [REPO_DIR ...]

Each unique blob (all refs, all history) is read once via `git cat-file --batch`.
Output never contains a secret value: only repo, blob id, one path, rule, a redacted
fingerprint (first 4 chars + length + sha256 prefix) and a live-looking heuristic.
"""
import hashlib
import json
import re
import subprocess
import sys

RULES = {
    "github-token": re.compile(rb"\b(gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})\b"),
    "aws-access-key-id": re.compile(rb"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    "private-key-block": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "slack-token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "openai-key": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
    "anthropic-key": re.compile(rb"\bsk-ant-[A-Za-z0-9_-]{32,}\b"),
    "nuget-api-key": re.compile(rb"\boy2[a-z0-9]{43}\b"),
    "google-api-key": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    "generic-assignment": re.compile(
        rb"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*[\"']([A-Za-z0-9/+_\-]{20,})[\"']"),
}
PLACEHOLDER = re.compile(rb"(?i)(example|dummy|placeholder|redacted|xxxx|fake|test|sample|changeme|your[_-]|0000|1234|abcd)")
MAX_BLOB = 2_000_000


def fingerprint(value: bytes) -> str:
    return f"{value[:4].decode(errors='replace')}…len={len(value)} sha256:{hashlib.sha256(value).hexdigest()[:12]}"


def live_looking(rule: str, value: bytes) -> bool:
    if PLACEHOLDER.search(value):
        return False
    if rule == "private-key-block":
        return True
    distinct = len(set(value))
    return distinct >= 12  # low-entropy repeats are placeholders


def scan_bytes(data: bytes):
    """Yield (rule, value) for every match; pure."""
    for rule, rx in RULES.items():
        for m in rx.finditer(data):
            value = m.group(1) if rx.groups else m.group(0)
            yield rule, value


def finding(repo, blob, path, rule, value):
    return {"repo": repo, "blob": blob, "path": path, "rule": rule,
            "fingerprint": fingerprint(value), "live_looking": live_looking(rule, value)}


def blobs(repo):
    out = subprocess.run(["git", "-C", repo, "rev-list", "--objects", "--all"],
                         capture_output=True, check=True).stdout.decode(errors="replace").splitlines()
    paths = {}
    for line in out:
        oid, _, path = line.partition(" ")
        if path and oid not in paths:
            paths[oid] = path
    return paths


def scan_repo(repo):
    paths = blobs(repo)
    proc = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    results = []
    for oid, path in paths.items():
        proc.stdin.write(oid.encode() + b"\n")
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) < 3:
            continue
        size = int(header[2])
        data = proc.stdout.read(size)
        proc.stdout.read(1)
        if header[1] != b"blob" or size > MAX_BLOB or b"\0" in data[:8000]:
            continue
        results.extend(finding(repo, oid, path, r, v) for r, v in scan_bytes(data))
    proc.stdin.close()
    proc.wait()
    return len(paths), results


def main(argv):
    out, repos = argv[1], argv[2:]
    report = {"repos": {}, "findings": []}
    for repo in repos:
        try:
            n, res = scan_repo(repo)
        except subprocess.CalledProcessError as exc:
            report["repos"][repo] = {"error": str(exc)}
            continue
        report["repos"][repo] = {"objects": n, "findings": len(res), "live_looking": sum(f["live_looking"] for f in res)}
        report["findings"].extend(res)
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report["repos"], indent=1))


if __name__ == "__main__":
    main(sys.argv)
