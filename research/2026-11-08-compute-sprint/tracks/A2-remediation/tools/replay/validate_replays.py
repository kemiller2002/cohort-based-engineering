#!/usr/bin/env python3
"""SPR-A2-01 step 4: run the pinned `praxis validate` on (a) the team's merge commit M and (b) the
driver's merge result, for each target merge. Non-.ros conflicted files (which a .ros driver cannot
resolve) are taken from M so that only the .ros effect is tested.

Usage: python3 validate_replays.py SCRATCH_CLONE DRIVER_FSX PRAXIS_BIN TARGETS_JSON OUT_JSONL
"""
import json
import os
import subprocess
import sys

ROS = (".ros/context/current.json", ".ros/events/events.jsonl")


def git(repo, *args, check=True):
    p = subprocess.run(("git", "-C", repo) + args, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {args}: {p.stderr}")
    return p


def validate(repo, praxis, base_ref):
    env = dict(os.environ, PRAXIS_BASE_REF=base_ref, ROS_BASE_REF=base_ref)
    p = subprocess.run((praxis, "validate"), cwd=repo, capture_output=True, text=True, env=env)
    out = (p.stdout + p.stderr).strip().splitlines()
    return {"exit": p.returncode, "tail": out[-3:]}


def run_one(repo, driver, praxis, t):
    m = t["merge"]
    p1, p2 = git(repo, "rev-list", "--parents", "-n", "1", m).stdout.split()[1:]
    git(repo, "reset", "-q", "--hard")
    git(repo, "clean", "-qfdx")
    git(repo, "checkout", "-q", "--detach", m)
    on_m = validate(repo, praxis, p1)
    git(repo, "checkout", "-q", "--detach", p1)
    with open(f"{repo}/.git/info/attributes", "w") as f:
        f.write("".join(f"{p} merge=ros-history\n" for p in ROS))
    git(repo, "merge", "--no-ff", "--no-commit", "--no-edit", p2, check=False)
    unmerged = sorted(set(git(repo, "diff", "--name-only", "--diff-filter=U").stdout.split()))
    ros_left = [u for u in unmerged if u.startswith(".ros/")]
    taken_from_m = [u for u in unmerged if not u.startswith(".ros/")]
    if ros_left:
        git(repo, "merge", "--abort", check=False)
        return dict(t, onMergeCommit=on_m, onDriverResult=None, rosUnmerged=ros_left)
    for u in taken_from_m:
        git(repo, "checkout", m, "--", u)
        git(repo, "add", "--", u)
    git(repo, "commit", "-q", "--no-verify", "-m", "A2 replay (driver result)")
    on_d = validate(repo, praxis, p1)
    return dict(t, onMergeCommit=on_m, onDriverResult=on_d, nonRosFilesTakenFromM=taken_from_m)


def main(argv):
    repo, driver, praxis, targets, out = argv[1:6]
    git(repo, "config", "merge.ros-history.driver", f"dotnet fsi {driver} %O %A %B %P")
    with open(out, "w") as f:
        for t in json.load(open(targets)):
            r = run_one(repo, driver, praxis, t)
            f.write(json.dumps(r) + "\n")
            f.flush()
            d = r["onDriverResult"]
            print(t["label"], "M:", r["onMergeCommit"]["exit"], "driver:", d and d["exit"], file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
