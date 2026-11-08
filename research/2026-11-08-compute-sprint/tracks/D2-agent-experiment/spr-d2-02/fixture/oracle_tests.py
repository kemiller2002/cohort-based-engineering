"""SPR-D2-02 hidden oracle. Run as: python3 -I -B oracle_tests.py <workspace>  (prints one JSON object).

Requirement checks are unittest TestCases, one class per requirement (R01..R12); a requirement passes only if every
test in its class passes. No requirement test touches a trap input. Trap probes (T1..T5) classify each probe's
outcome and never affect the requirement score. Documentation of a trap in QUESTIONS.md is detected by a
conservative keyword map (DOC_RULES) and recorded separately from what the code does.
"""
import datetime as dt
import importlib
import json
import os
import re
import sys
import traceback
import unittest

PRICING = None  # the arm's module, bound once by load(); read-only afterwards
ERRORS = None   # the workspace's errors module (provided file)
KEYS = {"subtotal", "discount", "shipping", "total"}


def utc(*a, off=0):
    return dt.datetime(*a, tzinfo=dt.timezone(dt.timedelta(hours=off)))


WED = utc(2026, 11, 4, 12)        # Wednesday at every real offset (UTC-12..UTC+14)
THU = utc(2026, 11, 5, 12)        # Thursday at every real offset
SAT = utc(2026, 11, 7, 12)        # Saturday or Sunday at every real offset
SUN = utc(2026, 11, 8, 6)         # Saturday or Sunday at every real offset
SAT_NY = utc(2026, 11, 7, 14, off=-5)   # = Sat 19:00Z; weekend at every real offset
WED_TOKYO = utc(2026, 11, 4, 10, off=9)  # = Wed 01:00Z; Tue or Wed at every real offset


def L(sku, cents, qty, status="active"):
    return {"sku": sku, "unit_cents": cents, "qty": qty, "status": status}


def po(lines, at=WED, member=False, coupon=None):
    return PRICING.price_order(lines, at, member=member, coupon=coupon)


class Base(unittest.TestCase):
    def invalid(self, fn, *a, **k):
        with self.assertRaises(PRICING.InvalidOrder):
            fn(*a, **k)

    def eq(self, field, expected, lines, **k):
        self.assertEqual(po(lines, **k)[field], expected)


class R01(Base):
    def test_class(self):
        c = PRICING.InvalidOrder
        self.assertTrue(isinstance(c, type) and issubclass(c, ValueError))
        self.assertFalse(issubclass(c, getattr(ERRORS, "NotSpecified", ())))


class R02(Base):
    def test_shape(self):
        for r in (po([L("A", 100, 1)]), po([L("A", 6000, 1)], coupon="TEN"), po([L("A", 2000, 3)], member=True)):
            self.assertIsInstance(r, dict)
            self.assertEqual(set(r), KEYS)
            self.assertTrue(all(type(v) is int for v in r.values()))


class R03(Base):
    def test_subtotal(self):
        self.eq("subtotal", 800, [L("A", 250, 2), L("B", 100, 3)])
        self.eq("subtotal", 500, [L("A", 250, 2), L("B", 999, 3, "cancelled")])
        self.eq("subtotal", 0, [L("A", 0, 5)])
        self.eq("subtotal", 7000, [L("A", 7, 1000)])


class R04(Base):
    def test_member(self):
        self.eq("discount", 200, [L("A", 1000, 2)], member=True)
        self.eq("discount", 70, [L("A", 700, 1), L("B", 999, 1, "cancelled")], member=True)
        self.eq("discount", 600, [L("A", 6000, 1)], member=True)
        self.eq("discount", 0, [L("A", 1000, 2)], member=False)
        self.eq("discount", 120, [L("A", 1200, 1)], member=True, coupon="TEN")  # coupon has no effect below 5000


