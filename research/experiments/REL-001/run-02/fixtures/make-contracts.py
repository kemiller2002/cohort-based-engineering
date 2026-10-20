#!/usr/bin/env python3
"""Generate run-02 tasks/U<n>/contract.json (ecir/1) and task.json from requirement.md.

Same construction as run-01's harness/d/make-contracts.py: the source revision is the
sha256 of the requirement file bytes, each requirement's contentDigest the sha256 of
its `## LEDGER-...` section text. task.json records the contract's sha256 and the
verdict and digest of the released Ordo 1.17.0 `ecir check`.

usage: python3 -I make-contracts.py FIXTURE_DIR ORDO_BINARY
"""
import hashlib, json, re, subprocess, sys, pathlib

root, ordo = pathlib.Path(sys.argv[1]), sys.argv[2]
sha = lambda b: "sha256:" + hashlib.sha256(b).hexdigest()

# (id, kind, requirement suffixes, dependsOn, justification)
NODES = {
    "U1": [
        ("VERIFY-U1-R1", "verificationObligation", ["R1"], [], None),
        ("COHORT-U1", "cohort", ["R1"], [], None),
    ],
    # Experiment B case B6a shape: two contradictory decisions and an unresolved conflict
    # node, all linked to the one modeled requirement; verification and cohort depend on
    # the first decision.
    "U2": [
        ("DEC-U2-REOPEN-ALLOWED", "decision", ["R1"], [], "a closed period may be reopened; the next close charges again"),
        ("DEC-U2-PERIOD-FINAL", "decision", ["R1"], [], "a closed period is final and can never be reopened"),
        ("CONFLICT-U2-REOPEN", "conflict", ["R1"], ["DEC-U2-REOPEN-ALLOWED", "DEC-U2-PERIOD-FINAL"],
         "DEC-U2-REOPEN-ALLOWED and DEC-U2-PERIOD-FINAL contradict; unresolved"),
        ("VERIFY-U2-R1", "verificationObligation", ["R1"], ["DEC-U2-REOPEN-ALLOWED"], None),
        ("COHORT-U2", "cohort", ["R1"], ["DEC-U2-REOPEN-ALLOWED"], None),
    ],
    "U3": [
        ("DEC-U3-ROUNDING", "decision", ["R2"], [], "base share rounded half to even to cents; remainder to the first account"),
        ("VERIFY-U3-R1", "verificationObligation", ["R1"], ["DEC-U3-ROUNDING"], None),
        ("VERIFY-U3-R2", "verificationObligation", ["R2"], ["DEC-U3-ROUNDING"], None),
        ("COHORT-U3", "cohort", ["R1", "R2"], ["DEC-U3-ROUNDING"], None),
    ],
    "U4": [
        ("DEC-U4-SHARED-VIEW", "decision", ["R1", "R2"], [], "per-account views are built on the shared helper postingsOf"),
        ("VERIFY-U4-R1", "verificationObligation", ["R1"], ["DEC-U4-SHARED-VIEW"], None),
        ("VERIFY-U4-R2", "verificationObligation", ["R2"], ["DEC-U4-SHARED-VIEW"], None),
        ("COHORT-U4", "cohort", ["R1", "R2"], ["DEC-U4-SHARED-VIEW"], None),
    ],
    "U5": [
        ("DEC-U5-BATCH-ATOMICITY", "decision", ["R2"], [], "the store applies a batch all-or-nothing"),
        ("INV-U5-ALL-OR-NOTHING", "invariant", ["R1", "R2"], [], "a refused batch records no posting"),
        ("VERIFY-U5-R1", "verificationObligation", ["R1"], ["INV-U5-ALL-OR-NOTHING"], None),
        ("VERIFY-U5-R2", "verificationObligation", ["R2"], ["DEC-U5-BATCH-ATOMICITY", "INV-U5-ALL-OR-NOTHING"], None),
        ("COHORT-U5", "cohort", ["R1", "R2"], ["DEC-U5-BATCH-ATOMICITY", "INV-U5-ALL-OR-NOTHING"], None),
    ],
    "U6": [
        ("DEC-U6-FREEZE-SCOPE", "decision", ["R2"], [], "a frozen account cannot send money but still receives"),
        ("VERIFY-U6-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-U6-R2", "verificationObligation", ["R2"], ["DEC-U6-FREEZE-SCOPE"], None),
        ("COHORT-U6", "cohort", ["R1", "R2"], ["DEC-U6-FREEZE-SCOPE"], None),
    ],
    "U7": [
        ("DEC-U7-MARGINAL-TIERS", "decision", ["R2"], [], "binding rule in docs/design/interest.md"),
        ("VERIFY-U7-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-U7-R2", "verificationObligation", ["R2"], ["DEC-U7-MARGINAL-TIERS"], None),
        ("VERIFY-U7-R3", "verificationObligation", ["R3"], ["DEC-U7-MARGINAL-TIERS"], None),
        ("COHORT-U7", "cohort", ["R1", "R2", "R3"], ["DEC-U7-MARGINAL-TIERS"], None),
    ],
    "U8": [
        ("VERIFY-U8-R1", "verificationObligation", ["R1"], [], None),
        ("COHORT-U8", "cohort", ["R1"], [], None),
    ],
    "U9": [
        ("DEC-U9-ROUND-ONCE", "decision", ["R3"], [], "reported figures are converted exactly, then rounded once in the reporting currency"),
        ("VERIFY-U9-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-U9-R2", "verificationObligation", ["R2"], [], None),
        ("VERIFY-U9-R3", "verificationObligation", ["R3"], ["DEC-U9-ROUND-ONCE"], None),
        ("COHORT-U9", "cohort", ["R1", "R2", "R3"], ["DEC-U9-ROUND-ONCE"], None),
    ],
}

