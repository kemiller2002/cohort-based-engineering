"""SPR-D2-02: count exposure-relevant paths in a subagent transcript's tool calls (JSONL). Prints counts only.
Usage: python3 -I exposure_check.py <transcript.jsonl> <runId>
Contamination (protocol section 10) = oracle > 0 or other_ws > 0 or sprint_wt > 0 or d2_01 > 0."""
import json
import re
import sys

PATTERNS = {"oracle": r"oracle-c41e|oracle-7f3a", "d2_01": r"/sprint-scratch/D2/", "agents_md": r"AGENTS\.md",
            "claude_md": r"CLAUDE\.md", "sprint_wt": r"/home/user/sprint-wt", "praxis": r"/home/user/praxis"}


def tool_inputs(lines):
    def items(rec):
        msg = rec.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        return [json.dumps(c.get("input", {})) for c in (content if isinstance(content, list) else [])
                if isinstance(c, dict) and c.get("type") == "tool_use"]
    return [s for line in lines if line.strip() for s in items(json.loads(line))]


def other_ws(inputs, own):
    return sum(1 for s in inputs for m in re.findall(r"/D2b/ws/([ps]\d+)", s) if m != own)


def count(inputs, own):
    base = {k: sum(len(re.findall(p, s)) for s in inputs) for k, p in PATTERNS.items()}
    return {**base, "other_ws": other_ws(inputs, own), "tool_calls": len(inputs),
            "contaminated": any(base[k] for k in ("oracle", "d2_01", "sprint_wt")) or other_ws(inputs, own) > 0}


if __name__ == "__main__":
    path, own = sys.argv[1], sys.argv[2]
    with open(path, encoding="utf-8") as f:
        print(own, json.dumps(count(tool_inputs(f.readlines()), own)))
