import unittest

import orders


class TestOrders(unittest.TestCase):
    def test_r02_line_total(self):
        self.assertEqual(orders.line_total(250, 4), 1000)

    def test_r03_invalid(self):
        for args in [(-1, 1), (1.5, 1), (True, 1), (1, 0), (1, False)]:
            with self.assertRaises(orders.InvalidInput):
                orders.line_total(*args)

    def test_r05_to_r11(self):
        r = orders.order_total([("A", 199, 10), ("B", 100, 1)])
        self.assertEqual(r, {"subtotal": 2090, "bulk_discount": 199, "coupon_discount": 0, "shipping": 499,
                             "total": 2390, "gift_sku": "A"})

    def test_r07_coupon(self):
        self.assertEqual(orders.order_total([("A", 5000, 1)], "SAVE500")["total"], 4500)
        with self.assertRaises(orders.CouponNotApplicable):
            orders.order_total([("A", 500, 10)], "SAVE500")

    def test_r08_unknown_coupon(self):
        with self.assertRaises(orders.InvalidInput):
            orders.order_total([("A", 5000, 1)], "X")

    def test_r12_invalid_orders(self):
        for lines in [[], [("", 1, 1)], [("A", 1, 1), ("A", 1, 1)]]:
            with self.assertRaises(orders.InvalidInput):
                orders.order_total(lines)

    def test_unspecified(self):
        for thunk in [lambda: orders.line_total(1, -1),
                      lambda: orders.order_total([("A", 5, 1), ("B", 5, 1)]),
                      lambda: orders.order_total([("A", 1, 11)])]:
            with self.assertRaises(orders.UnspecifiedPolicy):
                thunk()


if __name__ == "__main__":
    unittest.main()
