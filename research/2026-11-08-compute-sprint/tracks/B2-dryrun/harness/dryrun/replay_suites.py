"""R8-MSB1008 and R9-MSB1008 (D2): execute the frozen plan's suite command lines on the T0 bootstrap tree.

The bootstrap tree (Conditor + package output, test stubs, no application code) stands in for the throwaway repository.
dotnet commands run in list mode (--list-tests) with the pinned SDK 10.0.402; playwright commands with --list (no
browsers needed); @playwright/test 1.63.0 (the bootstrap's pin) is linked in from a scratch install. Runs are serial."""
import os
import re

from . import checks as c
from . import core

PW = core.SCRATCH / "pw" / "node_modules" / "@playwright"

CASES = {
    "R8-MSB1008": {"rehearsal": "R8", "t0": "2026-11-01T17:31:24Z", "event": "B-E-092",
                   "blocker": "live suites never ran (MSB1008) until CI fix at T+94",
                   "indy": "1cb27ec", "package": "v4.1.1",
                   "repo": "/home/user/ext/full/indy-init-rehearsal-008", "bootstrap": "616ec62"},
    "R9-MSB1008": {"rehearsal": "R9", "t0": "2026-11-04T00:30:01Z", "event": "B-E-106",
                   "blocker": "frozen v4.1.2 suite commands fail on pinned SDK (MSB1008) and name an undefined webkit project",
                   "indy": "bc3c381", "package": "v4.1.2",
                   "repo": "/home/user/indy-init-rehearsal-009", "bootstrap": "8001e7c"},
}
FIXED = {"indy": "89f5840", "package": "v4.1.5", "repo": "/home/user/indy-init-rehearsal-010", "bootstrap": "314cc8c"}


def _executable(suite):
    r = suite.get("runner", "")
    return r.startswith("dotnet test") or r.startswith("npx playwright test")


def run_plan(indy_rev, package, repo, bootstrap, label):
    plan = core.show_json(core.INDY_FULL, indy_rev, f"requirements-compiled/{package}/verification-execution-plan.json")
    tree = core.export(repo, bootstrap, core.SCRATCH / "suites" / label)
    nm = tree / "node_modules"
    nm.mkdir(exist_ok=True)
    if not (nm / "@playwright").exists():
        os.symlink(PW, nm / "@playwright")
    results = []
    for s in [s for s in plan["suites"] if _executable(s)]:
        cmd = s["runner"] + (" --list-tests" if s["runner"].startswith("dotnet") else " --list")
        res = core.run(cmd, tree, env=core.DOTNET_ENV | {"DOTNET_ROOT": "/root/.dotnet", "CI": ""}, timeout=900,
                       shell=True, limit=4000)
        text = res["stdout"] + "\n" + res["stderr"]
        results.append({"suite": s["id"], "command": s["runner"], "listCommand": cmd,
                        "dotnetTargets": c.dotnet_test_targets(s["runner"]),
                        "playwrightProjects": c.playwright_projects(s["runner"]),
                        "classification": c.classify_suite_run(text, res["exit"]),
                        "findings": c.suite_findings(text, res["exit"]),
                        "exit": res["exit"], "seconds": res["seconds"],
                        "evidence": [l.strip() for l in text.splitlines()
                                     if re.search(r"error MSB1008|not found|Skipping:|No test|Total|error ", l)][:8]})
    return {"plan": f"requirements-compiled/{package}/verification-execution-plan.json",
            "planAt": core.commit_info(core.INDY_FULL, indy_rev), "tree": core.commit_info(repo, bootstrap),
            "globalJson": (tree / "global.json").read_text() if (tree / "global.json").exists() else None,
            "suites": results, "seconds": round(sum(r["seconds"] for r in results), 2)}


def replay():
    fixed = run_plan(FIXED["indy"], FIXED["package"], FIXED["repo"], FIXED["bootstrap"], "fixed-r10-v415")
    labels = {"R8-MSB1008": "r8-pre-v411", "R9-MSB1008": "r9-pre-v412"}
    records = []
    for key, k in CASES.items():
        pre = core.commit_info(core.INDY_FULL, k["indy"])
        r = run_plan(k["indy"], k["package"], k["repo"], k["bootstrap"], labels[key])
        bad = [x for x in r["suites"] if x["classification"] in ("MSB1008", "UNDEFINED_PLAYWRIGHT_PROJECT")]
        records.append({
            "key": key, "rehearsal": k["rehearsal"], "blocker": k["blocker"], "trackBEvent": k["event"], "t0": k["t0"],
            "preT0": pre, "preT0IsBeforeT0": c.is_pre_t0(pre["committerTime"], k["t0"]),
            "dryRunRepo": f"{k['repo']}@{k['bootstrap']} (T0 bootstrap, no application code)",
            "toolsRun": [f"frozen {k['package']} plan suite commands (list mode), dotnet SDK 10.0.402, @playwright/test 1.63.0"],
            "check": r,
            "falsePositiveCheck": {"fixedPlan": fixed["plan"], "planAt": fixed["planAt"], "tree": fixed["tree"],
                                   "suites": [{k2: x[k2] for k2 in ("suite", "classification", "findings", "exit", "evidence")} for x in fixed["suites"]]},
            "otherConditions": {x["suite"]: x["findings"] for x in r["suites"] if "ASSEMBLY_SKIPPED" in x["findings"]},
            "outcome": c.outcome(True, bool(bad)),
            "matchEvidence": "; ".join(f"{x['suite']}: {x['classification']}" for x in bad) or
                             "; ".join(f"{x['suite']}: {x['classification']}" for x in r["suites"]),
            "dryRunSeconds": r["seconds"]})
    return records
