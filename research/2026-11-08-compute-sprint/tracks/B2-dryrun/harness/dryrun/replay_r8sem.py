"""R8-CMDBODY and R8-INV04 (D7): the pinned package pipeline on R8's frozen v4.1.1 at the pre-T0 Indy-init commit.

Runs (1) the frozen contracts' typecheck project ContractCheck.fsproj, (2) requirements-compiler v41 --check (the
package validation X01..X20 the freeze relied on), and (3) the D2 stub-tree suite listing from replay_suites (already
in raw/R8-MSB1008.json). A catch needs output naming the command body / CommandEnvelope (CMDBODY) or INV-04 / SM-SAVE
T-S31/T-S32 as a failure (INV04)."""
import json
import re
import time
from pathlib import Path

from . import checks as c
from . import core

T0 = "2026-11-01T17:31:24Z"
PRE = "1cb27ec"
ENV = core.DOTNET_ENV | {"DOTNET_ROOT": "/root/.dotnet"}


def pipeline():
    src = core.export(core.INDY_FULL, PRE, core.SCRATCH / "r8sem" / "src")
    builds, runs = [], []
    rc = core.run(["dotnet", "build", "tools/requirements-compiler/src", "-c", "Release", "-nologo", "-v", "q"],
                  src, env=ENV, timeout=1500, limit=6000)
    builds.append({"what": "requirements-compiler (Release)", **rc})
    dll = next(Path(src / "tools/requirements-compiler/src/bin/Release").rglob("requirements-compiler.dll"), None)
    if dll:
        v = core.run(["dotnet", str(dll), "v41", "--source", ".", "--package", "requirements-compiled/v4.1.1",
                      "--base", "requirements-compiled/v4", "--check"], src, env=ENV, timeout=1200, limit=12000)
        runs.append({"what": "requirements-compiler v41 --check (v4.1.1)", **v})
    # ContractCheck builds after --check: its bin/obj inside the package would otherwise fail --check (exit 4).
    cc = core.run(["dotnet", "build", "requirements-compiled/v4.1.1/contracts/ContractCheck.fsproj", "-nologo", "-v", "q"],
                  src, env=ENV, timeout=1200, limit=6000)
    builds.append({"what": "ContractCheck.fsproj (frozen v4.1.1 contracts typecheck)", **cc})
    return {"src": core.commit_info(core.INDY_FULL, PRE), "builds": builds, "runs": runs}


def mentions(text, pattern):
    return [l.strip() for l in text.splitlines() if re.search(pattern, l)][:10]


def replay():
    pre = core.commit_info(core.INDY_FULL, PRE)
    p = pipeline()
    track = Path(__file__).resolve().parents[2]
    suites = json.loads((track / "raw" / "R8-MSB1008.json").read_text())["check"]["suites"]
    text = "\n".join(x["stdout"] + x["stderr"] for x in p["builds"] + p["runs"]) + "\n" + json.dumps(suites)
    replayable = bool(p["runs"]) and p["builds"][0]["exit"] != "TIMEOUT"
    out = []
    first = True
    for key, blocker, event, pattern in (
            ("R8-CMDBODY", "frozen IF41-DOMAIN carries no command body", "B-E-093", r"command body|CommandEnvelope"),
            ("R8-INV04", "INV-04 contradicts SM-SAVE T-S31/T-S32", "B-E-094", r"INV-?04|T-S31|T-S32|SM-SAVE")):
        hits = [h for h in mentions(text, pattern) if re.search(r"fail|error|contradict|refus", h, re.I)]
        out.append({
            "key": key, "rehearsal": "R8", "blocker": blocker, "trackBEvent": event, "t0": T0, "preT0": pre,
            "preT0IsBeforeT0": c.is_pre_t0(pre["committerTime"], T0),
            "toolsRun": ["ContractCheck.fsproj build (frozen contracts)", "requirements-compiler v41 --check @1cb27ec",
                         "D2 stub-tree suite listing (raw/R8-MSB1008.json)"],
            "check": {"pipeline": p, "mentionsOfMechanism": mentions(text, pattern), "failingMentions": hits,
                      "toolExits": {x["what"]: x["exit"] for x in p["builds"] + p["runs"]}},
            "outcome": c.outcome(replayable, bool(hits)),
            "matchEvidence": ("failing output names the mechanism: " + "; ".join(hits[:3])) if hits else
            "pinned pipeline exits " + ", ".join(f"{k}={v}" for k, v in
                                                 {x["what"]: x["exit"] for x in p["builds"] + p["runs"]}.items()) +
            "; no failing output names the mechanism",
            "dryRunSeconds": round(sum(x["seconds"] for x in p["runs"]), 2) if first else 0.0,
            "buildSeconds": round(sum(x["seconds"] for x in p["builds"]), 2) if first else 0.0,
            "costNote": "pipeline run shared with R8-CMDBODY; seconds counted there" if not first else ""})
        first = False
    return out
