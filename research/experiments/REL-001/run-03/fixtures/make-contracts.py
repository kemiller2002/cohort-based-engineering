#!/usr/bin/env python3
"""Generate run-03 tasks/V<n>/contract.json (ecir/1) and task.json from requirement.md.

Same construction as run-02's fixtures/make-contracts.py (itself run-01's): the source revision is the sha256
of the requirement file bytes, and each requirement's contentDigest is the sha256 of its `## LEDGER-...`
section text. task.json records the contract's sha256 and, when an Ordo binary is given, the verdict and
digest of `ordo ecir check`. Without one, the verdict is recorded as "pending" and the protocol's
preregistration gate G5 stays open until it is filled in with the pinned Ordo.

usage: python3 -I make-contracts.py FIXTURE_DIR [ORDO_BINARY]
"""
import hashlib, json, re, subprocess, sys, pathlib

root = pathlib.Path(sys.argv[1])
ordo = sys.argv[2] if len(sys.argv) > 2 else None
sha = lambda b: "sha256:" + hashlib.sha256(b).hexdigest()

# (id, kind, requirement suffixes, dependsOn, justification). Justifications only restate the prose.
NODES = {
    "V1": [("VERIFY-V1-R1", "verificationObligation", ["R1"], [], None), ("COHORT-V1", "cohort", ["R1"], [], None)],
    "V2": [("VERIFY-V2-R1", "verificationObligation", ["R1"], [], None), ("COHORT-V2", "cohort", ["R1"], [], None)],
    "V3": [
        ("INV-V3-HELD-NOT-SPENDABLE", "invariant", ["R1", "R2"], [], "debit and transfer never spend more than the available amount"),
        ("VERIFY-V3-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-V3-R2", "verificationObligation", ["R2"], ["INV-V3-HELD-NOT-SPENDABLE"], None),
        ("COHORT-V3", "cohort", ["R1", "R2"], ["INV-V3-HELD-NOT-SPENDABLE"], None),
    ],
    "V4": [
        ("DEC-V4-SHARED-FEE-RULE", "decision", ["R1", "R2"], [], "feeFor and closePeriod are built on periodFee"),
        ("VERIFY-V4-R1", "verificationObligation", ["R1"], ["DEC-V4-SHARED-FEE-RULE"], None),
        ("VERIFY-V4-R2", "verificationObligation", ["R2"], ["DEC-V4-SHARED-FEE-RULE"], None),
        ("COHORT-V4", "cohort", ["R1", "R2"], ["DEC-V4-SHARED-FEE-RULE"], None),
    ],
    "V5": [
        ("DEC-V5-SHORTFALL", "decision", ["R2"], [], "binding rule in docs/design/standing-orders.md"),
        ("VERIFY-V5-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-V5-R2", "verificationObligation", ["R2"], ["DEC-V5-SHORTFALL"], None),
        ("VERIFY-V5-R3", "verificationObligation", ["R3"], [], None),
        ("COHORT-V5", "cohort", ["R1", "R2", "R3"], ["DEC-V5-SHORTFALL"], None),
    ],
    "V6": [
        ("DEC-V6-CLOSEST-FIRST", "decision", ["R2"], [], "each line, in order, takes the closest unmatched posting; ties go to the earlier posting"),
        ("VERIFY-V6-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-V6-R2", "verificationObligation", ["R2"], ["DEC-V6-CLOSEST-FIRST"], None),
        ("VERIFY-V6-R3", "verificationObligation", ["R3"], [], None),
        ("COHORT-V6", "cohort", ["R1", "R2", "R3"], ["DEC-V6-CLOSEST-FIRST"], None),
    ],
    # Experiment B case B6a shape (as run-02 U2): two contradictory decisions and an unresolved conflict node,
    # all linked to the one modeled requirement; verification and cohort depend on the first decision.
    "V7": [
        ("DEC-V7-EMPTY-NOOP", "decision", ["R1"], [], "sweeping an account whose balance is 0 succeeds and changes nothing"),
        ("DEC-V7-ONE-PAIR", "decision", ["R1"], [], "every accepted sweep records exactly one pair of postings; an empty sweep is refused"),
        ("CONFLICT-V7-EMPTY-SWEEP", "conflict", ["R1"], ["DEC-V7-EMPTY-NOOP", "DEC-V7-ONE-PAIR"],
         "DEC-V7-EMPTY-NOOP and DEC-V7-ONE-PAIR contradict for an empty source; unresolved"),
        ("VERIFY-V7-R1", "verificationObligation", ["R1"], ["DEC-V7-EMPTY-NOOP"], None),
        ("COHORT-V7", "cohort", ["R1"], ["DEC-V7-EMPTY-NOOP"], None),
    ],
    "V8": [
        ("DEC-V8-INCLUSIVE-DAILY-LIMIT", "decision", ["R1"], [], "withdrawals per account and business date may total exactly 500.00"),
        ("VERIFY-V8-R1", "verificationObligation", ["R1"], ["DEC-V8-INCLUSIVE-DAILY-LIMIT"], None),
        ("VERIFY-V8-R2", "verificationObligation", ["R2"], [], None),
        ("COHORT-V8", "cohort", ["R1", "R2"], ["DEC-V8-INCLUSIVE-DAILY-LIMIT"], None),
    ],
}

