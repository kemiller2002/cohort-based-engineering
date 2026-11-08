"""Safety guard: every V3 script refuses to run (or mutate) outside the V3 scratch root."""
import os
import subprocess

SCRATCH_ROOT = "/home/user/sprint-scratch/V3"


def is_under(path: str, root: str = SCRATCH_ROOT) -> bool:
    real, base = os.path.realpath(path), os.path.realpath(root)
    return real == base or real.startswith(base + os.sep)


def require_scratch_cwd() -> None:
    if not is_under(os.getcwd()):
        raise SystemExit(f"refusing to run: cwd {os.getcwd()} is outside {SCRATCH_ROOT}")


def require_scratch_path(path: str) -> str:
    if not is_under(path):
        raise SystemExit(f"refusing to touch {path}: outside {SCRATCH_ROOT}")
    return path


def git_toplevel(repo: str) -> str:
    return subprocess.run(["git", "-C", repo, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()


def mutating_git(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command that may write, only if repo, its toplevel AND its git dir are in scratch."""
    require_scratch_path(repo)
    require_scratch_path(git_toplevel(repo))
    gitdir = subprocess.run(["git", "-C", repo, "rev-parse", "--absolute-git-dir"],
                            capture_output=True, text=True, check=True).stdout.strip()
    require_scratch_path(gitdir)
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=check)


def read_git(repo: str, *args: str, check: bool = True) -> str:
    """Read-only git query; allowed on any repo."""
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=check).stdout
