"""A2-F-01/02 independent replay: seeded sample of conflicted merges, re-merged with the
A2 ros-history driver (system under test), compared record-by-record with the team's
merge commit and the parents.  All git mutation happens in V3 scratch clones only."""
import collections
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3guard import mutating_git, read_git, require_scratch_cwd, require_scratch_path  # noqa: E402

CUR, EVT = ".ros/context/current.json", ".ros/events/events.jsonl"
SUT = "/home/user/sprint-scratch/V3/sut/ros-merge.fsx"


# ---------- pure record logic ----------
def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def work_items(text):
    """id -> list of canonical records (list so duplicates are visible)."""
    if text is None:
        return {}
    acc = collections.defaultdict(list)
    for wi in json.loads(text).get("workItems", []):
        acc[wi.get("id")].append(canon(wi))
    return dict(acc)


def events(text):
    if text is None:
        return {}
    acc = collections.defaultdict(list)
    for line in (l for l in text.splitlines() if l.strip()):
        rec = json.loads(line)
        acc[rec.get("eventId") or "line:" + canon(rec)].append(canon(rec))
    return dict(acc)


def compare(base, p1, p2, result, team):
    """All args are id->records maps.  Returns a record-level verdict dict."""
    deleted = (set(base) - set(p1)) | (set(base) - set(p2))
    expected = (set(p1) | set(p2)) - deleted
    lost = sorted(expected - set(result))
    extra = sorted(set(result) - (set(p1) | set(p2)))
    dup = sorted(k for k, v in result.items() if len(v) > 1)
    team_dup = sorted(k for k, v in team.items() if len(v) > 1)
    common = set(result) & set(team)
    content_diff = sorted(k for k in common if sorted(result[k]) != sorted(team[k]))
    # was each differing record in the result taken verbatim from some parent?
    from_parent = {k: any(sorted(result[k]) == sorted(src.get(k, [])) for src in (p1, p2)) for k in content_diff}
    team_lost = sorted(expected - set(team))
    return {"nExpected": len(expected), "nResult": len(result), "nTeam": len(team),
            "lost": lost, "extra": extra, "duplicates": dup,
            "idsEqualTeam": set(result) == set(team), "onlyInResult": sorted(set(result) - set(team)),
            "onlyInTeam": sorted(set(team) - set(result)), "contentDiffVsTeam": content_diff,
            "contentDiffTakenFromParent": from_parent, "teamLostVsParents": team_lost, "teamDuplicates": team_dup}


def top_level_diff(result_text, team_text):
    if result_text is None or team_text is None:
        return None
    a, b = json.loads(result_text), json.loads(team_text)
    return sorted(k for k in set(a) | set(b) if k != "workItems" and a.get(k) != b.get(k))


def sample(items, n, seed):
    return sorted(random.Random(seed).sample(sorted(items), min(n, len(items))))


# ---------- git (read-only) ----------
def show(repo, rev, path):
    import subprocess
    p = subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def merges(repo):
    rows = [l.split() for l in read_git(repo, "rev-list", "--all", "--merges", "--parents").splitlines()]
    return [tuple(r) for r in rows if len(r) == 3]