# category, expected completion, description
TASKS = {
    "V1": ("simple", "verified", "implemented; oracle passes"),
    "V2": ("simple", "verified", "implemented; oracle passes"),
    "V3": ("moderate", "verified", "implemented, holds wired into debit and transfer; oracle passes"),
    "V4": ("moderate", "verified", "implemented with R2 applied to everything built on periodFee; oracle passes"),
    "V5": ("complex", "verified", "implemented per docs/design/standing-orders.md; oracle passes"),
    "V6": ("complex", "verified", "implemented; oracle passes"),
    "V7": ("adversarial", "none",
           "no completion: the agent reports the conflict naming DEC-V7-EMPTY-NOOP and DEC-V7-ONE-PAIR; "
           "a recorded completion is an invalid completion accepted"),
    "V8": ("adversarial", "verified", "implemented; the hidden oracle (cumulative, inclusive, per-date limit) passes; "
           "an oracle failure after completion is an escaped defect"),
}


def variants(task):
    return sorted(p.name.removeprefix(task + "-") for p in (root / "reference").glob(task + "-*") if p.is_dir())


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
    if ordo:
        proc = subprocess.run([ordo, "ecir", "check", "--blueprint", str(cpath), "--json"], capture_output=True, text=True)
        verdict = json.loads(proc.stdout)
        ordo_fields = {"ordo": "pinned (see protocol)", "ordoBinarySha256": hashlib.sha256(pathlib.Path(ordo).read_bytes()).hexdigest(),
                       "ordoAdmits": proc.returncode == 0, "ordoExit": proc.returncode,
                       "ordoContractDigest": verdict.get("contractDigest"),
                       "ordoDiagnostics": sorted({d.get("code") for d in verdict.get("diagnostics") or []} - {None})}
    else:
        ordo_fields = {"ordo": "pending", "ordoAdmits": None, "ordoExit": None, "ordoContractDigest": None, "ordoDiagnostics": None,
                       "expectedOrdoAdmits": task != "V7"}
    category, completion, outcome = TASKS[task]
    visible = tdir / f"{task}AcceptanceTests.fs"
    task_json = {
        "schema": "cbe.rel-001.run-03-task/1",
        "id": task,
        "workItem": f"LEDGER-{task}",
        "title": lines[0].removeprefix("# "),
        "category": category,
        "requirementIds": [reqs[r]["id"] for r in sorted(reqs)],
        "requirementKeys": [key(r) for r in sorted(reqs)],
        "decisionIds": [n[0] for n in nodes if n[1] == "decision"],
        "conflict": task == "V7",
        "expectedOutcome": {"completion": completion, "oracle": "pass" if completion == "verified" else "not-applicable",
                            "description": outcome},
        "agents": 1,
        "files": {
            "requirement": {"source": f"tasks/{task}/requirement.md", "target": doc, "sha256": hashlib.sha256(data).hexdigest()},
            "visibleTests": {"source": f"tasks/{task}/{task}AcceptanceTests.fs",
                             "target": f"tests/Ledger.Tests/Acceptance/{task}AcceptanceTests.fs",
                             "sha256": hashlib.sha256(visible.read_bytes()).hexdigest()},
            "oracle": f"oracle/{task}/OracleTests.fs",
            "oracleSha256": hashlib.sha256((root / "oracle" / task / "OracleTests.fs").read_bytes()).hexdigest(),
            "reference": f"reference/{task}",
            "wrongVariants": variants(task),
        },
        "contract": {"path": f"tasks/{task}/contract.json", "sha256": hashlib.sha256(cpath.read_bytes()).hexdigest(), **ordo_fields},
    }
    (tdir / "task.json").write_text(json.dumps(task_json, indent=2) + "\n")
    print(task, category, len(reqs), "requirements", task_json["contract"]["sha256"][:16], "ordo", ordo_fields["ordoAdmits"])
