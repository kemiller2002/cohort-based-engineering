#!/usr/bin/env python3
"""Build EVIDENCE-INDEX.json and FINDINGS.md from track findings, verifier verdicts and Director-level findings.

Pure functions over loaded data; the only side effects are in main(). Run from the sprint directory:
    python3 -I -B inventory/build_evidence.py [--check]
--check exits 1 if the generated files differ from the ones on disk.
"""
from __future__ import annotations

import json
import os
import re
import sys
from functools import reduce

SPRINT = "research/2026-11-08-compute-sprint"
CLASSES = ("VERIFIED", "SUPPORTED", "INCONCLUSIVE", "CONTRADICTED", "NOT TESTED")
VERIFIERS = ("V1", "V2", "V3", "V4", "V5", "V6")

# Director-level findings: experiment and safety results recorded in experiment reports rather than findings.json.
X = f"{SPRINT}/tracks/D2-agent-experiment"
DIRECTOR = (
    ("SPR-D2-01", "D2-agent-experiment", "SUPPORTED",
     "Governance block on the session model: no measurable authorization effect at ceiling; +6.1% tokens, +55% wall",
     [f"{X}/REPORT.md"], ["SPR-D2-01"]),
    ("SPR-D2-02/03", "D2-agent-experiment", "VERIFIED",
     "Ungoverned session-model baseline raises NotSpecified at all silent traps and refuses planted pseudo-decisions (stage-1 STOP, both fixtures)",
     [f"{X}/spr-d2-02/RESULT-STAGE1.md", f"{X}/spr-d2-03/RESULT-STAGE1.md"], ["D2-F-05", "D2-F-06"]),
    ("SPR-D3-01", "D2-agent-experiment", "SUPPORTED",
     "Ungoverned continuous 6-step chain stays compliant (stage-1 STOP, n=1 pilot chain)",
     [f"{X}/spr-d3-01/RESULT-STAGE1.md"], []),
    ("SPR-D4-01", "D2-agent-experiment", "SUPPORTED",
     "Ungoverned pilots do not over-claim status (0 over-claims; stage-1 STOP, n=2)",
     [f"{X}/spr-d4-01/RESULT-STAGE1.md"], []),
    ("X-F-01", "D2-agent-experiment", "SUPPORTED",
     "Haiku baseline invents policy where Sonnet and the session model do not (exploratory, n=1 per cell)",
     [f"{X}/spr-x-01/RESULT.md"], ["SPR-X-01"]),
    ("X-F-02", "D2-agent-experiment", "VERIFIED",
     "On Haiku the governance prompt reduces strict-measure violations by 2.17/run summed over two fixtures (stratified exact permutation p=0.00028)",
     [f"{X}/spr-x-02/REPORT.md", f"{X}/spr-x-02/harness/x02.py"], ["SPR-X-02"]),
    ("X-F-03", "D2-agent-experiment", "SUPPORTED",
     "Governance prompt cost replicates: about +7.6% tokens and +40% wall-clock on Haiku",
     [f"{X}/spr-x-02/REPORT.md"], ["SPR-X-02:secondaries-and-cost"]),
    ("X-F-05", "D2-agent-experiment", "VERIFIED",
     "On Haiku the Authority contract alone carries the benefit; the checklist alone does not (C vs K p=0.00046)",
     [f"{X}/spr-x-03/REPORT.md", f"{X}/spr-x-03/harness/x03.py"], ["SPR-X-03"]),
    ("X-F-07", "D2-agent-experiment", "SUPPORTED",
     "Documenting is not refusing: a question-listing checklist lets Haiku list a gap and still implement a default",
     [f"{X}/spr-x-03/REPORT.md"], ["SPR-X-03.descriptive-vs-X-02", "SPR-X-03.T5 (X-F-08)"]),
    ("X4-F-01", "D2-agent-experiment", "INCONCLUSIVE",
     "Authority contract did not significantly reduce violations in a second domain (booking): 4.125 vs 5.0, p=0.077; evidence against generality at the X-02/X-03 effect size",
     [f"{X}/spr-x-04/REPORT.md", f"{X}/spr-x-04/results/results.json"], ["SPR-X-04", "SPR-X-04.rescore", "SPR-X-04.scoring-order"]),
    ("X4-F-02", "D2-agent-experiment", "VERIFIED",
     "Authority contract raised tokens +9.9% (Holm p=0.0099) and wall-clock +38% (Holm p=0.0047) on the booking fixture",
     [f"{X}/spr-x-04/results/results.json", f"{X}/spr-x-04/results/usage.json"], ["SPR-X-04"]),
    ("X4-F-04", "D2-agent-experiment", "SUPPORTED",
     "Contract reductions appear only at visibly unspecified gaps (DST recurrence, cancelled-quota), never where a plausible default exists",
     [f"{X}/spr-x-04/REPORT.md"], []),
    ("SO-01", "D2-agent-experiment", "VERIFIED",
     "Haiku implementation subagents made 5 off-task session-tool calls (send_message, create_session, list_sessions, archive_session x2); none took effect; containment relied on validation and the classifier",
     [f"{SPRINT}/DECISION-LOG.md"], []),
)

# Classification changes made by the Director on later evidence (decision id, new class, reason).
OVERRIDES = {
    "B2-F-07": ("D-025", "CONTRADICTED", "B3 contradicts B2 on the Causa slice-plan cycle; H X-24 resolved for B/B3"),
}


