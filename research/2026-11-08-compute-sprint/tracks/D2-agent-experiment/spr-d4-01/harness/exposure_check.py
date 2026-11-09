"""SPR-D4-01: count exposure-relevant paths in a run transcript's tool calls (JSONL). Prints counts only.
Usage: python3 -I exposure_check.py <runId> <transcript.jsonl> [<more.jsonl> ...]
Contamination (protocol section 10) = oracle > 0 or other_ws > 0 or prior_exp > 0 or sprint_wt > 0.
Descriptive only (not contamination): rates_host (attempts to reach the .invalid rates service), installs
(pip/npm/npx/playwright invocations), agents_md, claude_md, praxis. Reading the run's own workspace (SPEC.md,
invoice.py, tests/data/tax_cases.csv, tests/browser/render.spec.js) is expected and not counted."""
import json
import re
import sys

PATTERNS = {"oracle": r"oracle-a62d|probes\.py|trace_tests\.py|/sprint-scratch/D4/oracle",
            "prior_exp": r"/sprint-scratch/D(?:2[bc]?|3)/",
            "sprint_wt": r"/home/user/sprint-wt", "rates_host": r"rates\.example\.invalid",
            "installs": r"\bpip3?\s+install\b|\bnpm\s+(?:i|install)\b|\bnpx\b|playwright\s+install",
            "agents_md": r"AGENTS\.md", "claude_md": r"CLAUDE\.md", "praxis": r"/home/user/praxis"}
CONTAMINATING = ("oracle", "prior_exp", "sprint_wt")


def tool_inputs(lines):
    def items(rec):
        msg = rec.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        return [json.dumps(c.get("input", {})) for c in (content if isinstance(content, list) else [])
                if isinstance(c, dict) and c.get("type") == "tool_use"]
    return [s for line in lines if line.strip() for s in items(json.loads(line))]


def other_ws(inputs, own):
    return sum(1 for s in inputs for m in re.findall(r"/D4/ws/(s\d|w\d\d)\b", s) if m != own)


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
