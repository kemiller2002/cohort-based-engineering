"""B4-F-01 / B4-F-05 recomputation: run a scratch-built percepta spec-preflight with the
r9.fsx (bc3c381) invocation and with the CI (dae2347) invocation, and summarise the report."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3guard import require_scratch_cwd, require_scratch_path  # noqa: E402

SECTIONS = ["blockingContradictions", "missingInterfaces", "missingDecisions", "unsupportedVerificationObligations"]


def r9_args(root, pkg, base="requirements-compiled/v4"):
    """Flag order and file choice exactly as r9.fsx specPreflight builds them from a lock."""
    j = lambda *p: os.path.abspath(os.path.join(root, *p))
    return ["--machines", j(pkg, "state-machine-contracts.json"), "--invariants", j(base, "invariants.json"),
            "--interfaces", j(pkg, "analysis", "interface-specifications.json"),
            "--catalog", j("docs", "COMMAND-EVENT-CATALOG.md")]


def ci_args(root, pkg, base="requirements-compiled/v4"):
    """preflight-tooling.yml lines 398-399: same inputs, no --catalog."""
    return r9_args(root, pkg, base)[:6]


def summarise(report):
    count = lambda s: len(report.get(s) or [])
    blocking = lambda s: len([f for f in (report.get(s) or []) if isinstance(f, dict) and str(f.get("blocking")).lower() != "false"])
    return {"blocked": report.get("blocked"), "analysed": report.get("analysed"),
            "counts": {s: count(s) for s in SECTIONS + ["warnings", "suggestedOwnerActions"] if s in report},
            "blockingCounts": {s: blocking(s) for s in SECTIONS if s in report},
            "otherKeys": sorted(k for k in report if k not in SECTIONS),
            "findings": {s: [(f.get("rule"), f.get("blocking"), (f.get("detail") or "")[:160]) for f in (report.get(s) or []) if isinstance(f, dict)]
                         for s in report if isinstance(report.get(s), list)}}


def ci_jq_gate(report):
    """The jq -e condition of preflight-tooling.yml line 400."""
    return (report.get("blocked") is False and len(report.get("blockingContradictions") or []) == 0
            and (report.get("analysed") or {}).get("transitions", 0) > 0)


def run(dll, args, out):
    require_scratch_path(out)
    env = {**os.environ, "DOTNET_ROLL_FORWARD": "Major", "DOTNET_ROOT": "/root/.dotnet"}
    p = subprocess.run(["/root/.dotnet/dotnet", dll, "spec-preflight", *args, "--out", out], capture_output=True, text=True, env=env)
    report = json.load(open(out)) if os.path.exists(out) else {}
    return {"exit": p.returncode, "summary": summarise(report), "ciJqGatePasses": ci_jq_gate(report), "stderr": p.stderr[-400:]}


def main(dll, outdir, cases):
    require_scratch_cwd()
    require_scratch_path(outdir)
    os.makedirs(outdir, exist_ok=True)
    results = {f"{name}/{mode}": run(dll, (r9_args if mode == "r9" else ci_args)(root, pkg), os.path.join(outdir, f"{name}.{mode}.json"))
               for name, root, pkg in cases for mode in ("r9", "ci")}
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    S = "/home/user/sprint-scratch/V3/pkgs"
    main("/home/user/sprint-scratch/V3/percepta-bin/Percepta.Cli.dll", "/home/user/sprint-scratch/V3/out/percepta",
         [("R8-v4.1.1@1cb27ec", f"{S}/1cb27ec", "requirements-compiled/v4.1.1"),
          ("v4.1.2@bc3c381", f"{S}/bc3c381", "requirements-compiled/v4.1.2"),
          ("v4.1.1@bc3c381", f"{S}/bc3c381", "requirements-compiled/v4.1.1")])
