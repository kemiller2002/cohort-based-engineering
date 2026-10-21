#!/usr/bin/env python3
"""Generate ARCH-001 tasks/T<n>/{contract.json, followup-contract.json, task.json}.

Construction follows REL-001 run-03 make-contracts.py: the source revision is the sha256 of the requirement
file bytes, and each requirement's contentDigest is the sha256 of its `## LEND-...` section text. Initial
requirements live at requirements/T<n>.md, follow-up requirements at requirements/T<n>-followup.md (the
targets the harness copies them to). When an Ordo binary is given, task.json records the verdict of
`ordo ecir check --blueprint ... --json` for both contracts. When the sealed directory is given (or
ARCH001_SEALED points at it), task.json records the sha256 of the sealed oracle files; nothing else from the
sealed directory is read or written.

usage: python3 -I make-contracts.py FIXTURE_DIR [ORDO_BINARY] [SEALED_DIR]
"""
import hashlib, json, os, re, subprocess, sys, pathlib

root = pathlib.Path(sys.argv[1])
ordo = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
sealed = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else os.environ.get("ARCH001_SEALED", "/nonexistent"))
sha = lambda b: "sha256:" + hashlib.sha256(b).hexdigest()
hexsha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

# Justifications only restate the decision records in repo/docs/decisions or the follow-up text.
DEC = {
    "DEC-001": "a loan lasts 21 days from the day the copy is borrowed",
    "DEC-003": "0.25 per day late, at most 10.00 per loan, assessed on return",
    "DEC-004": "at most 2 renewals; not when overdue; not when any member holds the book; each renewal adds 21 days to the due date",
    "DEC-004r2": "revision 2: the renewal limit is the borrower's member type's (standard 2, student 1, staff 4); the rest of DEC-004 is unchanged",
    "DEC-005": "per-book FIFO holds queue; while a book has holds its copies are lent only to the head of the queue",
    "DEC-006": "fines are assessed only by the schedule; no member type is exempt; a waiver needs a named approver for the specific fine",
    "DEC-006r2": "revision 2 (approved by Finance): a staff member's fine is waived when assessed, by the standing approval 'DEC-006 rev 2'",
    "DEC-007": "a returned copy of a held book is set aside for the head of its queue for 7 days; an uncollected hold expires",
    "DEC-007r2": "revision 2: a freed copy passes to the next waiting hold; a hold on a book with a copy on the shelf gets it at once",
    "DEC-008": "one notice per overdue loan and due date; delivered is final; rejected is sent again; unknown is not re-sent until staff reconcile",
    "DEC-009": "shelf capacity: main 8, east 4; a copy is never added to a full branch",
}


def dec(node_id, reqs, text_key=None):
    return (node_id, "decision", reqs, [], DEC[text_key or node_id])


def standard(task, reqs, decisions, phase):
    """verification obligation per requirement (depending on its decisions) and one owner cohort."""
    tag = task if phase == "initial" else task + "F"
    nodes = list(decisions)
    for r in reqs:
        deps = [d[0] for d in decisions if r in d[2]]
        nodes.append((f"VERIFY-{tag}-{r}", "verificationObligation", [r], deps, None))
    nodes.append((f"COHORT-{tag}", "cohort", list(reqs), sorted({d[0] for d in decisions}), None))
    return nodes


