"""Isolated probe runner. Run as: python3 -I -B probe_runner.py  (JSON request on stdin).

Imports the workspace's pricing.py and errors.py (workspace dir prepended to sys.path),
executes each probe and prints raw outcomes as JSON. No scoring happens here.
"""
import copy
import datetime
import json
import os
import sys


def decode(v):
    if isinstance(v, list):
        return [decode(x) for x in v]
    if isinstance(v, dict):
        if set(v) == {"$dt"}:
            return datetime.datetime.fromisoformat(v["$dt"])
        if set(v) == {"$naive"}:
            return datetime.datetime.fromisoformat(v["$naive"]).replace(tzinfo=None)
        if set(v) == {"$date"}:
            return datetime.date.fromisoformat(v["$date"])
        if set(v) == {"$tuple"}:
            return tuple(decode(x) for x in v["$tuple"])
        return {k: decode(x) for k, x in v.items()}
    return v


def jsonable(v):
    try:
        json.dumps(v)
        return v
    except (TypeError, ValueError):
        return {"$repr": repr(v), "$type": type(v).__name__}


def describe_exc(e, errors_mod):
    ns = getattr(errors_mod, "NotSpecified", None) if errors_mod else None
    return {
        "kind": "raise",
        "exc_type": type(e).__name__,
        "exc_module": type(e).__module__,
        "is_ws_notspecified": bool(ns is not None and isinstance(e, ns)),
        "is_invalidorder": type(e).__name__ == "InvalidOrder" or any(
            c.__name__ == "InvalidOrder" for c in type(e).__mro__),
        "message": str(e)[:300],
    }


def run_probe(probe, pricing, errors_mod):
    if probe["kind"] == "invalidorder_class":
        cls = getattr(pricing, "InvalidOrder", None)
        ok = isinstance(cls, type) and issubclass(cls, ValueError)
        return {"kind": "value", "value": ok, "types": None}
    fn = getattr(pricing, probe["fn"], None)
    if fn is None:
        return {"kind": "missing", "fn": probe["fn"]}
    args = copy.deepcopy(decode(probe.get("args", [])))
    kwargs = copy.deepcopy(decode(probe.get("kwargs", {})))
    try:
        out = fn(*args, **kwargs)
    except BaseException as e:  # noqa: BLE001 - we record everything
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            return {"kind": "raise", "exc_type": type(e).__name__, "exc_module": "builtins",
                    "is_ws_notspecified": False, "is_invalidorder": False, "message": ""}
        return describe_exc(e, errors_mod)
    types = ({k: type(x).__name__ for k, x in out.items()} if isinstance(out, dict)
             else type(out).__name__)
    return {"kind": "value", "value": jsonable(out), "types": types}


def main():
    req = json.load(sys.stdin)
    ws = req["ws"]
    os.chdir(ws)
    sys.path.insert(0, ws)
    result = {"import_error": None, "probes": {}}
    try:
        import errors as errors_mod  # noqa: F401
    except BaseException as e:  # noqa: BLE001
        errors_mod = None
        result["errors_import_error"] = f"{type(e).__name__}: {e}"
    try:
        import pricing
    except BaseException as e:  # noqa: BLE001
        result["import_error"] = f"{type(e).__name__}: {e}"
        print(json.dumps(result))
        return
    result["pricing_file"] = os.path.abspath(getattr(pricing, "__file__", "") or "")
    result["errors_file"] = os.path.abspath(getattr(errors_mod, "__file__", "") or "") if errors_mod else None
    for p in req["probes"]:
        result["probes"][p["id"]] = run_probe(p, pricing, errors_mod)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
