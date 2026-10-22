#!/usr/bin/env python3
"""Generate VAC-002 tasks/L<nn>/{contract.json, task.json} (adapted from ARCH-001 fixtures/make-contracts.py).

The source revision is the sha256 of the requirement file bytes; each requirement's contentDigest is the sha256 of its
`## LEND-...` section text. Contracts are what an ideal Echelon planning stage would produce from the requirement and
the decision records: decision nodes for the decisions a requirement depends on, one verification obligation per
requirement, one owner cohort, and a `conflict` node where a requirement contradicts another requirement or an accepted
decision. When an Ordo binary is given, task.json records `ordo ecir check --blueprint ... --json`. When the sealed
directory is given, task.json records the sha256 of the hidden oracle; nothing else from it is read.

usage: python3 -I make-contracts.py FIXTURE_DIR [ORDO_BINARY] [SEALED_DIR]
"""
import hashlib, json, re, subprocess, sys, pathlib

root = pathlib.Path(sys.argv[1])
ordo = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
sealed = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
sha = lambda b: "sha256:" + hashlib.sha256(b).hexdigest()
hexsha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

# Justifications restate the decision records (repo/docs/decisions and the staged revisions); nothing else.
DEC = {
    "DEC-001r2": "revision 2: a loan lasts 21 days; a due date on a closed day (OpenDays) moves to the next open day",
    "DEC-001r3": "revision 3: the loan period is the member type's (standard 21, student 14, staff 42 days); open-day rule kept",
    "DEC-002": "loan limits per member type: standard 5, student 3, staff 10; a borrow over the limit is refused",
    "DEC-003": "0.25 per day late, at most 10.00 per loan, assessed on return",
    "DEC-004": "at most 2 renewals; not when overdue, not when renewed twice, not when the book has holds (first reason given)",
    "DEC-004r2": "revision 2: a renewed due date on a closed day moves to the next open day",
    "DEC-004r3": "revision 3: a renewal adds the borrower's loan period (DEC-001 revision 3)",
    "DEC-005": "per-book first-come-first-served holds; copies of a held book are lent only to the head of its queue",
    "DEC-006": "fines only by the schedule; no member type exempt; nothing reduces a fine on its own initiative",
    "DEC-006r2": "revision 2: a waiver needs a named branch manager (Grace Hopper, Alan Turing) for the specific fine",
    "DEC-007r2": "revision 2: a returned held copy is set aside for 7 days for the head of the queue, deadline on an open day; uncollected holds expire",
    "DEC-008": "one notice per overdue loan and due date; delivered is final; rejected is sent again; unknown is never resent automatically until staff record the answer",
}

def dec(node_id, reqs, key=None):
    return (node_id, "decision", reqs, [], DEC[key or node_id])

def standard(task, reqs, decisions, extra=()):
    nodes = list(decisions)
    for r in reqs:
        deps = [d[0] for d in decisions if r in d[2]]
        nodes.append((f"VERIFY-{task}-{r}", "verificationObligation", [r], deps, None))
    nodes.append((f"COHORT-{task}", "cohort", list(reqs), sorted({d[0] for d in decisions}), None))
    return nodes + list(extra)

CONTRACTS = {
    "L01": standard("L01", ["R1", "R2", "R3"], []),
    "L02": standard("L02", ["R1", "R2"], [dec("DEC-003", ["R2"])]),
    "L03": standard("L03", ["R1", "R2"], [dec("DEC-004", ["R1"])]),
    "L04": standard("L04", ["R1", "R2", "R3"], [dec("DEC-002", ["R3"]), dec("DEC-006", ["R1", "R2"])],
                    [("CONFLICT-L04-STAFF-BORROWING", "conflict", ["R3"], ["DEC-002"],
                      "LEND-L04-R3 says a staff member below the loan limit is never refused for any other reason; "
                      "LEND-L04-R2 refuses any member owing more than 5.00, LEND-L01-R2 refuses suspended members and "
                      "DEC-005 reserves held copies; which rule wins for staff is unresolved")]),
    "L05": standard("L05", ["R1", "R2", "R3"], [dec("DEC-003", ["R2"]), dec("DEC-006", ["R2"])]),
    "L06": standard("L06", ["R1", "R2"], [dec("DEC-006", ["R1", "R2"], "DEC-006r2")]),
    "L07": standard("L07", ["R1", "R2", "R3"], [dec("DEC-008", ["R1", "R2", "R3"])]),
    "L08": standard("L08", ["R1", "R2"], [dec("DEC-008", ["R2"])],
                    [("CONFLICT-L08-AUTOMATIC-RESEND", "conflict", ["R2"], ["DEC-008"],
                      "LEND-L08-R2 (Customer Services) resends notices whose delivery is unknown automatically; accepted "
                      "DEC-008 (owner: Head of Lending) forbids automatic resending until staff record the answer; unresolved")]),
    "L09": standard("L09", ["R1", "R2"], [dec("DEC-001", ["R1"], "DEC-001r2"), dec("DEC-004", ["R1"], "DEC-004r2")]),
    "L10": standard("L10", ["R1", "R2", "R3"], [dec("DEC-005", ["R2"]), dec("DEC-007", ["R1", "R2", "R3"], "DEC-007r2")]),
    "L11": standard("L11", ["R1", "R2"], []),
    "L12": standard("L12", ["R1", "R2"], [dec("DEC-001", ["R1", "R2"], "DEC-001r3"), dec("DEC-004", ["R1"], "DEC-004r3")]),
}

