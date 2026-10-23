#!/usr/bin/env python3
"""EXP-2 phase 1: counterfactual replay of P-A (A1 selection) and P-B (checkpoint scheduling).

Deterministic and offline: reads data/<repo>.window.txt, data/<repo>.runs.json, data/<repo>.jobs.json,
data/failure-classes.json, maps/<repo>.verification-map.json and the local git clones (/home/user/<repo>, or
$EXP2_REPO_<REPO>), and writes results/replay.json (verdict table also printed to stdout).

Run from EXP-2/: python3 -I harness/replay.py
"""
import json
import math
import os
import re
import statistics
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
MAPS = os.path.join(ROOT, "maps")
OUT = os.path.join(ROOT, "results")
REPOS = ["praxis", "dokimos"]
WEIGHT = {"linux": 1, "windows": 2, "macos": 10}


# ---------- inputs ----------

def repo_dir(repo):
    return os.environ.get(f"EXP2_REPO_{repo.upper()}", f"/home/user/{repo}")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo_dir(repo), *args], check=True, capture_output=True, text=True).stdout


def load_window(repo):
    shas = [l.split()[0] for l in open(os.path.join(DATA, f"{repo}.window.txt")) if l.strip() and not l.startswith("#")]
    assert len(shas) == 61, (repo, len(shas))
    return shas[:60], shas[60]


def glob_re(pattern):
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$")


class Map:
    def __init__(self, repo):
        self.raw = json.load(open(os.path.join(MAPS, f"{repo}.verification-map.json")))
        self.classes = {cid: [glob_re(g) for g in c["globs"]] for cid, c in self.raw["path_classes"].items()}
        self.jobs = self.raw["jobs"]
        self.checks = {k: [re.compile(p) for p in v] for k, v in self.raw["checks"].items() if k != "description"}

    def classes_of(self, path):
        return {cid for cid, pats in self.classes.items() if any(p.match(path) for p in pats)}

    def entry_matches(self, entry, paths):
        sel = entry["select_when"]
        if sel == "always":
            return True
        for s in sel:
            if s in self.classes:
                if any(any(p.match(x) for p in self.classes[s]) for x in paths):
                    return True
            elif any(glob_re(s).match(x) for x in paths):
                return True
        return False

    def entry_for(self, workflow, job):
        for e in self.jobs:
            if re.search(e["workflow"], workflow) and re.search(e["job"], job):
                return e
        return None

    def select(self, paths):
        """Return (selected map-entry ids, unmapped paths)."""
        unmapped = sorted(p for p in paths if not self.classes_of(p))
        if unmapped:
            return {e["id"] for e in self.jobs}, unmapped
        sel = {e["id"] for e in self.jobs if e.get("mandatory") or self.entry_matches(e, paths)}
        # follows: only when the followed job is selected
        changed = True
        while changed:
            changed = False
            for e in self.jobs:
                f = e.get("follows")
                if f and e["id"] in sel and f not in sel:
                    sel.discard(e["id"])
                    changed = True
                if f and f in sel and e["select_when"] == "always" and e["id"] not in sel:
                    sel.add(e["id"])
                    changed = True
        return sel, []

    def mandatory(self):
        return {e["id"] for e in self.jobs if e.get("mandatory")}

    def check_of(self, step):
        if not step:
            return None
        for k, pats in self.checks.items():
            if any(p.search(step) for p in pats):
                return k
        return None


def changed_paths(repo, base, head):
    out = git(repo, "diff", "--name-status", "-M", base, head)
    paths = set()
    for line in out.splitlines():
        parts = line.split("\t")
        paths.update(parts[1:])
    return sorted(paths)


def is_checkpoint(repo, sha, base):
    parents = git(repo, "log", "-1", "--format=%P", sha).split()
    subject = git(repo, "log", "-1", "--format=%s", sha).strip()
    reasons = []
    if len(parents) > 1 and re.match(r"^Merge (pull request|PR) #\d+", subject):
        reasons.append("pr-merge")
    if len(parents) == 1 and re.search(r"\(#\d+\)$", subject):
        reasons.append("squash-merge")
    vfile, vre = (("release.json", r'"version"\s*:\s*"([^"]+)"') if repo == "praxis"
                  else ("Directory.Build.props", r"<Version>([^<]+)</Version>"))

    def version(rev):
        try:
            m = re.search(vre, git(repo, "show", f"{rev}:{vfile}"))
            return m.group(1) if m else None
        except subprocess.CalledProcessError:
            return None
    if version(sha) != version(base):
        reasons.append(f"version {version(base)}->{version(sha)}")
    tags = [t for t in git(repo, "tag", "--points-at", sha).split() if re.match(r"^(v|dokimos-v)\d", t)]
    if tags:
        reasons.append("tag " + ",".join(tags))
    return reasons, subject, len(parents)


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") if s else None


