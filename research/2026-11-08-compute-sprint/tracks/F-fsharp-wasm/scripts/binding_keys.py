"""Heuristic HTML-binding vs F#-projection key comparison for Limen apps (static, no build needed).

Usage: python3 binding_keys.py LABEL HTML_FILE_OR_DIR FSHARP_SRC_DIR > out.json
Top-level view keys are dotted names (e.g. "settings.heading"); item fields inside data-each rows are not compared.
F# keys are dotted string literals in the projection sources. Keys built at run time (sprintf, string concatenation)
are invisible to this scan, so 'boundNotProjected' over-reports and is a candidate list, not a defect list.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BINDING = re.compile(r'data-(text|if|each|bind-[a-z-]+|event)="([^"]+)"')
DOTTED = re.compile(r'^[a-z][a-z0-9-]*(\.[a-z0-9-]+)+$')
FS_LITERAL = re.compile(r'"([a-z][a-z0-9-]*(?:\.[a-z0-9-]+)+)"')
FS_PREFIX = re.compile(r'"([a-z][a-z0-9-]*(?:\.[a-z0-9-]+)*\.)"')


def html_keys(html: str) -> dict[str, set[str]]:
    """Dotted keys per binding kind (pure)."""
    out: dict[str, set[str]] = {}
    for kind, key in BINDING.findall(html):
        if DOTTED.match(key):
            out.setdefault("event" if kind == "event" else "view", set()).add(key)
    return out


def fs_keys(sources: list[str]) -> tuple[set[str], set[str]]:
    """Dotted string literals and dotted prefixes ("workspace.") found in F# sources (pure)."""
    lits, prefixes = set(), set()
    for s in sources:
        lits |= set(FS_LITERAL.findall(s))
        prefixes |= set(FS_PREFIX.findall(s))
    return lits, prefixes


def compare(html: dict[str, set[str]], lits: set[str], prefixes: set[str]) -> dict:
    view = html.get("view", set())
    covered = lambda k: k in lits or any(k.startswith(p) for p in prefixes)
    bound_not_projected = sorted(k for k in view if not covered(k))
    events = html.get("event", set())
    return {"htmlViewKeys": len(view), "htmlEventKeys": len(events), "fsDottedLiterals": len(lits), "fsDynamicPrefixes": sorted(prefixes),
            "boundNotProjected": bound_not_projected, "eventsNotInFs": sorted(k for k in events if not covered(k)),
            "projectedNotBound": sorted(k for k in lits if k not in view and k not in events)}


def main() -> None:
    label, html_path, fs_dir = sys.argv[1:4]
    p = Path(html_path)
    html = "\n".join(f.read_text(encoding="utf-8") for f in ([p] if p.is_file() else sorted(p.rglob("*.html"))))
    sources = [f.read_text(encoding="utf-8") for f in sorted(Path(fs_dir).rglob("*.fs"))]
    lits, prefixes = fs_keys(sources)
    print(json.dumps({"label": label, **compare(html_keys(html), lits, prefixes)}, indent=1))


if __name__ == "__main__":
    main()
