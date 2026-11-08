import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queue_fp_scan as q  # noqa: E402


class QueueScanTests(unittest.TestCase):
    def test_complete_row_without_event_is_flagged(self):
        done = q.completed_ids(['{"type":"work.completed","workItem":"A-1"}', "not json", ""])
        self.assertEqual(q.disagreements([{"id": "A-1", "status": "complete"}, {"id": "A-2", "status": "complete"},
                                          {"id": "A-3", "status": "ready"}], done), ["A-2"])

    def test_verified_completion_counts(self):
        done = q.completed_ids(['{"type":"work.completion.verified","workItem":"A-1"}'])
        self.assertEqual(q.disagreements([{"id": "A-1", "status": "complete"}], done), [])

    def test_scan_repo_reads_files(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".ros/work").mkdir(parents=True)
            (Path(d) / ".ros/work/queue.json").write_text(json.dumps({"items": [{"id": "A-9", "status": "complete"}]}))
            self.assertEqual(q.scan_repo(d)["flaggedIds"], ["A-9"])
            self.assertFalse(q.scan_repo(d + "/missing")["queue"])


if __name__ == "__main__":
    unittest.main()
