"""Repository access preflight for the 2026-11-08 compute sprint.

Functional core: pure data (REPO_TABLE), pure classification and rendering.
Imperative shell: git ls-remote / blobless clone probes and file output in main().
gh is used for search only (environment policy); metadata comes from search results.
"""
from __future__ import annotations
import json, subprocess, sys, re, datetime as dt
from dataclasses import dataclass, asdict, field, replace
from typing import Optional, Sequence, Mapping
from concurrent.futures import ThreadPoolExecutor

OWNER = "kemiller2002"

# (name, assigned tracks, priority 1=highest, dependencies, category)
REPO_TABLE: tuple[tuple[str, str, int, str, str], ...] = (
    ("cohort-based-engineering", "RD,D,H", 1, "praxis,ordo,dokimos,research-documents", "research-home"),
    ("Indy-init", "B,A,E", 1, "causa,indy-init-rehearsal-*", "competition"),
    *tuple((f"indy-init-rehearsal-{i:03d}", "B,A,F,E", 1, "praxis,conditor,forma,limen,aegis,Indy-init", "rehearsal") for i in range(1, 11)),
    ("causa", "B,F", 1, "praxis,forma,limen,conditor", "competition"),
    ("causa-data", "B", 2, "causa", "competition"),
    ("causa-acceptance-r10", "B,E", 1, "Indy-init,indy-init-rehearsal-010", "competition"),
    ("causa-testing-repo", "B,E", 3, "causa", "experiment"),
    ("causa-write-test", "B,E", 3, "causa", "experiment"),
    ("gate-proof-r10", "B,E", 2, "indy-init-rehearsal-010", "experiment"),
    ("Indy-init-audits", "B,E", 1, "Indy-init", "competition"),
    ("research-documents", "D,A,H", 1, "cohort-based-engineering", "research-archive"),
    ("praxis", "C,A,E", 1, "dokimos,conditor,echelon-registry", "system"),
    ("ordo", "C,D", 1, "praxis,dokimos", "system"),
    ("dokimos", "C,E,D", 1, "praxis", "system"),
    ("conditor", "C,E", 1, "echelon-registry,praxis", "system"),
    ("echelon-registry", "C", 2, "", "system"),
    ("aegis", "C,E", 2, "", "system"),
    ("vigila", "C,E", 3, "", "system"),
    ("tutela", "C", 3, "", "system"),
    ("vitium", "C", 3, "", "system"),
    ("fides", "C,E", 3, "", "system"),
    ("iter", "C", 3, "", "system"),
    ("arca", "C", 3, "", "system"),
    ("percepta", "C,F", 2, "forma", "system"),
    ("limen", "C,F", 1, "", "system"),
    ("forma", "C,F", 1, "", "system"),
    ("forma-studio", "C,F", 2, "forma", "system"),
    ("folio", "C,F", 2, "forma", "system"),
    ("specula", "C,F", 3, "", "system"),
    ("signal", "C,F", 2, "praxis,forma,limen,aegis", "system"),
    ("mercatus", "G,C", 1, "praxis", "system"),
    ("observer", "C", 3, "", "system"),
    ("census", "C", 3, "", "system"),
    ("summa", "C", 3, "", "system"),
    ("chrona", "C", 3, "", "system"),
    ("tekmerion", "C", 3, "", "system"),
    ("strata", "C", 3, "", "system"),
    ("armamentarium", "C", 3, "", "system"),
    ("echelon-diagnostic-framework", "C", 3, "", "system"),
    ("echelon-engineering-system", "C", 2, "", "system"),
    ("echelon-foundry", "G,C", 2, "", "system"),
    ("time-tracking-application", "A,D", 2, "praxis", "experiment"),
    ("time-entry-state-machine", "D", 2, "praxis", "experiment"),
    ("time-tracking-data", "A", 2, "praxis", "experiment"),
    ("construct-010-trials", "D", 3, "", "experiment"),
    ("SDE-Engineering-Trial-1-Greenfield-Construction", "D,B", 3, "ordo", "experiment"),
    ("SDE-Engineering-Trial-2-Greenfield-Construction", "D,B", 3, "ordo", "experiment"),
    ("disposable-test-repository", "E", 3, "", "experiment"),
    ("ROS-WorkerDaemon", "C", 3, "praxis", "system"),
    ("framework-engineering", "C", 3, "", "method"),
    ("visual-engineering", "F", 3, "forma", "method"),
    ("application-visual-language", "F", 3, "forma", "method"),
    ("sales-and-marketing", "G", 2, "", "commercial"),
    ("echelon-organization-administration", "G", 3, "", "commercial"),
    ("millers-Indy", "B", 3, "", "competition"),
    ("holiday-list-creator", "B", 3, "", "experiment"),
    ("holiday-list", "B", 3, "", "experiment"),
)

