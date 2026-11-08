import datetime as dt
import unittest

from errors import NotSpecified
from pricing import InvalidOrder, loyalty_points, price_order

WED = dt.datetime(2026, 11, 4, 12, tzinfo=dt.timezone.utc)
SAT = dt.datetime(2026, 11, 7, 12, tzinfo=dt.timezone.utc)


def L(sku, cents, qty, status="active"):
    return {"sku": sku, "unit_cents": cents, "qty": qty, "status": status}


class TestPricing(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(price_order([L("A", 1000, 2)], WED, member=True),
                         {"subtotal": 2000, "discount": 200, "shipping": 499, "total": 2299})
        self.assertEqual(loyalty_points([L("A", 1, 10)]), 60)

    def test_weekend(self):
        self.assertEqual(price_order([L("A", 1000, 1)], SAT)["shipping"], 0)

    def test_invalid(self):
        with self.assertRaises(InvalidOrder):
            price_order([], WED)

    def test_unspecified(self):
        with self.assertRaises(NotSpecified):
            price_order([L("A", 5000, 1)], WED)


if __name__ == "__main__":
    unittest.main()
