"""R10 replays: R10-AUTH (D3, authorize-implementation), R10-JOBCAP and R10-GATE (D6, time budgets)."""
import csv
import json
import re
import time
from pathlib import Path

from . import checks as c
from . import core

T0 = "2026-11-06T16:40:13Z"
PRE = "89f5840523b9e1185a5dbcd2a29d0799fe728598"     # R10 .echelon/r9-governance.json indyInitCommit
FIXED = "669fe04"                                     # Indy-init PR #174 repair of authorize-implementation
R10 = "/home/user/indy-init-rehearsal-010"
SETUP = "33fd372"                                     # merged setup: bootstrap + Praxis items + scope checkpoint, no app code
BOOTSTRAP = "314cc8c"                                 # T0 bootstrap commit (Conditor output)
PRAXIS = str(core.SCRATCH / "bin" / "praxis")         # Praxis 3.25.0 built from praxis@v3.25.0 (12bf9951)
STEPS_CSV = Path("/home/user/sprint-wt/A-economics/research/2026-11-08-compute-sprint/tracks/A-economics/data/ci-steps.csv")
JOBS_CSV = STEPS_CSV.with_name("ci-jobs.csv")


def authorize(indy_rev, label, relocate=True):
    src = core.export(core.INDY_FULL, indy_rev, core.SCRATCH / "r10" / f"src-{label}")
    target = core.clone_at(R10, SETUP, core.SCRATCH / "r10" / f"target-{label}")
    lock = json.loads((src / "kickoff/rehearsal-010/toolchain.lock.json").read_text())
    # Relocation: the committed suite-preflight report names the directory it ran in (R10's checkout path). The dry-run
    # copy lives elsewhere, so its root field is rewritten to the copy's path (content otherwise unchanged); without it
    # the gate adds one path-only cause. Both runs are kept in the raw record.
    sp = target / "evidence/t0/suite-preflight.json"
    report = json.loads(sp.read_text())
    original_root = report.get("root")
    if relocate:
        report["root"] = str(target.resolve())
        sp.write_text(json.dumps(report, indent=2))
        core.git(target, "-c", "user.name=dryrun", "-c", "user.email=dryrun@invalid", "commit", "-qam", "dry-run: relocate suite-preflight root")
    cmd = ["dotnet", "fsi", str(src / "tools/r9/r9.fsx"), "--", "authorize-implementation", "--target", ".",
           "--catalog", str(src / "requirements/catalogs/causa-investigation.requirement-catalog.json"),
           "--obligations", ".echelon/obligations.json", "--suite-preflight", "evidence/t0/suite-preflight.json",
           "--spec-preflight", "evidence/t0/spec-preflight.json", "--acceptance-preflight", "evidence/t0/acceptance.log",
           "--scope-sha256", lock["scope"]["scopeSha256"], "--praxis", PRAXIS]
    res = core.run(cmd, target, env=core.DOTNET_ENV | {"DOTNET_ROOT": "/root/.dotnet"}, timeout=900, limit=20000)
    text = res["stdout"] + "\n" + res["stderr"]
    causes = [l.strip() for l in text.splitlines() if l.strip().startswith("REFUSED")]
    return {"indyInit": core.commit_info(core.INDY_FULL, indy_rev), "target": core.commit_info(R10, SETUP),
            "suitePreflightRoot": {"original": original_root, "relocated": relocate},
            "run": res, "causes": causes, "causeCount": len(causes),
            "step3": sum(1 for x in causes if "REFUSED 3 " in x), "step4": sum(1 for x in causes if "REFUSED 4 " in x)}


def historical(lines):
    return [l.strip() for l in lines if l.strip().startswith("REFUSED")]