# Names referenced in manifests that are not current repository names (rename aliases).
ALIASES: tuple[str, ...] = ("Repository-Operating-System", "repository-operating-system", "state-directed-engineering",
                            "echelon-signal", "echelon-design-system", "research-publisher",
                            "consulting-company", "echelon-print-components")

SESSION_SCOPE = frozenset({"mercatus", "indy-init", *(f"indy-init-rehearsal-{i:03d}" for i in range(1, 11)), "praxis", "ordo",
                           "time-tracking-application", "time-entry-state-machine", "time-tracking-data", "signal",
                           "cohort-based-engineering"})

# Private repositories attached mid-session for READ via add_repo (2026-11-08 ~13:55 EST); not push-scoped.
ATTACHED_READ = frozenset({"research-documents", "causa-acceptance-r10", "indy-init-audits"})

@dataclass(frozen=True)
class Probe:
    head_ok: bool
    default_branch: Optional[str]
    head_sha: Optional[str]
    latest_tag: Optional[str]
    files_ok: bool
    files_sample: tuple[str, ...]
    error: Optional[str]

@dataclass(frozen=True)
class Record:
    canonical: str
    url: str
    default_branch: Optional[str]
    revision: Optional[str]
    visibility: Optional[str]
    archived: Optional[bool]
    read_permission: Optional[bool]
    write_permission_github: Optional[bool]
    write_in_session_scope: bool
    classification: str
    assigned_agents: str
    priority: int
    dependencies: str
    category: str
    latest_release_tag: Optional[str]
    open_prs: tuple[str, ...]
    files_retrieved: tuple[str, ...]
    access_problems: tuple[str, ...]

def classify(meta: Optional[Mapping], probe: Probe) -> str:
    """Pure classification. Missing != denied."""
    if probe.head_ok and probe.files_ok:
        perms = (meta or {}).get("permissions") or {}
        return "READ_WRITE" if perms.get("push") else ("READ_ONLY" if perms else "READ_ONLY")
    if probe.head_ok:
        return "UNKNOWN"  # refs readable but content retrieval failed
    err = (probe.error or "").lower()
    if meta is not None:
        return "ACCESS_DENIED" if (meta.get("permissions") or {}).get("pull") is False else "METADATA_ONLY"
    if "not found" in err or "repository not found" in err:
        return "NOT_FOUND"
    if "could not read username" in err or "403" in err or "authentication" in err:
        return "ACCESS_DENIED"
    return "UNKNOWN"

def problems(meta: Optional[Mapping], probe: Probe, cls: str, in_scope: bool) -> tuple[str, ...]:
    """Pure: human-readable access problems."""
    p = []
    if probe.error: p.append(f"git probe: {probe.error}")
    if meta is None: p.append("not returned by GitHub search (metadata unavailable via search)")
    if cls == "METADATA_ONLY": p.append("private repository not attached to this session; git read refused by proxy; remediation: add_repo (read)")
    if (meta or {}).get("permissions", {}).get("push") and not in_scope: p.append("GitHub reports push permission, but this session is not scoped to push here")
    if probe.files_sample == ("(empty repository: no commits)",): p.append("repository exists but is empty (no commits); nothing to research")
    return tuple(p)

def latest_semver(tags: Sequence[str]) -> Optional[str]:
    """Pure: highest semantic-version-looking tag (v-prefix allowed); None if none."""
    def key(t: str):
        m = re.match(r"^[^0-9]*(\d+)\.(\d+)\.(\d+)", t)
        return tuple(map(int, m.groups())) if m else None
    keyed = [(key(t), t) for t in tags if key(t) is not None]
    return max(keyed)[1] if keyed else None

