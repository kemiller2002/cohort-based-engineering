"""Score the 24 SPR-X-03 workspaces (scratch copies) with the reused V4 oracle.

Usage: python3 -I -B scripts/score_x03.py OUTDIR
Workspace code runs only inside oracle.run_workspace (isolated `python3 -I -B` subprocess on a temp copy).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "v4_oracle"))
import oracle  # noqa: E402

WS = "/home/user/sprint-scratch/V5/ws"
RUNS = tuple([(f"a{i:02d}", "D2b") for i in range(1, 13)] + [(f"b{i:02d}", "D2c") for i in range(1, 13)])


def score_all(ws_root=WS, runs=RUNS):
    raws = {rid: oracle.run_workspace(os.path.join(ws_root, rid)) for rid, _ in runs}
    return raws, {rid: oracle.score(raws[rid], fx) for rid, fx in runs}


def write(outdir, raws, scores):
    os.makedirs(os.path.join(outdir, "probe-raw"), exist_ok=True)
    for rid, raw in raws.items():
        with open(os.path.join(outdir, "probe-raw", f"{rid}.json"), "w") as f:
            json.dump(raw, f, indent=1, sort_keys=True)
    with open(os.path.join(outdir, "v5-scores.json"), "w") as f:
        json.dump(scores, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    os.environ.setdefault("V4_TMP", "/home/user/sprint-scratch/V5/tmp")
    raws, scores = score_all()
    write(sys.argv[1], raws, scores)
    for rid, s in scores.items():
        print(rid, "imp", s["import_error"], "acc", s["accepted"], "viol", s["violations"], "any", s["violations_any_probe"],
              "ctrl", s["controls_passed"], "fp", s["followed_planted"], s["followed_planted_detail"],
              {t: (v["category"], v["primary_value"]) for t, v in s["traps"].items()}, s["failed_requirement_probes"])
