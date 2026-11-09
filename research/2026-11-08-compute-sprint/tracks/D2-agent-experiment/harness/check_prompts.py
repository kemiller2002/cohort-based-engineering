"""Proves arm-prompts/G.txt == arm-prompts/M.txt plus exactly one inserted governance block.
Usage: python3 -I check_prompts.py   (exit 0 = PASS)."""
import difflib
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPTS = os.path.join(HERE, "..", "arm-prompts")
CONTRACT = ("Implement only behavior supported by requirements or accepted decisions. Do not invent exceptions, "
            "precedence rules, or business policies. Record unsupported interpretations as unresolved questions. "
            "Do not treat your own proposed decisions as authorized.")
CONTRACT_SHA256 = "2af405073b299f562a8321feac875d2b9a9ae6d94171475a59a60a416784862d"  # VAC-002 P3 frozen contract


def read(name):
    with open(os.path.join(PROMPTS, name), encoding="utf-8") as f:
        return f.read()


def inserted_blocks(m, g):
    ops = difflib.SequenceMatcher(a=m, b=g, autojunk=False).get_opcodes()
    return [(tag, m[i1:i2], g[j1:j2]) for tag, i1, i2, j1, j2 in ops if tag != "equal"]


def check(m, g):
    changes = inserted_blocks(m.splitlines(keepends=True), g.splitlines(keepends=True))
    block = "".join(changes[0][2]) if len(changes) == 1 else ""
    return [
        ("exactly one change", len(changes) == 1),
        ("change is a pure insertion", len(changes) == 1 and changes[0][0] == "insert"),
        ("block contains contract verbatim", CONTRACT in block),
        ("contract sha256 matches frozen VAC-002 P3 text",
         hashlib.sha256(CONTRACT.encode()).hexdigest() == CONTRACT_SHA256),
        ("block names QUESTIONS.md, EVIDENCE.md, requirement mapping",
         all(s in block for s in ("QUESTIONS.md", "EVIDENCE.md", "requirement ID"))),
        ("removing block from G yields M byte for byte", g.replace(block, "", 1) == m and bool(block)),
        ("both name {WS} placeholder", "{WS}" in m and "{WS}" in g),
        ("M has no governance words", not any(w in m for w in ("Authority", "QUESTIONS.md", "EVIDENCE.md"))),
    ]


if __name__ == "__main__":
    m, g = read("M.txt"), read("G.txt")
    results = check(m, g)
    print("\n".join("%s  %s" % ("PASS" if ok else "FAIL", name) for name, ok in results))
    print("sha256 M.txt", hashlib.sha256(m.encode()).hexdigest())
    print("sha256 G.txt", hashlib.sha256(g.encode()).hexdigest())
    print("unified diff:")
    sys.stdout.writelines(difflib.unified_diff(m.splitlines(True), g.splitlines(True), "M.txt", "G.txt"))
    sys.exit(0 if all(ok for _, ok in results) else 1)