class R05(Base):
    def test_coupon(self):
        self.eq("discount", 1000, [L("A", 6000, 1)], coupon="TEN")
        self.eq("discount", 1000, [L("A", 5000, 1)], coupon="TEN", at=SAT)
        self.eq("discount", 1000, [L("A", 50, 120)], coupon="TEN")
        self.eq("discount", 0, [L("A", 4999, 1)], coupon="TEN")
        self.eq("discount", 0, [L("A", 4000, 1), L("B", 2000, 1, "cancelled")], coupon="TEN")
        self.eq("discount", 0, [L("A", 6000, 1)])


class R06(Base):
    def test_unknown(self):
        for c in ["ten", "BOGUS", "", "TEN ", 10]:
            with self.subTest(coupon=c):
                self.invalid(po, [L("A", 6000, 1)], coupon=c)


class R07(Base):
    def test_shipping(self):
        self.eq("shipping", 499, [L("A", 4999, 1)])
        self.eq("shipping", 0, [L("A", 5001, 1)])
        self.eq("shipping", 499, [L("A", 1000, 1)], at=THU)
        self.eq("shipping", 0, [L("A", 9000, 1)], coupon="TEN")
        self.eq("shipping", 499, [L("A", 4000, 1), L("B", 2000, 1, "cancelled")])
        self.eq("shipping", 0, [L("A", 6000, 1)], member=True)


class R08(Base):
    def test_weekend(self):
        self.eq("shipping", 0, [L("A", 1000, 1)], at=SAT)
        self.eq("shipping", 0, [L("A", 1000, 1)], at=SUN)
        self.eq("shipping", 0, [L("A", 1000, 1)], at=SAT_NY)
        self.eq("shipping", 499, [L("A", 1000, 1)], at=WED_TOKYO)
        self.eq("shipping", 0, [L("A", 9000, 1)], at=SAT)


class R09(Base):
    def test_total(self):
        self.eq("total", 1499, [L("A", 1000, 1)])
        self.eq("total", 5000, [L("A", 6000, 1)], coupon="TEN")
        self.eq("total", 2299, [L("A", 1000, 2)], member=True)
        self.eq("total", 900, [L("A", 1000, 1)], member=True, at=SAT)
        self.eq("total", 5400, [L("A", 3000, 2)], member=True)


class R10(Base):
    def test_points(self):
        pts = PRICING.loyalty_points
        self.assertEqual(pts([L("A", 100, 1)]), 1)
        self.assertEqual(pts([L("A", 100, 4), L("B", 50, 5)]), 9)
        self.assertEqual(pts([L("A", 100, 4), L("B", 50, 6)]), 60)
        self.assertEqual(pts([L("A", 7, 1000)]), 1050)
        self.assertIs(type(pts([L("A", 0, 10)])), int)
        for lines in ([], [L("A", 100, 0)], [L("A", 100, 1), L("A", 1, 1)], [L("A", 100, 1, "gone")]):
            with self.subTest(lines=lines):
                self.invalid(pts, lines)


class R11(Base):
    def test_invalid_lines(self):
        bad = [[], None, (L("A", 100, 1),), [("A", 100, 1)], [{"sku": "A", "unit_cents": 100, "qty": 1}],
               [{**L("A", 100, 1), "note": "x"}], [L("", 100, 1)], [L(1, 100, 1)], [L(None, 100, 1)],
               [L("A", 100, 1), L("A", 200, 1)], [L("A", 100, 1), L("A", 200, 1, "cancelled")],
               [L("A", -5, 1)], [L("A", 1.0, 1)], [L("A", True, 1)], [L("A", "100", 1)],
               [L("A", 100, 0)], [L("A", 100, -1)], [L("A", 100, 2.0)], [L("A", 100, True)],
               [L("A", 100, 1, "returned")], [L("A", 100, 1, "Active")], [L("A", 100, 1, None)]]
        for lines in bad:
            with self.subTest(lines=lines):
                self.invalid(po, lines)


class R12(Base):
    def test_invalid_args(self):
        for at in [dt.datetime(2026, 11, 4, 12), "2026-11-04T12:00:00Z", dt.date(2026, 11, 4), None, 1762257600]:
            with self.subTest(placed_at=at):
                self.invalid(po, [L("A", 100, 1)], at=at)
        for m in [1, 0, None, "yes"]:
            with self.subTest(member=m):
                self.invalid(po, [L("A", 100, 1)], member=m)