def _rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def budgets():
    """D6: caps of the R10 bootstrap workflows vs pre-T0 historical durations (runs created before R10's T0)."""
    t = time.monotonic()
    jobs = _rows(JOBS_CSV)
    pre_runs = {r["runId"] for r in jobs if r["createdAt"] and c.is_pre_t0(r["createdAt"], T0)}
    steps = [r for r in _rows(STEPS_CSV) if r["runId"] in pre_runs and r["repo"].startswith("indy-init-rehearsal-")]
    bt = core.show(R10, BOOTSTRAP, ".github/workflows/build-and-test.yml").decode()
    gate = core.show(R10, BOOTSTRAP, ".github/workflows/verification-gate.yml").decode()
    bt_cap = int(re.search(r"build-and-test:.*?timeout-minutes:\s*(\d+)", bt, re.S).group(1))
    gate_cap = int(re.search(r"verify:.*?timeout-minutes:\s*(\d+)", gate, re.S).group(1))
    step = lambda r: r["step"].lower()
    install = lambda r: ("install" in step(r) or "download" in step(r)) and any(b in step(r) for b in ("webkit", "chromium", "playwright"))
    bt_kinds = {
        "dotnet build (step 'Build')": lambda r: step(r) == "build",
        "dotnet test (step 'Test')": lambda r: step(r) == "test",
        "browser suite chromium ('Verify the pages in a real browser')": lambda r: "verify the pages in a real browser" in step(r),
        "browser suite webkit": lambda r: "in webkit" in step(r) and "install" not in step(r),
        "browser install chromium": lambda r: install(r) and "chromium" in step(r) and "webkit" not in step(r),
        "browser install webkit": lambda r: install(r) and "webkit" in step(r),
    }
    gate_kinds = {
        "plan suites (run-suites)": lambda r: "run the plan's suites" in step(r),
        "fault probes": lambda r: "fault probes" in step(r),
        "browser install": install,
    }
    ok = [r for r in steps if r["conclusion"] == "success"]
    # Primary (fixed after the first run, see raw): successful steps only; a cancelled/failed step measures queueing,
    # hangs or the cap itself, not the suite. The all-conclusions figure is kept as a sensitivity row.
    bt_max, gate_max = c.max_by_kind(ok, bt_kinds), c.max_by_kind(ok, gate_kinds)
    bt_all, gate_all = c.max_by_kind(steps, bt_kinds), c.max_by_kind(steps, gate_kinds)
    v48 = [r for r in ok if r["repo"] in ("indy-init-rehearsal-008", "indy-init-rehearsal-009")]
    bt_v41, gate_v41 = c.max_by_kind(v48, bt_kinds), c.max_by_kind(v48, gate_kinds)
    job_max = {}
    for r in jobs:
        if r["runId"] in pre_runs and r["repo"].startswith("indy-init-rehearsal-") and r["durationSeconds"]:
            k = (r["repo"], r["job"])
            job_max[k] = max(job_max.get(k, 0.0), float(r["durationSeconds"]))
    top_jobs = sorted(((v, f"{k[0]}:{k[1]}") for k, v in job_max.items()), reverse=True)[:8]
    return {"preT0Runs": len(pre_runs), "preT0StepRows": len(steps),
            "buildAndTest": {"cap": bt_cap, "maxByKind": bt_max, **c.budget_verdict(bt_cap, sum(bt_max.values())),
                             "sensitivity": {"allConclusions": c.budget_verdict(bt_cap, sum(bt_all.values())) | {"maxByKind": bt_all},
                                             "successR8R9only": c.budget_verdict(bt_cap, sum(bt_v41.values())) | {"maxByKind": bt_v41}}},
            "gate": {"cap": gate_cap, "maxByKind": gate_max, **c.budget_verdict(gate_cap, sum(gate_max.values())),
                     "sensitivity": {"allConclusions": c.budget_verdict(gate_cap, sum(gate_all.values())) | {"maxByKind": gate_all},
                                     "successR8R9only": c.budget_verdict(gate_cap, sum(gate_v41.values())) | {"maxByKind": gate_v41}}},
            "longestPreT0Jobs": [{"job": j, "seconds": s} for s, j in top_jobs],
            "seconds": round(time.monotonic() - t, 2)}


