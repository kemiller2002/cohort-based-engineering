#!/usr/bin/env python3
"""Measure the Claude Code runtime prefix (system prompt + tool definitions + skill listing) by configuration.

EXPLORATORY measurement for research/token-efficiency (OVERHEAD-ANALYSIS.md section 3.2, section 5 item 5).

Each probe is one headless, one-turn `claude -p` call that mirrors the REL-001 run-03 K1 launcher
(harness/launch-agent.sh): `env -i`, a fresh CLAUDE_CONFIG_DIR and HOME, a fresh --session-id, a random
nonce in --append-system-prompt, --strict-mcp-config with no servers, bypassPermissions, stream-json.
The prompt asks for a one-word reply, so no tool is invoked and the only request is the first one.
The first request's context = input + cache_creation + cache_read tokens (all three are input-side).

usage:
  probe-prefix.py run OUT.json [--claude BIN] [--scratch DIR] [--only CONFIG ...]
  probe-prefix.py summarize OUT.json        # pure: recompute the summary block from the raw probes

Python 3 standard library only. The plan and the summary are deterministic functions of their inputs; the
probes themselves are API calls and are recorded raw, with timestamps.
"""
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN03 = REPO / "research/experiments/REL-001/run-03"
PRICE_TABLE = REPO / "research/pricing/anthropic.price-table.json"
MODEL = "claude-opus-5-5"
PROMPT = "Reply with OK"
# Tools every run-03 arm needs: read and edit files; run shell (dotnet test, git, praxis, find/grep).
# CORE_TOOLS is the subset of the 2.1.306 default set (which has no Glob/Grep) that the briefs need;
# MINIMAL_TOOLS adds the dedicated search tools.
CORE_TOOLS = "Bash,Read,Edit,Write"
MINIMAL_TOOLS = "Bash,Read,Edit,Write,Glob,Grep"

# (name, extra CLI args, files whose text is appended to the prompt, replicates, factor description)
CONFIGS = (
    ("baseline", (), (), 3, "run-03 K1 launcher as drafted (default tool set)"),
    ("tools-minimal", ("--tools", MINIMAL_TOOLS), (), 3, "built-in tools restricted to " + MINIMAL_TOOLS),
    ("tools-core", ("--tools", CORE_TOOLS), (), 3,
     "built-in tools restricted to " + CORE_TOOLS + " (subset of the default set; adopted for run-03)"),
    ("no-slash", ("--disable-slash-commands",), (), 3, "skills and slash commands disabled"),
    ("trimmed", ("--tools", MINIMAL_TOOLS, "--disable-slash-commands"), (), 3,
     "tools-minimal + no-slash (the proposed run-03 profile)"),
    ("no-tools", ("--tools", ""), (), 3, "no built-in tools (reference point: tool-definition size)"),
    ("trimmed+directives", ("--tools", MINIMAL_TOOLS, "--disable-slash-commands"),
     ("directives/DIRECTIVES.md",), 1, "arm B/C/D directives pack as an inline delta"),
    ("trimmed+workflow-c", ("--tools", MINIMAL_TOOLS, "--disable-slash-commands"),
     ("harness/briefs/workflow-c.md",), 1, "arm C workflow brief section as an inline delta"),
    ("trimmed+workflow-d", ("--tools", MINIMAL_TOOLS, "--disable-slash-commands"),
     ("harness/briefs/workflow-d.md",), 1, "arm D workflow brief section as an inline delta"),
    ("trimmed+core", ("--tools", MINIMAL_TOOLS, "--disable-slash-commands"),
     ("harness/briefs/core.md", "harness/briefs/outcome.md"), 1, "shared brief (core + outcome) as an inline delta"),
)


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prompt_for(files):
    return "\n\n".join((PROMPT,) + tuple(
        "Context (do not act on it):\n" + (RUN03 / f).read_text(encoding="utf-8") for f in files))


def argv_for(claude, extra, files, session_id, nonce):
    return (claude, "-p", prompt_for(files), "--model", MODEL, "--session-id", session_id,
            "--output-format", "stream-json", "--verbose", "--max-turns", "1",
            "--append-system-prompt", f"REL-001 run-03 trial isolation nonce {nonce}. It carries no instruction.",
            "--permission-mode", "bypassPermissions", "--strict-mcp-config", "--mcp-config",
            '{"mcpServers":{}}') + tuple(extra)


def plan(only):
    return tuple((name, rep, extra, files, desc)
                 for name, extra, files, reps, desc in CONFIGS if not only or name in only
                 for rep in range(1, reps + 1))


def first_request_usage(events):
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    usage = result.get("usage", {})
    first = (usage.get("iterations") or [usage])[0]
    keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
    return {k: first.get(k) for k in keys} | {"cache_creation": first.get("cache_creation"),
                                               "numTurns": result.get("num_turns"),
                                               "isError": result.get("is_error"),
                                               "resultModel": sorted((result.get("modelUsage") or {}).keys())}


def context_tokens(u):
    parts = (u.get("input_tokens"), u.get("cache_creation_input_tokens"), u.get("cache_read_input_tokens"))
    return sum(parts) if all(isinstance(p, int) for p in parts) else None


