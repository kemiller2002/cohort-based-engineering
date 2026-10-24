#!/usr/bin/env python3
"""EXP-3 phase 1b scorer: held-out, confirmatory evaluation of the Dokimos rule-provenance audit (zero cost,
deterministic). Run with `python3 -I`. Protocol: ../PREREGISTRATION-1b.md.

  score_heldout.py --dokimos <dokimos checkout or worktree> [--work DIR] [--allow-other-revision]

For each of the 17 frozen held-out scenarios (heldout/, frozen at 000e90a) and each analyzer (`ast` = v2, the
confirmatory subject; `lexical` = v1, reference only): copy the frozen tree to a work directory, run the audit in
legacy mode over the scenario's audited files (heldout/labels.json `auditScope`, missing files skipped) with the
FROZEN handoff, run it a second time and require byte-identical output, validate the report, and score it against
heldout/labels.json. Writes heldout-results/raw/<analyzer>/<id>.audit.json and heldout-results/scores.json.

Never writes inside heldout/ or the dokimos checkout. Reuses harness/exp3.py read-only (label resolution, schema
validation, handoff construction for a consistency check), without writing bytecode.
"""
import hashlib, importlib.util, json, math, os, shutil, subprocess, sys
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
EXP3 = HERE.parent
HELDOUT = EXP3 / "heldout"
OUT = EXP3 / "heldout-results"
PREREGISTERED_ANALYZER_SHA = "fc9b31fe7c1dc76020a78868fee316d897d681ca"
ANALYZERS = ("ast", "lexical")          # ast = v2 (confirmatory), lexical = v1 (reference)
MECHANISMS = ("superseded-value", "exemption", "silent-default")
CONTROLS = ("H16", "H17")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def load_exp3():
    spec = importlib.util.spec_from_file_location("exp3_readonly", HERE / "exp3.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_freeze():
    bad = []
    for line in (HELDOUT / "FREEZE.sha256").read_text().splitlines():
        if not line.strip():
            continue
        h, rel = line.split(None, 1)
        rel = rel.lstrip("*")
        p = HELDOUT / rel
        if not p.exists() or sha256(p) != h:
            bad.append(rel)
    if bad:
        raise SystemExit(f"FREEZE.sha256 check failed for {bad}: STOP")


# ------------------------------------------------------------------ statistics

def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def ratio(k, n):
    return {"k": k, "n": n, "value": round(k / n, 4) if n else None, "wilson95": wilson(k, n)}


# ------------------------------------------------------------------ audit

def run_audit(cli, env, analyzer, tree, handoff, files, out, sdk):
    args = ["dotnet", str(cli), "audit", "--analyzer", analyzer, "--root", str(tree), "--handoff", str(handoff),
            "--sdk-version", sdk, "--out", str(out)]
    for f in files:
        args += ["--legacy", str(f)]
    r = subprocess.run(args, capture_output=True, text=True, env=env)
    return r.returncode, r.stderr.strip()


# ------------------------------------------------------------------ scoring (PREREGISTRATION-1b.md section 4)

def score_report(exp3, sid, labels, report):
    lab = dict(labels["overrides"].get(sid, {}))
    rules = labels["plantedRules"].get(sid, [])
    rule_of = {}
    for r in rules:
        for s in r["symbols"]:
            rule_of.setdefault(s, []).append(r["rule"])
    scored = []
    for f in report.get("findings", []):
        loc = f.get("location", {}) or {}
        sym = loc.get("symbol")
        key, l = exp3.resolve_label(lab, sym)
        cat = l[0] if l else "UNLABELLED"
        outcome = {"PLANTED": "TP", "SUPPORTED": "FQ", "TECHNICAL": "FQ", "UNLABELLED": "FQ",
                   "OTHER-UNAUTHORIZED": "OTHER"}[cat]
        scored.append({"id": f.get("id"), "class": f.get("class"), "certainty": f.get("certainty"),
                       "path": loc.get("path"), "line": loc.get("line"), "symbol": sym, "labelKey": key,
                       "label": cat, "basis": l[1] if l else None, "outcome": outcome,
                       "rules": sorted(rule_of.get(key, [])) if key else [],
                       "message": f.get("message")})
    per_rule = []
    for r in rules:
        tps = [s for s in scored if s["labelKey"] in r["symbols"]]
        ok = None
        if tps:
            if r["mechanism"] == "superseded-value":
                ok = any(s["class"] == "superseded-authority" for s in tps)
            elif r["mechanism"] == "silent-default":
                ok = any("wildcard default" in (s["message"] or "") for s in tps)
            else:
                ok = any("exemption" in (s["message"] or "") for s in tps)
        per_rule.append({"rule": r["rule"], "mechanism": r["mechanism"], "form": r.get("form"),
                         "symbols": r["symbols"], "detected": bool(tps), "mechanismCorrect": ok,
                         "tpFindings": [s["symbol"] for s in tps]})
    return scored, per_rule


def agg(rows):
    findings = [s for r in rows for s in r["scored"]]
    rules = [x for r in rows for x in r["rules"]]
    n = len(findings)
    tp = sum(s["outcome"] == "TP" for s in findings)
    fq = sum(s["outcome"] == "FQ" for s in findings)
    other = sum(s["outcome"] == "OTHER" for s in findings)
    det = sum(1 for x in rules if x["detected"])
    split = {}
    for s in findings:
        if s["outcome"] == "FQ":
            split[s["label"]] = split.get(s["label"], 0) + 1
    # Secondary (phase 1 amendment A1 style): one count per distinct (path, symbol, label, class), pooled.
    distinct = {}
    for s in findings:
        distinct.setdefault((s["path"], s["symbol"], s["label"], s["class"]), s["outcome"])
    dn = len(distinct)
    dfq = sum(1 for o in distinct.values() if o == "FQ")
    dtp = sum(1 for o in distinct.values() if o == "TP")
    return {"scenarios": len(rows), "ownerQuestions": n, "tp": tp, "fq": fq, "other": other, "fqSplit": split,
            "plantedRules": len(rules), "detected": det,
            "recall": ratio(det, len(rules)) if rules else None,
            "precisionStrict": ratio(tp, n) if n else None,
            "precisionLenient": ratio(tp + other, n) if n else None,
            "falseQuestionRate": ratio(fq, n) if n else None,
            "mechanismCorrect": sum(1 for x in rules if x["mechanismCorrect"]),
            "missed": [x["rule"] for x in rules if not x["detected"]],
            "secondaryDistinct": {"ownerQuestions": dn, "tp": dtp, "fq": dfq,
                                  "falseQuestionRate": ratio(dfq, dn) if dn else None}}


def by_mechanism(rows, mech):
    rules = [x for r in rows for x in r["rules"] if x["mechanism"] == mech]
    det = sum(1 for x in rules if x["detected"])
    rule_ids = {x["rule"] for x in rules}
    tpf = sum(1 for r in rows for s in r["scored"] if s["outcome"] == "TP" and rule_ids & set(s["rules"]))
    return {"plantedRules": len(rules), "detected": det, "recall": ratio(det, len(rules)),
            "tpFindings": tpf, "mechanismCorrect": sum(1 for x in rules if x["mechanismCorrect"]),
            "missed": [x["rule"] for x in rules if not x["detected"]]}


def classify(a):
    """Evidence class for H1 / H1a / H1b (PREREGISTRATION-1b.md section 6)."""
    rec, fqr = a["recall"], a["falseQuestionRate"]
    if rec is None or fqr is None:
        return {"H1": "Inconclusive", "H1a": "Inconclusive", "H1b": "Inconclusive"}

    def one(point_ok, ci_ok):
        return "Demonstrated" if point_ok and ci_ok else ("Supported-preliminary" if point_ok else "Contradicted")
    h1a = one(rec["value"] >= 0.90, rec["wilson95"][0] >= 0.90)
    h1b = one(fqr["value"] <= 0.10, fqr["wilson95"][1] <= 0.10)
    if "Contradicted" in (h1a, h1b):
        h1 = "Contradicted"
    elif h1a == h1b == "Demonstrated":
        h1 = "Demonstrated"
    else:
        h1 = "Supported-preliminary"
    return {"H1": h1, "H1a": h1a, "H1b": h1b}


def main():
    dok = Path(arg("--dokimos") or sys.exit("--dokimos <dokimos checkout> is required"))
    rp = dok / "experiments/rule-provenance"
    cli = rp / "src/RuleProvenance.Cli/bin/Debug/net10.0/rule-provenance.dll"
    head = subprocess.run(["git", "-C", str(dok), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(dok), "status", "--porcelain", "--", "experiments/rule-provenance"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PREREGISTERED_ANALYZER_SHA and "--allow-other-revision" not in sys.argv:
        raise SystemExit(f"analyzer revision {head} != preregistered {PREREGISTERED_ANALYZER_SHA}")
    if dirty:
        raise SystemExit(f"analyzer tree has local changes:\n{dirty}")
    if not cli.exists():
        raise SystemExit(f"build the audit first: {cli}")

    exp3 = load_exp3()
    env = exp3.ENV
    verify_freeze()
    labels = json.loads((HELDOUT / "labels.json").read_text())
    work = Path(arg("--work") or (Path(os.environ.get("TMPDIR", "/tmp")) / "exp3-heldout-work"))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    sdk = subprocess.run(["dotnet", "--version"], capture_output=True, text=True, env=env, check=True).stdout.strip()
    rev = exp3.git_rev()
    scens = sorted(p.name for p in (HELDOUT / "scenarios").iterdir() if p.is_dir())

    results = {a: [] for a in ANALYZERS}
    handoff_check = {}
    determinism = {a: True for a in ANALYZERS}
    for sid in scens:
        scen = json.loads((HELDOUT / "scenarios" / sid / "scenario.json").read_text())
        dom = scen["domain"]
        tree = work / sid / "tree"
        shutil.copytree(HELDOUT / "scenarios" / sid / "tree", tree)
        hp = HELDOUT / "handoffs" / f"{sid}.handoff.json"
        exp3.validate("echelon-authority-handoff-0.1.schema.json", json.loads(hp.read_text()))
        # Consistency check only: the frozen handoff is what the audit receives either way.
        regen = json.dumps(exp3.build_handoff(sid, tree, rev), indent=2) + "\n"
        handoff_check[sid] = regen == hp.read_text()
        files = [tree / f for f in labels["auditScope"][dom] if (tree / f).exists()]
        all_src = sorted(p for p in (tree / "src").rglob("*.fs") if "bin" not in p.parts and "obj" not in p.parts)
        for a in ANALYZERS:
            raw = OUT / "raw" / a / f"{sid}.audit.json"
            raw.parent.mkdir(parents=True, exist_ok=True)
            code, err = run_audit(cli, env, a, tree, hp, files, raw, sdk)
            rerun = work / sid / f"{a}.rerun.audit.json"
            code2, _ = run_audit(cli, env, a, tree, hp, files, rerun, sdk)
            same = raw.exists() and rerun.exists() and raw.read_bytes() == rerun.read_bytes() and code == code2
            determinism[a] &= same
            ok = code in (0, 4) and raw.exists()
            if ok:
                rep = json.loads(raw.read_text())
                exp3.validate("echelon-provenance-audit-0.1.schema.json", rep)
            else:
                rep = {"findings": []}  # preregistered: a failed audit contributes no findings; its rules are missed
            scored, per_rule = score_report(exp3, sid, labels, rep)
            ex = work / sid / f"{a}.all-src.audit.json"
            code3, _ = run_audit(cli, env, a, tree, hp, all_src, ex, sdk)
            exq = len(json.loads(ex.read_text())["findings"]) if code3 in (0, 4) and ex.exists() else None
            results[a].append({"scenario": sid, "domain": dom, "control": sid in CONTROLS,
                               "auditedFiles": [f.relative_to(tree).as_posix() for f in files],
                               "auditExit": code, "auditSummary": err, "auditOk": ok, "deterministic": same,
                               "findings": len(scored), "tp": sum(s["outcome"] == "TP" for s in scored),
                               "fq": sum(s["outcome"] == "FQ" for s in scored), "rules": per_rule,
                               "exploratoryAllSrcOwnerQuestions": exq, "scored": scored})
            print(f"{a:7} {sid} {dom:13} exit={code} findings={len(scored)} "
                  f"detected={sum(x['detected'] for x in per_rule)}/{len(per_rule)} det={same}")
    verify_freeze()

    analyzers = {}
    for a in ANALYZERS:
        rows = results[a]
        overall = agg(rows)
        analyzers[a] = {
            "role": "confirmatory (v2)" if a == "ast" else "reference (v1)",
            "aggregate": overall,
            "plantedScenarios": agg([r for r in rows if not r["control"]]),
            "controls": agg([r for r in rows if r["control"]]),
            "byMechanism": {m: by_mechanism(rows, m) for m in MECHANISMS},
            "byDomain": {d: agg([r for r in rows if r["domain"] == d])
                         for d in sorted({r["domain"] for r in rows})},
            "evidence": classify(overall),
            "auditFailures": [r["scenario"] for r in rows if not r["auditOk"]],
            "deterministic": determinism[a],
            "exploratoryAllSrcOwnerQuestions": sum(r["exploratoryAllSrcOwnerQuestions"] or 0 for r in rows),
            "scenarios": rows}
    scores = {"schema": "cbe.exp-3.heldout-scores/1", "protocol": "research/experiments/EXP-3/PREREGISTRATION-1b.md",
              "analyzerCommit": head, "sdk": sdk, "corpusFrozenAt": "000e90a", "handoffCorpusRevision": rev,
              "freezeVerified": True, "frozenHandoffsMatchRegeneration": handoff_check,
              "ciMethod": "Wilson score interval, 95%", "analyzers": analyzers}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scores.json").write_text(json.dumps(scores, indent=2) + "\n")
    for a in ANALYZERS:
        x = analyzers[a]["aggregate"]
        print(a, json.dumps({"recall": x["recall"], "precision": x["precisionStrict"],
                             "fqRate": x["falseQuestionRate"], "evidence": analyzers[a]["evidence"],
                             "deterministic": determinism[a]}))


if __name__ == "__main__":
    main()
