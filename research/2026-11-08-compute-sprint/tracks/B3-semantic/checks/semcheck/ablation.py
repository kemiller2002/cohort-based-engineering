"""POST HOC (D2): sensitivity of C1-loop to the rules that were chosen with the answer in view.

A0 preregistered; A1 emission = noun present and not negated (no cue); A2 exhausted-budget words (spent, reached,
already, limit) also block repetition; A3 every transition repeatable; A4 no negation handling (cue still required).
Writes ../raw/ablation.json; prints alarm counts per package and whether R8-INV04 is caught."""
import json
import re
from pathlib import Path

from . import model, rate
from .run import INVARIANTS, PACKAGES, REPO, show


def emits_naive(t, head):
    w = re.compile(r"\b" + re.escape(model.stem(head)) + r"s?\b", re.I)
    return any(w.search(p) and not rate.NEGATION.search(p[:w.search(p).start()]) for p in rate.phrases(t))


def emits_no_negation(t, head):
    w = re.compile(r"\b" + re.escape(model.stem(head)) + r"s?\b", re.I)
    for p in rate.phrases(t):
        m = w.search(p)
        if m and set(x.lower() for x in re.findall(r"[A-Za-z]+", p[:m.start()])[-4:]) & rate.CUES:
            return True
    return False


EXH = re.compile(r"\bspent\b|\breached\b|\balready\b|\blimit\b", re.I)
VARIANTS = {
    "A0-preregistered": {},
    "A1-naive-emission": {"emits": emits_naive},
    "A2-exhausted-blocks": {"repeatable": lambda t: rate.repeatable(t) and not EXH.search(t.guard)},
    "A3-all-repeatable": {"repeatable": lambda t: True},
    "A4-no-negation": {"emits": emits_no_negation},
}


def main():
    out = {}
    for label, role, rev, pkg, _ in PACKAGES:
        ms = model.load_machines(json.loads(show(REPO, rev, pkg + "/state-machine-contracts.json")))
        bs = model.load_bounds(json.loads(show(REPO, rev, INVARIANTS)))
        for v, kw in VARIANTS.items():
            a = rate.check(ms, bs, ("loop", False), **kw)
            caught = any(x["invariant"] == "INV-04" and x["machine"] == "SM-SAVE" and x["transition"] in ("T-S31", "T-S32")
                         for x in a)
            out.setdefault(v, {})[label] = {"alarms": len(a), "caughtINV04": caught,
                                            "transitions": sorted({(x["transition"], x["bound"]) for x in a})}
            print(v, label, len(a), "caught" if caught else "-", sorted({x["transition"] for x in a}))
    (Path(__file__).resolve().parents[2] / "raw" / "ablation.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
