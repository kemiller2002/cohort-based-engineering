import unittest

import orders


class TestNaive(unittest.TestCase):
    def test_line(self):
        self.assertEqual(orders.line_total(250, 4), 1000)

    def test_refund(self):
        self.assertEqual(orders.line_total(100, -2), -200)
