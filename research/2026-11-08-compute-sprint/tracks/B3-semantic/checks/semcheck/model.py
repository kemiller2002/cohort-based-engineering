"""Package model: state machines and quantitative invariant clauses, parsed from JSON into immutable tuples.

Loaders accept the two machine formats seen in Indy-init packages:
  * a transition list  {machines:[{id, initial, transitions:[{id, from, event, to, guard, effects}]}]}
  * a pair table       {machines:[{id, initial, pairs:[{state, event, outcome, transitions:[{id, guard, next, effects}]}]}]}
Nothing here is specific to SM-SAVE or INV-04.
"""
import re
from typing import NamedTuple, Optional

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "twelve": 12, "twenty": 20, "a": 1, "an": 1}
NUM = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|twenty)"
TIME_UNITS = {"s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1, "min": 60, "mins": 60, "minute": 60,
              "minutes": 60, "h": 3600, "hour": 3600, "hours": 3600}
STOP_NOUNS = {"is", "was", "has", "as", "this", "its", "his", "does", "seconds", "minutes", "hours", "times", "less",
              "unless", "plus", "thus", "always", "towards", "across", "process"}


class Transition(NamedTuple):
    id: str
    src: str
    event: str
    dst: str
    guard: str
    effects: tuple


class Machine(NamedTuple):
    id: str
    initial: str
    transitions: tuple


class Bound(NamedTuple):
    invariant: str
    count: int
    phrase: str          # noun phrase as written, e.g. "reconciliation reads"
    head: str            # head noun, e.g. "reads"
    window_s: Optional[float]  # None = count bound with no time window
    clause: str
    machines: tuple      # machine ids the invariant names (empty = all)


def num(tok: str) -> int:
    return int(tok) if tok.isdigit() else NUMBER_WORDS[tok.lower()]


def stem(head: str) -> str:
    h = head.lower()
    return h[:-1] if h.endswith("s") and not h.endswith("ss") else h


def load_machines(doc: dict) -> tuple:
    def from_list(m):
        return tuple(Transition(t["id"], t["from"], t["event"], t["to"], t.get("guard", ""), tuple(t.get("effects", [])))
                     for t in m["transitions"])

    def from_pairs(m):
        return tuple(Transition(t["id"], p["state"], p["event"], t["next"], t.get("guard", ""), tuple(t.get("effects", [])))
                     for p in m["pairs"] if p.get("outcome") == "legal" for t in p.get("transitions", []))

    return tuple(Machine(m["id"], m.get("initial", ""), from_list(m) if "transitions" in m else from_pairs(m))
                 for m in doc["machines"])


WINDOW_RE = re.compile(r"\b(?:in|within|per|over|during)\s+(?:any\s+|a\s+|each\s+)?(\d+(?:\.\d+)?|one|a)?\s*"
                       r"(seconds?|secs?|s|minutes?|mins?|hours?|h)\b", re.I)
ITEM_RE = re.compile(r"\b(" + NUM + r")\s+((?:[a-z][a-z-]*\s+){0,3}?)([a-z][a-z-]{2,}s)\b", re.I)


def parse_bounds(inv: dict) -> tuple:
    """Quantitative 'at most N <noun>s [in W <unit>]' clauses of one invariant statement."""
    out = []
    for clause in re.split(r";", inv.get("statement", "")):
        lower = clause.lower()
        if "at most" not in lower:
            continue
        w = WINDOW_RE.search(lower)
        window = None
        if w and w.group(1) is not None:
            n = 1 if w.group(1) in ("one", "a") else float(w.group(1))
            window = n * TIME_UNITS[w.group(2).lower()]
        tail = clause[lower.index("at most"):]
        for m in ITEM_RE.finditer(tail):
            head = m.group(3)
            if head.lower() in STOP_NOUNS or head.lower() in TIME_UNITS:
                continue
            out.append(Bound(inv["id"], num(m.group(1)), (m.group(2) + head).strip(), head, window, clause.strip(),
                             tuple(inv.get("machines", []))))
    return tuple(out)


def load_bounds(doc: dict) -> tuple:
    invs = doc["invariants"] if isinstance(doc, dict) else doc
    return tuple(b for i in invs for b in parse_bounds(i))
