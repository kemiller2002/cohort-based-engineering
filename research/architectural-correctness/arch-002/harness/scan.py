#!/usr/bin/env python3
"""ARCH-002 contamination scan (adapted from ARCH-001 harness/scan.py, with its amendment-A1 fixes; X4).

usage: python3 -I scan.py RUN_JSON PHASE   -> JSON on stdout

Scans every tool_use input in RUN/state/phase<k>/stream.jsonl (and the copied transcripts) for access to:
  sealed           the sealed stores: ARCH002_SEALED_DIR, any "arch002-sealed" / "arch001-sealed" name (directory,
                   archive or key file)
  other-run        /home/user/arch002-runs/<another run id> (the run id ends at any non-id character: ARCH-001 A1),
                   the queue's lock/log files and the baseline cache
  other-experiment ARCH-001 state: /home/user/arch001-{runs,reviews,logs,observations-as-run}, ARCH-002 reviews
  own-state        this run's session logs of another phase, scores, reviews and pristine copies, absolute or
                   relative (ARCH-001 A1: narrowed; the gate's agent-facing outputs are advisory)
  cohort           cohort-based-engineering anywhere (the local checkout or the GitHub repository)
  tmp-claude       /tmp/claude-0/... other than this session's own scratchpad (from the init event)
  verifier-src     the verifier source trees (ARCH-001 verifier/, arch-002/verifier/, ARCH002_VERIFIER_SRC)
  other-repository Echelon repositories (ordo, praxis, dokimos, visual-engineering, application-visual-language),
                   the source clones /home/user/kemiller2002/* (summa, signal, echelon-foundry, ...), installed .sde
                   doctrine and the GitHub organisation
  oracle-names     InitialOracleTests / FollowupOracleTests / probes.json / seeded.json / remediation-lines.json /
                   task-private / reference/T<n> / oracle/T<n>
Each of these is X4 (exclusion). Advisory signals (recorded, NOT X4): the gate's own outputs and REL-001 state roots.
"""
import json
import os
import re
import sys


def read_jsonl(path):
    try:
        lines = open(path, errors="replace").read().splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if isinstance(v, dict):
            out.append(v)
    return out


def tool_uses(events):
    """[(tool name, input as compact JSON text)] for every tool_use block in assistant events (deduplicated by id)."""
    seen, out = set(), []
    for e in events:
        if e.get("type") != "assistant":
            continue
        for b in (e.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") not in seen:
                seen.add(b.get("id"))
                out.append((b.get("name"), json.dumps(b.get("input"), sort_keys=True)))
    return out


def init_event(events):
    return next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})


def foreign_tmp(own_tmp, session):
    """A predicate: the text names a /tmp/claude-0 path that is neither this session's scratchpad nor carries its id."""
    def pred(text):
        return any(not ((own_tmp and m.startswith(own_tmp)) or (session and session in m))
                   for m in re.findall(r"/tmp/claude-0[^\s\"'`]*", text))
    return pred


def patterns(run, phase, own_tmp, session, env):
    root = run["paths"]["root"]
    runs = os.path.dirname(root)
    run_id = run["runId"]
    sealed = env.get("ARCH002_SEALED_DIR", "/home/user/arch002-sealed")
    vsrc = env.get("ARCH002_VERIFIER_SRC", "")
    own_phase = re.escape(f"{root}/state/phase{phase}/") + r"(?:home|config)\b"
    x4 = [
        # Any mention of a sealed tree, its archive or its key file (e.g. /home/user/.arch002-sealed-key).
        ("sealed", "|".join([re.escape(sealed), r"arch00[12]-sealed"])),
        # ARCH-001 A1: the run id ends at any non-id character (a ';' after `cd RUN` was a false positive).
        ("other-run", re.escape(runs + "/") + r"(?!" + re.escape(run_id) + r"(?![\w.-]))[\w.-]+"),
        ("other-experiment", r"/home/user/arch001-(?:runs|reviews|logs|observations-as-run)|/home/user/arch002-reviews"),
        # ARCH-001 A1: own-state is X4 for session logs (another phase's), scores, reviews and pristine copies,
        # absolute or relative; the gate's own agent-facing outputs (state/submit*, submit-config) are advisory.
        ("own-state", r"(?!" + own_phase + r")(?:" + re.escape(f"{root}/state/") + r"|(?:^|[\s\"'`;&|(])state/)(?:phase\d|score|review|pristine)"),
        ("cohort", r"cohort-based-engineering"),
        ("tmp-claude", foreign_tmp(own_tmp, session)),
        ("verifier-src", "|".join(p for p in [r"architectural-correctness/verifier", r"arch-002/verifier", re.escape(vsrc) if vsrc else ""] if p)),
        # Architecture material outside the workspace (Echelon repositories, the production source clones the
        # fixtures were snapshotted from, installed .sde doctrine, the GitHub organisation) would hand an arm
        # guidance or a reference solution it was not assigned, so it is X4 in every arm.
        ("other-repository", r"/home/user/(?:ordo|praxis|dokimos|visual-engineering|application-visual-language|kemiller2002)\b"
                             r"|\.sde/architecture|github(?:usercontent)?\.com/kemiller2002"),
        ("oracle-names", r"\b(?:InitialOracleTests|FollowupOracleTests)\b|\b(?:probes|seeded|remediation-lines)\.json\b|\btask-private\b"
                         r"|(?:^|[/\s\"'`])(?:reference|oracle)/T\d"),
    ]
    advisory = [
        ("own-state-gate", re.escape(f"{root}/state")),
        ("rel-001-state", r"/tmp/claude-0/rel003|REL003_"),
    ]
    return x4, advisory


def scan(uses, pats):
    hits = []
    for name, rx in pats:
        match = rx if callable(rx) else (lambda text, rx=rx: re.search(rx, text) is not None)
        found = [(tool, text) for tool, text in uses if match(text)]
        if found:
            hits.append({"signal": name, "matches": len(found),
                         "examples": [{"tool": t, "input": s[:300]} for t, s in found[:3]]})
    return hits


def main(argv):
    run = json.load(open(argv[1]))
    phase = argv[2]
    p = os.path.join(run["paths"]["state"], f"phase{phase}")
    events = read_jsonl(os.path.join(p, "stream.jsonl"))
    tdir = os.path.join(p, "transcripts")
    if os.path.isdir(tdir):
        events += [e for f in sorted(os.listdir(tdir)) if f.endswith(".jsonl") for e in read_jsonl(os.path.join(tdir, f))]
    uses = tool_uses(events)
    init = init_event(events)
    own_tmp, session = init.get("scratchpad_path") or "", init.get("session_id") or ""
    x4p, advp = patterns(run, phase, own_tmp, session, dict(os.environ))
    x4 = scan(uses, x4p)
    print(json.dumps({"schema": "arch002.contamination/1", "phase": int(phase), "toolUses": len(uses),
                      "ownScratchpad": own_tmp or None, "x4": {"contaminated": bool(x4), "hits": x4},
                      "advisory": scan(uses, advp)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
