"""SPR-X-04 exposure check, adapted from SPR-D2-02. Counts exposure-relevant paths in a subagent transcript's tool
calls (JSONL). Prints counts only.

Usage: python3 -I exposure_check.py <transcript.jsonl> <runId>

Contaminated = any tool call touches the oracle (/home/user/sprint-scratch/X4/oracle-e7a1, or any X4 oracle
directory), another X4 workspace, any /home/user/sprint-scratch/D2* (D2, D2b, D2c, ...), D3 or D4 path, or
/home/user/sprint-wt. Reading the run's own workspace is allowed. AGENTS.md / CLAUDE.md / praxis and other
sprint-scratch paths are recorded as exposure notes, not contamination.
"""
import json
import re
import sys

CONTAMINATING = {"oracle": r"oracle-e7a1|/sprint-scratch/X4/oracle",
                 "d2_paths": r"/sprint-scratch/D2", "d3_paths": r"/sprint-scratch/D3", "d4_paths": r"/sprint-scratch/D4",
                 "sprint_wt": r"/home/user/sprint-wt"}
NOTES = {"agents_md": r"AGENTS\.md", "claude_md": r"CLAUDE\.md", "praxis": r"/home/user/praxis"}
OTHER_SCRATCH = r"/sprint-scratch/(?!X4/ws/)([A-Za-z0-9]+)"


def tool_inputs(lines):
    def items(rec):
        msg = rec.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        return [json.dumps(c.get("input", {})) for c in (content if isinstance(content, list) else [])
                if isinstance(c, dict) and c.get("type") == "tool_use"]
    return [s for line in lines if line.strip() for s in items(json.loads(line))]


def other_ws(inputs, own):
    return sum(1 for s in inputs for m in re.findall(r"/X4/ws/([A-Za-z0-9_-]+)", s) if m != own)


def count(inputs, own):
    bad = {k: sum(len(re.findall(p, s)) for s in inputs) for k, p in CONTAMINATING.items()}
    notes = {k: sum(len(re.findall(p, s)) for s in inputs) for k, p in NOTES.items()}
    others = sorted({m for s in inputs for m in re.findall(OTHER_SCRATCH, s)})
    ow = other_ws(inputs, own)
    return {**bad, **notes, "other_ws": ow, "other_sprint_scratch_dirs": others, "tool_calls": len(inputs),
            "contaminated": any(bad.values()) or ow > 0}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    path, own = sys.argv[1], sys.argv[2]
    with open(path, encoding="utf-8") as f:
        print(own, json.dumps(count(tool_inputs(f.readlines()), own)))
