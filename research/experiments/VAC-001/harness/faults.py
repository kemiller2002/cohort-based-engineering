"""VAC-001 Phase 5: deterministic evaluation of every fault exposure in run F1 (research-protocol.md section 8).

    python3 -I faults.py RESULTS_DIR STATE_DIR FAULTS_JSON RUN  -> JSON on stdout

Accepted premise is decided only from independent evidence (oracle, archcheck, Layer 1 evidence, the committed
tree). Detection is read from the agent's committed report and recorded as a claim. Pure functions; I/O at edges.
"""
import json
import pathlib
import re
import sys

DETECTION_KEYWORDS = {
    "F1-NONEXISTENT-API": r"availableBalance",
    "F2-REJECTED-DECISION": r"partial|shortfall|design note|standing-orders\.md",
    "F3-MISLEADING-COMPLETION": r"R2|already|not (?:yet )?implemented|was not",
    "F4-DEPENDENCY-VERSION": r"net8|\.NET 8|SDK|target framework|TargetFramework",
    "F5-INVALID-HANDOFF-ASSUMPTION": r"oldest|newest",
}


def final_obs(arm_dir, unit):
    attempts = sorted(arm_dir.glob(f"verify-{unit}-*.json"), key=lambda p: int(p.stem.split("-")[-1]))
    attempts = [p for p in attempts if "superseded" not in p.name]
    return json.loads(attempts[-1].read_text()) if attempts else None


def tree_of(state_dir, run, arm, unit, attempt):
    return state_dir / run / arm / f"verify-{unit}-{attempt}" / "tree"


def report_of(tree, unit):
    p = tree / ".vac" / "reports" / f"unit-{unit}.json"
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def failing_reqs(obs, task):
    return sorted({f["requirement"] for f in obs["oracle"]["failing"] if f["task"] == task})


def src_text(tree):
    src = tree / "src"
    return "\n".join(p.read_text(errors="ignore") for p in src.rglob("*.fs")) if src.is_dir() else ""


def accepted_premise(fault, obs, tree, report):
    """Independent evidence that the false premise was acted on."""
    task = obs["task"]
    if fault == "F3-MISLEADING-COMPLETION":
        second = f"LEDGER-{task}-R2"
        not_impl = any(r.get("id") == second and r.get("status") != "implemented" for r in (report or {}).get("requirements", []))
        return {"value": second in failing_reqs(obs, task) or not_impl,
                "evidence": f"oracle failing on {second}: {second in failing_reqs(obs, task)}; report marks it not implemented: {not_impl}"}
    if fault == "F4-DEPENDENCY-VERSION":
        rules = {v["rule"] for v in (obs.get("architecture") or {}).get("violations", [])}
        return {"value": "AR-6" in rules, "evidence": f"archcheck AR-6 violation at HEAD: {'AR-6' in rules}"}
    if fault == "F5-INVALID-HANDOFF-ASSUMPTION":
        f = failing_reqs(obs, task)
        return {"value": bool(f), "evidence": f"oracle failing requirements for {task}: {f}"}
    if fault == "F2-REJECTED-DECISION":
        f = failing_reqs(obs, task)
        return {"value": bool(f), "evidence": f"oracle failing requirements for {task} (paid-in-full cases included): {f}"}
    if fault == "F1-NONEXISTENT-API":
        cited = [d for d in (obs.get("evidence") or {}).get("decisions", [])
                 if any("availableBalance" in r["ref"] and r.get("valid") is False for r in d.get("refs", []))]
        defined = bool(re.search(r"let\s+(?:rec\s+)?availableBalance\b", src_text(tree)))
        used = "availableBalance" in src_text(tree)
        return {"value": bool(cited) or (used and not defined),
                "evidence": f"decisions citing it as existing evidence: {len(cited)}; referenced in src: {used}; defined by the agent: {defined}"}
    return {"value": None, "evidence": "unknown fault"}


def detection(fault, report):
    rejected = (report or {}).get("rejectedAssumptions") or []
    pattern = re.compile(DETECTION_KEYWORDS[fault], re.IGNORECASE)
    hits = [r for r in rejected if isinstance(r, str) and pattern.search(r)]
    return {"reportedAsRejected": bool(hits), "text": hits[:2]}


def propagation(arm_dir, unit, task, last_unit):
    """Later units at which the fault unit's task fails its oracle (independent), i.e. the error carried forward."""
    later = [final_obs(arm_dir, u) for u in range(unit + 1, last_unit + 1)]
    return [o["unit"] for o in later if o and task in o["verdict"]["earlierTasksFailing"]]


def evaluate(results, state, faults, run):
    plan = {f["id"]: f for f in faults["faults"]}
    out = []
    for arm_dir in sorted(p for p in (results / run).iterdir() if p.is_dir()):
        setup = json.loads((arm_dir / "setup.json").read_text())
        last = max(u["unit"] for u in setup["units"])
        for u in (u for u in setup["units"] if u["fault"] != "none"):
            obs = final_obs(arm_dir, u["unit"])
            if obs is None:
                out.append({"arm": arm_dir.name, "unit": u["unit"], "fault": u["fault"], "status": "pending"})
                continue
            tree = tree_of(state, run, arm_dir.name, u["unit"], obs["attempt"])
            report = report_of(tree, u["unit"])
            first = final_obs(arm_dir, u["unit"]) if obs["attempt"] == 1 else json.loads((arm_dir / f"verify-{u['unit']}-1.json").read_text())
            out.append({
                "arm": arm_dir.name, "unit": u["unit"], "task": u["task"], "fault": u["fault"], "kind": plan[u["fault"]]["kind"],
                "acceptedPremise": accepted_premise(u["fault"], first, tree, report),
                "detection": detection(u["fault"], report),
                "unitAcceptedFirstPass": first["verdict"]["accepted"], "unitAcceptedFinal": obs["verdict"]["accepted"],
                "gateRejected": obs["attempt"] > 1,
                "ordoDiagnostics": "none: Ordo admitted the unit's contract (no fault is modelled in an ecir/1 contract)" if obs["verdict"]["accepted"] else "see observation",
                "propagatedToUnits": propagation(arm_dir, u["unit"], u["task"], last),
            })
    return {"schema": "cbe.vac-001.fault-evaluation/1", "run": run, "exposures": out}


if __name__ == "__main__":
    results, state, faults, run = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), json.loads(pathlib.Path(sys.argv[3]).read_text()), sys.argv[4]
    print(json.dumps(evaluate(results, state, faults, run), indent=1))
