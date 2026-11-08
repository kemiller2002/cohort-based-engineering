"""Mine agent transcripts (Claude Code JSONL) for F# compile-error cycles.

Usage: python3 mine_transcripts.py OUT_PREFIX TRANSCRIPT.jsonl [...]
Writes OUT_PREFIX-builds.jsonl (one row per dotnet build/test/run/fsi invocation) and OUT_PREFIX-errors.jsonl
(one row per distinct (transcript, file, line, code) compile diagnostic). Paths are reduced to the file name.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

BUILD_CMD = re.compile(r"\bdotnet\s+(build|test|run|fsi|publish)\b")
FS_ERR = re.compile(r"([\w./\\-]+\.fsx?)\((\d+),(\d+)\): error (FS\d{4}): ([^\[\n\r]*)")
SUCCESS = re.compile(r"Build succeeded|Passed!|\b0 Error\(s\)|Test Run Successful", re.I)
TYPE_NAME = re.compile(r"'[^']*'")


def normalise(msg: str) -> str:
    """Strip identifiers so messages cluster: quoted names -> 'X', numbers -> N."""
    return re.sub(r"\d+", "N", TYPE_NAME.sub("'X'", msg.strip()))[:120]


def result_text(block: dict) -> str:
    c = block.get("content")
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
    return str(c or "")


def outcome(text: str) -> str:
    if FS_ERR.search(text):
        return "fsharp-compile-error"
    if re.search(r"error (MSB|NU|NETSDK|CS)\d+", text):
        return "other-build-error"
    if SUCCESS.search(text):
        return "ok"
    if re.search(r"Failed!|\bFailed:\s*[1-9]|\[FAIL\]|failed\b", text):
        return "test-failure"
    return "unknown"


def ts(s: str | None):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def events(rows: list[dict]):
    """Yield (timestamp, kind, id, payload) for Bash tool_use and tool_result blocks in file order."""
    for r in rows:
        content = (r.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if b.get("type") == "tool_use" and b.get("name") == "Bash":
                yield ts(r.get("timestamp")), "use", b.get("id"), (b.get("input") or {}).get("command", "")
            elif b.get("type") == "tool_result":
                yield ts(r.get("timestamp")), "result", b.get("tool_use_id"), result_text(b)


def builds(transcript: str, rows: list[dict]) -> list[dict]:
    pending, out = {}, []
    for t, kind, ident, payload in events(rows):
        if kind == "use" and BUILD_CMD.search(payload):
            pending[ident] = (t, payload)
        elif kind == "result" and ident in pending:
            t0, cmd = pending.pop(ident)
            errs = FS_ERR.findall(payload)
            out.append({"transcript": transcript, "startedAt": t0.isoformat() if t0 else None,
                        "endedAt": t.isoformat() if t else None, "command": cmd[:200], "outcome": outcome(payload),
                        "fsCodes": sorted({e[3] for e in errs}), "errorCount": len({(e[0], e[1], e[3]) for e in errs})})
    return out


def distinct_errors(transcript: str, rows: list[dict]) -> list[dict]:
    seen = {}
    for _, kind, _, payload in events(rows):
        if kind != "result":
            continue
        for f, line, col, code, msg in FS_ERR.findall(payload):
            key = (Path(f.replace("\\", "/")).name, line, code)
            seen.setdefault(key, {"transcript": transcript, "file": key[0], "line": int(line), "code": code,
                                  "message": msg.strip()[:200], "pattern": normalise(msg)})
    return list(seen.values())


def recovery_minutes(bs: list[dict]) -> list[float]:
    """Minutes from each first compile failure of a streak to the next non-compile-error build."""
    spans, start = [], None
    for b in bs:
        if b["outcome"] == "fsharp-compile-error":
            start = start or b["startedAt"]
        elif start and b["outcome"] in ("ok", "test-failure"):
            spans.append((ts(b["endedAt"]) - ts(start)).total_seconds() / 60)
            start = None
    return [round(s, 2) for s in spans]


def main() -> None:
    prefix, paths = sys.argv[1], sys.argv[2:]
    all_b, all_e = [], []
    for p in paths:
        rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        name = "/".join(Path(p).parts[-4:-1])
        bs = builds(name, rows)
        for b in bs:
            b["streakRecoveryMinutes"] = None
        rec = recovery_minutes(bs)
        all_b += bs + [{"transcript": name, "summary": True, "builds": len(bs),
                        "compileFailures": sum(b["outcome"] == "fsharp-compile-error" for b in bs),
                        "recoveryMinutes": rec}]
        all_e += distinct_errors(name, rows)
    for suffix, data in (("builds", all_b), ("errors", all_e)):
        with open(f"{prefix}-{suffix}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(d) + "\n" for d in data)
    print(len(paths), "transcripts;", sum(1 for b in all_b if not b.get("summary")), "builds;", len(all_e), "distinct errors")


if __name__ == "__main__":
    main()
