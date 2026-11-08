#!/usr/bin/env python3
"""Echelon architecture dependency extractor (Track C, compute sprint 2026-11-08).

Functional style: every parser is a pure function from text to data; IO is confined to
`read_repo_facts` and `main`. Repository content is treated as untrusted data: files are only
parsed (json / xml / regex), never executed.

Usage:
  python3 -I archgraph.py --repos-root /home/user/ext --extra /home/user/indy-init-rehearsal-010 \
      --registry /home/user/ext/echelon-registry --out ../data
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Mapping, Optional

EDGE_TYPES = ("package-ref", "CLI-invocation", "contract/schema", "doc-only-claim")

# ---------------------------------------------------------------- package -> system mapping

NPM_PACKAGE_SYSTEM = {
    "@echelon-foundry/design-system": "forma",
    "@echelon-foundry/forma-conformance": "forma",
    "@echelon-foundry/forma-workflow": "forma",
    "@echelon-foundry/forma-studio": "forma-studio",
    "@echelon-foundry/print-components": "folio",
    "@echelon-foundry/limen": "limen",
    "@echelon-foundry/sde": "ordo",
    "@echelon-foundry/percepta-repository-lifecycle": "percepta",
    "@echelon-foundry/research-publisher": "tekmerion",
    "@echelon-foundry/tutela": "tutela",
    "@echelon-foundry/repository-operating-system": "praxis",
}

# Conditor / Registry component ids that are not repository names.
REGISTRY_ID_SYSTEM = {
    "percepta-semantic": "percepta",
    "limen-fsharp": "limen",
    "summa-contracts": "summa",
    "forma-workflow": "forma",
}

SCHEMA_PREFIX_SYSTEM = {
    "praxis": "praxis", "ordo": "ordo", "dokimos": "dokimos", "conditor": "conditor",
    "aegis": "aegis", "percepta": "percepta", "tutela": "tutela", "limen": "limen",
    "forma": "forma", "causa": "causa", "summa": "summa", "arca": "arca", "fides": "fides",
}
REGISTRY_SCHEMAS = ("echelon.release", "echelon.profile", "echelon.catalog-snapshot",
                    "echelon.resolved-release-set", "echelon.current-channel", "echelon.release-set")

CLI_TOOLS = ("praxis", "dokimos", "conditor", "ordo", "percepta", "tutela", "sde", "ros")
CLI_TOOL_SYSTEM = {"sde": "ordo", "ros": "praxis"}


def nuget_package_system(package: str) -> Optional[str]:
    """EchelonFoundry.<System>[.Sub] -> lower-case system id; None for third-party packages."""
    m = re.match(r"^EchelonFoundry\.([A-Za-z]+)", package)
    return m.group(1).lower() if m else None


def npm_package_system(package: str) -> Optional[str]:
    return NPM_PACKAGE_SYSTEM.get(package)


def registry_id_system(component_id: str) -> str:
    return REGISTRY_ID_SYSTEM.get(component_id, component_id)


def schema_system(schema: str) -> Optional[str]:
    if schema.startswith(REGISTRY_SCHEMAS):
        return "echelon-registry"
    prefix = re.split(r"[./]", schema, maxsplit=1)[0]
    return SCHEMA_PREFIX_SYSTEM.get(prefix)


# ---------------------------------------------------------------- pure parsers

def parse_json(text: str) -> Optional[dict]:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except (ValueError, TypeError):
        return None


def parse_ros_installed(text: str) -> Optional[str]:
    """`.echelon/ros.json` installedVersion = the Praxis release a repository has installed."""
    data = parse_json(text) or {}
    return data.get("installedVersion")


def parse_ros_root(text: str) -> Optional[str]:
    """Root `ros.json` rosVersion (repository specification version; often stale)."""
    data = parse_json(text) or {}
    return data.get("rosVersion")


def parse_conditor(text: str) -> dict:
    data = parse_json(text) or {}
    authority = data.get("registryAuthority") or {}
    comps = tuple((c.get("id"), c.get("version")) for c in data.get("components", []) if isinstance(c, dict))
    return {"authorityKind": authority.get("kind"), "authoritySha256": authority.get("sha256"),
            "authorityPath": authority.get("path"), "components": comps}


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def parse_msbuild_items(text: str, item: str) -> tuple:
    """Returns ((Include, Version-or-None), ...) for an MSBuild item kind; tolerant of bad XML."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return tuple((m.group(1), m.group(2)) for m in re.finditer(
            rf'<{item}\s+Include="([^"]+)"(?:\s+Version="([^"]+)")?', text))
    return tuple((e.get("Include"), e.get("Version") or e.get("VersionOverride"))
                 for e in root.iter() if _strip_ns(e.tag) == item and e.get("Include"))