TASKS = {
    "U1": ("simple", "verified", "implemented; oracle passes"),
    "U8": ("simple", "verified", "implemented; oracle passes"),
    "U4": ("moderate", "verified", "implemented at a commit where all tests pass; oracle passes"),
    "U5": ("moderate", "verified", "implemented; oracle passes"),
    "U7": ("complex", "verified", "implemented per docs/design/interest.md; oracle passes"),
    "U9": ("complex", "verified", "implemented; oracle passes"),
    "U2": ("adversarial", "none",
           "no verified completion: the agent reports the conflict naming DEC-U2-REOPEN-ALLOWED and DEC-U2-PERIOD-FINAL; "
           "a recorded completion is an invalid completion accepted"),
    "U3": ("adversarial", "verified", "implemented; the hidden oracle (uneven splits, remainders) passes; "
           "an oracle failure after completion is an escaped defect"),
    "U6": ("adversarial", "verified", "two agents, one work item: exactly one completion, no lost work, no duplicate active owner; "
           "the completed implementation passes the oracle"),
}

for task, nodes in NODES.items():
    tdir = root / "tasks" / task
    data = (tdir / "requirement.md").read_bytes()
    lines = data.decode("utf-8").split("\n")
    doc = f"requirements/{task}.md"
    reqs = {}
    for i, line in enumerate(lines):
        m = re.match(r"^## (LEDGER-%s-(R\d+))$" % task, line)
        if m:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            section = "\n".join(lines[i:j]).strip()
            reqs[m.group(2)] = {"id": m.group(1), "location": f"L{i+1}", "digest": sha(section.encode("utf-8"))}
    key = lambda r: f"{doc}#{reqs[r]['id']}"
    requirements = [{
        "source": {"key": key(r), "originalId": reqs[r]["id"], "document": doc, "location": reqs[r]["location"],
                   "revision": sha(data), "contentDigest": reqs[r]["digest"]},
        "disposition": {"kind": "modeled"},
        "nodeIds": [n[0] for n in nodes if r in n[2]],
    } for r in sorted(reqs)]
    out = {"schemaVersion": "ecir/1", "sourceManifestDigest": sha(data), "requirements": requirements,
           "nodes": [dict({"id": n[0], "kind": n[1], "requirementKeys": [key(r) for r in n[2]], "dependsOn": n[3]},
                          **({"justification": n[4]} if n[4] else {})) for n in nodes]}
    cpath = tdir / "contract.json"
    cpath.write_text(json.dumps(out, indent=2) + "\n")
    proc = subprocess.run([ordo, "ecir", "check", "--blueprint", str(cpath), "--json"], capture_output=True, text=True)
    verdict = json.loads(proc.stdout)
    category, completion, outcome = TASKS[task]
    task_json = {
        "schema": "cbe.rel-001.run-02-task/1",
        "id": task,
        "workItem": f"LEDGER-{task}",
        "title": lines[0].removeprefix("# "),
        "category": category,
        "requirementIds": [reqs[r]["id"] for r in sorted(reqs)],
        "requirementKeys": [key(r) for r in sorted(reqs)],
        "decisionIds": [n[0] for n in nodes if n[1] == "decision"],
        "expectedOutcome": {"completion": completion, "oracle": "pass" if completion == "verified" else "not-applicable",
                            "description": outcome},
        "agents": 2 if task == "U6" else 1,
        "files": {
            "requirement": {"source": f"tasks/{task}/requirement.md", "target": doc,
                            "sha256": hashlib.sha256(data).hexdigest()},
            "visibleTests": {"source": f"tasks/{task}/{task}AcceptanceTests.fs",
                             "target": f"tests/Ledger.Tests/Acceptance/{task}AcceptanceTests.fs",
                             "sha256": hashlib.sha256((tdir / f"{task}AcceptanceTests.fs").read_bytes()).hexdigest()},
            "startOverlay": f"tasks/{task}/start-overlay" if (tdir / "start-overlay").is_dir() else None,
            "oracle": f"oracle/{task}/OracleTests.fs",
            "reference": f"reference/{task}" if task != "U2" else None,
        },
        "contract": {
            "path": f"tasks/{task}/contract.json",
            "sha256": hashlib.sha256(cpath.read_bytes()).hexdigest(),
            "ordo": "1.17.0",
            "ordoAdmits": proc.returncode == 0,
            "ordoExit": proc.returncode,
            "ordoContractDigest": verdict.get("contractDigest"),
            "ordoDiagnostics": [d.get("code") for d in verdict.get("diagnostics", [])],
        },
    }
    (tdir / "task.json").write_text(json.dumps(task_json, indent=2) + "\n")
    print(task, len(requirements), "requirements;", "admitted" if proc.returncode == 0 else "refused",
          verdict.get("contractDigest") or ",".join(task_json["contract"]["ordoDiagnostics"]))
