"""Checkpoint harvester: merge committed track branches into the sprint branch and push.

Functional core (pure planning) + thin imperative shell (git subprocess calls)."""
from __future__ import annotations
import subprocess, sys, datetime as dt
from dataclasses import dataclass
from typing import Callable, Sequence

REPO = "/home/user/cohort-based-engineering"
BRANCH = "claude/echelon-compute-sprint-nov8-bkaw2t"
TRACKS = ("A-economics","B-forensics","C-architecture","D-experiments","E-security","F-fsharp-wasm","G-market","H-synthesis","V1-verification","A2-remediation","V2-verification","B2-dryrun","E2-hardening","D2-agent-experiment","B3-semantic","B4-preflight","C2-signed-registry","V3-verification","V4-verification","V5-verification")
LOG = "research/2026-11-08-compute-sprint/inventory/auto-checkpoints.log"

@dataclass(frozen=True)
class TrackState:
    track: str
    ahead: int  # commits on track branch not yet in sprint branch

def plan_merges(states: Sequence[TrackState]) -> tuple[str, ...]:
    """Pure: which track branches need merging."""
    return tuple(s.track for s in states if s.ahead > 0)

def log_line(now: str, merged: Sequence[str], states: Sequence[TrackState]) -> str:
    """Pure: one log line summarizing the checkpoint."""
    detail = ",".join(f"{s.track}:+{s.ahead}" for s in states)
    return f"{now}\tmerged={','.join(merged) or 'none'}\t{detail}\n"

def git(*args: str) -> str:
    return subprocess.run(["git","-C",REPO,*args],check=True,capture_output=True,text=True).stdout.strip()

def read_state(track: str) -> TrackState:
    return TrackState(track, int(git("rev-list","--count",f"{BRANCH}..sprint/track-{track}")))

def push_with_retry(attempts: int = 4) -> bool:
    delays = [2,4,8,16][:attempts]
    def attempt(i: int) -> bool:
        r = subprocess.run(["git","-C",REPO,"push","-q","origin",BRANCH],capture_output=True,text=True)
        if r.returncode == 0: return True
        if i + 1 >= len(delays): return False
        subprocess.run(["sleep",str(delays[i])]); return attempt(i+1)
    return attempt(0)

def main() -> int:
    states = tuple(map(read_state, TRACKS))
    merged = plan_merges(states)
    for t in merged:
        git("merge","--no-edit","-q","-m",f"Checkpoint: merge track {t}",f"sprint/track-{t}")
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).isoformat(timespec="seconds")
    with open(f"{REPO}/{LOG}","a") as f: f.write(log_line(now, merged, states))
    git("add",LOG); git("commit","-q","-m",f"Auto-checkpoint {now}: merged {len(merged)} track(s)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01G1iECcw8ww9jBtGb1vGiem","--",LOG)
    if "--no-push" in sys.argv[1:]:  # D-054: public remote; pushes held for owner decision
        print(log_line(now, merged, states).strip(), "not pushed (--no-push)"); return 0
    ok = push_with_retry()
    print(log_line(now, merged, states).strip(), "pushed" if ok else "PUSH-FAILED")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
