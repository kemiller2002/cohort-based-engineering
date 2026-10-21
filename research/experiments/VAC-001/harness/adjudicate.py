"""VAC-001 Layer 3: reviewer agreement, disagreement list, unblinding and per-arm Layer 3 UDR (protocol section 7).

    python3 -I adjudicate.py agree REVIEW_DIR                 -> agreement JSON; writes REVIEW_DIR/disagreements.jsonl
    python3 -I adjudicate.py final REVIEW_DIR MAPPING DATASET -> final labelled dataset summary JSON

Pure functions over the label files; I/O only at the edges.
"""
import collections
import json
import pathlib
import sys

UNSUPPORTED = {"fabricated-premise", "stale-decision", "unsupported-requirement", "unverified-completion-claim"}
HALLUCINATION = {"fabricated-premise", "stale-decision", "unverified-completion-claim"}


def load(paths):
    return {o["key"]: o for p in paths for o in (json.loads(l) for l in p.read_text().splitlines() if l.strip())}


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def agree(review):
    r1 = load(sorted(review.glob("labels-R1-*.jsonl")))
    r2 = load(sorted(review.glob("labels-R2-*.jsonl")))
    keys = sorted(set(r1) & set(r2))
    pairs = [(r1[k]["label"], r2[k]["label"]) for k in keys]
    binary = [(a in UNSUPPORTED, b in UNSUPPORTED) for a, b in pairs]
    dis = [{"key": k, "R1": r1[k], "R2": r2[k]} for k in keys if r1[k]["label"] != r2[k]["label"]]
    (review / "disagreements.jsonl").write_text("".join(json.dumps(d) + "\n" for d in dis))
    return {"items": len(keys), "missingR1": sorted(set(r2) - set(r1)), "missingR2": sorted(set(r1) - set(r2)),
            "percentAgreement": round(sum(a == b for a, b in pairs) / len(pairs), 4) if pairs else None,
            "kappaLabel": round(kappa(pairs), 4) if kappa(pairs) is not None else None,
            "kappaUnsupportedBinary": round(kappa(binary), 4) if kappa(binary) is not None else None,
            "disagreements": len(dis),
            "labelCountsR1": dict(collections.Counter(a for a, _ in pairs)),
            "labelCountsR2": dict(collections.Counter(b for _, b in pairs))}


def final(review, mapping, dataset):
    r1 = load(sorted(review.glob("labels-R1-*.jsonl")))
    r2 = load(sorted(review.glob("labels-R2-*.jsonl")))
    r3 = load(sorted(review.glob("labels-R3-*.jsonl")))
    m = json.loads(mapping.read_text())["items"]
    def label(k):
        a, b = r1.get(k, {}).get("label"), r2.get(k, {}).get("label")
        return a if a == b else r3.get(k, {}).get("label", "unadjudicated")
    rows = [{**m[k], "key": k, "label": label(k), "R1": r1.get(k, {}).get("label"), "R2": r2.get(k, {}).get("label"),
             "R3": r3.get(k, {}).get("label"), "note": (r3.get(k) or r1.get(k) or {}).get("note")} for k in sorted(m)]
    by_arm = collections.defaultdict(list)
    for r in rows:
        by_arm[(r["run"], r["arm"])].append(r)
    per_arm = {f"{run}/{arm}": {"reviewed": len(rs),
                                "unsupported": sum(r["label"] in UNSUPPORTED for r in rs),
                                "hallucinationClass": sum(r["label"] in HALLUCINATION for r in rs),
                                "labels": dict(collections.Counter(r["label"] for r in rs))}
               for (run, arm), rs in sorted(by_arm.items())}
    pooled_arm = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        pooled_arm[r["arm"]]["reviewed"] += 1
        pooled_arm[r["arm"]]["unsupported"] += r["label"] in UNSUPPORTED
        pooled_arm[r["arm"]]["hallucinationClass"] += r["label"] in HALLUCINATION
    # Layer 1 accuracy against the adjudicated label: Layer 1 flags invalid/no-evidence; truth = fabricated/stale/unverified
    tp = sum(r["layer1"] in ("invalid-evidence", "no-evidence") and r["label"] in HALLUCINATION for r in rows)
    fp = sum(r["layer1"] in ("invalid-evidence", "no-evidence") and r["label"] not in HALLUCINATION for r in rows)
    fn = sum(r["layer1"] not in ("invalid-evidence", "no-evidence") and r["label"] in HALLUCINATION for r in rows)
    (review / "adjudicated.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return {"schema": "cbe.vac-001.layer3/1", "reviewed": len(rows), "labels": dict(collections.Counter(r["label"] for r in rows)),
            "perArmRun": per_arm, "perArm": {a: dict(c) for a, c in sorted(pooled_arm.items())},
            "layer1VsAdjudicated": {"truePositive": tp, "falsePositive": fp, "falseNegative": fn,
                                    "note": "Layer 1 flags only invalid or missing evidence; positives = adjudicated fabricated-premise, stale-decision or unverified-completion-claim"}}


if __name__ == "__main__":
    cmd, review = sys.argv[1], pathlib.Path(sys.argv[2])
    out = agree(review) if cmd == "agree" else final(review, pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4]))
    print(json.dumps(out, indent=1))
