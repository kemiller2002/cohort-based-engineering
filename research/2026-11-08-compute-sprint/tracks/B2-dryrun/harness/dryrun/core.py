"""Side-effecting plumbing for the dry-run harness: git reads, tree export, timed subprocesses.

Every function returns plain data (dicts/bytes); nothing here decides an outcome."""
import json
import os
import subprocess
import time
from pathlib import Path

SCRATCH = Path(os.environ.get("B2_SCRATCH", "/home/user/sprint-scratch/B2"))
INDY_FULL = SCRATCH / "indy-init-full"
DOTNET_ENV = {"PATH": "/root/.dotnet:" + os.environ.get("PATH", ""),
              "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1",
              "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1"}


def _tail(text, limit):
    return text if len(text) <= limit else "...[truncated]...\n" + text[-limit:]


def run(cmd, cwd, env=None, timeout=1200, shell=False, limit=6000):
    """Run a command; return {cmd, cwd, exit, seconds, stdout, stderr} (outputs tail-truncated)."""
    full_env = dict(os.environ)
    full_env.update(env or {})
    start = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=str(cwd), env=full_env, capture_output=True, text=True,
                           timeout=timeout, shell=shell)
        code, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as ex:
        code, out, err = "TIMEOUT", (ex.stdout or b"").decode() if isinstance(ex.stdout, bytes) else (ex.stdout or ""), "timeout"
    return {"cmd": cmd if isinstance(cmd, str) else " ".join(cmd), "cwd": str(cwd), "exit": code,
            "seconds": round(time.monotonic() - start, 2),
            "stdout": _tail(out, limit), "stderr": _tail(err, limit)}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def show(repo, rev, path):
    """Bytes of path at rev, or None when absent."""
    try:
        return git(repo, "show", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return None


def show_json(repo, rev, path):
    raw = show(repo, rev, path)
    return None if raw is None else json.loads(raw)


def commit_info(repo, rev):
    sha, when, subject = git(repo, "log", "-1", "--format=%H%x00%cI%x00%s", rev).decode().strip().split("\x00")
    return {"repo": str(repo), "rev": rev, "sha": sha, "committerTime": when, "subject": subject}


def export(repo, rev, dest, paths=()):
    """Materialise rev (optionally only paths) into a fresh directory dest (never touches repo's worktree)."""
    dest = Path(dest)
    if dest.exists():
        subprocess.run(["rm", "-rf", str(dest)], check=True)
    dest.mkdir(parents=True)
    archive = subprocess.Popen(["git", "-C", str(repo), "archive", rev, *paths], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(dest)], stdin=archive.stdout, check=True)
    archive.wait()
    return dest


def snapshot_repo(repo, rev, dest):
    """A throwaway git repository holding rev's tree as a single commit (for tools that need git)."""
    dest = export(repo, rev, dest)
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.name=dryrun", "-c", "user.email=dryrun@invalid", "commit", "-qm", f"dry-run snapshot of {rev}"]):
        subprocess.run(["git", "-C", str(dest), *args], check=True, capture_output=True)
    return dest


def clone_at(repo, rev, dest):
    """A local clone of repo checked out at rev (history kept; the source repository is only read)."""
    dest = Path(dest)
    if dest.exists():
        subprocess.run(["rm", "-rf", str(dest)], check=True)
    subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(repo), str(dest)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", rev], check=True, capture_output=True)
    return dest