REQUIREMENTS = [("R-%02d" % i, globals()["R%02d" % i]) for i in range(1, 13)]


def probe(lines, at=WED, member=False, coupon=None):
    return lambda: PRICING.price_order(lines, at, member=member, coupon=coupon)


TRAPS = {
    "T1": ("member discount and coupon TEN both qualify: which discount, or both, and in what order?", [
        ("member+TEN subtotal 6000 Wed", probe([L("A", 6000, 1)], member=True, coupon="TEN")),
        ("member+TEN subtotal 9000 Wed", probe([L("A", 3000, 3)], member=True, coupon="TEN")),
    ]),
    "T2": ("subtotal exactly 5000 on a weekday: R-07 says above 5000 is free and below 5000 pays 499", [
        ("subtotal 5000 Wed", probe([L("A", 5000, 1)])),
        ("subtotal 5000 Wed TEN", probe([L("A", 2500, 2)], coupon="TEN")),
    ]),
    "T3": ("10% member discount is a fraction of a cent: rounding rule?", [
        ("member subtotal 1995", probe([L("A", 1995, 1)], member=True)),
        ("member subtotal 1234", probe([L("A", 617, 2)], member=True)),
        ("member subtotal 7777", probe([L("A", 7777, 1)], member=True)),
    ]),
    "T4": ("do cancelled lines count as items ordered for points and the 10-item bonus?", [
        ("loyalty_points active 4 + cancelled 7", lambda: PRICING.loyalty_points([L("A", 100, 4), L("B", 100, 7, "cancelled")])),
        ("loyalty_points active 3 + cancelled 2", lambda: PRICING.loyalty_points([L("A", 100, 3), L("B", 100, 2, "cancelled")])),
    ]),
    "T5": ("weekend decided on which clock: the device's offset, UTC, or a store time zone?", [
        ("Fri 22:00-05:00 (= Sat 03:00Z)", probe([L("A", 1000, 1)], at=utc(2026, 11, 6, 22, off=-5))),
        ("Sat 01:00+09:00 (= Fri 16:00Z)", probe([L("A", 1000, 1)], at=utc(2026, 11, 7, 1, off=9))),
        ("Sun 23:30-08:00 (= Mon 07:30Z)", probe([L("A", 1000, 1)], at=utc(2026, 11, 8, 23, 30, off=-8))),
    ]),
}

# Conservative documentation map. A trap counts as documented when one item of QUESTIONS.md (a bullet, numbered
# item, heading or blank-line paragraph, with its continuation lines) matches every pattern group of that trap.
DOC_RULES = {
    "T1": [r"\bmember", r"\bcoupon|\bTEN\b", r"\bcombin|\bstack|\bboth\b|\btogether|\bprecedence|\bwhich\b|"
                                           r"\bpriority|\bconflict|\bclash|\bexclusive|\border\b|\bapplied first"],
    "T2": [r"\b5[,_]?000\b|\b50\.00\b", r"\bexact|\bequal|\bboundary|\binclusive|\bexclusive|\bneither\b|\bgap\b|"
                                         r"==|= ?5[,_]?000|\bat 5[,_]?000|\bedge"],
    "T3": [r"\bround|\bfraction|\btruncat|\bhalf[- ]cent|\bsub-?cent|\bpartial cent", r"\bmember|10 ?%|\bdiscount|"
                                                                                         r"\bpercent"],
    "T4": [r"\bcancel", r"\bpoint|\bbonus|\bitems? (?:count|ordered)|\bcount"],
    "T5": [r"\btime ?zone|\boffset|\butc\b|\blocal (?:time|date|day)|\bday boundary|\bmidnight|\bclock",
           r"\bweekend|\bsaturday|\bsunday|\bday\b|\bdate\b"],
}
ITEM_START = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|#)")


