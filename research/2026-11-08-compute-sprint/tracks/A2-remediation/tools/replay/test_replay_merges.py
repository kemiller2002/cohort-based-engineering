"""Unit tests for the pure parts of replay_merges.py (run: python3 -m unittest test_replay_merges)."""
import json
import unittest

import replay_merges as rm

CTX = ".ros/context/current.json"
EVT = ".ros/events/events.jsonl"


def ctx(updated, ids):
    return json.dumps({"schemaVersion": "1.0.0", "updatedAt": updated, "workItems": [{"id": i, "s": 1} for i in ids]})


def evs(ids):
    return "".join(json.dumps({"eventId": i}) + "\n" for i in ids)


class CompareTests(unittest.TestCase):
    def test_instant_equivalence(self):
        self.assertEqual(rm.instant("2026-11-01T17:45:52.270Z"), rm.instant("2026-11-01T17:45:52.2700000+00:00"))

    def test_semantically_equal_context(self):
        c = rm.compare(CTX, ctx("2026-01-01T00:00:00.5Z", ["a", "b"]), ctx("2026-01-01T00:00:00.5000000+00:00", ["a", "b"]),
                       ctx("2026-01-01T00:00:00Z", ["a"]), ctx("2026-01-01T00:00:00Z", ["b"]))
        self.assertTrue(c["idSetEqualToMergeCommit"])
        self.assertEqual(c["metaDifferences"], [])
        self.assertEqual(c["lostVsParents"], [])
        self.assertFalse(c["byteIdentical"])

    def test_lost_and_duplicate_detection(self):
        c = rm.compare(EVT, evs(["a", "a"]), evs(["a", "b"]), evs(["a"]), evs(["b"]))
        self.assertEqual(c["duplicatesInResult"], 1)
        self.assertEqual(c["lostVsParents"], ["b"])
        self.assertEqual(c["inMergeCommitNotInResult"], ["b"])

    def test_post_merge_record_reported(self):
        c = rm.compare(EVT, evs(["a", "b"]), evs(["a", "b", "z"]), evs(["a"]), evs(["b"]))
        self.assertEqual(c["inMergeCommitNotInParents"], ["z"])

    def test_content_difference(self):
        r = json.dumps({"workItems": [{"id": "a", "s": 1}], "updatedAt": "2026-01-01T00:00:00Z"})
        m = json.dumps({"workItems": [{"id": "a", "s": 2}], "updatedAt": "2026-01-01T00:00:00Z"})
        self.assertEqual(rm.compare(CTX, r, m, r, r)["recordsWithDifferentContent"], ["a"])


if __name__ == "__main__":
    unittest.main()