def load(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def as_list(d, key: str) -> list:
    return d if isinstance(d, list) else d.get(key, [])


def expand_claim(claim_id: str) -> list[str]:
    """'A2-F-01/02' -> ['A2-F-01', 'A2-F-02']; other ids unchanged."""
    m = re.fullmatch(r"([A-Z0-9]+-F-)(\d+)/(\d+)", claim_id)
    return [m.group(1) + m.group(2), m.group(1) + m.group(3)] if m else [claim_id]


def normalise_class(c: str) -> str:
    return next((k for k in CLASSES if c.upper().startswith(k)), "NOT TESTED" if c.upper().startswith("NOT") else c)


def verdict_rows(root: str) -> list[dict]:
    paths = [(v, os.path.join(root, f"tracks/{v}-verification/verdicts.json")) for v in VERIFIERS]
    return [{"verifier": v, "claim": cid, "verdict": x["verdict"],
             "path": f"{SPRINT}/tracks/{v}-verification/verdicts.json"}
            for v, p in paths if os.path.exists(p)
            for x in as_list(load(p), "verdicts")
            for cid in expand_claim(x["claimId"])]


def track_findings(root: str) -> list[dict]:
    tracks = sorted(d for d in os.listdir(os.path.join(root, "tracks"))
                    if os.path.exists(os.path.join(root, "tracks", d, "findings.json")))
    return [{"id": x["id"], "track": t, "title": x["title"], "classification": normalise_class(x["classification"]),
             "trackClassification": x["classification"], "statement": x["statement"],
             "measuredOrEstimate": x.get("measuredOrEstimate"),
             "evidence": [e if e.startswith("research/") else f"{SPRINT}/tracks/{t}/{e}" for e in x["evidence"]],
             "limitations": x.get("limitations"), "source": f"{SPRINT}/tracks/{t}/findings.json"}
            for t in tracks for x in as_list(load(os.path.join(root, "tracks", t, "findings.json")), "findings")]


def director_findings() -> list[dict]:
    return [{"id": i, "track": t, "title": title, "classification": c, "trackClassification": c, "statement": title,
             "measuredOrEstimate": "MEASURED", "evidence": ev, "limitations": "See linked report",
             "source": "Director-level (experiment report)", "verifierClaims": vc}
            for i, t, c, title, ev, vc in DIRECTOR]


def attach(finding: dict, verdicts: list[dict]) -> dict:
    keys = {finding["id"], *finding.get("verifierClaims", [])}
    vs = [v for v in verdicts if v["claim"] in keys or v["claim"].split(":")[0].split(".")[0] in keys]
    ov = OVERRIDES.get(finding["id"])
    base = {**finding, "independentVerification": [{k: v[k] for k in ("verifier", "claim", "verdict", "path")} for v in vs]}
    return {**base, "classification": ov[1], "override": {"decision": ov[0], "reason": ov[2]}} if ov else base


def build(root: str) -> dict:
    verdicts = verdict_rows(root)
    findings = [attach(f, verdicts) for f in track_findings(root) + director_findings()]
    count = lambda pred: sum(1 for f in findings if pred(f))
    return {"schema": "echelon-sprint-evidence/1",
            "generatedBy": f"{SPRINT}/inventory/build_evidence.py",
            "summary": {"findings": len(findings),
                        "byClass": {c: count(lambda f, c=c: f["classification"] == c) for c in CLASSES},
                        "independentlyChecked": count(lambda f: f["independentVerification"]),
                        "verifierVerdicts": len(verdicts)},
            "findings": findings,
            "unmatchedVerdicts": [v for v in verdicts
                                  if not any(attach(f, [v])["independentVerification"] for f in findings)]}


def md_cell(s) -> str:
    return str(s if s is not None else "").replace("|", "\\|").replace("\n", " ")


def render_findings(index: dict) -> str:
    s = index["summary"]
    head = ["# Findings (generated)", "",
            f"> Generated by `inventory/build_evidence.py` from each track's `findings.json`, verifier `verdicts.json` and "
            "Director-level experiment results. Do not edit by hand; edit the sources and rebuild.", "",
            f"**{s['findings']} findings.** " + ", ".join(f"{k}: {v}" for k, v in s["byClass"].items()) +
            f". Independently checked by a verifier track: {s['independentlyChecked']}.", "",
            "Classes follow the sprint brief: VERIFIED / SUPPORTED / INCONCLUSIVE / CONTRADICTED / NOT TESTED. "
            "A verifier verdict of PARTIALLY VERIFIED is shown next to the class and its correction is in the verifier's REPORT.md.", ""]
    by_track = reduce(lambda acc, f: {**acc, f["track"]: acc.get(f["track"], []) + [f]}, index["findings"], {})
    sections = [line for t in sorted(by_track) for line in
                [f"## {t}", "", "| ID | Class | Independent check | Finding |", "|---|---|---|---|"] +
                [f"| {f['id']} | {f['classification']}{' (override ' + f['override']['decision'] + ')' if f.get('override') else ''} | "
                 f"{md_cell('; '.join(v['verifier'] + ': ' + v['verdict'] for v in f['independentVerification']) or '—')} | "
                 f"{md_cell(f['title'])} |" for f in by_track[t]] + [""]]
    return "\n".join(head + sections)


def main(argv: list[str]) -> int:
    root = os.getcwd()
    index = build(root)
    outputs = {"EVIDENCE-INDEX.json": json.dumps(index, indent=1, ensure_ascii=False) + "\n",
               "FINDINGS.md": render_findings(index)}
    if "--check" in argv:
        stale = [p for p, text in outputs.items() if not os.path.exists(p) or open(p, encoding="utf-8").read() != text]
        print("stale:", stale) if stale else print("up to date")
        return 1 if stale else 0
    [open(p, "w", encoding="utf-8").write(text) for p, text in outputs.items()]
    print(json.dumps(index["summary"]), "unmatched verdicts:", [v["claim"] for v in index["unmatchedVerdicts"]])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
