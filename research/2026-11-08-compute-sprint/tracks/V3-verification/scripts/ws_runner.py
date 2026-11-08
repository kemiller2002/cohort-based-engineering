"""Executed in a subprocess against a COPY of one workspace.  Reads probes (JSON) on stdin,
imports the workspace module, runs each probe and writes raw outcomes (JSON) on stdout.
No scoring happens here; scoring is in d2_oracle.py."""
import datetime
import importlib
import json
import sys


def decode(x):
    if isinstance(x, dict) and set(x) == {"__tuple__"}:
        return tuple(decode(v) for v in x["__tuple__"])
    if isinstance(x, dict) and set(x) == {"__dt__"}:
        return datetime.datetime.fromisoformat(x["__dt__"])
    if isinstance(x, dict) and set(x) == {"__date__"}:
        return datetime.date.fromisoformat(x["__date__"])
    if isinstance(x, dict):
        return {k: decode(v) for k, v in x.items()}
    if isinstance(x, list):
        return [decode(v) for v in x]
    return x


def jsonable(v):
    try:
        json.dumps(v)
        return v
    except TypeError:
        return repr(v)


def class_info(mod, names):
    get = lambda n: getattr(mod, n, None)
    isexc = lambda c: isinstance(c, type) and issubclass(c, BaseException)
    return {"classes": {n: {"exists": isexc(get(n)), "subclassOf": [b.__name__ for b in get(n).__mro__[1:]] if isexc(get(n)) else []}
                        for n in names}}


def run_probe(mod, refusal, p):
    if p["op"] == "classinfo":
        return class_info(mod, p["names"])
    fn = getattr(mod, p["func"], None)
    if not callable(fn):
        return {"kind": "missing_function"}
    try:
        value = fn(*decode(p.get("args", [])), **decode(p.get("kwargs", {})))
        types = {k: type(v).__name__ for k, v in value.items()} if isinstance(value, dict) else type(value).__name__
        return {"kind": "value", "value": jsonable(value), "types": types}
    except BaseException as e:  # noqa: BLE001  (untrusted code; classify everything)
        cls = type(e)
        return {"kind": "raise", "cls": cls.__name__, "msg": str(e)[:200],
                "isRefusal": refusal is not None and isinstance(e, refusal),
                "isValueError": isinstance(e, ValueError),
                "isNotImplemented": isinstance(e, NotImplementedError),
                "definedInWorkspace": getattr(cls, "__module__", "") in (mod.__name__, "errors"),
                "mroNames": [b.__name__ for b in cls.__mro__]}


def main():
    ws, module, refusal_spec = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.path.insert(0, ws)
    sys.dont_write_bytecode = True
    probes = json.load(sys.stdin)
    try:
        mod = importlib.import_module(module)
    except BaseException as e:  # noqa: BLE001
        print(json.dumps({"importError": f"{type(e).__name__}: {e}"[:300], "outcomes": {}}))
        return
    owner, _, name = refusal_spec.partition(":")
    try:
        refusal = getattr(importlib.import_module(owner), name, None)
    except BaseException:  # noqa: BLE001
        refusal = None
    refusal = refusal if isinstance(refusal, type) else None
    out = {p["id"]: run_probe(mod, refusal, p) for p in probes}
    print(json.dumps({"importError": None, "refusalFound": refusal is not None, "outcomes": out}))


if __name__ == "__main__":
    main()
