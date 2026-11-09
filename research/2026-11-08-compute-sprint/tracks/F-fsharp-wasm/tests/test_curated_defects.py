import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from curated_defects import rows, validate


class CuratedTests(unittest.TestCase):
    def test_dataset_valid_and_unique(self):
        rs = rows()
        self.assertEqual(validate(rs), [])
        self.assertEqual(len({r["id"] for r in rs}), len(rs))

    def test_validate_flags_missing(self):
        self.assertTrue(validate([{"id": "X", "rehearsal": "R1", "source": "none", "defect": "", "pattern": "p", "contract": "c", "contractExists": "no"}]))


if __name__ == "__main__":
    unittest.main()
