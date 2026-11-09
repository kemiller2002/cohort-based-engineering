"""Fixture-fitter tests (validation only): R5 acceptance from the provided tests/data/tax_cases.csv."""
import csv
import os
import unittest

import invoice

DATA = os.path.join(os.path.dirname(__file__), "data", "tax_cases.csv")


class TaxCsv(unittest.TestCase):
    def test_tax_cases_csv(self):
        with open(DATA, newline="") as f:
            for row in csv.DictReader(f):
                self.assertEqual(invoice.apply_tax(int(row["amount_cents"]), row["region"]),
                                 int(row["expected_total_cents"]))
