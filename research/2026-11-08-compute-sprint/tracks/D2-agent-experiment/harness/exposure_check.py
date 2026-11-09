"""Count exposure-relevant paths in a subagent transcript's tool calls. Prints counts only."""
import json, sys, re
from functools import reduce
PATTERNS = {"oracle":r"oracle-7f3a","agents_md":r"AGENTS\.md","claude_md":r"CLAUDE\.md","sprint_wt":r"/home/user/sprint-wt","praxis":r"/home/user/praxis"}
def tool_inputs(lines):
    def items(rec):
        msg = rec.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        return [json.dumps(c.get("input",{})) for c in (content or []) if isinstance(c, dict) and c.get("type")=="tool_use"]
    return [s for l in lines if l.strip() for s in items(json.loads(l))]
def other_ws(inputs, own):
    return sum(1 for s in inputs for m in re.findall(r"/D2/ws/(r\d+)", s) if m != own)
def count(inputs, own):
    base = {k: sum(len(re.findall(p, s)) for s in inputs) for k, p in PATTERNS.items()}
    return {**base, "other_ws": other_ws(inputs, own), "tool_calls": len(inputs)}
if __name__ == "__main__":
    path, own = sys.argv[1], sys.argv[2]
    print(own, json.dumps(count(tool_inputs(open(path).readlines()), own)))
