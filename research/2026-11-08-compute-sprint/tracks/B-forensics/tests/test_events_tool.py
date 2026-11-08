import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "data"))
import events_tool as t  # noqa: E402

CODES = ("RC-A", "RC-B", "NONE")


def ev(r, rc, contrib=(), human=False, **kw):
    return {"rehearsal": r, "timestamp": None, "eventType": "x", "description": "d", "source": "s",
            "rootCause": rc, "contributingFactors": list(contrib), "requirementIds": [],
            "humanIntervention": human, **kw}


class EventsToolTests(unittest.TestCase):
    def test_valid_dataset_has_no_problems(self):
        self.assertEqual(t.validate([ev("R1", "RC-A")], CODES), ())

    def test_validation_rejects_unknown_codes_and_missing_fields(self):
        bad = [ev("R11", "RC-Z", ["RC-Q"]), {"rehearsal": "R1"}, ev("R2", "RC-A", source=" "),
               ev("R2", "RC-A", human="yes"), ev("R2", "RC-A", measuredOrEstimate="GUESS")]
        problems = t.validate(bad, CODES)
        self.assertEqual(len(problems), 7)

    def test_tally_ignores_milestones(self):
        evs = [ev("R1", "RC-A"), ev("R2", "RC-A"), ev("R2", "RC-B"), ev("R3", "NONE")]
        self.assertEqual(t.tally_primary(evs), {"RC-A": 2, "RC-B": 1})

    def test_recurrence_counts_contributing_and_orders_rehearsals(self):
        evs = [ev("R10", "RC-A"), ev("R2", "RC-B", ["RC-A"]), ev("CAUSA", "RC-A")]
        self.assertEqual(t.recurrence(evs), {"RC-A": ["R2", "R10", "CAUSA"], "RC-B": ["R2"]})

    def test_human_counts(self):
        h = t.human_by_rehearsal([ev("R1", "RC-A", human=True), ev("R1", "NONE", human=True), ev("R2", "RC-A")])
        self.assertEqual((h["R1"], h["R2"], h["R3"]), (2, 0, 0))

    def test_ids_are_stable_and_input_unchanged(self):
        src = (ev("R1", "RC-A"),)
        out = t.with_ids(src)
        self.assertEqual(out[0]["id"], "B-E-001")
        self.assertNotIn("id", src[0])

    def test_curated_dataset_is_valid(self):
        from events_source import EVENTS
        codes = json.loads((ROOT / "taxonomy.json").read_text())["codes"].keys()
        self.assertEqual(t.validate(EVENTS, codes), ())
        self.assertTrue(all(e["rehearsal"] in t.REHEARSALS for e in EVENTS))
        self.assertEqual({e["rehearsal"] for e in EVENTS}, set(t.REHEARSALS))


if __name__ == "__main__":
    unittest.main()
