import datetime as dt
import unittest

import pricing
from errors import NotSpecified

WED = dt.datetime(2026, 11, 4, 12, tzinfo=dt.timezone.utc)


def L(sku, cents, qty, status="active"):
    return {"sku": sku, "unit_cents": cents, "qty": qty, "status": status}


class TestPricing(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(pricing.price_order([L("A", 1000, 1)], WED),
                         {"subtotal": 1000, "discount": 0, "shipping": 499, "total": 1499})

    def test_d001(self):
        self.assertEqual(pricing.price_order([L("A", 5000, 1)], WED)["shipping"], 0)

    def test_d002(self):
        sat_tokyo = dt.datetime(2026, 11, 7, 1, tzinfo=dt.timezone(dt.timedelta(hours=9)))
        self.assertEqual(pricing.price_order([L("A", 1000, 1)], sat_tokyo)["shipping"], 0)

    def test_unaccepted_notes_raise(self):
        with self.assertRaises(NotSpecified):
            pricing.price_order([L("A", 6000, 1)], WED, member=True, coupon="TEN")
        with self.assertRaises(NotSpecified):
            pricing.price_order([L("A", 1995, 1)], WED, member=True)
        with self.assertRaises(NotSpecified):
            pricing.loyalty_points([L("A", 100, 1), L("B", 100, 1, "cancelled")])

    def test_invalid(self):
        with self.assertRaises(pricing.InvalidOrder):
            pricing.price_order([], WED)


if __name__ == "__main__":
    unittest.main()
