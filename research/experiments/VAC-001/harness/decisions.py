"""VAC-001 Layer 2 decision dataset and Layer 3 blinded review bundle (research-protocol.md section 7).

    python3 -I decisions.py dataset RESULTS_DIR RUN [RUN...]            -> RESULTS_DIR/decision-dataset.jsonl
    python3 -I decisions.py blind RESULTS_DIR STATE_DIR OUT_DIR SEED      -> OUT_DIR/{items.jsonl, trees/<key>/}
                                                                           and STATE_DIR/blind-mapping.json (never shown to reviewers)
Pure transformations over committed observations; I/O only at the edges.
"""
import hashlib
import json
import pathlib
import random
import shutil
import sys

ARCH_HINTS = ("Domain.fs", "LedgerState", "Store", "RULES.md", "AR-", "DEC-BASE")


def observations(results, run):
    for arm_dir in sorted(p for p in (results / run).iterdir() if p.is_dir()):
        finals = {}
        for f in sorted(arm_dir.glob("verify-*-*.json")):
            if "superseded" in f.name:
                continue
            o = json.loads(f.read_text())
            if o["unit"] not in finals or o["attempt"] > finals[o["unit"]]["attempt"]:
                finals[o["unit"]] = o
        yield from (finals[u] for u in sorted(finals))


def rows(obs):
    failing_reqs = {f["requirement"] for f in obs["oracle"]["failing"]}
    for d in (obs.get("evidence") or {}).get("decisions", []):
        refs = d.get("refs", [])
        req_ids = d.get("requirementIds") or []
        yield {
            "run": obs["run"], "arm": obs["arm"], "unit": obs["unit"], "task": obs["task"], "fault": obs["fault"],
            "attempt": obs["attempt"], "decisionId": d.get("id"), "statement": d.get("statement"),
            "basis": d.get("basis"), "evidence": [r["ref"] for r in refs],
            "layer1": d.get("layer1"), "invalidRefs": [r["ref"] for r in refs if r.get("valid") is False],
            "unknownRequirementIds": d.get("unknownRequirementIds", []),
            "architecturalApplicability": any(h in json.dumps(d) for h in ARCH_HINTS),
            "outcome": {"unitAccepted": obs["verdict"]["accepted"],
                        "requirementFailing": sorted(failing_reqs & set(req_ids) | {r for r in failing_reqs if any(r.startswith(q) for q in req_ids)})},
            "layer3": None,
        }


def key(row, seed):
    return "K" + hashlib.sha256(f"{seed}|{row['run']}|{row['arm']}|{row['unit']}|{row['decisionId']}".encode()).hexdigest()[:10]


def dataset(results, runs):
    return [r for run in runs for o in observations(results, run) for r in rows(o)]


def sample(data, seed):
    """Every Layer 1 invalid / no-evidence decision, every fault-unit decision, plus a seeded 25% of the rest."""
    rnd = random.Random(seed)
    must = [r for r in data if r["layer1"] in ("invalid-evidence", "no-evidence") or r["fault"] != "none"]
    rest = [r for r in data if r not in must]
    return must + [r for r in rest if rnd.random() < 0.25]


def blind(results, state, out, seed):
    data = [json.loads(l) for l in (results / "decision-dataset.jsonl").read_text().splitlines()]
    chosen = sorted(sample(data, seed), key=lambda r: key(r, seed))
    trees = {}
    for r in chosen:
        unit_key = "T" + hashlib.sha256(f"{seed}|{r['run']}|{r['arm']}|{r['unit']}".encode()).hexdigest()[:8]
        src = state / r["run"] / r["arm"] / f"verify-{r['unit']}-{r['attempt']}" / "tree"
        if unit_key not in trees and src.is_dir():
            shutil.copytree(src, out / "trees" / unit_key, ignore=shutil.ignore_patterns(".ros", ".praxis", ".echelon", "bin", "obj"))
        trees[unit_key] = str(src)
        r["_blind"] = {"key": key(r, seed), "tree": unit_key}
    items = [{"key": r["_blind"]["key"], "tree": f"trees/{r['_blind']['tree']}", "task": r["task"],
              "requirement": f"trees/{r['_blind']['tree']}/requirements/{r['task']}.md",
              "statement": r["statement"], "basis": r["basis"], "evidence": r["evidence"]} for r in chosen]
    (out / "items.jsonl").write_text("".join(json.dumps(i) + "\n" for i in items))
    mapping = {r["_blind"]["key"]: {k: r[k] for k in ("run", "arm", "unit", "decisionId", "layer1", "fault")} for r in chosen}
    (state / "blind-mapping.json").write_text(json.dumps({"seed": seed, "items": mapping, "trees": trees}, indent=1))
    return len(items), len(trees)


if __name__ == "__main__":
    cmd, results = sys.argv[1], pathlib.Path(sys.argv[2])
    if cmd == "dataset":
        data = dataset(results, sys.argv[3:])
        (results / "decision-dataset.jsonl").write_text("".join(json.dumps(r) + "\n" for r in data))
        print(len(data))
    elif cmd == "blind":
        state, out, seed = pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4]), int(sys.argv[5])
        out.mkdir(parents=True, exist_ok=True)
        print(*blind(results, state, out, seed))
