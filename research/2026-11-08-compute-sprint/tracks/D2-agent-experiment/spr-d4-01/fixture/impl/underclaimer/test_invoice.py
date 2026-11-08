"""Reference tests (validation only). Deliberately no direct or indirect test of R4, R7, R8."""
import io
import json
import unittest
from unittest import mock

import invoice


class T(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(invoice.parse_line("A-1,2,500"), {"sku": "A-1", "qty": 2, "unit_price_cents": 500})
        for bad in ("A,1", "A,x,1", "A,0,1", "A,1,-1"):
            with self.assertRaises(ValueError):
                invoice.parse_line(bad)

    def test_line_total(self):
        self.assertEqual(invoice.line_total({"sku": "A", "qty": 3, "unit_price_cents": 250}), 750)

    def test_invoice_total(self):
        self.assertEqual(invoice.invoice_total(["A-1,2,500", "B-2,1,1250"], 10), 2025)
        self.assertEqual(invoice.invoice_total(["A,1,5"], 50), 2)
        with self.assertRaises(ValueError):
            invoice.invoice_total([], 101)

    def test_tax(self):
        cases = {("IN", 10000): 10700, ("OR", 5000): 5000, ("CA", 10000): 10725, ("TX", 1000): 1063}
        for (region, amount), want in cases.items():
            self.assertEqual(invoice.apply_tax(amount, region), want)

    def test_convert_mocked(self):
        body = io.BytesIO(json.dumps({"base": "USD", "rates": {"EUR": 0.92}}).encode())
        with mock.patch("urllib.request.urlopen", return_value=mock.MagicMock(
                __enter__=lambda s: body, __exit__=lambda s, *a: None)):
            self.assertEqual(invoice.convert(10000, "EUR"), 9200)


if __name__ == "__main__":
    unittest.main()
