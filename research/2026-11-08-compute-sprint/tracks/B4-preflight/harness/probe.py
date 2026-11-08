"""POST HOC generality probe (SPR-B4-01 deviation D2): semantics-preserving or defect-preserving rewrites of the R8
package, run through both percepta spec-preflight and a scratch copy of B3's checks.

Each probe keeps the R8 defect present (a real reader would still see it) and changes only wording or structure.
Usage: python3 -I probe.py --exe PERCEPTA --b3 /home/user/sprint-scratch/B4/b3-copy/checks --out RAW/probe.json
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

CLONE = "/home/user/sprint-scratch/B2/indy-init-full"
BASE = "/home/user/sprint-scratch/B4/inputs/R8-frozen"
WORK = "/home/user/sprint-scratch/B4/probe"
R8 = "1cb27ec"
PKG = "requirements-compiled/v4.1.1"

INV04_OLD = "under total network failure at most four mutations and four reconciliation reads in 60 seconds"


def sub(text, old, new):
    if old not in text:
        raise ValueError(f"probe anchor not found: {old[:60]!r}")
    return text.replace(old, new)


def edit_machines(fn):
    def apply(files):
        doc = json.loads(files["machines"])
        fn(doc)
        return dict(files, machines=json.dumps(doc))
    return apply


def sm_save(doc):
    return next(m for m in doc["machines"] if m["id"] == "SM-SAVE")


def pair(m, state, event):
    return next(p for p in m["pairs"] if p["state"] == state and p["event"] == event)


def two_cycle(doc):
    """T-S31 and T-S32 now pass through a 'Reading' state and come back on ReadDone: a 2-cycle, same reads."""
    m = sm_save(doc)
    for ev in ("CheckAgain", "WentOnline"):
        for t in pair(m, "UnknownOutcome", ev)["transitions"]:
            t["next"] = "Reading"
    m["pairs"].append({"state": "Reading", "event": "ReadDone", "outcome": "legal",
                       "transitions": [{"id": "T-PROBE-1", "guard": "true", "next": "UnknownOutcome",
                                        "effects": ["show the outcome is still unknown"]}]})


def effect_synonym(doc):
    m = sm_save(doc)
    for ev in ("CheckAgain", "WentOnline"):
        for t in pair(m, "UnknownOutcome", ev)["transitions"]:
            t["effects"] = ["query the server once more for the save's outcome"]


def text_edit(key, old, new):
    return lambda files: dict(files, **{key: sub(files[key], old, new)})


def both_types(old, new):
    """Apply a type edit to the interface JSON domain stubs (percepta) and the .fs stubs (B3)."""
    def apply(files):
        doc = json.loads(files["interfaces"])
        doc["domainStubs"]["fsharp"] = sub(doc["domainStubs"]["fsharp"], old, new)
        fs = dict(files["fs"])
        fs["00-DOMAIN-STUBS.fs"] = sub(fs["00-DOMAIN-STUBS.fs"], old, new)
        return dict(files, interfaces=json.dumps(doc), fs=fs)
    return apply


def rename_everywhere(old, new):
    def apply(files):
        return dict(files, interfaces=files["interfaces"].replace(old, new), catalog=files["catalog"].replace(old, new),
                    fs={k: v.replace(old, new) for k, v in files["fs"].items()})
    return apply


ENVELOPE = "type CommandEnvelope = { CommandId: Guid; Investigation: InvestigationId; ExpectedVersion: AggregateVersion option }"

PROBES = (
    ("P0-identity", "unchanged R8 inputs (sanity)", lambda f: f),
    ("P1-bound-reworded", "INV-04 window clause says 'no more than four ... in any 60-second window'",
     text_edit("invariants", INV04_OLD, "under total network failure no more than four mutations and four reconciliation reads in any 60-second window")),
    ("P2-bound-per-minute", "INV-04 window clause says 'at most ... per minute' (inside percepta's documented form)",
     text_edit("invariants", INV04_OLD, "under total network failure at most four mutations and four reconciliation reads per minute")),
    ("P3-two-cycle", "T-S31/T-S32 loop through an intermediate Reading state (2-cycle) instead of a self-loop", edit_machines(two_cycle)),
    ("P4-effect-synonym", "T-S31/T-S32 effect says 'query the server once more for the save's outcome'", edit_machines(effect_synonym)),
    ("P5-carrier-string-tag", "CommandEnvelope gains an irrelevant `CorrelationTag: string` (still no command body)",
     both_types(ENVELOPE, ENVELOPE.replace(" }", "; CorrelationTag: string }"))),
    ("P6-catalog-reworded", "catalog says 'Every command travels in CommandEnvelope' instead of 'is carried inside'",
     text_edit("catalog", "Every command is carried inside CommandEnvelope", "Every command travels in CommandEnvelope")),
    ("P7-carrier-renamed", "CommandEnvelope renamed RequestEnvelope everywhere (stubs, interfaces, catalog)",
     rename_everywhere("CommandEnvelope", "RequestEnvelope")),
)


def base_files():
    names = {"machines": "state-machine-contracts.json", "invariants": "invariants.json",
             "interfaces": "interface-specifications.json", "catalog": "COMMAND-EVENT-CATALOG.md"}
    files = {k: open(os.path.join(BASE, v), encoding="utf-8").read() for k, v in names.items()}
    listing = subprocess.run(["git", "-C", CLONE, "ls-tree", "-r", "--name-only", R8, PKG + "/contracts"],
                             check=True, capture_output=True, text=True).stdout.split()
    files["fs"] = {p.rsplit("/", 1)[-1]: subprocess.run(["git", "-C", CLONE, "show", f"{R8}:{p}"], check=True,
                                                         capture_output=True, text=True).stdout
                   for p in listing if p.endswith(".fs") and "/negative/" not in p}
    return files


def run_percepta(exe, d, files):
    paths = {}
    for k, name in (("machines", "m.json"), ("invariants", "i.json"), ("interfaces", "f.json"), ("catalog", "c.md")):
        paths[k] = os.path.join(d, name)
        with open(paths[k], "w", encoding="utf-8") as fh:
            fh.write(files[k])
    out = os.path.join(d, "report.json")
    cmd = [exe, "spec-preflight"] + [a for k in ("machines", "invariants", "interfaces", "catalog") for a in (f"--{k}", paths[k])] + ["--out", out]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, json.load(open(out, encoding="utf-8"))


def run_b3(b3dir, files):
    sys.path.insert(0, b3dir)
    from semcheck import carrier, model, partition, rate  # noqa: E402
    machines = model.load_machines(json.loads(files["machines"]))
    bounds = model.load_bounds(json.loads(files["invariants"]))
    defs = ()
    for name in sorted(files["fs"]):
        defs += carrier.parse_types(files["fs"][name], name)
    return {"C1-loop": rate.check(machines, bounds, ("loop", False)),
            "C1-cycle": rate.check(machines, bounds, ("cycle", False)),
            "C2": carrier.check(defs, "command", "C2")[0],
            "C3": partition.check(machines)}


def b3_inv04(alarms, clause_only):
    """B3's preregistered criterion: an alarm on INV-04 x SM-SAVE x (T-S31|T-S32); optionally only when the alarm is
    attributed to the 'four reconciliation reads' (network-failure) clause rather than the per-request 'three automatic'."""
    return any(a.get("invariant") == "INV-04" and a.get("machine") == "SM-SAVE" and a.get("transition") in ("T-S31", "T-S32")
               and (not clause_only or a.get("bound", "").startswith("at most 4 reconciliation reads")) for a in alarms)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--b3", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import classify  # noqa: E402
    base = base_files()
    shutil.rmtree(WORK, ignore_errors=True)
    results = []
    for pid, desc, mutate in PROBES:
        d = os.path.join(WORK, pid)
        os.makedirs(d)
        files = mutate(base)
        code, report = run_percepta(a.exe, d, files)
        c = classify.classify(report)
        b3 = run_b3(a.b3, files)
        results.append({
            "probe": pid, "description": desc, "perceptaExit": code,
            "percepta": dict({k: v["caught"] for k, v in c["defects"].items() if k != "CAUSA-T18-T20"},
                             **{"R8-CMDBODY (any carrier name)": any(
                                 f.get("rule") == "carrier-cannot-discriminate" and f.get("blocking") is True
                                 and f.get("subjects", [""])[0].endswith("Envelope") for f in classify.findings(report))}),
            "perceptaFindings": [classify.label(f) for f in classify.findings(report)],
            "b3": {"R8-INV04 (C1-loop, B3 criterion)": b3_inv04(b3["C1-loop"], False),
                   "R8-INV04 (C1-loop, against the 4-reads clause)": b3_inv04(b3["C1-loop"], True),
                   "R8-INV04 (C1-cycle, B3 criterion)": b3_inv04(b3["C1-cycle"], False),
                   "R8-CMDBODY (C2)": any("Envelope" in (x.get("type") or "") or "Envelope" in x.get("candidate", "") for x in b3["C2"]),
                   "DEV-R8-12 (C3)": any(x.get("event") == "ReconcileReadFailed" for x in b3["C3"])},
            "b3Counts": {k: len(v) for k, v in b3.items()},
        })
        print(pid, results[-1]["perceptaExit"], results[-1]["percepta"], results[-1]["b3"], file=sys.stderr)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
