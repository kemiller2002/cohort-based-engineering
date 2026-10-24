#!/usr/bin/env python3
"""EXP-3 phase 1 harness (zero cost, deterministic). Run with `python3 -I`.

  exp3.py [--work DIR]

Per P3 scenario: materialize the starting tree, build the authority handoff from the scenario's own requirement,
decision and approval documents (PREREGISTRATION.md section 4), run the Dokimos rule-provenance audit in legacy mode
over the domain's rules modules, and score the findings against harness/labels.json (section 6).
Writes results/handoffs/, results/raw/, results/exploratory/ and results/scores.json.
"""
import hashlib, json, math, os, re, shutil, subprocess, sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP3 = HERE.parent
REPO = EXP3.parents[2]
VAC = REPO / "research/experiments/VAC-002"
P3 = VAC / "P3"
SCHEMAS = REPO / "program/contracts/schemas"
DOKIMOS = Path("/home/user/dokimos/experiments/rule-provenance")
CLI = DOKIMOS / "src/RuleProvenance.Cli/bin/Debug/net10.0/rule-provenance.dll"
RESULTS = EXP3 / "results"
ENV = dict(os.environ, PATH="/root/.dotnet:" + os.environ.get("PATH", ""), DOTNET_ROOT="/root/.dotnet",
           DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")

LABELS = json.loads((HERE / "labels.json").read_text())


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_rev() -> str:
    return subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%H", "--", "research/experiments/VAC-002"],
                          capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ tree

def materialize(scen: dict, out: Path):
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(VAC / "P2/fixture" / scen["domain"] / "repo", out,
                    ignore=shutil.ignore_patterns("bin", "obj"))
    for o in scen["overlays"]:
        shutil.copytree(VAC / o, out, dirs_exist_ok=True)
    rm = out / ".remove"
    if rm.exists():
        for line in rm.read_text().splitlines():
            line = line.strip()
            if line:
                t = out / line
                if t.is_dir():
                    shutil.rmtree(t)
                elif t.exists():
                    t.unlink()
        rm.unlink()


# ------------------------------------------------------------------ handoff (PREREGISTRATION.md section 4)

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TIME = re.compile(r"\b\d{1,2}:\d{2}\b")
IDISH = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b|\b[A-Za-z]+\d+\b")
NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(\s*%)?")


def pct(tok: str) -> str:
    v = Decimal(tok) / Decimal(100)
    s = format(v.normalize(), "f")
    return s


def numbers(text: str):
    t = DATE.sub(" ", text)
    t = TIME.sub(" ", t)
    t = IDISH.sub(" ", t)
    out = []
    for m in NUM.finditer(t):
        tok, p = m.group(1), m.group(2)
        out.append(pct(tok) if p else tok)
    return out


def table_params(path: Path):
    stem = path.stem
    params = []
    for line in path.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cells) < 2 or set("".join(cells)) <= set("-: "):
            continue
        key = cells[0].split()[0] if cells[0] else ""
        for c in cells[1:]:
            m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(%?)(?:\s*[A-Za-z]+)?", c)
            if m and key:
                params.append((f"{stem}.{key}", pct(m.group(1)) if m.group(2) else m.group(1)))
                break
    return params


STATUS = re.compile(r"^Status:\s*(.*)$", re.M)