def parse_package_json(text: str) -> tuple:
    data = parse_json(text) or {}
    deps = {**(data.get("devDependencies") or {}), **(data.get("dependencies") or {})}
    return tuple(sorted(deps.items()))


def parse_nuget_sources(text: str) -> tuple:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return ()
    return tuple((e.get("key"), e.get("value")) for e in root.iter()
                 if _strip_ns(e.tag) == "add" and e.get("value"))


def version_from_npm_spec(spec: str) -> Optional[str]:
    """'0.9.1' -> 0.9.1; release-tarball URL '.../v0.4.1/x-0.4.1.tgz' -> 0.4.1; ranges keep digits."""
    m = re.search(r"/download/v?(\d+\.\d+\.\d+[^/]*)/", spec)
    if m:
        return m.group(1)
    m = re.search(r"(\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?)", spec)
    return m.group(1) if m else None


STOPWORDS = frozenset({"is", "the", "and", "or", "to", "in", "a", "it", "has", "will", "must", "version",
                       "release", "releases", "repository", "binary", "installs", "pins", "itself", "on", "for"})
SYSTEM_WORDS = frozenset({"limen", "aegis", "forma", "folio", "tutela", "arca", "fides", "strata", "summa"})

CLI_RE = re.compile(
    r"(?:^|[\s/\"'`(])(?:\./)?(" + "|".join(CLI_TOOLS) + r")(?:\.cmd|\.ps1)?\s+([a-z][a-z0-9-]+)")


def parse_cli_invocations(text: str) -> tuple:
    """(tool, subcommand) pairs on non-comment workflow lines that look like command execution."""
    found = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or re.match(r"^-?\s*(name|uses|description|if)\s*:", stripped):
            continue
        for m in CLI_RE.finditer(line):
            tool, sub = m.group(1), m.group(2)
            if sub in STOPWORDS or sub in CLI_TOOLS or sub in SYSTEM_WORDS or re.match(r"^v\d", sub):
                continue
            found.append((CLI_TOOL_SYSTEM.get(tool, tool), sub))
    return tuple(found)


USES_RE = re.compile(r"uses:\s*kemiller2002/([A-Za-z0-9_.-]+)(/[^@\s]*)?@(\S+)")


def parse_uses(text: str) -> tuple:
    return tuple((m.group(1), (m.group(2) or "").lstrip("/"), m.group(3)) for m in USES_RE.finditer(text))


SCHEMA_RE = re.compile(r'"(?:\$schema|schema)"\s*:\s*"([a-z][a-z0-9.-]*[./][^"]{0,80})"')


def parse_schema_refs(text: str) -> tuple:
    return tuple(sorted({m.group(1) for m in SCHEMA_RE.finditer(text)}))


def readme_mentions(text: str, systems: Iterable[str]) -> tuple:
    return tuple(sorted(s for s in systems if re.search(rf"\b{re.escape(s)}\b", text, re.IGNORECASE)))


# ---------------------------------------------------------------- semver helpers

def semver_key(v: str) -> tuple:
    core, _, pre = (v or "0").lstrip("v").partition("-")
    nums = tuple(int(x) if x.isdigit() else 0 for x in (core.split(".") + ["0", "0"])[:3])
    return nums + ((1,) if not pre else (0, pre))


def latest_version(tags: Iterable[str], prefix: str = "v") -> Optional[str]:
    vals = [t[len(prefix):] for t in tags if t.startswith(prefix) and re.match(r"\d+\.\d+\.\d+", t[len(prefix):])]
    return max(vals, key=semver_key) if vals else None


