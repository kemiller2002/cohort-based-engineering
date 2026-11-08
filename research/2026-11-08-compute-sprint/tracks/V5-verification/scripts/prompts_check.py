"""Check that X-03 arm prompts = frozen M.txt + exactly one section of the frozen G block, inserted before the 'Task:' line.

Usage: python3 -I -B scripts/prompts_check.py OUT.json   (pure functions below; IO only in __main__)
"""
import hashlib
import json
import sys

T = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment"
G_SHA = "9e6b22568c8045f6695b54ce32d69379988ac9825dc192f02fff1fd2b79ce309"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def g_block(m_text, g_text):
    """The block = G with M's lines removed, as a contiguous insertion. Returns (block, insert_line_index_in_M)."""
    m, g = m_text.splitlines(keepends=True), g_text.splitlines(keepends=True)
    i = next((k for k in range(len(m)) if m[k] != g[k]), len(m))
    extra = len(g) - len(m)
    if extra <= 0 or g[:i] + g[i + extra:] != m:
        raise ValueError("G is not M plus one contiguous insertion")
    return "".join(g[i:i + extra]), i


def sections(block):
    """Split the block into '## ' sections, each keeping its trailing blank line(s)."""
    out, cur = [], []
    for ln in block.splitlines(keepends=True):
        if ln.startswith("## ") and cur:
            out.append("".join(cur))
            cur = []
        cur.append(ln)
    if cur:
        out.append("".join(cur))
    return out


def normalize_section(sec):
    """Section text with exactly one trailing blank line (the separator before the next paragraph)."""
    return sec.rstrip("\n") + "\n\n"


def insert_before_task(m_text, insertion):
    lines = m_text.splitlines(keepends=True)
    idx = [k for k, ln in enumerate(lines) if ln.startswith("Task:")]
    if len(idx) != 1:
        raise ValueError("expected exactly one 'Task:' line")
    return "".join(lines[:idx[0]] + [insertion] + lines[idx[0]:])


def check(m_text, g_text, arms):
    block, pos = g_block(m_text, g_text)
    secs = sections(block)
    names = [s.splitlines()[0][3:].strip() for s in secs]
    expected = {n: insert_before_task(m_text, normalize_section(s)) for n, s in zip(names, secs)}
    expected["G_as_delivered"] = insert_before_task(m_text, "".join(normalize_section(s) for s in secs))
    result = {"g_block_sections": names, "g_block_inserted_after_M_line": pos,
              "g_frozen_places_block_after_task_line": m_text.splitlines()[pos - 2].startswith("Task:")}
    for arm, (want_section, text) in arms.items():
        result[arm] = {"equals_M_plus_section_before_Task": text == expected[want_section],
                       "section": want_section,
                       "other_sections_absent": all(normalize_section(s).strip() not in text
                                                    for n, s in zip(names, secs) if n != want_section and want_section != "G_as_delivered")}
    return result


if __name__ == "__main__":
    rb = lambda p: open(p, "rb").read()
    m_b, g_b = rb(f"{T}/arm-prompts/M.txt"), rb(f"{T}/arm-prompts/G.txt")
    files = {"C": f"{T}/spr-x-03/arm-prompts/C.txt", "K": f"{T}/spr-x-03/arm-prompts/K.txt",
             "G_as_delivered": f"{T}/spr-x-03/arm-prompts/G_as_delivered.txt"}
    arms = {"C": ("Authority", rb(files["C"]).decode()), "K": ("Checklist", rb(files["K"]).decode()),
            "G_as_delivered": ("G_as_delivered", rb(files["G_as_delivered"]).decode())}
    res = check(m_b.decode(), g_b.decode(), arms)
    res["sha256"] = {"M.txt": sha(m_b), "G.txt": sha(g_b), "G.txt_matches_frozen": sha(g_b) == G_SHA,
                     **{k: sha(rb(p)) for k, p in files.items()}}
    json.dump(res, open(sys.argv[1], "w"), indent=1)
    print(json.dumps(res, indent=1))