def parse_record(path: Path, tree: Path, rev: str, approval: bool):
    text = path.read_text()
    head = re.search(r"^#\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+):\s*(.*)$", text, re.M)
    rid = head.group(1)
    sm = STATUS.search(text)
    status_line = sm.group(1).strip()
    body = text[sm.end():].strip()
    sl = status_line.lower()
    sup_by = re.search(r"superseded by ([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)", status_line)
    supersedes = re.findall(r"Supersedes ([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)", status_line)
    if approval:
        status = "accepted" if sl.startswith("granted") else ("rejected" if sl.startswith("rejected") else "proposed")
        om = re.search(r"by:\s*([^)]*)\)", status_line)
    else:
        status = "superseded" if sl.startswith("superseded") else ("accepted" if sl.startswith("accepted")
                                                                    else ("rejected" if sl.startswith("rejected") else "proposed"))
        om = re.search(r"owner:\s*([^)]*)\)", status_line)
    owner = om.group(1).strip() if om else "unknown"
    date = DATE.search(status_line)
    rel = path.relative_to(tree).as_posix()
    params = {}
    for i, v in enumerate(numbers(body), 1):
        params[f"p{i}"] = v
    for ref in re.findall(r"`(docs/[^`]+\.md)`", body):
        rp = tree / ref
        if rp.exists():
            for k, v in table_params(rp):
                params[k] = v
    d = {"id": rid, "statement": " ".join(body.split()) or head.group(2), "status": status,
         "kind": "exception" if approval else "business-rule", "owner": owner}
    if status == "accepted":
        d["authorizedBy"] = {"kind": "human", "id": owner, "role": "decision-owner"}
        d["authorizedAt"] = (date.group(0) if date else "2026-01-01") + "T00:00:00Z"
    d.update({"requirementIds": [],
              "source": {"path": rel, "locator": f"# {rid}", "revision": rev, "sha256": "sha256:" + sha(path)},
              "supersedes": supersedes})
    if sup_by:
        d["supersededBy"] = sup_by.group(1)
    if params:
        d["parameters"] = params
    return d


def parse_requirements(path: Path, tree: Path, rev: str):
    text = path.read_text()
    om = re.search(r"Owners?:\s*(.+)$", text, re.M)
    owner = om.group(1).strip().rstrip(".") if om else "unknown"
    parts = re.split(r"^##\s+", text, flags=re.M)
    out = []
    for part in parts[1:]:
        first, _, rest = part.partition("\n")
        rid = first.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", rid):
            continue
        stmt = " ".join(rest.split())
        out.append({"id": rid, "statement": stmt or rid, "status": "accepted", "owner": owner,
                    "source": {"path": path.relative_to(tree).as_posix(), "locator": f"## {rid}", "revision": rev,
                               "sha256": "sha256:" + sha(path)},
                    "supersedes": []})
    return out


def build_handoff(sid: str, tree: Path, rev: str):
    reqs = []
    for p in sorted((tree / "requirements").glob("*.md")):
        reqs += parse_requirements(p, tree, rev)
    decs = [parse_record(p, tree, rev, False) for p in sorted((tree / "docs/decisions").glob("*.md"))]
    decs += [parse_record(p, tree, rev, True) for p in sorted((tree / "docs/approvals").glob("*.md"))]
    return {
        "schema": "echelon.authority-handoff", "schemaVersion": "0.1",
        "handoffId": f"HND-EXP3-{sid}",
        "produced": {"by": {"kind": "automation", "id": "exp3-harness", "role": "experimenter"},
                     "at": "2026-10-23T00:00:00Z", "repository": "kemiller2002/cohort-based-engineering",
                     "revision": rev},
        "authorityContract": {"id": "VAC-002-P3-AUTHORITY-CONTRACT", "sha256": sha(P3 / "AUTHORITY-CONTRACT.md")},
        "requirements": reqs, "decisions": decs, "policyQuestions": [], "observations": [], "invariants": []}


def validate(schema: str, doc):
    import jsonschema
    s = json.loads((SCHEMAS / schema).read_text())
    jsonschema.Draft202012Validator(s).validate(doc)


# ------------------------------------------------------------------ audit

def audit_files(domain: str, tree: Path, scope: str):
    if scope == "rules":
        return [tree / f for f in LABELS["auditScope"][domain] if (tree / f).exists()]
    return sorted(p for p in (tree / "src").rglob("*.fs") if "bin" not in p.parts and "obj" not in p.parts)