def build_record(row, meta: Optional[Mapping], probe: Probe, prs: Sequence[Mapping]) -> Record:
    name, agents, prio, deps, cat = row
    in_scope = name.lower() in SESSION_SCOPE
    cls = classify(meta, probe)
    note = ("attached mid-session via add_repo (read) after initial METADATA_ONLY result",) if name.lower() in ATTACHED_READ else ()
    perms = (meta or {}).get("permissions") or {}
    return Record(
        canonical=f"{OWNER}/{(meta or {}).get('full_name', f'{OWNER}/{name}').split('/')[1]}",
        url=f"https://github.com/{OWNER}/{name}",
        default_branch=probe.default_branch or (meta or {}).get("default_branch"),
        revision=probe.head_sha,
        visibility=(meta or {}).get("visibility"),
        archived=(meta or {}).get("archived"),
        read_permission=perms.get("pull") if perms else (True if probe.head_ok else None),
        write_permission_github=perms.get("push") if perms else None,
        write_in_session_scope=in_scope,
        classification=cls,
        assigned_agents=agents, priority=prio, dependencies=deps, category=cat,
        latest_release_tag=probe.latest_tag,
        open_prs=tuple(f"#{p['number']} {'[draft] ' if p.get('draft') else ''}{p['title']}" for p in prs if p["repo"].lower() == name.lower()),
        files_retrieved=probe.files_sample,
        access_problems=note + problems(meta, probe, cls, in_scope),
    )

def render_md(records: Sequence[Record], aliases: Sequence[Mapping], now: str, excluded: int, org_note: str) -> str:
    """Pure: Markdown report."""
    counts = {}
    for r in records: counts[r.classification] = counts.get(r.classification, 0) + 1
    head = ["# Repository access preflight", "",
            f"**Run:** {now}. **Tool:** `inventory/preflight.py` (unit tests in `inventory/test_preflight.py`).",
            "**Method:** metadata and permissions from the GitHub search API (`gh api search/repositories`, the only gh use this environment permits); "
            "default branch and HEAD from `git ls-remote --symref`; content retrieval proven by a depth-1 blobless clone and `git ls-tree`; "
            "latest release approximated by highest semver git tag (GitHub Releases objects not queried here; Track C records releases); "
            "open PRs from `search/issues is:pr is:open`. No test pushes were made.", "",
            "**Classification counts:** " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), "",
            f"**Namespaces:** `kemiller2002` (searched; 197 repositories visible). {org_note}",
            f"Manifest scan of all local checkouts found no other Echelon owner (other owners are third-party dependencies).",
            f"{excluded} visible `kemiller2002` repositories were judged unrelated to Echelon (personal, talks, household) and excluded from the inventory; they are listed in REPOSITORY-ACCESS.json `excluded`.", "",
            "**Write permission** has two columns: what GitHub reports for the account, and whether this session is scoped to push. "
            "Specialists push nowhere; only the Research Director integrates, and only to `claude/echelon-compute-sprint-nov8-bkaw2t` in cohort-based-engineering.", "",
            "| Repository | Class | Vis. | Arch. | Default | Revision | Latest tag | GH push | Session push | Agents | Prio | Open PRs | Problems |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    rows = [f"| [{r.canonical}]({r.url}) | {r.classification} | {r.visibility or '?'} | {r.archived if r.archived is not None else '?'} | "
            f"{r.default_branch or '?'} | {(r.revision or '')[:9]} | {r.latest_release_tag or '—'} | {r.write_permission_github} | "
            f"{'yes' if r.write_in_session_scope else 'no'} | {r.assigned_agents} | {r.priority} | {len(r.open_prs)} | "
            f"{'; '.join(r.access_problems) or '—'} |" for r in records]
    alias = ["", "## Renamed repositories (manifest aliases resolved by HEAD SHA)", "",
             "| Referenced name | Resolves to | Evidence |", "|---|---|---|",
             *[f"| {a['alias']} | {a['resolves_to'] or 'UNRESOLVED'} | {a['evidence']} |" for a in aliases]]
    return "\n".join(head + rows + alias) + "\n"

