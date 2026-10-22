#!/usr/bin/env python3
"""REL-001 run-02: render AGENT_BRIEF.md from the committed templates in briefs/.

usage: python3 -I render-brief.py VALUES.json TEMPLATE... > AGENT_BRIEF.md
Each {{NAME}} is replaced by VALUES[NAME]. A line that is only a placeholder whose value
is empty is dropped. An unknown placeholder is an error (no brief is written half-filled).
"""
import json
import re
import sys

PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def render_line(values, line):
    names = PLACEHOLDER.findall(line)
    missing = [n for n in names if n not in values]
    if missing:
        raise SystemExit(f"unknown placeholder(s) {missing}")
    if names and line.strip() == "{{%s}}" % names[0] and values[names[0]] == "":
        return None
    return PLACEHOLDER.sub(lambda m: values[m.group(1)], line)


def render(values, text):
    lines = (render_line(values, l) for l in text.splitlines(keepends=True))
    return "".join(l for l in lines if l is not None)


def main(argv):
    values = json.load(open(argv[1]))
    sys.stdout.write("".join(render(values, open(t).read()) for t in argv[2:]))


if __name__ == "__main__":
    main(sys.argv)
