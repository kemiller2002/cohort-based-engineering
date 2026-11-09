#!/usr/bin/env python3
"""Dependency-integrity inventory (read-only, working tree only).

Usage: python3 -I supply_chain.py OUT.json REPO_DIR [REPO_DIR ...]
Per repo: NuGet config sources and whether packageSourceMapping exists; .NET projects with floating
or ranged PackageReference versions; whether NuGet lock files are enabled/present; npm manifests with
range specifiers and whether a lockfile sits beside them; global.json SDK rollForward.
"""
import json
import re
import sys
from pathlib import Path

PKGREF = re.compile(r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"', re.I)
SKIP = {"node_modules", ".git", "bin", "obj", "vendor", "archive", "dist"}


def is_floating_nuget(version: str) -> bool:
    return "*" in version or version.startswith(("[", "(")) and "," in version


def is_range_npm(spec: str) -> bool:
    return bool(re.match(r"^\s*(\^|~|>|<|\*|latest|x\b)", spec)) or spec.strip() in ("", "*")


def walk(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and not (SKIP & set(p.relative_to(root).parts)):
            yield p


def audit_repo(root: Path):
    files = list(walk(root))
    projs = [p for p in files if p.suffix in (".fsproj", ".csproj") or p.name == "Directory.Packages.props"]
    floating = [{"file": str(p.relative_to(root)), "package": n, "version": v}
                for p in projs for n, v in PKGREF.findall(p.read_text(errors="replace")) if is_floating_nuget(v)]
    props = [p for p in files if p.name in ("Directory.Build.props",) or p.suffix in (".fsproj", ".csproj")]
    lock_enabled = any("RestorePackagesWithLockFile" in p.read_text(errors="replace") for p in props)
    nuget_cfgs = [p for p in files if p.name.lower() == "nuget.config"]
    mapping = any("packageSourceMapping" in p.read_text(errors="replace") for p in nuget_cfgs)
    npm = []
    for pj in (p for p in files if p.name == "package.json"):
        try:
            d = json.loads(pj.read_text())
        except ValueError:
            continue
        deps = {**d.get("dependencies", {}), **d.get("devDependencies", {})}
        lock = any((pj.parent / n).exists() for n in ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml"))
        npm.append({"file": str(pj.relative_to(root)), "deps": len(deps),
                    "ranged": sorted(k for k, v in deps.items() if isinstance(v, str) and is_range_npm(v)),
                    "lockfile": lock})
    gj = root / "global.json"
    roll = json.loads(gj.read_text()).get("sdk", {}) if gj.exists() else None
    return {"projects": len(projs), "floating_nuget": floating,
            "nuget_lock_enabled": lock_enabled,
            "nuget_lock_files": sum(1 for p in files if p.name == "packages.lock.json"),
            "nuget_configs": [str(p.relative_to(root)) for p in nuget_cfgs], "source_mapping": mapping,
            "npm": npm, "global_json_sdk": roll}


def main(argv):
    out = {r: audit_repo(Path(r)) for r in argv[2:]}
    Path(argv[1]).write_text(json.dumps(out, indent=1))
    for r, a in out.items():
        print(f"{r}: proj={a['projects']} floating={len(a['floating_nuget'])} lockEnabled={a['nuget_lock_enabled']} "
              f"lockFiles={a['nuget_lock_files']} mapping={a['source_mapping']} "
              f"npm={[(n['file'], len(n['ranged']), n['lockfile']) for n in a['npm']][:3]} sdk={a['global_json_sdk']}")


if __name__ == "__main__":
    main(sys.argv)