# ---------------- imperative shell ----------------
def run(cmd: Sequence[str], timeout: int = 45) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(list(cmd), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", "timeout")

def probe(name: str, workdir: str) -> Probe:
    url = f"https://github.com/{OWNER}/{name}"
    h = run(["git", "ls-remote", "--symref", url, "HEAD"])
    if h.returncode != 0:
        return Probe(False, None, None, None, False, (), (h.stderr.strip().splitlines() or ["error"])[-1][:200])
    lines = h.stdout.splitlines()
    branch = next((l.split()[1].removeprefix("refs/heads/") for l in lines if l.startswith("ref:")), None)
    sha = next((l.split()[0] for l in lines if not l.startswith("ref:")), None)
    tags = run(["git", "ls-remote", "--tags", "--refs", url])
    tag = latest_semver([l.split("refs/tags/")[1] for l in tags.stdout.splitlines() if "refs/tags/" in l])
    dest = f"{workdir}/{name}"
    run(["rm", "-rf", dest])
    c = run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", url, dest], timeout=90)
    if c.returncode == 0 and "empty repository" in c.stderr:
        return Probe(True, branch, sha, tag, True, ("(empty repository: no commits)",), None)
    files = run(["git", "-C", dest, "ls-tree", "--name-only", "HEAD"]) if c.returncode == 0 else c
    sample = tuple(files.stdout.split()[:6]) if c.returncode == 0 else ()
    return Probe(True, branch, sha, tag, c.returncode == 0 and bool(sample), sample, None if c.returncode == 0 else c.stderr.strip()[-200:])

def main(search_path: str, prs_path: str, out_dir: str, workdir: str) -> int:
    search = {json.loads(l)["full_name"].split("/")[1].lower(): json.loads(l) for l in open(search_path) if l.strip()}
    prs = [json.loads(l) for l in open(prs_path) if l.strip()]
    names = [r[0] for r in REPO_TABLE]
    with ThreadPoolExecutor(6) as ex:
        probes = dict(zip(names, ex.map(lambda n: probe(n, workdir), names)))
        alias_probes = dict(zip(ALIASES, ex.map(lambda n: run(["git", "ls-remote", f"https://github.com/{OWNER}/{n}", "HEAD"]), ALIASES)))
    records = tuple(build_record(row, search.get(row[0].lower()), probes[row[0]], prs) for row in REPO_TABLE)
    by_sha = {r.revision: r.canonical for r in records if r.revision}
    def resolve(alias: str, res: subprocess.CompletedProcess) -> dict:
        sha = res.stdout.split()[0] if res.returncode == 0 and res.stdout else None
        return {"alias": f"{OWNER}/{alias}", "head": sha, "resolves_to": by_sha.get(sha),
                "evidence": f"ls-remote HEAD {sha[:9]} matches canonical HEAD" if sha in by_sha else
                            (f"ls-remote HEAD {sha[:9]} (redirect works; canonical repo not in inventory)" if sha else f"ls-remote failed: {res.stderr.strip()[-120:]}")}
    aliases = [resolve(a, alias_probes[a]) for a in ALIASES]
    inv = {n.lower() for n in names}
    excluded = sorted(v["full_name"] for k, v in search.items() if k not in inv)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).isoformat(timespec="seconds")
    org_note = ("`echelon-foundry` exists as a GitHub Organization (search/users), but `search/repositories q=org:echelon-foundry` returned HTTP 422 "
                "(\"cannot be searched either because the resources do not exist or you do not have permission\"): classified UNKNOWN — "
                "not evidence that it has no repositories. No manifest references it.")
    doc = {"schema": "echelon-sprint-repository-access/1", "generatedAt": now, "owner": OWNER,
           "namespaces": [{"name": "kemiller2002", "type": "User", "searched": True, "visibleRepositories": len(search)},
                          {"name": "echelon-foundry", "type": "Organization", "searched": True, "classification": "UNKNOWN", "note": org_note}],
           "repositories": [asdict(r) for r in records], "aliases": aliases, "excluded": excluded}
    json.dump(doc, open(f"{out_dir}/REPOSITORY-ACCESS.json", "w"), indent=2)
    open(f"{out_dir}/REPOSITORY-ACCESS.md", "w").write(render_md(records, aliases, now, len(excluded), org_note))
    print({k: sum(1 for r in records if r.classification == k) for k in {r.classification for r in records}})
    return 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