def replay():
    pre = core.commit_info(core.INDY_FULL, PRE)
    hist = historical((Path(R10) / "evidence/t0/authorize-implementation.refused.log").read_text().splitlines())
    a = authorize(PRE, "pre")
    a_unrel = authorize(PRE, "pre-unrelocated", relocate=False)
    fx = authorize(FIXED, "fixed")
    same = sorted(a["causes"]) == sorted(hist)
    auth_rec = {
        "key": "R10-AUTH", "rehearsal": "R10", "blocker": "authorize-implementation refused the real approved plan (55 causes)",
        "trackBEvent": "B-E-110", "t0": T0, "preT0": pre, "preT0IsBeforeT0": c.is_pre_t0(pre["committerTime"], T0),
        "dryRunRepo": f"indy-init-rehearsal-010@{SETUP} (bootstrap + Praxis items + scope checkpoint; no application code)",
        "toolsRun": ["r9.fsx authorize-implementation @89f5840", "praxis 3.25.0 (built from v3.25.0)"],
        "check": a, "unrelocatedRun": {"causeCount": a_unrel["causeCount"], "extraCauses": sorted(set(a_unrel["causes"]) - set(hist))},
        "historical": {"causeCount": len(hist), "identicalCauseSet": same},
        "falsePositiveCheck": {"fixedRev": fx["indyInit"], "exit": fx["run"]["exit"], "causeCount": fx["causeCount"],
                               "causes": fx["causes"], "stdoutTail": fx["run"]["stdout"][-1500:]},
        "outcome": c.outcome(a["run"]["exit"] not in ("TIMEOUT",), a["run"]["exit"] == 4 and (a["step3"] + a["step4"]) > 0),
        "matchEvidence": f"exit {a['run']['exit']}; {a['causeCount']} causes (step3 {a['step3']}, step4 {a['step4']}); "
                         f"historical 55; identical cause set: {same}",
        "dryRunSeconds": a["run"]["seconds"]}
    b = budgets()
    bt, gate = b["buildAndTest"], b["gate"]
    jobcap = {
        "key": "R10-JOBCAP", "rehearsal": "R10", "blocker": "build-and-test 20-min job cap vs ~29-min browser suite",
        "trackBEvent": "B-E-115", "t0": T0, "preT0": core.commit_info(R10, BOOTSTRAP), "preT0IsBeforeT0": False,
        "toolsRun": ["harness D6 budget check: bootstrap build-and-test.yml timeout vs Track A ci-steps.csv (runs before T0)"],
        "check": b, "outcome": c.outcome(True, bt["exceedsCap"]),
        "matchEvidence": f"cap {bt['cap']} min vs pre-T0 estimate {bt['estimateMinutes']} min (sum of per-kind maxima {bt['maxByKind']})",
        "dryRunSeconds": b["seconds"]}
    gate_rec = {
        "key": "R10-GATE", "rehearsal": "R10", "blocker": "governed gate deadlock (40-min cap, write-once record, Playwright install timeouts, branch-name refusal)",
        "trackBEvent": "B-E-113", "t0": T0, "preT0": core.commit_info(R10, BOOTSTRAP), "preT0IsBeforeT0": False,
        "toolsRun": ["harness D6 budget check: bootstrap verification-gate.yml verify timeout vs pre-T0 durations"],
        "check": b, "causesCovered": ["40-min cap (time budget)"],
        "causesNotReplayable": ["write-once governance record", "Playwright install timeouts on hosted runners",
                                "branch-name refusal", "cancellation by concurrency"],
        "outcome": c.outcome(True, gate["exceedsCap"]),
        "matchEvidence": f"gate cap {gate['cap']} min vs pre-T0 estimate {gate['estimateMinutes']} min ({gate['maxByKind']}); "
                         "other causes need hosted Actions runs and were not replayed",
        "dryRunSeconds": 0.0}
    return [auth_rec, jobcap, gate_rec]
