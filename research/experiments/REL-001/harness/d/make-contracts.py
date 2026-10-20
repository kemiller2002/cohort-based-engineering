#!/usr/bin/env python3
"""Generate fixtures/d/tasks/Tn/contract.json (ecir/1) from requirement.md.

Deterministic: source revision/contentDigest are sha256 of the requirement
file bytes / the requirement section text. usage: python3 -I make-contracts.py FIXTURE_DIR
"""
import hashlib, json, re, sys, pathlib

root = pathlib.Path(sys.argv[1])
sha = lambda b: "sha256:" + hashlib.sha256(b).hexdigest()

NODES = {
    "T1": [
        ("DEC-T1-AMOUNT-GUARD", "decision", ["R1"], [], "amount validation precedes account and funds checks"),
        ("VERIFY-T1-R1", "verificationObligation", ["R1"], ["DEC-T1-AMOUNT-GUARD"], None),
        ("COHORT-T1", "cohort", ["R1"], ["DEC-T1-AMOUNT-GUARD"], None),
    ],
    "T2": [
        ("DEC-T2-ERROR-ORDER", "decision", ["R2"], [], "refusal order: amount, source, destination, same account, funds"),
        ("INV-T2-CONSERVATION", "invariant", ["R3"], [], "sum of balances unchanged by any transfer"),
        ("VERIFY-T2-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-T2-R2", "verificationObligation", ["R2"], ["DEC-T2-ERROR-ORDER"], None),
        ("VERIFY-T2-R3", "verificationObligation", ["R3"], ["INV-T2-CONSERVATION"], None),
        ("COHORT-T2", "cohort", ["R1", "R2", "R3"], ["DEC-T2-ERROR-ORDER", "INV-T2-CONSERVATION"], None),
    ],
    "T3": [
        ("DEC-T3-IDEMPOTENCY-KEY", "decision", ["R2"], [], "idempotency keyed by period id with the first summary kept in ledger state"),
        ("VERIFY-T3-R1", "verificationObligation", ["R1"], [], None),
        ("VERIFY-T3-R2", "verificationObligation", ["R2"], ["DEC-T3-IDEMPOTENCY-KEY"], None),
        ("COHORT-T3", "cohort", ["R1", "R2"], ["DEC-T3-IDEMPOTENCY-KEY"], None),
    ],
}

for task, nodes in NODES.items():
    path = root / "tasks" / task / "requirement.md"
    data = path.read_bytes()
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
    requirements = []
    for r in sorted(reqs):
        requirements.append({
            "source": {"key": key(r), "originalId": reqs[r]["id"], "document": doc, "location": reqs[r]["location"],
                       "revision": sha(data), "contentDigest": reqs[r]["digest"]},
            "disposition": {"kind": "modeled"},
            "nodeIds": [n[0] for n in nodes if r in n[2]],
        })
    out = {"schemaVersion": "ecir/1", "sourceManifestDigest": sha(data), "requirements": requirements,
           "nodes": [dict({"id": n[0], "kind": n[1], "requirementKeys": [key(r) for r in n[2]], "dependsOn": n[3]},
                          **({"justification": n[4]} if n[4] else {})) for n in nodes]}
    (root / "tasks" / task / "contract.json").write_text(json.dumps(out, indent=2) + "\n")
    print(task, len(requirements), "requirements")