def build(task):
    tdir = root / "tasks" / task
    data = (tdir / "requirement.md").read_bytes()
    doc = f"requirements/{task}.md"
    lines = data.decode("utf-8").split("\n")
    reqs = {}
    for i, line in enumerate(lines):
        m = re.match(r"^## (LEND-%s-(R\d+))$" % task, line)
        if m:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## ") and not lines[j].startswith("Acceptance criteria"):
                j += 1
            reqs[m.group(2)] = {"id": m.group(1), "location": f"L{i+1}",
                                "digest": sha("\n".join(lines[i:j]).strip().encode("utf-8"))}
    nodes = CONTRACTS[task]
    used = sorted({r for n in nodes for r in n[2]})
    assert used == sorted(reqs), (task, used, sorted(reqs))
    key = lambda r: f"{doc}#{reqs[r]['id']}"
    order = sorted(reqs, key=lambda r: int(r[1:]))
    contract = {
        "schemaVersion": "ecir/1", "sourceManifestDigest": sha(data),
        "requirements": [{"source": {"key": key(r), "originalId": reqs[r]["id"], "document": doc,
                                     "location": reqs[r]["location"], "revision": sha(data), "contentDigest": reqs[r]["digest"]},
                          "disposition": {"kind": "modeled"}, "nodeIds": [n[0] for n in nodes if r in n[2]]} for r in order],
        "nodes": [dict({"id": n[0], "kind": n[1], "requirementKeys": [key(r) for r in n[2]], "dependsOn": n[3]},
                       **({"justification": n[4]} if n[4] else {})) for n in nodes]}
    cpath = tdir / "contract.json"
    cpath.write_text(json.dumps(contract, indent=2) + "\n")
    conflicts = [n for n in nodes if n[1] == "conflict"]
    verdict = {"path": f"tasks/{task}/contract.json", "sha256": hexsha(cpath), "expectedOrdoAdmits": not conflicts}
    if ordo:
        proc = subprocess.run([ordo, "ecir", "check", "--blueprint", str(cpath), "--json"], capture_output=True, text=True)
        out = json.loads(proc.stdout)
        verdict.update({"ordoAdmits": proc.returncode == 0, "ordoExit": proc.returncode, "ordoContractDigest": out.get("contractDigest"),
                        "ordoDiagnostics": sorted({d.get("code") for d in out.get("diagnostics") or []} - {None})})
    return {"requirementIds": [reqs[r]["id"] for r in order], "requirementKeys": [key(r) for r in order],
            "decisionIds": sorted({n[0] for n in nodes if n[1] == "decision"}), "conflictIds": [n[0] for n in conflicts],
            "conflictRequirementIds": sorted({reqs[r]["id"] for n in conflicts for r in n[2]}),
            "title": lines[0].removeprefix("# "), "requirementSha256": hashlib.sha256(data).hexdigest(), "contract": verdict}

META = json.loads((root / "tasks-meta.json").read_text())
for task in sorted(CONTRACTS):
    tdir = root / "tasks" / task
    b = build(task)
    meta = META["tasks"][task]
    oracle = (sealed / "oracle" / task / "OracleTests.fs") if sealed else None
    task_json = {
        "schema": "cbe.vac-002.task/1", "id": task, "workItem": f"LEND-{task}", "title": b["title"],
        "categories": meta["categories"], "difficulty": meta["difficulty"], "kind": meta["kind"],
        "expectedOutcome": meta["expectedOutcome"],
        "requirementIds": b["requirementIds"], "requirementKeys": b["requirementKeys"], "decisionIds": b["decisionIds"],
        "conflictIds": b["conflictIds"], "conflictRequirementIds": b["conflictRequirementIds"],
        "dependsOn": meta["dependsOn"], "interactsWith": meta["interactsWith"],
        "files": {"requirement": {"source": f"tasks/{task}/requirement.md", "target": f"requirements/{task}.md", "sha256": b["requirementSha256"]},
                  "visibleTests": [{"source": f"tasks/{task}/acceptance/{p.name}", "target": f"tests/Lending.Tests/Acceptance/{p.name}", "sha256": hexsha(p)}
                                   for p in sorted((tdir / "acceptance").glob("*.fs"))],
                  "stage": sorted(str(p.relative_to(tdir / "stage")) for p in (tdir / "stage").rglob("*") if p.is_file()) if (tdir / "stage").exists() else [],
                  "before": sorted(str(p.relative_to(tdir / "before")) for p in (tdir / "before").rglob("*") if p.is_file()) if (tdir / "before").exists() else [],
                  "oracle": {"path": f"sealed:oracle/{task}/OracleTests.fs", "sha256": hexsha(oracle) if oracle and oracle.exists() else None}},
        "contract": b["contract"],
    }
    (tdir / "task.json").write_text(json.dumps(task_json, indent=2) + "\n")
    print(task, "contract", b["contract"]["sha256"][:12], "admits", b["contract"].get("ordoAdmits"), b["contract"].get("ordoDiagnostics"))
