#!/usr/bin/env python3
"""ARCH-001 change-set scrubber for the blinded review (new).

usage: python3 -I review-scrub.py REPO FROM TO OUT.patch LABEL

Writes `git diff FROM TO` with a fixed, deterministic format (no colour, no renames, Myers, 3 lines of context,
path order), excluding docs/architecture/ and docs/contracts/, and scrubbed of arm signals:
  * `index <blob>..<blob>` lines are dropped;
  * decision ids (DEC-...) become DECISION-REF everywhere (comments, test names, strings);
  * in code comments (// ..., (* ... *), /// ...) and in Markdown lines, the words ARCH001, ordo, archcheck,
    submit, arm, contract, verifier and rule ids (ARC-XXX-nn) (any case) become [redacted];
  * ARCH001 and archcheck are redacted everywhere.
The first line is the neutral LABEL; no commit message, author or date appears.
"""
import re
import subprocess
import sys

EXCLUDE = [":(exclude)docs/architecture", ":(exclude)docs/contracts"]
DEC = re.compile(r"\bDEC-[A-Za-z0-9][A-Za-z0-9-]*")
WORDS = re.compile(r"\b(?:ARCH001|ARCH-001|ordo|archcheck|submit(?:ted|s|ting)?|arms?|contracts?|verifier|ARC-[A-Z]{3}-\d\d)\b", re.IGNORECASE)
ALWAYS = re.compile(r"\b(?:ARCH001|ARCH-001|archcheck)\b", re.IGNORECASE)
COMMENT = re.compile(r"(//.*$|\(\*.*?(?:\*\)|$))")


def raw_diff(repo, a, b):
    cmd = ["git", "-C", repo, "-c", "core.quotepath=false", "diff", "--no-color", "--no-ext-diff", "--no-renames",
           "--diff-algorithm=myers", "-U3", "--src-prefix=a/", "--dst-prefix=b/", a, b, "--", ".", *EXCLUDE]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def scrub_line(line, markdown):
    if line.startswith("index "):
        return None
    line = DEC.sub("DECISION-REF", line)
    line = ALWAYS.sub("[redacted]", line)
    if line[:1] in "+- " and not line.startswith(("+++", "---")):
        if markdown:
            return line[0] + WORDS.sub("[redacted]", line[1:])
        return COMMENT.sub(lambda m: WORDS.sub("[redacted]", m.group(0)), line)
    return line


def scrub(text):
    out, markdown = [], False
    for line in text.splitlines():
        if line.startswith("diff --git "):
            markdown = line.endswith(".md")
        s = scrub_line(line, markdown)
        if s is not None:
            out.append(s)
    return "\n".join(out) + ("\n" if out else "")


def main(argv):
    repo, a, b, out, label = argv[1:6]
    body = scrub(raw_diff(repo, a, b))
    with open(out, "w") as f:
        f.write(f"# {label}\n" + (body if body else "# (no changes)\n"))


if __name__ == "__main__":
    main(sys.argv)