def run_audit(tree: Path, handoff: Path, files, out: Path, sdk: str):
    args = ["dotnet", str(CLI), "audit", "--root", str(tree), "--handoff", str(handoff), "--sdk-version", sdk,
            "--out", str(out)]
    for f in files:
        args += ["--legacy", str(f)]
    r = subprocess.run(args, capture_output=True, text=True, env=ENV)
    return r.returncode, r.stderr.strip()


# ------------------------------------------------------------------ scoring

def labels_for(sid: str, domain: str):
    lab = dict(LABELS["base"][domain])
    lab.update(LABELS["overrides"].get(sid, {}))
    return lab


def resolve_label(lab: dict, symbol):
    if not symbol:
        return None, None
    s = symbol
    while s:
        if s in lab:
            return s, lab[s]
        if "." not in s:
            break
        s = s.rsplit(".", 1)[0]
    return None, None


def clopper_pearson(k, n, a=0.05):
    if n == 0:
        return None
    from math import comb

    def cdf(x, p):
        return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, x + 1))

    def solve(f, lo=0.0, hi=1.0):
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid):
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(lambda p: 1 - cdf(k - 1, p) >= a / 2)
    upper = 1.0 if k == n else solve(lambda p: cdf(k, p) <= a / 2)
    return [round(lower, 4), round(upper, 4)]


