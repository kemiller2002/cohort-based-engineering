"""C1: state machine vs quantitative invariant (bounded-trace counterexample search).

For a bound 'at most N <R> [in W]' on machine M, a transition t is an *unbounded emitter* when
  (E) one of its effects issues an R (emission cue before the R noun, no negation in that effect), and
  (B) neither its guard (strict) -- nor, in the delegation variant, its effects -- states a count over R or a time window,
  (P) its guard does not depend on a remaining budget (it stays true when t repeats).
A counterexample trace is: shortest event path from M.initial to t.src, then N+1 traversals of a repeatable cycle
through t (loop variant: t itself is a self-loop; cycle variant: t plus the shortest return path whose guards satisfy
(P)), with the cycle's stated delays summing (over N traversals) to less than W.
Guards are free text: they are treated as satisfiable unless (P) says otherwise (an over-approximation).
"""
import re
from collections import deque

from .model import NUM, stem

NEGATION = re.compile(r"\b(no|nothing|never|not|none|without|zero)\b", re.I)
CUES = {"send", "sends", "schedule", "schedules", "issue", "issues", "resend", "resends", "retry", "perform", "one",
        "another", "new", "fresh", "next", "a", "an", "extra", "additional", "immediate", "two", "three", "four"}
BUDGET = re.compile(r"fewer than|less than|not (?:yet )?reached|\bleft\b|remaining|\bbelow\b|\bunder\b|at most|up to|"
                    r"\bwithin\b", re.I)
TIME = re.compile(r"\b\d+(?:\.\d+)?\s*(?:s|secs?|seconds?|min|minutes?)\b", re.I)
DELAY = re.compile(r"\b(?:after (?:at least )?|at |in )(\d+(?:\.\d+)?)\s*(?:s|secs?|seconds?)\b", re.I)


def phrases(t):
    return tuple(p.strip() for e in t.effects for p in e.split(";") if p.strip())


def emits(t, head):
    word = re.compile(r"\b" + re.escape(stem(head)) + r"s?\b", re.I)
    for p in phrases(t):
        m = word.search(p)
        if not m:
            continue
        before = p[:m.start()]
        if NEGATION.search(before):
            continue
        if set(w.lower() for w in re.findall(r"[A-Za-z]+", before)[-4:]) & CUES:
            return True
    return False


def counts_resource(text, head):
    return bool(re.search(r"\b" + re.escape(stem(head)) + r"s?\b", text, re.I)) and bool(
        re.search(r"\b" + NUM + r"\b", text, re.I))


def bounded(t, b, delegation):
    if counts_resource(t.guard, b.head) or TIME.search(t.guard):
        return True
    if delegation and b.window_s is not None:
        w = int(b.window_s) if float(b.window_s).is_integer() else b.window_s
        return any(re.search(r"\b%s\s*(?:s|seconds?)\b" % re.escape(str(w)), e, re.I) for e in t.effects)
    return False


def repeatable(t):
    return not (BUDGET.search(t.guard) or TIME.search(t.guard))


def delay(t):
    ds = [float(m.group(1)) for e in t.effects for m in DELAY.finditer(e)]
    return min(ds) if ds else 0.0


def bfs(transitions, start, goal, allowed=lambda t: True):
    """Shortest transition path start -> goal (empty when start == goal); None when unreachable."""
    if start == goal:
        return ()
    seen, q = {start}, deque([(start, ())])
    while q:
        s, path = q.popleft()
        for t in transitions:
            if t.src == s and allowed(t) and t.dst not in seen:
                np = path + (t,)
                if t.dst == goal:
                    return np
                seen.add(t.dst)
                q.append((t.dst, np))
    return None


def check(machines, bounds, variant):
    """variant in {'loop', 'cycle'} x delegation flag: e.g. ('loop', False). Returns alarm dicts."""
    kind, delegation = variant
    alarms = []
    for b in bounds:
        for m in machines:
            if b.machines and m.id not in b.machines:
                continue
            for t in m.transitions:
                if not (emits(t, b.head) and not bounded(t, b, delegation) and repeatable(t)):
                    continue
                back = () if t.src == t.dst else (None if kind == "loop" else bfs(m.transitions, t.dst, t.src, repeatable))
                if back is None:
                    continue
                cycle = (t,) + back
                cyc_delay = sum(delay(x) for x in cycle)
                span = cyc_delay * b.count
                if b.window_s is not None and span >= b.window_s:
                    continue
                prefix = bfs(m.transitions, m.initial, t.src) or ()
                alarms.append({
                    "check": "C1-%s%s" % (kind, "-deleg" if delegation else ""),
                    "invariant": b.invariant, "bound": "at most %d %s%s" % (
                        b.count, b.phrase, "" if b.window_s is None else " in %g s" % b.window_s),
                    "machine": m.id, "transition": t.id, "guard": t.guard, "effects": list(t.effects),
                    "cycle": [x.id for x in cycle],
                    "witness": {"prefix": [x.event for x in prefix],
                                "repeat": [x.event for x in cycle], "times": b.count + 1,
                                "emissions": b.count + 1, "statedDelaySeconds": span},
                    "reason": "transition %s issues '%s' with no count or window in its guard and stays enabled when "
                              "repeated: %d traversals give %d > %d within %s" % (
                                  t.id, b.head, b.count + 1, b.count + 1, b.count,
                                  "a single trace" if b.window_s is None else "%g s (stated delays %g s)" % (b.window_s, span))})
    return alarms
