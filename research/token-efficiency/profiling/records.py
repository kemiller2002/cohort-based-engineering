"""Shared pure helpers: record construction, pricing, statistics, schema checking, output."""
import hashlib
import json
import os
from functools import reduce

SCHEMA = "cbe.token-overhead/1"
GENERATOR = {"name": "cbe-token-overhead-profiler", "version": "1.0.0"}


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(obj):
    """Canonical, deterministic JSON text."""
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def write(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(obj))


def median(xs):
    s = sorted(x for x in xs if x is not None)
    n = len(s)
    return None if n == 0 else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def total(xs):
    vals = [x for x in xs if x is not None]
    return sum(vals) if vals else None


def ratio(a, b, digits=4):
    return None if a is None or not b else round(a / b, digits)


def get(obj, *path, default=None):
    """Safe nested lookup."""
    return reduce(lambda o, k: o.get(k) if isinstance(o, dict) else (o[k] if isinstance(o, list) and isinstance(k, int) and k < len(o) else None), path, obj) if obj is not None else default


def tokens(inp=None, out=None, cr=None, cw=None, cw5=None, cw1=None, lower=False):
    return {"input": inp, "output": out, "cacheRead": cr, "cacheWrite": cw, "cacheWrite5m": cw5, "cacheWrite1h": cw1, "outputLowerBound": lower}


def price_entry(table, model):
    entries = (table or {}).get("entries", [])
    return next((e for e in entries if e.get("model") == model), None)


def cost(tok, entry):
    """Estimated USD from measured buckets; None when no price or no tokens."""
    if not entry or not tok or all(tok.get(k) is None for k in ("input", "output", "cacheRead", "cacheWrite")):
        return None
    cw5 = tok.get("cacheWrite5m") if tok.get("cacheWrite5m") is not None else tok.get("cacheWrite")
    cw1 = tok.get("cacheWrite1h") or 0
    parts = (
        (tok.get("input") or 0) * entry["input"],
        (tok.get("output") or 0) * entry["output"],
        (tok.get("cacheRead") or 0) * entry["cacheRead"],
        (cw5 or 0) * entry["cacheWrite5m"],
        cw1 * entry["cacheWrite1h"],
    )
    return round(sum(parts) / 1e6, 6)


def cost_by_kind(tok, entry):
    if not entry or not tok:
        return None
    cw = (tok.get("cacheWrite") or 0)
    return {
        "input": round((tok.get("input") or 0) * entry["input"] / 1e6, 6),
        "output": round((tok.get("output") or 0) * entry["output"] / 1e6, 6),
        "cacheRead": round((tok.get("cacheRead") or 0) * entry["cacheRead"] / 1e6, 6),
        "cacheWrite": round(cw * entry["cacheWrite5m"] / 1e6, 6),
    }


def record(**kw):
    base = {
        "schema": SCHEMA + "#record",
        "tokens": None,
        "tokenEstimate": None,
        "providerSession": {"provider": None, "sessionId": None, "requestKey": None, "model": None},
        "agent": {"agentId": None, "role": None},
        "workItem": None,
        "executionId": None,
        "toolCalls": None,
        "toolNames": [],
        "testRuns": None,
        "toolResultBytes": None,
        "elapsedMs": None,
        "estimatedCostUsd": None,
        "flags": [],
    }
    return {**base, **kw}


def document(dataset_id, label, inputs, records, summary):
    return {
        "schema": SCHEMA,
        "generator": GENERATOR,
        "dataset": {"id": dataset_id, "label": label},
        "inputs": sorted(inputs, key=lambda i: i["path"]),
        "records": records,
        "summary": summary,
    }


# --- a minimal JSON Schema checker (the subset overhead-schema.json uses), stdlib only

def _types(t):
    return t if isinstance(t, list) else [t]


def _is(value, t):
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }[t]


def check(schema, value, root=None, at="$"):
    """List of violation strings (empty when valid)."""
    root = root or schema
    if "$ref" in schema:
        node = reduce(lambda o, k: o[k], schema["$ref"].lstrip("#/").split("/"), root)
        return check(node, value, root, at)
    if "oneOf" in schema:
        ok = [s for s in schema["oneOf"] if not check(s, value, root, at)]
        return [] if len(ok) == 1 else [f"{at}: matches {len(ok)} of oneOf"]
    errs = []
    if "const" in schema and value != schema["const"]:
        errs.append(f"{at}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{at}: {value!r} not in enum")
    if "type" in schema and not any(_is(value, t) for t in _types(schema["type"])):
        return errs + [f"{at}: type {type(value).__name__} not {schema['type']}"]
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        errs.append(f"{at}: below minimum")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        errs += [f"{at}: missing {k}" for k in schema.get("required", []) if k not in value]
        if schema.get("additionalProperties") is False:
            errs += [f"{at}: unexpected {k}" for k in value if k not in props]
        errs += [e for k, v in value.items() if k in props for e in check(props[k], v, root, f"{at}.{k}")]
    if isinstance(value, list) and "items" in schema:
        errs += [e for i, v in enumerate(value) for e in check(schema["items"], v, root, f"{at}[{i}]")]
    return errs