CONTRACTS = {
    ("T1", "initial"): standard("T1", ["R1", "R2"], [dec("DEC-004", ["R1", "R2"])], "initial"),
    ("T1", "followup"): standard("T1", ["F1"], [dec("DEC-004", ["F1"], "DEC-004r2")], "followup"),
    ("T2", "initial"): standard("T2", ["R1", "R2", "R3"], [], "initial"),
    ("T2", "followup"): standard("T2", ["F1"], [], "followup"),
    ("T3", "initial"): standard("T3", ["R1", "R2", "R3"], [], "initial"),
    ("T3", "followup"): standard("T3", ["F1", "F2"], [dec("DEC-009", ["F1", "F2"])], "followup"),
    ("T4", "initial"): standard("T4", ["R1", "R2", "R3", "R4"], [dec("DEC-008", ["R1", "R2", "R3"])], "initial"),
    ("T4", "followup"): standard("T4", ["F1", "F2", "F3"], [dec("DEC-008", ["F2", "F3"])], "followup"),
    # REL-001 V7 shape: the decision and an unresolved conflict node are linked to the modeled requirement R3,
    # so ecir/1 refuses the contract (ORDO.CONTRACT.UNRESOLVED_CONFLICT).
    ("T5", "initial"): standard("T5", ["R1", "R2", "R3"], [dec("DEC-003", ["R1"]), dec("DEC-006", ["R1", "R2", "R3"])], "initial")
    + [("CONFLICT-T5-STAFF-WAIVER", "conflict", ["R3"], ["DEC-006"],
        "LEND-T5-R3 asks the command line to waive staff fines automatically; accepted DEC-006 allows no automatic waiver "
        "and no exempt member type; unresolved")],
    ("T5", "followup"): standard("T5", ["F1"], [dec("DEC-003", ["F1"]), dec("DEC-006", ["F1"], "DEC-006r2")], "followup"),
    ("T6", "initial"): standard("T6", ["R1", "R2", "R3", "R4"],
                                [dec("DEC-005", ["R2"]), dec("DEC-007", ["R1", "R2", "R3", "R4"])], "initial"),
    ("T6", "followup"): standard("T6", ["F1", "F2"], [dec("DEC-007", ["F1", "F2"], "DEC-007r2")], "followup"),
    ("T7", "initial"): standard("T7", ["R1", "R2", "R3"], [], "initial"),
    ("T7", "followup"): standard("T7", ["F1", "F2"], [], "followup"),
    ("T8", "initial"): standard("T8", ["R1", "R2"], [], "initial"),
    ("T8", "followup"): standard("T8", ["F1"], [], "followup"),
}

CATEGORY_NAMES = {
    1: "business logic in UI", 2: "domain depending on persistence", 3: "cross-tier dependency violations",
    4: "bypassed repository/service abstractions", 5: "duplicated domain rules", 6: "async operations",
    7: "decisions conflicting with existing constraints", 8: "works initially but makes follow-ups expensive",
    9: "integration across tiers", 10: "refactoring that preserves function but damages boundaries",
}

# Harness and scoring metadata (public; it names no oracle content).
META = json.loads((root / "tasks-meta.json").read_text())


def build(task, phase):
    tdir = root / "tasks" / task
    name = "requirement.md" if phase == "initial" else "followup.md"
    doc = f"requirements/{task}.md" if phase == "initial" else f"requirements/{task}-followup.md"
    data = (tdir / name).read_bytes()
    lines = data.decode("utf-8").split("\n")
    prefix = "R" if phase == "initial" else "F"
    reqs = {}
    for i, line in enumerate(lines):
        m = re.match(r"^## (LEND-%s-(%s\d+))$" % (task, prefix), line)
        if m:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## ") and not lines[j].startswith("Acceptance criteria"):
                j += 1
            section = "\n".join(lines[i:j]).strip()
            reqs[m.group(2)] = {"id": m.group(1), "location": f"L{i+1}", "digest": sha(section.encode("utf-8"))}
    nodes = CONTRACTS[(task, phase)]
    used = sorted({r for n in nodes for r in n[2]})
    assert used == sorted(reqs), (task, phase, used, sorted(reqs))
    key = lambda r: f"{doc}#{reqs[r]['id']}"
    requirements = [{
        "source": {"key": key(r), "originalId": reqs[r]["id"], "document": doc, "location": reqs[r]["location"],
                   "revision": sha(data), "contentDigest": reqs[r]["digest"]},
        "disposition": {"kind": "modeled"},
        "nodeIds": [n[0] for n in nodes if r in n[2]],
    } for r in sorted(reqs, key=lambda r: int(r[1:]))]
    contract = {"schemaVersion": "ecir/1", "sourceManifestDigest": sha(data), "requirements": requirements,
                "nodes": [dict({"id": n[0], "kind": n[1], "requirementKeys": [key(r) for r in n[2]], "dependsOn": n[3]},
                               **({"justification": n[4]} if n[4] else {})) for n in nodes]}
    cname = "contract.json" if phase == "initial" else "followup-contract.json"
    cpath = tdir / cname
    cpath.write_text(json.dumps(contract, indent=2) + "\n")
    expected = not (task == "T5" and phase == "initial")
    verdict = {"path": f"tasks/{task}/{cname}", "sha256": hexsha(cpath), "expectedOrdoAdmits": expected}
    if ordo:
        proc = subprocess.run([ordo, "ecir", "check", "--blueprint", str(cpath), "--json"], capture_output=True, text=True)
        out = json.loads(proc.stdout)
        verdict.update({"ordoBinarySha256": hexsha(pathlib.Path(ordo)), "ordoAdmits": proc.returncode == 0, "ordoExit": proc.returncode,
                        "ordoContractDigest": out.get("contractDigest"),
                        "ordoDiagnostics": sorted({d.get("code") for d in out.get("diagnostics") or []} - {None})})
    else:
        verdict.update({"ordoAdmits": None, "ordoExit": None, "ordoContractDigest": None, "ordoDiagnostics": None})
    return {
        "requirementIds": [reqs[r]["id"] for r in sorted(reqs, key=lambda r: int(r[1:]))],
        "requirementKeys": [key(r) for r in sorted(reqs, key=lambda r: int(r[1:]))],
        "decisionIds": [n[0] for n in nodes if n[1] == "decision"],
        "conflictIds": [n[0] for n in nodes if n[1] == "conflict"],
        "title": lines[0].removeprefix("# "),
        "file": {"source": f"tasks/{task}/{name}", "target": doc, "sha256": hashlib.sha256(data).hexdigest()},
        "contract": verdict,
    }


