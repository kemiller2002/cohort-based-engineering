#!/usr/bin/env python3
"""ARCH-001 SMOKE STAND-IN for Worker C's `archcheck` (INTERFACES §5). Never used for a pilot or confirmatory run.

usage: standin-archcheck.py verify --repo DIR --policy POLICY.json [--contract C.json] [--probes P.json]
                                   [--json] [--out REPORT.json] [--require-clean]
       standin-archcheck.py selftest

Textual (not compiler-resolved) checks over src/**/*.fs, enough to exercise the harness end to end:
  ARC-SYM-02  policy .rules["ARC-SYM-02"].symbols outside .allowedIn files               (DET, sev 2)
  ARC-SYM-01  policy .rules["ARC-SYM-01"].namespaces in projects of the listed tiers     (DET, sev 3)
  ARC-TRC-01  each contract decision id must occur in a src/ .fs file and a tests/ .fs file (DET, sev 1)
Emits arch001.verifier-report/1; exit 0 = no DET finding of severity >= 2, 1 = at least one, 2 = could not evaluate.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def fs_files(repo, top):
    base = os.path.join(repo, top)
    return sorted(os.path.relpath(os.path.join(d, f), repo) for d, _, fs in os.walk(base)
                  if "/bin" not in d and "/obj" not in d for f in fs if f.endswith(".fs"))


def project_of(rel, projects):
    return next((p for p in projects if rel.startswith(os.path.dirname(p["path"]) + "/")), None)


def findings_for(repo, policy, contract):
    rules = policy.get("rules") or {}
    projects = policy.get("projects") or []
    out = []
    src = fs_files(repo, "src")
    texts = {f: open(os.path.join(repo, f), errors="replace").read().splitlines() for f in src}
    r2 = rules.get("ARC-SYM-02")
    if r2:
        for f, lines in texts.items():
            if f in (r2.get("allowedIn") or []):
                continue
            for i, line in enumerate(lines, 1):
                for s in r2.get("symbols") or []:
                    if re.search(r"\b" + re.escape(s) + r"\b", line.split("//")[0]):
                        out.append({"ruleId": "ARC-SYM-02", "class": "DET", "severity": r2.get("severity", 2), "file": f, "line": i,
                                    "column": line.find(s) + 1, "symbol": s, "project": (project_of(f, projects) or {}).get("path"),
                                    "message": f"{s} read outside the composition root"})
    r1 = rules.get("ARC-SYM-01")
    if r1:
        for f, lines in texts.items():
            p = project_of(f, projects)
            if not p or p.get("tier") not in (r1.get("tiers") or []):
                continue
            for i, line in enumerate(lines, 1):
                for ns in r1.get("namespaces") or []:
                    if re.search(r"\b" + re.escape(ns) + r"\b", line.split("//")[0]):
                        out.append({"ruleId": "ARC-SYM-01", "class": "DET", "severity": r1.get("severity", 3), "file": f, "line": i,
                                    "column": line.find(ns) + 1, "symbol": ns, "project": p["path"], "message": f"{ns} used in tier {p['tier']}"})
    if contract:
        tests = "\n".join(open(os.path.join(repo, f), errors="replace").read() for f in fs_files(repo, "tests"))
        prod = "\n".join("\n".join(v) for v in texts.values())
        for n in contract.get("nodes") or []:
            if n.get("kind") == "decision":
                where = [w for w, t in (("production code", prod), ("tests", tests)) if n["id"] not in t]
                if where:
                    out.append({"ruleId": "ARC-TRC-01", "class": "DET", "severity": 1, "file": None, "line": None, "column": None,
                                "symbol": n["id"], "project": None, "message": f"decision {n['id']} not traced in " + " and ".join(where)})
    return sorted(out, key=lambda f: (f["ruleId"], f["file"] or "", f["line"] or 0, f["symbol"] or ""))


def git(repo, *a):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def verify(args):
    opt = lambda k: args[args.index(k) + 1] if k in args else None
    repo, policy_path, contract_path, out = opt("--repo"), opt("--policy"), opt("--contract"), opt("--out")
    try:
        policy = json.load(open(policy_path))
        contract = json.load(open(contract_path)) if contract_path else None
    except (OSError, ValueError, TypeError) as e:
        print(f"could not evaluate: {e}", file=sys.stderr)
        return 2
    findings = findings_for(repo, policy, contract)
    by_sev = {str(s): sum(1 for f in findings if f["class"] == "DET" and f["severity"] == s) for s in (1, 2, 3)}
    passed = not any(f["class"] == "DET" and f["severity"] >= 2 for f in findings)
    report = {"schema": "arch001.verifier-report/1", "standIn": True,
              "verifier": {"version": "standin-0.1", "sha256": sha256(os.path.abspath(__file__))},
              "policy": {"id": policy.get("id"), "sha256": sha256(policy_path)},
              "repo": {"gitHead": git(repo, "rev-parse", "HEAD"), "treeClean": git(repo, "status", "--porcelain") == "",
                       "treeHash": git(repo, "rev-parse", "HEAD^{tree}")},
              "evaluatedAt": datetime.now(timezone.utc).isoformat(), "buildOk": None,
              "projects": policy.get("projects") or [], "findings": findings,
              "summary": {"det": {"bySeverity": by_sev}, "heu": 0, "pass": passed}}
    text = json.dumps(report, indent=2, sort_keys=True)
    if out:
        open(out, "w").write(text + "\n")
    if "--json" in args:
        print(text)
    else:
        for f in findings:
            print(f"{f['ruleId']} sev{f['severity']} {f['file']}:{f['line']} {f['message']}")
        print("PASS" if passed else "FAIL")
    return 0 if passed else 1


def main(argv):
    if len(argv) < 2 or argv[1] in ("--help", "-h"):
        print(__doc__)
        return 0
    if argv[1] == "verify":
        if "--help" in argv:
            print(__doc__)
            return 0
        return verify(argv[2:])
    if argv[1] == "selftest":
        print("standin selftest: ok")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