def minutes(j):
    a, b = ts(j.get("started_at")), ts(j.get("completed_at"))
    if not a or not b or j.get("conclusion") == "skipped":
        return 0.0
    return max(0.0, (b - a).total_seconds() / 60.0)


def os_of(j):
    lab = " ".join(j.get("labels") or []).lower()
    if "windows" in lab:
        return "windows"
    if "macos" in lab:
        return "macos"
    return "linux"


def failing_step(j):
    for s in j.get("steps") or []:
        if s.get("conclusion") == "failure":
            return s["name"]
    return None


# ---------- replay ----------

def replay(repo, flaky_classes):
    m = Map(repo)
    win, pred = load_window(repo)
    order = list(reversed(win))  # oldest -> newest
    idx = {s: i for i, s in enumerate(order)}
    runs = json.load(open(os.path.join(DATA, f"{repo}.runs.json")))["runs"]
    jobs = json.load(open(os.path.join(DATA, f"{repo}.jobs.json")))["jobs"]
    run_by_id = {r["id"]: r for r in runs}

    commits = []
    for i, sha in enumerate(order):
        base = pred if i == 0 else order[i - 1]
        paths = changed_paths(repo, base, sha)
        reasons, subject, np = is_checkpoint(repo, sha, base)
        sel, unmapped = m.select(paths)
        commits.append({"index": i, "sha": sha, "subject": subject, "parents": np, "checkpoint": bool(reasons),
                        "checkpoint_reasons": reasons, "changed_paths": len(paths), "unmapped_paths": unmapped,
                        "classes": sorted({c for p in paths for c in m.classes_of(p)}),
                        "pa_selected": sorted(sel)})
    mand = m.mandatory()

    # gaps: first-parent commits between window ends that have no push run
    fp = git(repo, "rev-list", "--first-parent", f"{pred}..{win[0]}").split()
    gaps = [{"sha": s, "subject": git(repo, "log", "-1", "--format=%s", s).strip()} for s in fp if s not in idx]

    # job instances
    unknown = set()
    inst = []
    for j in jobs:
        r = run_by_id[j["run_id"]]
        e = m.entry_for(r["name"], j["name"])
        if e is None:
            unknown.add((r["name"], j["name"]))
        inst.append({"sha": r["head_sha"], "run_id": r["id"], "workflow": r["name"], "job": j["name"],
                     "key": f"{r['name']} / {j['name']}", "entry": e["id"] if e else None,
                     "mandatory": (e is None) or bool(e.get("mandatory")), "attempt": j["run_attempt"],
                     "job_id": j["id"], "conclusion": j["conclusion"], "minutes": minutes(j), "os": os_of(j),
                     "failing_step": failing_step(j), "run_created": r["created_at"]})

    def runs_policy(policy, sha, i):
        c = commits[idx[sha]]
        if i["entry"] is None:
            return True
        if policy == "baseline":
            return True
        if policy == "P-A":
            return i["entry"] in c["pa_selected"]
        if policy == "P-B":
            return c["checkpoint"] or i["entry"] in mand
        if policy == "P-AB":
            return c["checkpoint"] or i["entry"] in c["pa_selected"]
        raise ValueError(policy)

    policies = ["baseline", "P-A", "P-B", "P-AB"]
    cost = {}
    for p in policies:
        kept = [i for i in inst if runs_policy(p, i["sha"], i)]
        run_ids = {i["run_id"] for i in inst}
        kept_runs = {i["run_id"] for i in kept}
        cost[p] = {"job_instances": len(kept), "job_minutes": round(sum(i["minutes"] for i in kept), 2),
                   "weighted_minutes": round(sum(i["minutes"] * WEIGHT[i["os"]] for i in kept), 2),
                   "workflow_runs": len(kept_runs), "workflow_runs_total": len(run_ids)}

    saved_by_entry = {}
    for p in ["P-A", "P-B"]:
        agg = {}
        for i in inst:
            if not runs_policy(p, i["sha"], i):
                agg[i["entry"]] = round(agg.get(i["entry"], 0.0) + i["minutes"], 2)
        saved_by_entry[p] = dict(sorted(agg.items(), key=lambda kv: -kv[1]))

    # E1: split mandatory steps out of Praxis validate
    e1 = None
    if repo == "praxis":
        saved = 0.0
        jmap = {j["id"]: j for j in jobs}
        for i in inst:
            if i["entry"] == "validate" and not ({"cli_closure", "test_closure"} & set(commits[idx[i["sha"]]]["classes"])) \
                    and not commits[idx[i["sha"]]]["unmapped_paths"]:
                for s in jmap[i["job_id"]]["steps"]:
                    if s["name"] in ("F# tests", "F# browser tests (headless Chrome)"):
                        a, b = ts(s.get("started_at")), ts(s.get("completed_at"))
                        if a and b:
                            saved += (b - a).total_seconds() / 60.0
        e1 = {"additional_minutes_saved_by_PA": round(saved, 2),
              "PA_minutes_with_split": round(cost["P-A"]["job_minutes"] - saved, 2)}

    # outcomes per (sha, key): latest attempt
    latest, attempts = {}, {}
    for i in sorted(inst, key=lambda x: (x["run_created"], x["run_id"], x["attempt"])):
        k = (i["sha"], i["key"])
        attempts.setdefault(k, []).append(i)
        if i["conclusion"] in ("success", "failure", "cancelled", "skipped") or k not in latest:
            latest[k] = i
    rerun_flaky = []
    for k, lst in attempts.items():
        if any(x["conclusion"] == "failure" for x in lst) and latest[k]["conclusion"] == "success":
            rerun_flaky.append({"sha": k[0], "job": k[1], "failed_attempts": [x["job_id"] for x in lst if x["conclusion"] == "failure"]})

    # episodes
    keys = sorted({k for (_, k) in latest})
    episodes = []
    for key in keys:
        cur = None
        for c in commits:
            o = latest.get((c["sha"], key))
            if not o or o["conclusion"] not in ("success", "failure"):
                continue
            if o["conclusion"] == "failure":
                if cur is None:
                    cur = {"job": key, "entry": o["entry"], "start": c["index"], "commits": [], "failing_steps": []}
                    episodes.append(cur)
                cur["commits"].append(c["index"])
                cur["failing_steps"].append(o["failing_step"])
                cur.setdefault("job_ids", []).append(o["job_id"])
            else:
                cur = None

    ckpt_idx = [c["index"] for c in commits if c["checkpoint"]]

    def detect(policy, ep):
        start = ep["start"]
        horizon = next((k for k in ckpt_idx if k >= start), None)
        check = m.check_of(ep["failing_steps"][0])
        unobservable = False
        # Detection is possible only while the episode lasts: from its first to its last failing commit.
        for c in commits[start:ep["commits"][-1] + 1]:
            o = latest.get((c["sha"], ep["job"]))
            if o and runs_policy(policy, c["sha"], o):
                if o["conclusion"] == "failure":
                    return c["index"], "same job", horizon, unobservable
                if o["conclusion"] not in ("success", "failure") and (horizon is None or c["index"] <= horizon):
                    unobservable = True
            if check:
                for (s2, k2), o2 in latest.items():
                    if s2 == c["sha"] and k2 != ep["job"] and o2["conclusion"] == "failure" and \
                            m.check_of(o2["failing_step"]) == check and runs_policy(policy, s2, o2):
                        return c["index"], f"check {check} via {k2}", horizon, unobservable
        return None, None, horizon, unobservable

    det = {}
    for p in ["P-A", "P-B", "P-AB", "baseline"]:
        rows = []
        for ep in episodes:
            d, how, horizon, unobs = detect(p, ep)
            start_sha = commits[ep["start"]]["sha"]
            if d is None:
                delay_c = delay_k = math.inf
            else:
                delay_c = d - ep["start"]
                delay_k = sum(1 for k in ckpt_idx if ep["start"] < k <= d)
            escaped = d is None or horizon is None or d > horizon
            unresolved = horizon is None or (escaped and unobs)
            sc = commits[ep["start"]]
            rows.append({
                "job": ep["job"], "entry": ep["entry"], "start_index": ep["start"], "start_sha": start_sha,
                "start_subject": sc["subject"], "episode_commits": [commits[x]["sha"][:10] for x in ep["commits"]],
                "failing_step": ep["failing_steps"][0], "job_ids": ep["job_ids"],
                "start_is_checkpoint": sc["checkpoint"], "horizon_index": horizon,
                "detected_index": d, "detected_by": how, "delay_commits": delay_c, "delay_checkpoints": delay_k,
                "escaped": escaped, "unresolved": unresolved, "delayed": (d is not None and d > ep["start"]),
                "flaky_class": flaky_classes.get(f"{repo}:{ep['job_ids'][0]}", {}).get("class", "unclassified"),
                "why_skipped": why_skipped(p, sc, ep["entry"], mand),
            })
        det[p] = rows

    return {"repo": repo, "window_newest": win[0], "window_oldest": win[-1], "diff_base": pred,
            "commits": commits, "checkpoints": len(ckpt_idx), "non_checkpoints": len(commits) - len(ckpt_idx),
            "gaps": gaps, "saved_minutes_by_entry": saved_by_entry, "unknown_jobs": sorted(map(list, unknown)), "cost": cost, "e1": e1,
            "episodes": det, "rerun_flaky": rerun_flaky, "job_instances": len(inst)}


