"""Time .NET builds of rehearsal-app copies under /home/user/sprint-scratch/F.

Usage: python3 measure_build.py OUT.csv REPO_DIR LABEL [--reps 3] [--modes publish-cold,publish-noop,...]
Each row is appended as soon as it is measured, so partial runs survive interruption.
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ENV = {**os.environ, "PATH": "/root/.dotnet:" + os.environ.get("PATH", ""),
       "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1"}

FIELDS = ["timestampUtc", "label", "mode", "rep", "seconds", "exitCode", "command", "note", "loadavg1Start", "batch"]


def build_dirs(repo: Path, roots: tuple[str, ...]) -> list[Path]:
    """bin/ and obj/ directories under the given top-level roots (pure apart from directory listing)."""
    return sorted(p for r in roots for p in (repo / r).rglob("*")
                  if p.is_dir() and p.name in ("bin", "obj") and "node_modules" not in p.parts)


def plan(modes: list[str], reps: int) -> list[tuple[str, int]]:
    """Interleave nothing: run each mode's reps back to back, cold modes first within each family."""
    return [(m, r) for m in modes for r in range(1, reps + 1)]


def mode_spec(mode: str, publish_project: str, solution: str, out: str) -> dict:
    """What to clean, what to touch, which command to time, for one mode."""
    publish = ["dotnet", "publish", publish_project, "-c", "Release", "-o", out]
    build = ["dotnet", "build", solution, "-c", "Debug"]
    table = {
        "publish-cold": {"clean": ("src",), "touch": False, "cmd": publish},
        "publish-noop": {"clean": (), "touch": False, "cmd": publish},
        "publish-incr": {"clean": (), "touch": True, "cmd": publish},
        "sln-cold": {"clean": ("src", "tests"), "touch": False, "cmd": build},
        "sln-noop": {"clean": (), "touch": False, "cmd": build},
        "sln-incr": {"clean": (), "touch": True, "cmd": build},
    }
    return table[mode]


def run_one(repo: Path, label: str, mode: str, rep: int, spec: dict, touch_file: str) -> dict:
    for d in build_dirs(repo, spec["clean"]):
        shutil.rmtree(d, ignore_errors=True)
    if spec["touch"]:
        with open(repo / touch_file, "a", encoding="utf-8") as f:
            f.write(f"\n// sprint-F incremental touch {mode} {rep}\n")
    load = open("/proc/loadavg").read().split()[0]
    start = time.perf_counter()
    proc = subprocess.run(spec["cmd"], cwd=repo, env=ENV, capture_output=True, text=True)
    seconds = time.perf_counter() - start
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] if proc.returncode else []
    return {"timestampUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "label": label,
            "mode": mode, "rep": rep, "seconds": round(seconds, 3), "exitCode": proc.returncode,
            "command": " ".join(spec["cmd"]), "note": " | ".join(tail)[:300], "loadavg1Start": load, "batch": os.environ.get("SPRINT_BATCH", "")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("repo"); ap.add_argument("label")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--modes", default="publish-cold,publish-noop,publish-incr")
    ap.add_argument("--publish-project", default="src/Causa.Host")
    ap.add_argument("--solution", default="Causa.slnx")
    ap.add_argument("--touch-file", default="src/Causa.App/View.fs")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    pub_out = str(Path("/home/user/sprint-scratch/F/pub") / a.label)
    new = not Path(a.out).exists()
    with open(a.out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for mode, rep in plan(a.modes.split(","), a.reps):
            row = run_one(repo, a.label, mode, rep, mode_spec(mode, a.publish_project, a.solution, pub_out), a.touch_file)
            w.writerow(row); f.flush()
            print(row["label"], row["mode"], row["rep"], row["seconds"], row["exitCode"], flush=True)


if __name__ == "__main__":
    main()
