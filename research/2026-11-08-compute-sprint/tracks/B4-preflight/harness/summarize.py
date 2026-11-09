"""Build results.csv and comparison.json from raw/ (spec-preflight runs) and B3's committed results.

Usage (from the track directory): python3 -I harness/summarize.py
"""
import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import classify  # noqa: E402

B3 = "/home/user/sprint-wt/B3-semantic/research/2026-11-08-compute-sprint/tracks/B3-semantic"
VERSIONS = ("v0.4.0-4a53688", "first-0ad2bd3")
FIELDS = ("version", "package", "commit", "packageDir", "role", "condition", "runs", "exits", "medianSeconds",
          "minSeconds", "maxSeconds", "reportsIdentical", "blocked", "R8-INV04", "R8-CMDBODY", "DEV-R8-12",
          "CAUSA-T18-T20", "unmatchedBlocking", "unmatchedNonBlocking", "findings")


def rows(track=TRACK):
    out = []
    for v in VERSIONS:
        path = os.path.join(track, "raw", v, "runs.json")
        if not os.path.exists(path):
            continue
        for r in json.load(open(path, encoding="utf-8")):
            rep = json.load(open(os.path.join(track, "raw", v, os.path.basename(r["report"])), encoding="utf-8"))
            c = classify.classify(rep)
            out.append({
                "version": v, "package": r["package"], "commit": r["commit"], "packageDir": r["packageDir"],
                "role": r["role"], "condition": r["condition"], "runs": len(r["exits"]),
                "exits": "/".join(map(str, r["exits"])), "medianSeconds": classify.median(r["seconds"]),
                "minSeconds": min(r["seconds"]), "maxSeconds": max(r["seconds"]),
                "reportsIdentical": r["reportsIdentical"], "blocked": rep.get("blocked"),
                **{d: c["defects"][d]["caught"] for d in ("R8-INV04", "R8-CMDBODY", "DEV-R8-12", "CAUSA-T18-T20")},
                "unmatchedBlocking": c["unmatchedBlocking"], "unmatchedNonBlocking": c["unmatchedNonBlocking"],
                "findings": "; ".join(classify.label(f) + ("" if f.get("blocking") else " (non-blocking)")
                                      for f in classify.findings(rep)),
            })
    return out


def csv_text(rs):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rs:
        w.writerow(r)
    return buf.getvalue()


def b3_rows():
    return list(csv.DictReader(open(os.path.join(B3, "results.csv"), encoding="utf-8")))


def b3_outcome(b3, package, check):
    r = next((x for x in b3 if x["package"] == package and x["check"] == check), None)
    return None if r is None else {"alarms": int(r["alarms"]), "outcome": r["outcome"], "subjects": r["alarmSubjects"]}


def comparison(rs, b3):
    doc = {r["package"]: r for r in rs if r["version"] == VERSIONS[0] and r["condition"] == "DOC"}
    ci = {r["package"]: r for r in rs if r["version"] == VERSIONS[0] and r["condition"] == "CI"}
    defects = [
        ("R8-INV04", "R8-frozen", "C1-loop", "INV-04 x SM-SAVE T-S31/T-S32"),
        ("R8-CMDBODY", "R8-frozen", "C2", "CommandEnvelope has no command body"),
        ("DEV-R8-12", "R8-frozen", "C3", "(UnknownOutcome, ReconcileReadFailed) unspecified at the read limit"),
        ("CAUSA-T18-T20", "Causa-frozen", "C4-browser", "T18<->T20 dependency cycle"),
    ]
    table = []
    for d, pkg, check, desc in defects:
        b = b3_outcome(b3, pkg, check)
        b3_caught = b is not None and ("CAUGHT" in b["outcome"] or "FLAGGED" in b["outcome"] or "DETECTABLE" in b["outcome"])
        sp = bool(doc[pkg][d]) if pkg in doc else None
        table.append({"defect": d, "description": desc, "package": pkg, "b3Check": check, "b3": b, "b3Caught": b3_caught,
                      "specPreflightDOC": sp, "specPreflightCI": bool(ci[pkg][d]) if pkg in ci else None,
                      "agreement": "both" if (b3_caught and sp) else "B3 only" if b3_caught else "spec-preflight only" if sp else "neither"})
    controls = ("R8-corrected", "R10-frozen", "Causa-frozen")
    primary = ("C1-loop", "C2")
    secondary = ("C1-cycle", "C2b", "C3", "C4-browser", "C4-all")
    false_alarms = {p: {"specPreflightBlocking": doc[p]["unmatchedBlocking"] + sum(doc[p][d] for d in ("R8-INV04", "R8-CMDBODY")),
                        "specPreflightNonBlocking": doc[p]["unmatchedNonBlocking"] + int(doc[p]["DEV-R8-12"]),
                        "specPreflightExit": doc[p]["exits"],
                        "b3Primary": sum((b3_outcome(b3, p, c) or {"alarms": 0})["alarms"] for c in primary),
                        "b3Secondary": {c: (b3_outcome(b3, p, c) or {"alarms": None})["alarms"] for c in secondary}}
                    for p in controls}
    return {"version": VERSIONS[0], "condition": "DOC", "perDefect": table, "controlFalseAlarms": false_alarms,
            "r8Extras": {"specPreflight": [x for x in doc["R8-frozen"]["findings"].split("; ")
                                           if "T-S29" not in x and "carrier" not in x and "rate-bound" not in x],
                         "b3": {c: (b3_outcome(b3, "R8-frozen", c) or {}).get("subjects") for c in ("C1-loop", "C2", "C2b", "C3")}}}


def main():
    rs = rows()
    with open(os.path.join(TRACK, "results.csv"), "w", encoding="utf-8") as fh:
        fh.write(csv_text(rs))
    with open(os.path.join(TRACK, "comparison.json"), "w", encoding="utf-8") as fh:
        json.dump(comparison(rs, b3_rows()), fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
