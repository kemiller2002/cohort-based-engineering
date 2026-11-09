#!/usr/bin/env python3
"""V2 claim 2 (B-F-07): compare two git trees by blob hash, path for path.

Pure core (parse_ls_tree, compare_trees) plus a thin git I/O shell.
Usage: blob_compare.py REPO_A REV_A REPO_B REV_B [--ext .fs,.css,.html]
"""
import json
import subprocess
import sys
from collections import namedtuple

Entry = namedtuple("Entry", "mode kind blob path")
DEFAULT_EXTS = (".fs", ".css", ".html")


def parse_ls_tree(text):
    """Parse `git ls-tree -r` output into a tuple of Entry (blobs only)."""
    def one(line):
        meta, path = line.split("\t", 1)
        mode, kind, blob = meta.split()
        return Entry(mode, kind, blob, path)
    return tuple(e for e in (one(l) for l in text.splitlines() if l.strip()) if e.kind == "blob")


def has_ext(path, exts):
    return any(path.endswith(x) for x in exts)


def compare_trees(a, b, exts=DEFAULT_EXTS):
    """Return counts of path+blob identity of tree b against tree a."""
    amap = {e.path: e.blob for e in a}
    bmap = {e.path: e.blob for e in b}
    src_b = tuple(p for p in bmap if has_ext(p, exts))
    src_a = tuple(p for p in amap if has_ext(p, exts))
    same = lambda paths: tuple(p for p in paths if amap.get(p) == bmap[p])
    src_same = same(src_b)
    all_same = same(tuple(bmap))
    a_blobs = frozenset(amap.values())
    return {
        "source_files_b": len(src_b),
        "source_files_a": len(src_a),
        "source_identical_same_path": len(src_same),
        "source_differing": sorted(set(src_b) - set(src_same)),
        "source_only_in_a": sorted(set(src_a) - set(src_b)),
        "all_files_b": len(bmap),
        "all_identical_same_path": len(all_same),
        "source_blob_present_anywhere_in_a": sum(1 for p in src_b if bmap[p] in a_blobs),
    }


def ls_tree(repo, rev):
    return subprocess.run(["git", "-C", repo, "ls-tree", "-r", rev],
                          capture_output=True, text=True, check=True).stdout


def main(argv):
    exts = DEFAULT_EXTS
    if "--ext" in argv:
        i = argv.index("--ext")
        exts = tuple(argv[i + 1].split(","))
        argv = argv[:i] + argv[i + 2:]
    repo_a, rev_a, repo_b, rev_b = argv
    result = compare_trees(parse_ls_tree(ls_tree(repo_a, rev_a)),
                           parse_ls_tree(ls_tree(repo_b, rev_b)), exts)
    print(json.dumps({"a": [repo_a, rev_a], "b": [repo_b, rev_b], "exts": exts, **result}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
