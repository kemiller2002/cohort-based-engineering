"""Own tests shipped with the reference validation implementation (shows the scorer's own-tests field works)."""
import unittest

import pricing
from errors import NotSpecified


class Smoke(unittest.TestCase):
    def test_order(self):
        self.assertEqual(pricing.price_order([{"sku": "A", "unit_cents": 1000, "qty": 1}])["total"], 1499)

    def test_trap_refused(self):
        with self.assertRaises(NotSpecified):
            pricing.bulk_unit_price(1000, 60)


if __name__ == "__main__":
    unittest.main()