def main():
    work = Path(sys.argv[sys.argv.index("--work") + 1]) if "--work" in sys.argv else Path(os.environ.get("TMPDIR", "/tmp")) / "exp3-work"
    work.mkdir(parents=True, exist_ok=True)
    for d in ("handoffs", "raw", "exploratory"):
        (RESULTS / d).mkdir(parents=True, exist_ok=True)
    sdk = subprocess.run(["dotnet", "--version"], capture_output=True, text=True, env=ENV, check=True).stdout.strip()
    rev = git_rev()
    scens = sorted(p.name for p in (P3 / "scenarios").iterdir() if re.fullmatch(r"[CD]\d\d", p.name))
    per = []
    for sid in scens:
        scen = json.loads((P3 / "scenarios" / sid / "scenario.json").read_text())
        dom = scen["domain"]
        tree = work / sid / "tree"
        materialize(scen, tree)
        h = build_handoff(sid, tree, rev)
        validate("echelon-authority-handoff-0.1.schema.json", h)
        hp = RESULTS / "handoffs" / f"{sid}.handoff.json"
        hp.write_text(json.dumps(h, indent=2) + "\n")
        raw = RESULTS / "raw" / f"{sid}.audit.json"
        code, err = run_audit(tree, hp, audit_files(dom, tree, "rules"), raw, sdk)
        rep = json.loads(raw.read_text())
        validate("echelon-provenance-audit-0.1.schema.json", rep)
        ex = RESULTS / "exploratory" / f"{sid}.all-src.audit.json"
        code2, _ = run_audit(tree, hp, audit_files(dom, tree, "all"), ex, sdk)
        exrep = json.loads(ex.read_text())

        lab = labels_for(sid, dom)
        planted_syms = {k for k, v in lab.items() if v[0] == "PLANTED"}
        mech = LABELS["plantedRules"].get(sid)
        scored = []
        for f in rep["findings"]:
            loc = f.get("location", {})
            sym = loc.get("symbol")
            key, l = resolve_label(lab, sym)
            cat = l[0] if l else "UNLABELLED"
            outcome = {"PLANTED": "TP", "SUPPORTED": "FQ", "TECHNICAL": "FQ", "UNLABELLED": "FQ",
                       "OTHER-UNAUTHORIZED": "OTHER"}[cat]
            scored.append({"id": f.get("id"), "class": f.get("class"), "certainty": f.get("certainty"),
                           "path": loc.get("path"), "line": loc.get("line"), "symbol": sym, "labelKey": key,
                           "label": cat, "basis": l[1] if l else None, "outcome": outcome,
                           "owner": f.get("owner"), "authorityRefs": f.get("authorityRefs"),
                           "message": f.get("message")})
        tps = [s for s in scored if s["outcome"] == "TP"]
        detected = bool(tps) if mech else None
        mech_ok = None
        if mech and tps:
            if mech == "superseded-value":
                mech_ok = any(s["class"] == "superseded-authority" for s in tps)
            elif mech == "silent-default":
                mech_ok = any("wildcard default" in (s["message"] or "") for s in tps)
            else:
                mech_ok = any("exemption" in (s["message"] or "") for s in tps)
        per.append({"scenario": sid, "domain": dom, "mechanism": mech, "plantedSymbols": sorted(planted_syms),
                    "auditExit": code, "auditSummary": err, "findings": len(scored),
                    "tp": len(tps), "fq": sum(s["outcome"] == "FQ" for s in scored),
                    "other": sum(s["outcome"] == "OTHER" for s in scored),
                    "detected": detected, "mechanismCorrect": mech_ok,
                    "exploratoryAllSrcOwnerQuestions": len(exrep["findings"]), "exploratoryExit": code2,
                    "scored": scored})
        print(f"{sid} {dom:8} exit={code} findings={len(scored)} tp={len(tps)} detected={detected} {err}")

    def agg(rows):
        n = sum(r["findings"] for r in rows)
        tp = sum(r["tp"] for r in rows)
        fq = sum(r["fq"] for r in rows)
        other = sum(r["other"] for r in rows)
        planted = [r for r in rows if r["mechanism"]]
        det = sum(1 for r in planted if r["detected"])
        split = {}
        for r in rows:
            for s in r["scored"]:
                if s["outcome"] == "FQ":
                    split[s["label"]] = split.get(s["label"], 0) + 1
        return {"scenarios": len(rows), "ownerQuestions": n, "tp": tp, "fq": fq, "other": other,
                "fqSplit": split, "plantedRules": len(planted), "detected": det,
                "recall": det / len(planted) if planted else None,
                "recallCI95": clopper_pearson(det, len(planted)) if planted else None,
                "precisionStrict": tp / n if n else None, "precisionLenient": (tp + other) / n if n else None,
                "precisionCI95": clopper_pearson(tp, n) if n else None,
                "falseQuestionRate": fq / n if n else None,
                "falseQuestionRateCI95": clopper_pearson(fq, n) if n else None,
                "mechanismCorrect": sum(1 for r in planted if r["mechanismCorrect"]),
                "missed": [r["scenario"] for r in planted if not r["detected"]]}

    scores = {
        "schema": "cbe.exp-3.scores/1", "auditCommit": subprocess.run(
            ["git", "-C", str(DOKIMOS), "log", "-1", "--format=%H"], capture_output=True, text=True).stdout.strip(),
        "sdk": sdk, "corpusRevision": rev,
        "aggregate": agg(per),
        "plantedScenariosOnly": agg([r for r in per if r["mechanism"]]),
        "withoutD08": agg([r for r in per if r["scenario"] != "D08"]),
        "byMechanism": {m: agg([r for r in per if r["mechanism"] == m])
                        for m in ("superseded-value", "exemption", "silent-default")},
        "byStage": {"confirmatory": agg([r for r in per if r["scenario"].startswith("C")]),
                    "discovery": agg([r for r in per if r["scenario"].startswith("D")])},
        "byDomain": {d: agg([r for r in per if r["domain"] == d]) for d in ("billing", "clinic", "lending")},
        "exploratoryAllSrcOwnerQuestions": sum(r["exploratoryAllSrcOwnerQuestions"] for r in per),
        "scenarios": per}
    (RESULTS / "scores.json").write_text(json.dumps(scores, indent=2) + "\n")
    a = scores["aggregate"]
    print(json.dumps({k: a[k] for k in a if k != "missed"} | {"missed": a["missed"]}, indent=1))


if __name__ == "__main__":
    main()