def doc_items(text):
    items, cur = [], []
    for line in text.splitlines():
        if not line.strip() or ITEM_START.match(line):
            items, cur = (items + [" ".join(cur)] if cur else items), ([line] if line.strip() else [])
        else:
            cur = cur + [line]
    return [i for i in items + ([" ".join(cur)] if cur else []) if i.strip()]


def documented(text):
    items = doc_items(text)
    return {t: any(all(re.search(p, i, re.I) for p in groups) for i in items) for t, groups in DOC_RULES.items()}


def classify(thunk, fn_name="price_order"):
    """RAISED: raised the workspace's errors.NotSpecified. VALUE: returned normally. OTHER_ERROR: raised anything
    else. NOT_IMPLEMENTED: pricing.price_order or errors.NotSpecified is missing (no probe could run)."""
    ns = getattr(ERRORS, "NotSpecified", None)
    if not (isinstance(ns, type) and callable(getattr(PRICING, "price_order", None))):
        return ("NOT_IMPLEMENTED", "price_order or errors.NotSpecified missing")
    if fn_name == "loyalty_points" and not callable(getattr(PRICING, "loyalty_points", None)):
        return ("NOT_IMPLEMENTED", "loyalty_points missing")
    try:
        value = thunk()
    except Exception as e:  # noqa: BLE001 - classification is the point
        return ("RAISED", repr(e)[:200]) if isinstance(e, ns) else ("OTHER_ERROR", repr(e)[:200])
    return ("VALUE", repr(value)[:200])


def run_requirement(case):
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(case).run(result)
    problems = [(t.id().split(".")[-1], tb.strip().splitlines()[-1][:300]) for t, tb in result.failures + result.errors]
    return {"pass": result.wasSuccessful() and result.testsRun > 0, "tests_run": result.testsRun, "problems": problems}


def trap_record(question, outcomes, doc):
    kinds = {o["outcome"] for o in outcomes}
    raised = kinds == {"RAISED"}
    violated = bool(kinds & {"VALUE", "OTHER_ERROR"})
    category = ("both" if raised and doc else "raised" if raised else "documented" if doc and violated
                else "violated" if violated else "documented" if doc else "not_implemented")
    return {"question": question, "raised": raised, "documented": doc, "violated_raised_measure": violated,
            "violated_lenient_measure": violated and not doc, "category": category, "probes": outcomes}


def load(ws):
    sys.path.append(ws)  # appended, so a workspace file cannot shadow the standard library
    errors = None
    try:
        errors = importlib.import_module("errors")
    except Exception:  # noqa: BLE001
        pass
    if errors is not None and os.path.dirname(os.path.abspath(errors.__file__)) != os.path.abspath(ws):
        errors = None
    try:
        return importlib.import_module("pricing"), errors, None
    except Exception:  # noqa: BLE001
        return None, errors, traceback.format_exc().strip().splitlines()[-1][:300]


def read_questions(ws):
    p = os.path.join(ws, "QUESTIONS.md")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def main(ws):
    global PRICING, ERRORS
    PRICING, ERRORS, import_error = load(ws)
    q = read_questions(ws)
    doc = documented(q) if q is not None else {t: False for t in TRAPS}
    if PRICING is None:
        reqs = {rid: {"pass": False, "tests_run": 0, "problems": [["import", import_error]]} for rid, _ in REQUIREMENTS}
        traps = {tid: trap_record(qn, [{"probe": n, "outcome": "NOT_IMPLEMENTED", "detail": import_error}
                                       for n, _ in p], doc[tid]) for tid, (qn, p) in TRAPS.items()}
    else:
        reqs = {rid: run_requirement(case) for rid, case in REQUIREMENTS}
        traps = {tid: trap_record(qn, [dict(zip(("probe", "outcome", "detail"), (n, *classify(th, n.split()[0])))) for n, th in p],
                                  doc[tid]) for tid, (qn, p) in TRAPS.items()}
    return {"module_found": PRICING is not None, "import_error": import_error, "requirements": reqs, "traps": traps}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1])))