def skew_class(pinned: Optional[str], selected: Optional[str]) -> str:
    if not pinned or not selected:
        return "unknown"
    a, b = semver_key(pinned), semver_key(selected)
    if a == b:
        return "current"
    if a > b:
        return "ahead-of-approved-set"
    if a[0] != b[0]:
        return "major-behind"
    if a[1] != b[1]:
        return "minor-behind"
    return "patch-behind"


# ---------------------------------------------------------------- edge construction (pure)

def edge(src: str, dst: str, etype: str, via: str, evidence: str, version: Optional[str] = None) -> dict:
    assert etype in EDGE_TYPES
    return {"from": src, "to": dst, "type": etype, "via": via, "version": version, "evidence": evidence}


def edges_from_facts(repo: str, facts: Mapping, systems: frozenset) -> tuple:
    """Derive typed edges from one repository's parsed facts. Self-edges are dropped."""
    out = []
    for path, pkg, ver in facts.get("nugetRefs", ()):
        sysid = nuget_package_system(pkg)
        if sysid:
            out.append(edge(repo, sysid, "package-ref", f"nuget:{pkg}", path, ver))
    for path, pkg, spec in facts.get("npmRefs", ()):
        sysid = npm_package_system(pkg)
        if sysid:
            out.append(edge(repo, sysid, "package-ref", f"npm:{pkg}", path, version_from_npm_spec(spec)))
    for path, ref in facts.get("projectRefs", ()):
        m = re.search(r"(?:^|[\\/])\.\.[\\/]+(?:\.\.[\\/]+)*([A-Za-z0-9_.-]+)[\\/]", ref)
        if m and m.group(1).lower() in systems and m.group(1).lower() != repo:
            out.append(edge(repo, m.group(1).lower(), "package-ref", f"project:{ref}", path))
    cond = facts.get("conditor")
    if cond:
        out.append(edge(repo, "conditor", "contract/schema", "conditor.json", "conditor.json"))
        for cid, ver in cond["components"]:
            out.append(edge(repo, registry_id_system(cid), "contract/schema", f"conditor-pin:{cid}",
                            "conditor.json", ver))
        if cond.get("authoritySha256"):
            out.append(edge(repo, "echelon-registry", "contract/schema", "registry-authority",
                            "conditor.json", facts.get("authoritySet")))
    if facts.get("rosInstalled"):
        out.append(edge(repo, "praxis", "contract/schema", "ros-pin", ".echelon/ros.json", facts["rosInstalled"]))
    if facts.get("limenConfig"):
        out.append(edge(repo, "limen", "contract/schema", "limen.config.json", "limen.config.json"))
    if facts.get("aegisBoundaries"):
        out.append(edge(repo, "aegis", "contract/schema", "aegis-boundaries.json", "aegis-boundaries.json"))
    for path, schema in facts.get("schemaRefs", ()):
        sysid = schema_system(schema)
        if sysid:
            out.append(edge(repo, sysid, "contract/schema", f"schema:{schema}", path))
    for path, tool, sub in facts.get("cliCalls", ()):
        out.append(edge(repo, tool, "CLI-invocation", f"{tool} {sub}", path))
    for path, target, sub, ref in facts.get("usesRefs", ()):
        out.append(edge(repo, target.lower(), "CLI-invocation", f"uses:{target}/{sub}@{ref}", path))
    concrete = {e["to"] for e in out}
    for mention in facts.get("readmeMentions", ()):
        if mention not in concrete:
            out.append(edge(repo, mention, "doc-only-claim", "README mention without code/config edge", "README.md"))
    return tuple(e for e in out if e["to"] != repo)


def collapse_edges(edges: Iterable[dict]) -> tuple:
    """One aggregated edge per (from,to,type) with its distinct vias, versions and evidence."""
    groups: dict = {}
    for e in edges:
        k = (e["from"], e["to"], e["type"])
        g = groups.setdefault(k, {"from": k[0], "to": k[1], "type": k[2], "vias": set(), "versions": set(),
                                  "evidence": set(), "count": 0})
        g["vias"].add(e["via"])
        if e["version"]:
            g["versions"].add(e["version"])
        g["evidence"].add(e["evidence"])
        g["count"] += 1
    return tuple({**g, "vias": sorted(g["vias"])[:12], "versions": sorted(g["versions"], key=semver_key),
                  "evidence": sorted(g["evidence"])[:8]} for g in sorted(groups.values(),
                  key=lambda g: (g["from"], g["to"], g["type"])))


