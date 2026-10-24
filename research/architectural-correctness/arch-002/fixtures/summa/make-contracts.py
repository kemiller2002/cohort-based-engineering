#!/usr/bin/env python3
"""Generate ARCH-002 F2 (summa) tasks/T<n>/{contract.json, followup-contract.json, task.json}.

Adapted from ARCH-001 fixtures/make-contracts.py (same construction, after REL-001 run-03): the source
revision is the sha256 of the requirement file bytes, and each requirement's contentDigest is the sha256 of
its `## SUMMA-...` section text. Initial requirements live at requirements/T<n>.md, follow-up requirements at
requirements/T<n>-followup.md (the targets the harness copies them to). When an Ordo binary is given,
task.json records the verdict of `ordo ecir check --blueprint ... --json` for both contracts. When the sealed
directory is given (or ARCH002_SEALED points at it), task.json records the sha256 of the sealed oracle files
and the private fields go to the sealed task-private/<task>.json.

Changes from ARCH-001: requirement ids are SUMMA-T<n>-R/F<k>; decisions are Summa's DF-SUMMA records under
repo/research/decisions; no task carries a conflict (every contract is expected to be admitted); visible tests
target tests/Summa.Acceptance.Tests/Acceptance/; the schema ids are arch002.*.

usage: python3 -I make-contracts.py FIXTURE_DIR [ORDO_BINARY] [SEALED_DIR]
"""
import hashlib, json, os, re, subprocess, sys, pathlib

root = pathlib.Path(sys.argv[1])
ordo = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
sealed = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else os.environ.get("ARCH002_SEALED", "/nonexistent"))
sha = lambda b: "sha256:" + hashlib.sha256(b).hexdigest()
hexsha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

# Justifications only restate the decision records in repo/research/decisions.
DEC = {
    "DF-SUMMA-2026-0009": "local books are a browser snapshot of the manifest and every record as canonical text; reading them back runs every record and invariant check, and books that fail are refused, never used",
    "DF-SUMMA-2026-0020": "every export describes itself: kind, export schema, when it was generated (UTC), the accounting period, the books' data version and the filters",
    "DF-SUMMA-2026-0028": "Payments.settlement lists every event that settled or unsettled an invoice in date order, each with its effect and what was owed after; the last balance is the outstanding amount",
    "DF-SUMMA-2026-0041": "financial exports are sensitive files: each says it is confidential financial data, the download is its only effect, and on books on GitHub it needs the ExportData capability",
}


def dec(node_id, reqs):
    return (node_id, "decision", reqs, [], DEC[node_id])


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
    ("T1", "initial"): standard("T1", ["R1", "R2", "R3"], [dec("DF-SUMMA-2026-0028", ["R1"]), dec("DF-SUMMA-2026-0041", ["R2", "R3"])], "initial"),
    ("T1", "followup"): standard("T1", ["F1", "F2"], [dec("DF-SUMMA-2026-0020", ["F2"]), dec("DF-SUMMA-2026-0041", ["F2"])], "followup"),
    ("T2", "initial"): standard("T2", ["R1", "R2", "R3"], [dec("DF-SUMMA-2026-0009", ["R2", "R3"]), dec("DF-SUMMA-2026-0041", ["R1", "R3"])], "initial"),
    ("T2", "followup"): standard("T2", ["F1", "F2"], [dec("DF-SUMMA-2026-0009", ["F1", "F2"])], "followup"),
    ("T3", "initial"): standard("T3", ["R1", "R2", "R3"], [], "initial"),
    ("T3", "followup"): standard("T3", ["F1", "F2"], [], "followup"),
}

CATEGORY_NAMES = {
    1: "business logic in UI", 2: "domain depending on persistence", 3: "cross-tier dependency violations",
    4: "bypassed repository/service abstractions", 5: "duplicated domain rules", 6: "async operations",
    7: "decisions conflicting with existing constraints", 8: "works initially but makes follow-ups expensive",
    9: "integration across tiers", 10: "refactoring that preserves function but damages boundaries",
}

# Trap descriptions and expected placements are hidden scoring data: the source lives in the sealed store
# (tasks-meta.json); task.json carries only the public fields.
META = json.loads((sealed / "tasks-meta.json").read_text()) if (sealed / "tasks-meta.json").exists() else None
PRIVATE_FIELDS = ("trap", "expectedPlacement", "expectedOutcome", "scoringNotes", "referenceVariants")
PUBLIC = json.loads((root / "tasks-public.json").read_text())


