"""A2-F-03: run my own praxis 3.25.0 build's `validate` on d8447ed1, both parents, and on
d8447ed1 with current.json replaced by the SUT driver's merge of the parents.
Worktrees are created only inside V3 scratch clones."""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3guard import mutating_git, read_git, require_scratch_cwd, require_scratch_path  # noqa: E402

PRAXIS = "/home/user/sprint-scratch/V3/praxis-bin/praxis.dll"
CUR = ".ros/context/current.json"


def worktree(repo, rev, path):
    require_scratch_path(path)
    if os.path.exists(path):
        mutating_git(repo, "worktree", "remove", "--force", path, check=False)
        shutil.rmtree(path, ignore_errors=True)
    mutating_git(repo, "worktree", "add", "-q", "--detach", path, rev)
    return path


def validate(path, args):
    env = {**os.environ, "DOTNET_ROOT": "/root/.dotnet", "DOTNET_ROLL_FORWARD": "Major", "HOME": "/home/user/sprint-scratch/V3/home",
           "ECHELON_HOME": "/home/user/sprint-scratch/V3/echelon"}
    p = subprocess.run(["/root/.dotnet/dotnet", PRAXIS, "--root", path, *args], capture_output=True, text=True, env=env, cwd=path)
    return {"exit": p.returncode, "stdout": p.stdout[-3000:], "stderr": p.stderr[-1500:]}


def main(repo, merge, driver_current, outdir, args):
    require_scratch_cwd()
    require_scratch_path(outdir)
    p1, p2 = read_git(repo, "rev-list", "--parents", "-1", merge).split()[1:3]
    targets = {"M-" + merge[:8]: merge, "P1-" + p1[:8]: p1, "P2-" + p2[:8]: p2}
    results = {name: validate(worktree(repo, rev, os.path.join(outdir, name)), args) for name, rev in targets.items()}
    if driver_current:
        wt = worktree(repo, merge, os.path.join(outdir, "M-with-driver-current"))
        shutil.copyfile(driver_current, os.path.join(wt, CUR))
        results["M-with-driver-current"] = validate(wt, args)
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] or None, sys.argv[4], sys.argv[5:])