for task in sorted({t for t, _ in CONTRACTS}):
    tdir = root / "tasks" / task
    meta = META[task]
    initial, followup = build(task, "initial"), build(task, "followup")
    visible = sorted((tdir / "acceptance").glob("*.fs"))
    fvisible = sorted((tdir / "followup-acceptance").glob("*.fs"))

    def oracle(kind):
        p = sealed / "oracle" / task / f"{kind}OracleTests.fs"
        return {"path": f"sealed:oracle/{task}/{kind}OracleTests.fs", "sha256": hexsha(p) if p.exists() else None}

    probes = sealed / "oracle" / task / "probes.json"
    task_json = {
        "schema": "arch001.task/1",
        "id": task,
        "workItem": f"LEND-{task}",
        "title": initial["title"],
        "categories": meta["categories"],
        "categoryNames": [CATEGORY_NAMES[c] for c in meta["categories"]],
        "control": meta["categories"] == [],
        "initial": {k: initial[k] for k in ("requirementIds", "requirementKeys", "decisionIds", "conflictIds")},
        "followup": {"title": followup["title"], **{k: followup[k] for k in ("requirementIds", "requirementKeys", "decisionIds", "conflictIds")}},
        "conflict": bool(initial["conflictIds"]),
        "expectedOutcome": meta["expectedOutcome"],
        "expectedPlacement": meta["expectedPlacement"],
        "trap": meta["trap"],
        "scoringNotes": meta["scoringNotes"],
        "files": {
            "requirement": initial["file"],
            "visibleTests": [{"source": f"tasks/{task}/acceptance/{p.name}", "target": f"tests/Lending.Tests/Acceptance/{p.name}",
                              "sha256": hexsha(p)} for p in visible],
            "followup": followup["file"],
            "followupVisibleTests": [{"source": f"tasks/{task}/followup-acceptance/{p.name}",
                                      "target": f"tests/Lending.Tests/Acceptance/{p.name}", "sha256": hexsha(p)} for p in fvisible],
            "oracle": {"initial": oracle("Initial"), "followup": oracle("Followup")},
            "probes": {"path": f"sealed:oracle/{task}/probes.json", "sha256": hexsha(probes) if probes.exists() else None},
            "reference": {k: f"sealed:reference/{task}/{k}" for k in meta["referenceVariants"]},
        },
        "contract": initial["contract"],
        "followupContract": followup["contract"],
    }
    (tdir / "task.json").write_text(json.dumps(task_json, indent=2) + "\n")
    print(task, "initial", initial["contract"]["sha256"][:12], "admits", initial["contract"]["ordoAdmits"],
          "| followup", followup["contract"]["sha256"][:12], "admits", followup["contract"]["ordoAdmits"])