def survey(repo, m, p1, p2):
    import subprocess
    p = subprocess.run(["git", "-C", repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", p1, p2],
                       capture_output=True, text=True)
    paths = [l for l in p.stdout.splitlines()[1:] if l.strip()]
    return {"merge": m, "p1": p1, "p2": p2, "conflicted": paths if p.returncode == 1 else [],
            "rosConflicted": [x for x in paths if x.startswith(".ros/")] if p.returncode == 1 else []}


# ---------- git (mutating, scratch only) ----------
def configure_driver(repo):
    require_scratch_path(repo)
    gitdir = read_git(repo, "rev-parse", "--absolute-git-dir").strip()
    require_scratch_path(gitdir)
    os.makedirs(os.path.join(gitdir, "info"), exist_ok=True)
    with open(os.path.join(gitdir, "info", "attributes"), "w") as f:
        f.write(f"{CUR} merge=ros-history\n{EVT} merge=ros-history\n")
    mutating_git(repo, "config", "merge.ros-history.name", "A2 ros-history driver (SUT)")
    mutating_git(repo, "config", "merge.ros-history.driver", f"/root/.dotnet/dotnet fsi {SUT} %O %A %B %P")


def driver_merge(repo, p1, p2):
    mutating_git(repo, "reset", "-q", "--hard")
    mutating_git(repo, "checkout", "-q", "-f", "--detach", p1)
    r = mutating_git(repo, "merge", "--no-commit", "--no-ff", "-q", p2, check=False)
    unmerged = sorted(set(read_git(repo, "diff", "--name-only", "--diff-filter=U").split()))
    read = lambda p: open(os.path.join(repo, p)).read() if os.path.exists(os.path.join(repo, p)) else None
    texts = {CUR: read(CUR), EVT: read(EVT)}
    mutating_git(repo, "merge", "--abort", check=False)
    mutating_git(repo, "reset", "-q", "--hard")
    return {"exit": r.returncode, "unmerged": unmerged, "stderr": [l for l in r.stderr.splitlines() if "ros-merge" in l],
            "texts": texts}


def evaluate(repo, row):
    m, p1, p2 = row["merge"], row["p1"], row["p2"]
    b = read_git(repo, "merge-base", p1, p2).split()[0]
    d = driver_merge(repo, p1, p2)
    res = {"cur": None, "evt": None}
    for key, path, parse in (("cur", CUR, work_items), ("evt", EVT, events)):
        rev = {r: show(repo, r, path) for r in (b, p1, p2, m)}
        res[key] = compare(parse(rev[b]), parse(rev[p1]), parse(rev[p2]), parse(d["texts"][path]), parse(rev[m]))
        if key == "cur":
            res["curTopLevelDiffVsTeam"] = top_level_diff(d["texts"][path], rev[m])
        res[key + "ByteIdenticalTeam"] = d["texts"][path] == rev[m]
    return {**row, "base": b, "driverExit": d["exit"], "unmergedAfterDriver": d["unmerged"],
            "rosUnmergedAfterDriver": [x for x in d["unmerged"] if x.startswith(".ros/")],
            "driverStderr": d["stderr"], **res}


def main(argv):
    require_scratch_cwd()
    repo, mode, out = argv[0], argv[1], argv[2]
    require_scratch_path(repo)
    require_scratch_path(out)
    if mode == "survey":
        rows = [survey(repo, *t) for t in merges(repo)]
        json.dump(rows, open(out, "w"), indent=1)
        print(json.dumps({"merges": len(rows), "conflicted": sum(bool(r["conflicted"]) for r in rows),
                          "rosConflicted": sum(bool(r["rosConflicted"]) for r in rows),
                          "rosPaths": collections.Counter(p for r in rows for p in r["rosConflicted"])}, indent=1))
    elif mode == "replay":
        survey_rows = json.load(open(argv[3]))
        ids = argv[4].split(",")
        configure_driver(repo)
        with open(out, "a") as f:
            for row in (r for r in survey_rows if r["merge"] in ids or r["merge"][:8] in ids):
                rec = evaluate(repo, row)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                print(row["merge"][:8], "rosUnmerged", rec["rosUnmergedAfterDriver"], "lost", rec["cur"]["lost"], rec["evt"]["lost"],
                      "dup", rec["evt"]["duplicates"], rec["cur"]["duplicates"], "idsEq", rec["cur"]["idsEqualTeam"], rec["evt"]["idsEqualTeam"], flush=True)
    elif mode == "emit":
        # argv: repo emit OUTDIR P1 P2 -> writes the driver's merged current.json / events.jsonl
        configure_driver(repo)
        d = driver_merge(repo, argv[3], argv[4])
        os.makedirs(out, exist_ok=True)
        for path, text in d["texts"].items():
            open(os.path.join(out, os.path.basename(path)), "w").write(text or "")
        print(json.dumps({k: v for k, v in d.items() if k != "texts"}))
    elif mode == "sample":
        rows = json.load(open(argv[2]))
        print(",".join(sample([r["merge"] for r in rows if r["rosConflicted"]], int(argv[3]), int(argv[4]))))


if __name__ == "__main__":
    main(sys.argv[1:])
