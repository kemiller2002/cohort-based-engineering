"""SPR-D3-01: count exposure-relevant paths in a chain transcript's tool calls (JSONL; all K steps of the chain in one
file, or several files passed in step order). Prints counts only.
Usage: python3 -I exposure_check.py <runId> <transcript.jsonl> [<transcript-step2.jsonl> ...]
Contamination (protocol section 10) = oracle > 0 or snapshots > 0 or other_ws > 0 or sprint_wt > 0 or prior_exp > 0.
Reading the chain's own workspace files (SPEC.md, STEP-*.md, DECISIONS.md, HANDOFF-NOTES.md, legacy_bulk.py,
slack-export-pricing.txt, errors.py, pricing.py) is expected and not counted."""
import json
import re
import sys

PATTERNS = {"oracle": r"oracle-5e83|oracle-9b27|oracle-c41e|oracle-7f3a|oracle_tests\.py",
            "snapshots": r"/sprint-scratch/D3/snap", "prior_exp": r"/sprint-scratch/D2[bc]?/",
            "sprint_wt": r"/home/user/sprint-wt", "agents_md": r"AGENTS\.md", "claude_md": r"CLAUDE\.md",
            "praxis": r"/home/user/praxis"}
CONTAMINATING = ("oracle", "snapshots", "prior_exp", "sprint_wt")


def tool_inputs(lines):
    def items(rec):
        msg = rec.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        return [json.dumps(c.get("input", {})) for c in (content if isinstance(content, list) else [])
                if isinstance(c, dict) and c.get("type") == "tool_use"]
    return [s for line in lines if line.strip() for s in items(json.loads(line))]


def other_ws(inputs, own):
    return sum(1 for s in inputs for m in re.findall(r"/D3/ws/(c\d+|u\d\d)\b", s) if m != own)


def count(inputs, own):
    base = {k: sum(len(re.findall(p, s)) for s in inputs) for k, p in PATTERNS.items()}
    ow = other_ws(inputs, own)
    return {**base, "other_ws": ow, "tool_calls": len(inputs),
            "contaminated": any(base[k] for k in CONTAMINATING) or ow > 0}


def read_all(paths):
    out = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            out += f.readlines()
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    own = sys.argv[1]
    print(own, json.dumps(count(tool_inputs(read_all(sys.argv[2:])), own)))
