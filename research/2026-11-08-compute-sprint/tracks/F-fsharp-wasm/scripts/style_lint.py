"""Candidate automatic styling rules for Forma-based apps, measured over app-owned CSS.

Usage: python3 style_lint.py OUT.json LABEL=FILE[,FILE...] ...
Rules (each derived from a defect class in data/curated-ui-defects.jsonl):
  raw-color        colour literal (#hex, rgb(), hsl()) in a declaration that is not a custom-property definition
                   -> contrast-and-theme (app colours bypass Forma's contrast-checked tokens)
  focus-suppressed outline: none|0 in a rule whose selector is not :focus-visible-specific -> focus-management
  hidden-control   opacity: 0 / visibility: hidden on input/select/radio/checkbox selectors -> focus-management (causa 3ae3ac9)
  px-font-size     font-size in px (does not scale with user text size) -> responsive-target-size / 200% text
  forma-override   app rule whose selector targets a Forma .ef-* class -> component contract drift
  important        !important -> cascade fights with Forma
  fixed-measure    max-inline-size/max-width in ch below 30 on headings -> R3 96c8175 headline measure
A count is a lint candidate, not a confirmed defect.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def rules(css: str):
    """Yield (selector, declarations) pairs, flattening @media/@layer wrappers (pure, approximate)."""
    for sel, body in RULE.findall(strip_comments(css)):
        sel = sel.strip().split("{")[-1].strip()
        if sel and not sel.startswith("@"):
            yield sel, [d.strip() for d in body.split(";") if ":" in d]


def lint(css: str) -> dict[str, int]:
    counts = dict.fromkeys(["raw-color", "focus-suppressed", "hidden-control", "px-font-size", "forma-override", "important", "fixed-measure", "rules"], 0)
    for sel, decls in rules(css):
        counts["rules"] += 1
        if ".ef-" in sel:
            counts["forma-override"] += 1
        for d in decls:
            prop, _, val = d.partition(":")
            prop, val = prop.strip().lower(), val.strip().lower()
            if not prop.startswith("--") and COLOR.search(val):
                counts["raw-color"] += 1
            if prop == "outline" and re.match(r"^(none|0)\b", val) and ":focus-visible" not in sel:
                counts["focus-suppressed"] += 1
            if ((prop == "opacity" and re.match(r"^0(\.0+)?$", val)) or (prop == "visibility" and val == "hidden")) and re.search(r"input|select|radio|checkbox", sel):
                counts["hidden-control"] += 1
            if prop == "font-size" and re.search(r"\d+px", val):
                counts["px-font-size"] += 1
            if "!important" in val:
                counts["important"] += 1
            if prop in ("max-inline-size", "max-width") and re.search(r"h[1-6]|title|heading", sel):
                m = re.search(r"(\d+(?:\.\d+)?)ch", val)
                if m and float(m.group(1)) < 30:
                    counts["fixed-measure"] += 1
    return counts


def main() -> None:
    out, specs = sys.argv[1], sys.argv[2:]
    result = {}
    for spec in specs:
        label, files = spec.split("=", 1)
        css = "\n".join(Path(f).read_text(encoding="utf-8") for f in files.split(",") if f)
        result[label] = {"files": files.count(",") + 1, "bytes": len(css), **lint(css)}
    Path(out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    for k, v in result.items():
        print(k, v)


if __name__ == "__main__":
    main()
