"""unittest for prompts_check. Run: python3 -I -B scripts/test_prompts_check.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prompts_check as pc  # noqa: E402

M = "Intro.\n\nRules:\n- a\n\nTask: do it.\n\nDone.\n"
G = "Intro.\n\nRules:\n- a\n\nTask: do it.\n\n## A\nauth.\n\n## B\n- chk\n\nDone.\n"


class T(unittest.TestCase):
    def test_block_and_sections(self):
        block, pos = pc.g_block(M, G)
        self.assertEqual(pc.sections(block), ["## A\nauth.\n\n", "## B\n- chk\n\n"])
        self.assertEqual(pos, 7)

    def test_good_arms_pass(self):
        c = "Intro.\n\nRules:\n- a\n\n## A\nauth.\n\nTask: do it.\n\nDone.\n"
        k = "Intro.\n\nRules:\n- a\n\n## B\n- chk\n\nTask: do it.\n\nDone.\n"
        r = pc.check(M, G, {"C": ("A", c), "K": ("B", k)})
        self.assertTrue(r["C"]["equals_M_plus_section_before_Task"] and r["K"]["equals_M_plus_section_before_Task"])
        self.assertTrue(r["C"]["other_sections_absent"] and r["K"]["other_sections_absent"])

    def test_wrong_position_or_edit_fails(self):
        after = "Intro.\n\nRules:\n- a\n\nTask: do it.\n\n## A\nauth.\n\nDone.\n"
        edited = "Intro.\n\nRules:\n- a\n\n## A\nauth!\n\nTask: do it.\n\nDone.\n"
        r = pc.check(M, G, {"X": ("A", after), "Y": ("A", edited)})
        self.assertFalse(r["X"]["equals_M_plus_section_before_Task"])
        self.assertFalse(r["Y"]["equals_M_plus_section_before_Task"])

    def test_non_contiguous_g_rejected(self):
        with self.assertRaises(ValueError):
            pc.g_block(M, "Intro!\n\nRules:\n- a\n\nTask: do it.\n\n## A\nx\n\nDone.\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
