"""C3 (secondary, exploratory): a legal (state, event) pair whose transitions are guarded by a remaining budget
('fewer than N', 'limit not reached', 'left', 'remaining') must also have a transition for the exhausted budget
('already', 'reached', 'spent', 'exhausted', 'no ... left'); otherwise the machine has no move when the budget runs out."""
import re

BUDGET = re.compile(r"fewer than|less than|not (?:yet )?reached|\bleft\b|remaining", re.I)
EXHAUSTED = re.compile(r"\balready\b|(?<!not )\breached\b|\bspent\b|\bexhausted\b|\bno\b[\w\s]*\bleft\b|\bat least\b", re.I)


def check(machines):
    alarms = []
    for m in machines:
        pairs = {}
        for t in m.transitions:
            pairs.setdefault((t.src, t.event), []).append(t)
        for (s, e), ts in sorted(pairs.items()):
            budget = [t for t in ts if BUDGET.search(t.guard)]
            exhausted = [t for t in ts if EXHAUSTED.search(BUDGET.sub("", t.guard))]
            if budget and not exhausted:
                alarms.append({"check": "C3", "machine": m.id, "state": s, "event": e,
                               "transitions": [t.id for t in ts], "guards": [t.guard for t in ts],
                               "reason": "guards depend on a remaining budget but no transition covers the exhausted "
                                         "budget: the pair has no legal move when it runs out"})
    return alarms
