"""Export a content-free per-request usage ledger for every finished unit (no prompt, output or tool-input text).

    python3 -I ledger.py RESULTS_DIR STATE_DIR TRANSCRIPT_DIR RUN
Writes RESULTS_DIR/RUN/ARM/requests.jsonl: one line per de-duplicated model request inside a unit's recorded window.
"""
import json
import pathlib
import sys
from datetime import datetime


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def stream(text):
    """Parse concatenated JSON values (finish.jsonl is written by `jq -n`, one pretty object per record)."""
    dec, i = json.JSONDecoder(), 0
    while i < len(text):
        while i < len(text) and text[i].isspace():
            i += 1
        if i < len(text):
            obj, i = dec.raw_decode(text, i)
            yield obj


def windows(state_arm):
    setup = json.loads((state_arm / "setup.json").read_text())
    staged = {u["unit"]: u["stagedAt"] for u in setup["units"]}
    fin = list(stream((state_arm / "finish.jsonl").read_text()))
    last = {}
    for f in fin:
        last[(f["unit"], f["attempt"])] = f
    for (u, a), f in sorted(last.items()):
        start = staged[u] if a == 1 else last[(u, a - 1)]["finishedAt"]
        yield u, a, f["agentId"], ts(start), ts(f["finishedAt"])


def requests(transcript, start, end):
    best = {}
    for line in transcript.read_text().splitlines():
        o = json.loads(line)
        m = o.get("message") or {}
        if not (isinstance(m, dict) and m.get("id") and m.get("usage") and o.get("timestamp")):
            continue
        t = ts(o["timestamp"])
        if not (start <= t <= end):
            continue
        u = m["usage"]
        cc = u.get("cache_creation") or {}
        tools = [b.get("name") for b in m.get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
        row = {"at": o["timestamp"], "model": m.get("model"), "effort": o.get("effort"),
               "input": u.get("input_tokens", 0), "cacheWrite5m": cc.get("ephemeral_5m_input_tokens", 0),
               "cacheWrite1h": cc.get("ephemeral_1h_input_tokens", 0), "cacheRead": u.get("cache_read_input_tokens", 0),
               "outputLowerBound": u.get("output_tokens", 0), "tools": tools}
        prev = best.get(m["id"])
        best[m["id"]] = row if prev is None or row["outputLowerBound"] >= prev["outputLowerBound"] else prev
        if prev is not None:
            best[m["id"]]["tools"] = sorted(set(prev["tools"]) | set(tools))
    return sorted(best.values(), key=lambda r: r["at"])


if __name__ == "__main__":
    results, state, tdir, run = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
    for arm_state in sorted(p for p in (state / run).iterdir() if p.is_dir() and (p / "finish.jsonl").exists()):
        rows = [{"unit": u, "attempt": a, **r} for u, a, agent, s, e in windows(arm_state)
                for r in requests(tdir / f"agent-{agent}.jsonl", s, e)]
        (results / run / arm_state.name / "requests.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(run, arm_state.name, len(rows))
