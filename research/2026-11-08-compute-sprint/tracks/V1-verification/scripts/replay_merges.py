"""Claim A-F-07: replay every merge commit of R8 in a scratch clone with `git merge-tree --write-tree`
and list conflicted paths. Usage: python3 -I replay_merges.py SCRATCH_CLONE MERGES_JSONL OUT_JSON
Only reads the clone (merge-tree writes loose objects into the scratch clone's object store; no refs change)."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1lib as L  # noqa: E402


def git(repo, *args):
    return subprocess.run(("git", "-C", repo) + args, capture_output=True, text=True)


def merge_commits(repo):
    out = git(repo, "log", "--merges", "--format=%H%x09%P%x09%aI%x09%s", "HEAD").stdout.strip().split("\n")
    return tuple(dict(zip(("sha", "parents", "at", "subject"), (f[0], tuple(f[1].split()), f[2], f[3])))
                 for f in (ln.split("\t") for ln in out if ln))


def recorded_conflicts(body):
    """Paths git itself listed under '# Conflicts:' in the merge commit message."""
    lines = body.split("\n")
    if "# Conflicts:" not in lines:
        return ()
    rest = lines[lines.index("# Conflicts:") + 1:]
    return tuple(l[2:].strip() for l in rest if l.startswith("#\t"))


def replay(repo, m):
    if len(m["parents"]) != 2:
        return dict(m, conflicts=None, note="octopus")
    r = git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", *m["parents"])
    conflicts = L.parse_merge_tree_conflicts(r.stdout) if r.returncode == 1 else ()
    body = git(repo, "log", "-1", "--format=%b", m["sha"]).stdout
    return dict(m, conflicts=conflicts, exit=r.returncode, recorded=recorded_conflicts(body),
                nonState=tuple(p for p in conflicts if not L.is_praxis_state(p)))


def main(repo, merges_jsonl, out):
    logged = tuple(json.loads(l) for l in open(merges_jsonl) if l.strip())
    results = tuple(replay(repo, m) for m in merge_commits(repo))
    conflicted = tuple(r for r in results if r["conflicts"])
    by_sha = {r["sha"]: r for r in results}
    # For each logged PR merge, find the branch-side merge(s) of main into the PR branch:
    # second-parent history of the PR merge commit that is not reachable from its first parent.
    pr_rows = []
    for e in logged:
        mc = e.get("mergeCommit")
        if not mc or mc not in by_sha:
            pr_rows.append(dict(pr=e["pr"], loggedConflict=e["conflict"], found=False))
            continue
        p1, p2 = by_sha[mc]["parents"]
        side = git(repo, "rev-list", "--merges", f"{p1}..{p2}").stdout.split()
        side_conf = sorted({p for s in side for p in (by_sha[s]["conflicts"] or ())})
        pr_rows.append(dict(pr=e["pr"], loggedConflict=e["conflict"], loggedFiles=e["conflictFiles"].split(),
                            prMergeConflicts=list(by_sha[mc]["conflicts"] or ()), branchSideMerges=len(side),
                            branchSideConflictPaths=side_conf, found=True))
    all_paths = sorted({p for r in conflicted for p in r["conflicts"]})
    summary = {
        "mergeCommits": len(results), "conflictingOnReplay": len(conflicted),
        "conflictPaths": all_paths,
        "nonStateConflicts": [dict(sha=r["sha"], subject=r["subject"], paths=r["nonState"]) for r in conflicted if r["nonState"]],
        "loggedPRs": len(logged), "loggedConflicts": sum(1 for e in logged if e["conflict"]),
        "loggedConflictWithReplayEvidence": sum(1 for p in pr_rows if p.get("loggedConflict") and (p.get("prMergeConflicts") or p.get("branchSideConflictPaths"))),
        "loggedCleanButReplayConflict": [p["pr"] for p in pr_rows if not p.get("loggedConflict") and (p.get("prMergeConflicts") or p.get("branchSideConflictPaths"))],
        "loggedConflictNoReplayEvidence": [p["pr"] for p in pr_rows if p.get("loggedConflict") and not (p.get("prMergeConflicts") or p.get("branchSideConflictPaths"))],
        "mergesWithRecordedConflicts": sum(1 for r in results if r.get("recorded")),
        "recordedNonStatePaths": sorted({p for r in results for p in (r.get("recorded") or ()) if not L.is_praxis_state(p)}),
        "prRows": pr_rows,
        "conflicted": [dict(sha=r["sha"][:10], at=r["at"], subject=r["subject"], paths=r["conflicts"]) for r in conflicted],
    }
    json.dump(summary, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("prRows", "conflicted")}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
