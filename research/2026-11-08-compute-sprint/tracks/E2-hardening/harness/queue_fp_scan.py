"""SPR-E2-01 control C4: read-only false-positive scan of the E-F-11 cross-check over real repositories.

Mirrors BacklogQueueValidation.eventDisagreements: a queue row with status 'complete' is flagged unless the
tracked log .ros/events/events.jsonl has a work.completed or work.completion.verified event for its id.
Only reads files. usage: python3 -I queue_fp_scan.py OUT.json REPO...
"""
import json
import sys
from pathlib import Path

COMPLETION_TYPES = frozenset({"work.completed", "work.completion.verified"})


def completed_ids(event_lines):
    def parse(line):
        try:
            return json.loads(line)
        except ValueError:
            return None
    events = (parse(line) for line in event_lines if line.strip())
    return frozenset(e.get("workItem") for e in events
                     if isinstance(e, dict) and e.get("type") in COMPLETION_TYPES)


def disagreements(queue_items, completed):
    return [item["id"] for item in queue_items
            if item.get("status") == "complete" and item.get("id") not in completed]


def scan_repo(repo):
    root = Path(repo)
    queue_path, events_path = root / ".ros/work/queue.json", root / ".ros/events/events.jsonl"
    if not queue_path.is_file():
        return {"repo": str(root), "queue": False}
    items = json.loads(queue_path.read_text()).get("items", [])
    lines = events_path.read_text().splitlines() if events_path.is_file() else []
    flagged = disagreements(items, completed_ids(lines))
    return {"repo": str(root), "queue": True, "completeRows": sum(1 for i in items if i.get("status") == "complete"),
            "flagged": len(flagged), "flaggedIds": flagged[:20]}


def main(argv):
    out, repos = argv[1], argv[2:]
    results = [scan_repo(r) for r in repos]
    Path(out).write_text(json.dumps({"scan": "E-F-11 cross-check false positives", "results": results}, indent=2) + "\n")
    for r in results:
        print(json.dumps(r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
