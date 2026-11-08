"""Score the X-02 and X-01 (D2b/D2c) workspaces with the V4 oracle. Usage: score_runs.py OUTDIR"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle  # noqa: E402

WS = "/home/user/sprint-scratch/V4/ws"
RUNS = ([(f"s{i:02d}", "D2b") for i in range(1, 15)] + [(f"t{i:02d}", "D2c") for i in range(1, 15)])


def main(outdir):
    os.makedirs(os.path.join(outdir, "probe-raw"), exist_ok=True)
    scores = {}
    for rid, fx in RUNS:
        raw = oracle.run_workspace(os.path.join(WS, rid))
        with open(os.path.join(outdir, "probe-raw", f"{rid}.json"), "w") as f:
            json.dump(raw, f, indent=1, sort_keys=True)
        scores[rid] = oracle.score(raw, fx)
    with open(os.path.join(outdir, "v4-scores.json"), "w") as f:
        json.dump(scores, f, indent=1, sort_keys=True)
    return scores


if __name__ == "__main__":
    for rid, s in main(sys.argv[1]).items():
        print(rid, "acc", s["accepted"], "viol", s["violations"], "any", s["violations_any_probe"],
              "ctrl", s["controls_passed"], "fp", s["followed_planted"],
              {t: v["category"] for t, v in s["traps"].items()}, s["failed_requirement_probes"])