def build(task, phase):
    tdir = root / "tasks" / task
    name = "requirement.md" if phase == "initial" else "followup.md"
    doc = f"requirements/{task}.md" if phase == "initial" else f"requirements/{task}-followup.md"
    data = (tdir / name).read_bytes()
    lines = data.decode("utf-8").split("\n")
    prefix = "R" if phase == "initial" else "F"
    reqs = {}
    for i, line in enumerate(lines):
        m = re.match(r"^## (SUMMA-%s-(%s\d+))$" % (task, prefix), line)
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
    order = lambda r: int(r[1:])
    requirements = [{
        "source": {"key": key(r), "originalId": reqs[r]["id"], "document": doc, "location": reqs[r]["location"],
                   "revision": sha(data), "contentDigest": reqs[r]["digest"]},
        "disposition": {"kind": "modeled"},
        "nodeIds": [n[0] for n in nodes if r in n[2]],
    } for r in sorted(reqs, key=order)]
    contract = {"schemaVersion": "ecir/1", "sourceManifestDigest": sha(data), "requirements": requirements,
                "nodes": [dict({"id": n[0], "kind": n[1], "requirementKeys": [key(r) for r in n[2]], "dependsOn": n[3]},
                               **({"justification": n[4]} if n[4] else {})) for n in nodes]}
    cname = "contract.json" if phase == "initial" else "followup-contract.json"
    cpath = tdir / cname
    cpath.write_text(json.dumps(contract, indent=2) + "\n")
    verdict = {"path": f"tasks/{task}/{cname}", "sha256": hexsha(cpath), "expectedOrdoAdmits": True}
    if ordo:
        proc = subprocess.run([ordo, "ecir", "check", "--blueprint", str(cpath), "--json"], capture_output=True, text=True)
        out = json.loads(proc.stdout)
        verdict.update({"ordoBinarySha256": hexsha(pathlib.Path(ordo)), "ordoAdmits": proc.returncode == 0, "ordoExit": proc.returncode,
                        "ordoContractDigest": out.get("contractDigest"),
                        "ordoDiagnostics": sorted({d.get("code") for d in out.get("diagnostics") or []} - {None})})
    else:
        verdict.update({"ordoAdmits": None, "ordoExit": None, "ordoContractDigest": None, "ordoDiagnostics": None})
    return {
        "requirementIds": [reqs[r]["id"] for r in sorted(reqs, key=order)],
        "requirementKeys": [key(r) for r in sorted(reqs, key=order)],
        "decisionIds": [n[0] for n in nodes if n[1] == "decision"],
        "conflictIds": [n[0] for n in nodes if n[1] == "conflict"],
        "title": lines[0].removeprefix("# "),
        "file": {"source": f"tasks/{task}/{name}", "target": doc, "sha256": hashlib.sha256(data).hexdigest()},
        "contract": verdict,
    }


TARGET = "tests/Summa.Acceptance.Tests/Acceptance"
for task in sorted({t for t, _ in CONTRACTS}):
    tdir = root / "tasks" / task
    pub = PUBLIC[task]
    initial, followup = build(task, "initial"), build(task, "followup")
    visible = sorted((tdir / "acceptance").glob("*.fs"))
    fvisible = sorted((tdir / "followup-acceptance").glob("*.fs"))

    def sealed_file(rel):
        p = sealed / rel
        return {"path": f"sealed:{rel}", "sha256": hexsha(p) if p.exists() else None}

    task_json = {
        "schema": "arch002.task/1",
        "fixture": "summa",
        "id": task,
        "workItem": f"SUMMA-{task}",
        "title": initial["title"],
        "categories": pub["categories"],
        "categoryNames": [CATEGORY_NAMES[c] for c in pub["categories"]],
        "control": pub["categories"] == [],
        "initial": {k: initial[k] for k in ("requirementIds", "requirementKeys", "decisionIds", "conflictIds")},
        "followup": {"title": followup["title"], **{k: followup[k] for k in ("requirementIds", "requirementKeys", "decisionIds", "conflictIds")}},
        "conflict": bool(initial["conflictIds"]),
        "files": {
            "requirement": initial["file"],
            "visibleTests": [{"source": f"tasks/{task}/acceptance/{p.name}", "target": f"{TARGET}/{p.name}", "sha256": hexsha(p)} for p in visible],
            "followup": followup["file"],
            "followupVisibleTests": [{"source": f"tasks/{task}/followup-acceptance/{p.name}", "target": f"{TARGET}/{p.name}", "sha256": hexsha(p)}
                                     for p in fvisible],
            "oracle": {"initial": sealed_file(f"oracle/{task}/InitialOracleTests.fs"),
                       "followup": sealed_file(f"oracle/{task}/FollowupOracleTests.fs"),
                       "manifest": sealed_file(f"oracle/{task}/oracle.json")},
            "probes": sealed_file(f"oracle/{task}/probes.json"),
            "baseline": sealed_file("baseline/start.report.json"),
            # Only the variants every task has; whether a task also has a trap is private (task-private).
            "reference": {k: f"sealed:reference/{task}/{k}" for k in ("good", "followup-good")},
        },
        "contract": initial["contract"],
        "followupContract": followup["contract"],
        "crossTierCount": pub["crossTierCount"],
        "privateMetadata": f"sealed:task-private/{task}.json",
    }
    (tdir / "task.json").write_text(json.dumps(task_json, indent=2) + "\n")
    if META is not None:
        meta = META[task]
        assert meta["categories"] == pub["categories"], task
        assert len({p["tier"] for p in meta["expectedPlacement"]}) == pub["crossTierCount"], task
        private = {"id": task, **{k: meta[k] for k in PRIVATE_FIELDS}}
        (sealed / "task-private").mkdir(exist_ok=True)
        (sealed / "task-private" / f"{task}.json").write_text(json.dumps(private, indent=2) + "\n")
    print(task, "initial", initial["contract"]["sha256"][:12], "admits", initial["contract"]["ordoAdmits"],
          "| followup", followup["contract"]["sha256"][:12], "admits", followup["contract"]["ordoAdmits"])