def run_probe(claude, scratch, step):
    name, rep, extra, files, desc = step
    # Same paths for every probe (fresh contents), so path text in the system prompt has the same length.
    for d in ("cfg", "home", "work"):
        shutil.rmtree(scratch / d, ignore_errors=True)
        (scratch / d).mkdir(parents=True)
    sid, nonce = str(uuid.uuid4()), os.urandom(16).hex()
    argv = argv_for(claude, extra, files, sid, nonce)
    # IS_SANDBOX=1: this host runs as root, where bypassPermissions is otherwise refused (recorded deviation).
    env = {"HOME": str(scratch / "home"), "CLAUDE_CONFIG_DIR": str(scratch / "cfg"),
           "PATH": os.environ.get("PATH", ""), "TERM": "dumb", "IS_SANDBOX": "1"}
    started = utc()
    proc = subprocess.run(argv, cwd=scratch / "work", env=env, capture_output=True, text=True, timeout=300)
    events = tuple(json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{"))
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    usage = first_request_usage(events)
    return {"config": name, "replicate": rep, "factor": desc, "extraArgs": list(extra),
            "inlineFiles": [{"path": f"research/experiments/REL-001/run-03/{f}", "sha256": sha256(RUN03 / f)}
                            for f in files],
            "startedAt": started, "endedAt": utc(), "exit": proc.returncode, "stderrHead": proc.stderr[:400],
            "sessionId": sid, "claudeVersion": init.get("claude_code_version"), "model": init.get("model"),
            "toolsLoaded": init.get("tools"), "skillsLoaded": init.get("skills"),
            "slashCommandCount": len(init.get("slash_commands") or ()), "mcpServers": init.get("mcp_servers"),
            "plugins": [p.get("name") for p in init.get("plugins") or ()],
            "usage": usage, "contextTokens": context_tokens(usage)}


def stats(values):
    vals = tuple(v for v in values if isinstance(v, int))
    return {"n": len(vals), "mean": round(statistics.fmean(vals), 1) if vals else None,
            "min": min(vals) if vals else None, "max": max(vals) if vals else None}


def price(table_path):
    entry = next(e for e in json.loads(Path(table_path).read_text())["entries"] if e["model"] == MODEL)
    return {k: entry[k] for k in ("cacheRead", "cacheWrite5m", "cacheWrite1h", "input")} | {
        "tableVersion": json.loads(Path(table_path).read_text())["tableVersion"]}


ADOPTED = "tools-core"
# Pooled median requests per run, run-02 (OVERHEAD-ANALYSIS.md section 3.5, out/run-02-context-sizes.json).
REQUESTS_PER_RUN = 11


def saving_costs(tokens, prices):
    usd = lambda tok, rate: round(tok * rate / 1e6, 6)
    return {"perRequestTokens": tokens,
            "perRequestUSD": {"atCacheRead": usd(tokens, prices["cacheRead"]),
                              "atCacheWrite5m": usd(tokens, prices["cacheWrite5m"]),
                              "atCacheWrite1h": usd(tokens, prices["cacheWrite1h"])},
            "perRunTokens": round(tokens * REQUESTS_PER_RUN, 1),
            "perRunUSD": {"allCacheRead": usd(tokens * REQUESTS_PER_RUN, prices["cacheRead"]),
                          "coldFirstWrite1hThenReads": round(usd(tokens, prices["cacheWrite1h"])
                                                             + usd(tokens * (REQUESTS_PER_RUN - 1), prices["cacheRead"]), 6),
                          "coldFirstWrite5mThenReads": round(usd(tokens, prices["cacheWrite5m"])
                                                             + usd(tokens * (REQUESTS_PER_RUN - 1), prices["cacheRead"]), 6)}}


def summarize(probes, prices):
    names = tuple(dict.fromkeys(p["config"] for p in probes))
    per = {n: stats(p["contextTokens"] for p in probes if p["config"] == n) for n in names}
    base = per.get("baseline", {}).get("mean")
    delta = {n: (round(per[n]["mean"] - base, 1) if base is not None and per[n]["mean"] is not None else None)
             for n in names}
    adopted = per.get(ADOPTED, {}).get("mean")
    saving = round(base - adopted, 1) if base is not None and adopted is not None else None
    return {"metric": "first-request context tokens = input + cache_creation + cache_read (one-turn probe)",
            "perConfig": per, "deltaVsBaseline": delta, "adoptedConfig": ADOPTED,
            "requestsPerRun": REQUESTS_PER_RUN,
            "adoptedSaving": saving_costs(saving, prices) if saving is not None else None,
            "prices": prices}


def main(argv):
    if len(argv) < 3 or argv[1] not in ("run", "summarize"):
        sys.exit(__doc__)
    out = Path(argv[2])
    opt = lambda flag, default: argv[argv.index(flag) + 1] if flag in argv else default
    prices = price(PRICE_TABLE)
    if argv[1] == "summarize":
        doc = json.loads(out.read_text())
        out.write_text(json.dumps(doc | {"summary": summarize(doc["probes"], prices)}, indent=2) + "\n")
        return
    claude = opt("--claude", shutil.which("claude") or "claude")
    scratch = Path(opt("--scratch", "/tmp/prefix-probe")).resolve()
    only = tuple(argv[argv.index("--only") + 1:]) if "--only" in argv else ()
    version = subprocess.run((claude, "--version"), capture_output=True, text=True).stdout.strip()
    probes = tuple(run_probe(claude, scratch, step) for step in plan(only))
    doc = {"schema": "cbe.token-efficiency.prefix-probes/1", "status": "EXPLORATORY",
           "claude": claude, "claudeVersion": version, "model": MODEL, "prompt": PROMPT,
           "minimalTools": MINIMAL_TOOLS, "isolation": "mirrors run-03 harness/launch-agent.sh K1 (env -i, fresh "
           "CLAUDE_CONFIG_DIR and HOME, fresh --session-id, nonce, empty strict MCP config); plus IS_SANDBOX=1 "
           "and --max-turns 1",
           "priceTable": {"path": "research/pricing/anthropic.price-table.json", "sha256": sha256(PRICE_TABLE)},
           "probes": list(probes)}
    out.write_text(json.dumps(doc | {"summary": summarize(probes, prices)}, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv)
