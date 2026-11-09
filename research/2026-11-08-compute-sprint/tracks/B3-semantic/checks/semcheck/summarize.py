"""Build ../results.csv from ../raw/<package>.json (one row per package x check variant)."""
import csv
import json
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "raw"
FILES = ("R8-frozen", "R8-corrected", "R10-frozen", "Causa-frozen")
PRIMARY = {"C1-loop", "C2"}


def subject(k, a):
    if k.startswith("C1"):
        return "%s:%s[%s]" % (a["invariant"], a["transition"], a["bound"])
    if k.startswith("C2"):
        return a["candidate"]
    if k == "C3":
        return "%s/%s(%s)" % (a["state"], a["event"], ",".join(a["transitions"]))
    return ""


def caught(label, k, res):
    if label != "R8-frozen" and not (label == "Causa-frozen" and k.startswith("C4")):
        return ""
    if k.startswith("C1"):
        return "R8-INV04 CAUGHT" if any(a["invariant"] == "INV-04" and a["machine"] == "SM-SAVE" and a["transition"] in
                                        ("T-S31", "T-S32") for a in res) else "R8-INV04 NOT CAUGHT"
    if k == "C2":
        return "R8-CMDBODY CAUGHT" if any(a["type"] == "CommandEnvelope" or a["candidate"] == "type CommandEnvelope"
                                          for a in res) else "R8-CMDBODY NOT CAUGHT"
    if k == "C2b":
        return "EventPayload (DEV-R8-09 part) " + ("FLAGGED" if res else "not flagged")
    if k == "C3":
        return "DEV-R8-12 " + ("FLAGGED" if any(a["state"] == "UnknownOutcome" and a["event"] == "ReconcileReadFailed"
                                                 for a in res) else "not flagged")
    if k.startswith("C4"):
        ok = any("SL-T18" in c["slices"] and "SL-T20" in c["slices"] and "SL-T18->SL-T20" in c["impliedEdgesInside"]
                 for c in res["cycles"])
        return "CAUSA-CYCLE " + ("DETECTABLE" if ok else "NOT DETECTED")
    return ""


def main():
    rows = []
    for f in FILES:
        d = json.loads((RAW / (f + ".json")).read_text())
        for k, res in d["results"].items():
            if k.endswith("-examined"):
                continue
            if k.startswith("C4"):
                n = len(res["cycles"])
                subj = "; ".join("SCC%d[%s] implied:%s" % (c["size"], ",".join(c["slices"]) if c["size"] <= 8 else "...",
                                                           ",".join(c["impliedEdgesInside"]) if c["size"] <= 8 else
                                                           "%d edges" % len(c["impliedEdgesInside"])) for c in res["cycles"])
            else:
                n = len(res)
                subj = "; ".join(sorted({subject(k, a) for a in res}))
            rows.append({"package": f, "role": d["role"], "commit": d["rev"][:7], "packageDir": d["package"], "check": k,
                         "primary": "yes" if k in PRIMARY else "no", "alarms": n,
                         "outcome": caught(f, k, res) or ("control: %d alarm(s)" % n),
                         "alarmSubjects": subj, "checkSeconds": d["timing"].get(k, ""),
                         "loadSeconds": d["timing"]["loadSeconds"]})
    with open(RAW.parent / "results.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["package"], r["check"], r["alarms"], r["outcome"])


if __name__ == "__main__":
    main()
