"""Mine rehearsal git history for F#/WASM/UI defect signals.

Usage: python3 mine_defects.py OUT.jsonl REPO_DIR [REPO_DIR ...]
Classification is keyword-based (see TAXONOMY) and is a screening heuristic, not a ground-truth label:
every row keeps the matched terms so a reviewer can audit it.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# category -> regex (case-insensitive). Order is irrelevant; a commit may match several.
TAXONOMY: dict[str, str] = {
    "fsharp-compile": r"\bFS\d{4}\b|does not compile|did not compile|compil(e|ation) error|type error|build (fix|break|broke|failure)|fix(es|ed)? the (site )?build|warnings? as errors|TreatWarningsAsErrors|nullness",
    "fsharp-file-order": r"compile order|<Compile Include|file order|fsproj order",
    "build-stale-or-race": r"stale (build )?output|build race|incremental|--no-incremental|--no-build|bin/ and obj/|stale",
    "sdk-toolchain-pin": r"global\.json|rollForward|roll-forward|SDK 10\.|pinned SDK|install the (pinned )?\.?NET SDK",
    "wasm-runtime": r"\bwasm\b|webassembly|dotnet\.js|_framework|interpreter|tier-up|\bAOT\b|trimm|ILLink|JSExport|JSImport",
    "wasm-startup": r"WASM-LOAD|boot shell|loading status|start(up)? (time|timeout|deadline)|could not start|engine start",
    "limen-binding": r"\blimen\b|data-bind|data-text|data-if|BrowserKernel|binding grammar|capabilit(y|ies)",
    "forma-component": r"\bforma\b|\bef-[a-z]|design-system|layout kit",
    "folio-print": r"\bfolio\b|print(-components| view| presentation|able)|@media print",
    "a11y-contrast": r"contrast",
    "a11y-focus-keyboard": r"focus|keyboard|tab order|skip link|tabindex",
    "a11y-aria-semantics": r"\baria-|screen reader|role=|accessible name|landmark|axe|wcag|a11y|accessib",
    "a11y-motion-resize": r"reduced motion|prefers-reduced|200% text|text-resize|reflow|target size",
    "ui-layout-css": r"\bcss\b|layout|spacing|wrap(ped|s)? |measure|phone width|mobile|ipad|viewport|overflow|responsive",
    "ui-copy-state": r"copy (fix|says)|plain-language|wording|label(s)? |placeholder|empty state|lozenge|status text",
    "ui-template-dom": r"template|two root|root element|MutationObserver|hidden attribute|duplicate (section )?nav",
    "playwright-test": r"playwright|browser (suite|test|spec)|\.spec\.|flak|retry|timeout|port",
    "ci-pipeline": r"\bCI\b|workflow|pipefail|tee |actions|runner",
    "security-token": r"token|credential|secret|PAT\b",
}
FIX_HINT = re.compile(r"\bfix|defect|regress|bug|broke|wrong|fail(ed|s|ing)?\b|repair|correct", re.I)
COMPILED = {k: re.compile(v, re.I) for k, v in TAXONOMY.items()}
SEP = "\x1e"


def classify(text: str) -> dict[str, list[str]]:
    """Map each matching category to the distinct terms that matched (lower-cased, max 5)."""
    out = {}
    for cat, rx in COMPILED.items():
        hits = sorted({m.group(0).lower().strip() for m in rx.finditer(text)})
        if hits:
            out[cat] = hits[:5]
    return out


def file_kinds(files: list[str]) -> dict[str, int]:
    kinds: dict[str, int] = {}
    for f in files:
        k = ("spec" if re.search(r"\.spec\.(m?js|ts)$", f) else Path(f).suffix.lstrip(".") or "none")
        kinds[k] = kinds.get(k, 0) + 1
    return kinds


def parse_log(raw: str) -> list[dict]:
    """Parse `git log --format=<SEP>%H%x1f%aI%x1f%s%x1f%b%x1f --name-only` output."""
    commits = []
    for chunk in raw.split(SEP)[1:]:
        parts = chunk.split("\x1f")
        if len(parts) < 5:
            continue
        sha, date, subject, body, rest = parts[0], parts[1], parts[2], parts[3], parts[4]
        names = [l for l in rest.splitlines() if l.strip()]
        commits.append({"sha": sha, "date": date, "subject": subject, "body": body, "files": names})
    return commits


def to_row(repo: str, c: dict) -> dict:
    text = c["subject"] + "\n" + c["body"]
    cats = classify(text)
    return {"source": f"git:{repo}@{c['sha'][:12]}", "repo": repo, "sha": c["sha"], "date": c["date"],
            "subject": c["subject"][:240], "isFix": bool(FIX_HINT.search(text)), "isMerge": c["subject"].startswith("Merge"),
            "categories": sorted(cats), "matched": cats, "fileKinds": file_kinds(c["files"]), "filesChanged": len(c["files"])}


def git_log(repo_dir: Path) -> str:
    fmt = SEP + "%H%x1f%aI%x1f%s%x1f%b%x1f"
    return subprocess.run(["git", "-C", str(repo_dir), "log", "--no-renames", f"--format={fmt}", "--name-only"],
                          capture_output=True, text=True, check=True).stdout


def main() -> None:
    out, repos = sys.argv[1], sys.argv[2:]
    rows = [to_row(Path(r).name, c) for r in repos for c in parse_log(git_log(Path(r)))]
    with open(out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} commits from {len(repos)} repos -> {out}")


if __name__ == "__main__":
    main()