def why_skipped(policy, c, entry, mand):
    if policy == "P-A":
        if entry in c["pa_selected"]:
            return "selected"
        return f"no changed path selects {entry}; changed classes: {', '.join(c['classes']) or '(none)'}"
    if policy == "P-B":
        if c["checkpoint"] or entry in mand:
            return "run"
        return f"non-checkpoint direct push; {entry} not mandatory"
    if policy == "P-AB":
        if c["checkpoint"] or entry in c["pa_selected"]:
            return "run"
        return f"non-checkpoint and not selected; classes: {', '.join(c['classes']) or '(none)'}"
    return "run"


# ---------- summary ----------

def pct(saved, base):
    return 100.0 * saved / base if base else 0.0


def finite_median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    if n % 2:
        return s[n // 2]
    a, b = s[n // 2 - 1], s[n // 2]
    return math.inf if math.isinf(b) else (a + b) / 2


def main():
    os.makedirs(OUT, exist_ok=True)
    fc_path = os.path.join(DATA, "failure-classes.json")
    flaky = json.load(open(fc_path)) if os.path.exists(fc_path) else {}
    flaky = {k: v for k, v in flaky.items() if not k.startswith("_")}
    res = {r: replay(r, flaky) for r in REPOS}
    pooled = {}
    for p in ["baseline", "P-A", "P-B", "P-AB"]:
        pooled[p] = {k: round(sum(res[r]["cost"][p][k] for r in REPOS), 2) for k in res[REPOS[0]]["cost"][p]}
    verdict = {}
    for p in ["P-A", "P-B", "P-AB"]:
        v = {}
        for scope in REPOS + ["pooled"]:
            base = pooled["baseline"] if scope == "pooled" else res[scope]["cost"]["baseline"]
            pol = pooled[p] if scope == "pooled" else res[scope]["cost"][p]
            eps = [e for r in REPOS for e in res[r]["episodes"][p]] if scope == "pooled" else res[scope]["episodes"][p]
            esc = [e for e in eps if e["escaped"]]
            esc_nf = [e for e in esc if e["flaky_class"] not in ("rerun-flaky", "environmental")]
            delays = [e["delay_checkpoints"] for e in eps]
            v[scope] = {
                "minutes_saved_pct": round(pct(base["job_minutes"] - pol["job_minutes"], base["job_minutes"]), 1),
                "minutes_saved": round(base["job_minutes"] - pol["job_minutes"], 1),
                "weighted_saved_pct": round(pct(base["weighted_minutes"] - pol["weighted_minutes"], base["weighted_minutes"]), 1),
                "runs_avoided": base["workflow_runs"] - pol["workflow_runs"],
                "job_instances_avoided": base["job_instances"] - pol["job_instances"],
                "episodes": len(eps), "escaped_strict": len(esc), "escaped_excluding_flaky_env": len(esc_nf),
                "unresolved": sum(1 for e in esc if e["unresolved"]),
                "delayed_detected": sum(1 for e in eps if e["delayed"] and not e["escaped"]),
                "median_delay_checkpoints": finite_median(delays),
                "H1_holds": pct(base["job_minutes"] - pol["job_minutes"], base["job_minutes"]) >= 30 and len(esc) == 0,
                "H2_holds": (finite_median(delays) is not None and finite_median(delays) <= 1),
            }
        verdict[p] = v
    out = {"repos": res, "pooled_cost": pooled, "verdict": verdict}

    def enc(o):
        if isinstance(o, float) and math.isinf(o):
            return "inf"
        raise TypeError

    s = json.dumps(out, indent=1, default=str, allow_nan=True).replace("Infinity", '"inf"')
    open(os.path.join(OUT, "replay.json"), "w").write(s + "\n")
    print(json.dumps(verdict, indent=1, default=str).replace("Infinity", '"inf"'))
    for r in REPOS:
        print(r, json.dumps(res[r]["cost"]), "ckpt", res[r]["checkpoints"], "e1", res[r]["e1"],
              "unknown", res[r]["unknown_jobs"], file=sys.stderr)


if __name__ == "__main__":
    main()
