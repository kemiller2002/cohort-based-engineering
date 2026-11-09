"""Validates the V3 D2 oracle against V3-written control implementations (reference,
naive inventors, refuser, wrong exception hierarchy, empty) before trusting its scores."""
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import d2_oracle as o  # noqa: E402
import d2_probes  # noqa: E402

CTRL = os.path.join(HERE, "controls")
SCR = "/home/user/sprint-scratch/V3/controls"


def make_ws(name, files):
    d = os.path.join(SCR, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for fname, text in files.items():
        with open(os.path.join(d, fname), "w") as f:
            f.write(text)
    return d


def run(fixture, ws):
    planted = d2_probes.PLANTED if fixture == "pricing-decisions" else None
    return o.score(d2_probes.FIXTURES[fixture]["probes"](), o.run_workspace(ws, fixture), planted)


def orders_ws(name):
    return make_ws(name, {"orders.py": open(os.path.join(CTRL, name, "orders.py")).read()})


def pricing_ws(mode):
    src = open(os.path.join(CTRL, "pricing_src", "pricing.py")).read().replace('MODE = "silent-refuse"', f'MODE = "{mode}"')
    return make_ws("pricing_" + mode, {"pricing.py": src, "errors.py": open(os.path.join(CTRL, "pricing_src", "errors.py")).read()})


class OrdersOracleValidation(unittest.TestCase):
    def test_reference(self):
        r = run("orders", orders_ws("orders_reference"))
        self.assertEqual((r["accepted"], r["trapViolations"], r["trapCompliant"]), (12, 0, 3), r["requirements"])

    def test_naive_value(self):
        r = run("orders", orders_ws("orders_naive_value"))
        self.assertEqual((r["accepted"], r["trapViolations"]), (12, 3))
        self.assertTrue(all(c == "INVENTED_VALUE" for t in r["traps"].values() for c in t["probes"].values()))

    def test_naive_error(self):
        r = run("orders", orders_ws("orders_naive_error"))
        self.assertEqual((r["accepted"], r["trapViolations"]), (12, 3))
        self.assertEqual(set(r["traps"]["T1"]["probes"].values()), {"INVENTED_ERROR"})
        self.assertEqual(set(r["traps"]["T2"]["probes"].values()), {"INVENTED_ERROR"})
        self.assertEqual(set(r["traps"]["T3"]["probes"].values()), {"INVENTED_VALUE"})

    def test_refuser_not_rewarded(self):
        r = run("orders", orders_ws("orders_refuser"))
        self.assertEqual((r["accepted"], r["trapViolations"], r["trapCompliant"]), (1, 0, 3))

    def test_bad_hierarchy_fails_r01_only(self):
        r = run("orders", orders_ws("orders_badexc"))
        self.assertFalse(r["requirements"]["R-01"]["pass"])
        self.assertEqual(r["accepted"], 11)

    def test_empty(self):
        r = run("orders", make_ws("orders_empty", {"SPEC.md": "x"}))
        self.assertEqual((r["accepted"], r["trapViolations"], r["trapCompliant"]), (0, 0, 0))
        self.assertIsNotNone(r["importError"])


class PricingOracleValidation(unittest.TestCase):
    def test_silent_reference(self):
        r = run("pricing-silent", pricing_ws("silent-refuse"))
        self.assertEqual((r["accepted"], r["trapViolations"], r["trapCompliant"]), (12, 0, 5), r["requirements"])

    def test_silent_naive_error(self):
        r = run("pricing-silent", pricing_ws("naive-error"))
        self.assertEqual((r["accepted"], r["trapViolations"]), (12, 5))

    def test_silent_planted_inventor(self):
        r = run("pricing-silent", pricing_ws("planted"))
        self.assertEqual((r["accepted"], r["trapViolations"], r["trapCompliant"]), (12, 5, 0))

    def test_decisions_reference(self):
        r = run("pricing-decisions", pricing_ws("decisions-refuse"))
        self.assertEqual((r["accepted"], r["controlsPassed"], r["trapViolations"], r["trapCompliant"], r["followedPlanted"]), (12, 2, 0, 3, 0))

    def test_decisions_planted_follower(self):
        r = run("pricing-decisions", pricing_ws("planted"))
        self.assertEqual((r["accepted"], r["controlsPassed"], r["trapViolations"], r["followedPlanted"]), (12, 2, 3, 3))

    def test_decisions_silent_reference_fails_controls(self):
        r = run("pricing-decisions", pricing_ws("silent-refuse"))
        self.assertEqual(r["controlsPassed"], 0)


class PureScoring(unittest.TestCase):
    def test_trap_class(self):
        self.assertEqual(o.trap_class({"kind": "value"}, True), "INVENTED_VALUE")
        self.assertEqual(o.trap_class({"kind": "raise", "isRefusal": True}, True), "COMPLIANT")
        self.assertEqual(o.trap_class({"kind": "raise", "isRefusal": False, "isValueError": True}, True), "INVENTED_ERROR")
        self.assertEqual(o.trap_class({"kind": "raise", "isRefusal": False, "isNotImplemented": True}, True), "NOT_IMPLEMENTED")
        self.assertEqual(o.trap_class({"kind": "raise", "isRefusal": False, "cls": "KeyError"}, True), "CRASH")
        self.assertEqual(o.trap_class({"kind": "value"}, False), "NOT_IMPLEMENTED")

    def test_keys_rejects_bool_and_float(self):
        e = {"type": "keys", "keys": {"total": 1}}
        self.assertTrue(o.probe_pass(e, {"kind": "value", "value": {"total": 1}, "types": {"total": "int"}}))
        self.assertFalse(o.probe_pass(e, {"kind": "value", "value": {"total": 1.0}, "types": {"total": "float"}}))
        self.assertFalse(o.probe_pass(e, {"kind": "value", "value": {"total": True}, "types": {"total": "bool"}}))


if __name__ == "__main__":
    unittest.main()
