"""Pure matching functions for SPR-B4-01 (no I/O). Criteria are those preregistered in protocols/SPR-B4-01.md."""

SECTIONS = ("blockingContradictions", "missingInterfaces", "missingDecisions", "warnings")


def findings(report):
    """All findings of a percepta.specification-preflight/1 report, de-duplicated by (rule, subjects)."""
    seen = {}
    for section in SECTIONS:
        for f in report.get(section, []) or []:
            key = (f.get("rule"), tuple(f.get("subjects", [])))
            seen.setdefault(key, f)
    return list(seen.values())


def is_inv04(f):
    s = f.get("subjects", [])
    return (f.get("rule") == "rate-bound-vs-unbounded-loop" and f.get("blocking") is True
            and "INV-04" in s and "SM-SAVE" in s and ("T-S31" in s or "T-S32" in s))


def is_cmdbody(f):
    s = f.get("subjects", [])
    return f.get("rule") == "carrier-cannot-discriminate" and f.get("blocking") is True and s[:1] == ["CommandEnvelope"]


def is_dev_r8_12(f):
    return (f.get("rule") == "counter-guard-without-complement" and "SM-SAVE" in f.get("subjects", [])
            and "(UnknownOutcome, ReconcileReadFailed)" in f.get("detail", ""))


def mentions_t18_t20(f):
    text = " ".join(f.get("subjects", [])) + " " + f.get("detail", "")
    return "T18" in text and "T20" in text


DEFECTS = (("R8-INV04", is_inv04), ("R8-CMDBODY", is_cmdbody), ("DEV-R8-12", is_dev_r8_12),
           ("CAUSA-T18-T20", mentions_t18_t20))


def label(f):
    return f"{f.get('rule')}:{'/'.join(f.get('subjects', []))}"


def classify(report):
    """Per-defect outcome plus findings matched to no defect (extra / false-alarm candidates)."""
    fs = findings(report)
    matched = {name: [label(f) for f in fs if pred(f)] for name, pred in DEFECTS}
    claimed = {label(f) for name, pred in DEFECTS for f in fs if pred(f)}
    unmatched = [f for f in fs if label(f) not in claimed]
    return {
        "blocked": report.get("blocked"),
        "defects": {name: {"caught": bool(m), "by": m} for name, m in matched.items()},
        "unmatched": [{"label": label(f), "blocking": f.get("blocking"), "kind": f.get("kind"),
                       "detail": f.get("detail")} for f in unmatched],
        "unmatchedBlocking": sum(1 for f in unmatched if f.get("blocking") is True),
        "unmatchedNonBlocking": sum(1 for f in unmatched if f.get("blocking") is not True),
        "analysed": report.get("analysed"),
    }


def median(xs):
    s = sorted(xs)
    n = len(s)
    return None if n == 0 else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)
