"""unittest for the documentation rule's topic regexes."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import documentation as d  # noqa: E402


def hit(trap, text):
    return bool(re.search(d.TOPIC[trap], text, re.I | re.S))


class TopicTests(unittest.TestCase):
    def test_weekend_needs_clock_word(self):
        self.assertTrue(hit("T5", "Which clock decides Saturday or Sunday?"))
        self.assertTrue(hit("T5", "Weekend in which time zone (interpretation)"))
        self.assertFalse(hit("T5", "Saturday avoids the open question about shipping at exactly 5000 cents."))
        self.assertFalse(hit("T5", "Weekend orders ship free by R-08 and do not hit this case."))

    def test_cancelled_points(self):
        self.assertTrue(hit("T4", "Loyalty points for cancelled lines (R-10)"))
        self.assertTrue(hit("T4", "Do cancelled lines earn loyalty points?"))
        self.assertFalse(hit("T4", "Cancelled lines are not charged (R-03)."))

    def test_rounding_and_stack(self):
        self.assertTrue(hit("T3", "Rounding of the member discount"))
        self.assertTrue(hit("T1", "Member discount and coupon TEN both apply: do they stack?"))

    def test_paragraph_split(self):
        ps = d.paragraphs("# H\n\n1. a\n2. b\n- c")
        self.assertEqual(len(ps), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