def pin_skew(edges: Iterable[dict], approved: Mapping[str, str]) -> tuple:
    """Version pins (conditor-pin, ros-pin, package-ref) compared with the approved release set."""
    rows = []
    for e in edges:
        if not e["version"] or e["via"] == "registry-authority":
            continue
        is_pin = e["via"].startswith(("conditor-pin:", "ros-pin", "nuget:", "npm:"))
        if not is_pin:
            continue
        key = e["via"].split(":", 1)[1] if e["via"].startswith("conditor-pin:") else e["to"]
        if e["via"].startswith("nuget:EchelonFoundry.Limen") or e["via"] == "npm:@echelon-foundry/limen":
            key = "limen-fsharp" if e["via"].startswith("nuget:") else "limen"
        if e["via"].startswith("nuget:EchelonFoundry.Summa"):
            key = "summa-contracts"
        selected = approved.get(key)
        rows.append({"consumer": e["from"], "component": key, "via": e["via"], "pinned": e["version"],
                     "approved": selected, "skew": skew_class(e["version"], selected), "evidence": e["evidence"]})
    return tuple(sorted(rows, key=lambda r: (r["consumer"], r["component"], r["via"])))


def to_dot(nodes: Iterable[dict], edges: Iterable[dict]) -> str:
    style = {"package-ref": 'color="#1f6feb"', "CLI-invocation": 'color="#2da44e",style=bold',
             "contract/schema": 'color="#8250df",style=dashed', "doc-only-claim": 'color="#999999",style=dotted'}
    lines = ["digraph echelon {", '  rankdir=LR; node [shape=box,fontname="Helvetica"];']
    for n in nodes:
        shape = "ellipse" if n.get("kind") == "referenced-only" else "box"
        lines.append(f'  "{n["id"]}" [shape={shape},label="{n["id"]}\\n{n.get("release") or "-"}"];')
    for e in edges:
        label = ",".join(e["versions"][:2]) if e["versions"] else ""
        lines.append(f'  "{e["from"]}" -> "{e["to"]}" [{style[e["type"]]},label="{label}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- IO

def keep_path(p: str) -> bool:
    """Exclude vendored, fixture and research-evidence copies: they are not the repository's own dependencies."""
    return ("node_modules/" not in p and "/vendor/" not in p and "/fixtures/" not in p and "/testdata/" not in p
            and not p.startswith(("vendor/", "research/", "fixtures/", "testdata/")))


def git_files(repo: Path, patterns: Iterable[str]) -> list:
    try:
        out = subprocess.run(["git", "-C", str(repo), "ls-files", "--", *patterns],
                             capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return []
    return [p for p in out.splitlines() if keep_path(p)]


def read(repo: Path, rel: str) -> str:
    try:
        return (repo / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def read_repo_facts(repo: Path, systems: frozenset, set_by_sha: Mapping[str, str]) -> dict:
    nuget, npm, projrefs = [], [], []
    for rel in git_files(repo, ["*Directory.Packages.props", "*.fsproj", "*.csproj"]):
        text = read(repo, rel)
        nuget += [(rel, p, v) for p, v in parse_msbuild_items(text, "PackageVersion")]
        nuget += [(rel, p, v) for p, v in parse_msbuild_items(text, "PackageReference")]
        projrefs += [(rel, p) for p, _ in parse_msbuild_items(text, "ProjectReference")]
    for rel in git_files(repo, ["package.json", "*/package.json"]):
        npm += [(rel, p, s) for p, s in parse_package_json(read(repo, rel))]
    cond_text = read(repo, "conditor.json")
    cond = parse_conditor(cond_text) if cond_text else None
    auth_text = read(repo, cond["authorityPath"]) if cond and cond.get("authorityPath") else ""
    auth = parse_json(auth_text) or {}
    authority_set = (auth.get("profile") or {}).get("version") or (set_by_sha.get(cond["authoritySha256"]) if cond else None)
    cli, uses = [], []
    for rel in git_files(repo, [".github/workflows/*.yml", ".github/workflows/*.yaml", ".github/actions/*/action.yml"]):
        text = read(repo, rel)
        cli += [(rel, t, s) for t, s in parse_cli_invocations(text)]
        uses += [(rel, *u) for u in parse_uses(text)]
    schema_refs = []
    for rel in git_files(repo, ["*.json"])[:4000]:
        if rel.startswith((".ros/", ".praxis/", "registries/", "generated/", "telemetry/")):
            continue
        schema_refs += [(rel, s) for s in parse_schema_refs(read(repo, rel)[:200000])]
    head = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%H %cs"], capture_output=True,
                          text=True).stdout.split()
    return {
        "head": head[0] if head else None, "headDate": head[1] if len(head) > 1 else None,
        "nugetRefs": tuple(nuget), "npmRefs": tuple(npm), "projectRefs": tuple(projrefs),
        "nugetSources": parse_nuget_sources(read(repo, "NuGet.config") or read(repo, "nuget.config")),
        "conditor": cond, "authoritySet": authority_set,
        "rosInstalled": parse_ros_installed(read(repo, ".echelon/ros.json")),
        "rosRootVersion": parse_ros_root(read(repo, "ros.json")),
        "limenConfig": bool(read(repo, "limen.config.json")),
        "aegisBoundaries": bool(read(repo, "aegis-boundaries.json")),
        "schemaRefs": tuple(schema_refs), "cliCalls": tuple(cli), "usesRefs": tuple(uses),
        "readmeMentions": readme_mentions(read(repo, "README.md"), systems - {repo.name}),
    }


def sets_by_sha(registry: Path) -> dict:
    """Map sha256 of each resolved-release-set file the Registry ships to its profile version."""
    out = {}
    for p in registry.glob("resolved/**/*.json"):
        data = parse_json(p.read_text(errors="replace")) or {}
        ver = (data.get("profile") or {}).get("version")
        if ver:
            out[hashlib.sha256(p.read_bytes()).hexdigest()] = f'{(data.get("profile") or {}).get("id")}@{ver}'
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos-root", required=True)
    ap.add_argument("--repos", nargs="+", required=True)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--registry", required=True)
    ap.add_argument("--approved-set", required=True)
    ap.add_argument("--latest", required=True, help="json {system: {version, source, date}}")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root, out = Path(a.repos_root), Path(a.out)
    repo_paths = [root / r for r in a.repos] + [Path(x) for x in a.extra]
    systems = frozenset(p.name for p in repo_paths)
    by_sha = sets_by_sha(Path(a.registry))
    facts = {p.name: read_repo_facts(p, systems, by_sha) for p in repo_paths if p.exists()}
    raw = tuple(e for name, f in facts.items() for e in edges_from_facts(name, f, systems))
    approved_doc = json.loads(Path(a.approved_set).read_text())
    approved = {c["systemId"]: c["version"] for c in approved_doc["components"]}
    latest = json.loads(Path(a.latest).read_text())
    collapsed = collapse_edges(raw)
    node_ids = sorted(set(facts) | {e["to"] for e in collapsed})
    nodes = [{"id": n, "kind": "repository" if n in facts else "referenced-only",
              "head": (facts.get(n) or {}).get("head"), "release": (latest.get(n) or {}).get("version"),
              "approvedInSet": {k: v for k, v in approved.items() if registry_id_system(k) == n} or None}
             for n in node_ids]
    graph = {"schema": "track-c.dependency-graph/1", "approvedSet": f'echelon-current@{approved_doc["profile"]["version"]}',
             "edgeTypes": list(EDGE_TYPES), "nodes": nodes, "edges": list(collapsed)}
    out.mkdir(parents=True, exist_ok=True)
    (out / "dependency-graph.json").write_text(json.dumps(graph, indent=1, sort_keys=False) + "\n")
    (out / "dependency-graph.dot").write_text(to_dot(nodes, [e for e in collapsed if e["type"] != "doc-only-claim"]))
    (out / "pin-skew.json").write_text(json.dumps(list(pin_skew(raw, approved)), indent=1) + "\n")
    (out / "repo-facts.json").write_text(json.dumps(
        {k: {**v, "schemaRefs": sorted({s for _, s in v["schemaRefs"]}),
             "cliCalls": sorted({f"{t} {s}" for _, t, s in v["cliCalls"]})} for k, v in facts.items()},
        indent=1, default=list) + "\n")


if __name__ == "__main__":
    main()
