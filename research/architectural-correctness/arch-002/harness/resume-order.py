"""Amendment A4: rebuild the resume order after a host interruption.

usage: resume-order.py BASE_ORDER.json RUNS OUT.json
A slot's attempts are its runId, then runId-rr1, runId-rr2, ... An attempt is lost if setup never wrote run.json or an
agent phase started without finishing (trial.sh's interrupted rule), or if it carries x1.json/interrupted.json. A
slot keeps its first attempt that is not lost (done, or unscored: scoring resumes); otherwise it gets the next unused
suffix. Arm-blind: the rule looks only at harness state files, never at results.
"""
import json, os, sys

def attempts(run_id):
    return [run_id] + [f"{run_id}-rr{n}" for n in range(1, 10)]

def state(runs, rid):
    st = os.path.join(runs, rid, "state")
    has = lambda *p: os.path.exists(os.path.join(st, *p))
    if not os.path.isdir(st):
        return "absent"
    if has("done"):
        return "done"
    if has("x1.json") or has("interrupted.json") or not has("run.json"):
        return "lost"
    return "lost" if any(has(f"phase{k}", "integrity-before.json") and not has(f"phase{k}", "integrity.json")
                         for k in (1, 2)) else "resumable"

def slot(runs, trial):
    base = trial.get("replacesRunId", trial["runId"])
    tried = [(r, state(runs, r)) for r in attempts(base)]
    used = [x for x in tried if x[1] != "absent"]
    live = [r for r, st in used if st != "lost"]
    rid = live[0] if live else tried[len(used)][0]
    return {**{k: v for k, v in trial.items() if k != "replacesRunId"}, "runId": rid,
            **({"replacesRunId": base} if rid != base else {})}

def main(order_path, runs, out):
    src = json.load(open(order_path))
    bases = {t.get("replacesRunId", t["runId"]): t for t in src["trials"]}
    trials = [slot(runs, t) for t in bases.values()]
    json.dump({**src, "trials": trials, "derivedFrom": f"{os.path.basename(order_path)} via resume-order.py (A4)"},
              open(out, "w"), indent=1)
    for t in trials:
        if "replacesRunId" in t:
            print(t["runId"])

if __name__ == "__main__":
    main(*sys.argv[1:4])
