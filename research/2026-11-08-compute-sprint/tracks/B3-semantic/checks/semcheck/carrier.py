"""C2: every command carrier in the frozen F# interface must carry a body that can tell commands apart.

A type expression *has a body* when some value-level part of it can discriminate between alternatives:
  * a union with two or more cases, or an opaque owner-defined type (class end / interface), or a type the package does
    not define (benefit of the doubt);
  * a record or tuple with at least one part that has a body; option/list/array/seq/Set/Map/Result of a part with a body.
Scalars (Guid, string, int, int64, bool, DateTime*, decimal, float, TimeSpan, Uri, unit), single-case wrappers of them,
and function-typed fields have no body: they are identifiers, versions, timestamps or free strings (metadata).
Candidates (C2, primary): every defined type whose name contains 'Command', every union case or record field whose name
contains 'Command' (its payload/field type). C2b (secondary) uses 'Payload' instead of 'Command'.
"""
import re
from typing import NamedTuple

PRIMITIVES = {"guid", "string", "int", "int32", "int64", "uint32", "uint64", "bool", "datetime", "datetimeoffset",
              "decimal", "float", "double", "single", "timespan", "uri", "unit", "byte", "char", "int16", "dateonly",
              "timeonly", "bigint", "obj"}
CONTAINERS = {"option", "voption", "list", "array", "seq", "set", "result", "map", "async", "task", "nonemptylist",
              "readonlylist", "ilist", "ienumerable"}


class TypeDef(NamedTuple):
    name: str
    kind: str      # record | union | opaque | abbrev
    parts: tuple   # record: ((field, type), ...); union: ((case, payload-or-''), ...); abbrev: (expr,)
    file: str


def strip_comments(src):
    src = re.sub(r"\(\*.*?\*\)", "", src, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", l) for l in src.splitlines())


def split_top(s, sep):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "<({[":
            depth += 1
        elif ch in ">)}]":
            depth -= 1
        if ch == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


HEAD = re.compile(r"^\s*(?:type|and)\s+(?:private\s+|internal\s+)?([A-Z]\w*)(?:<[^>]*>)?\s*=\s*(.*)$")
STOP = re.compile(r"^\s*(?:type|and|module|namespace|open|let|\[<|#)\b|^\s*\[<")
MEMBER = re.compile(r"^\s*(?:with|member|static|override|interface\s+\w|abstract|default|new)\b")


def parse_types(src, file=""):
    lines = strip_comments(src).splitlines()
    defs, i = [], 0
    while i < len(lines):
        m = HEAD.match(lines[i])
        if not m:
            i += 1
            continue
        name, body = m.group(1), [m.group(2)]
        i += 1
        while i < len(lines) and not STOP.match(lines[i]) and not HEAD.match(lines[i]):
            if MEMBER.match(lines[i]):
                while i < len(lines) and not STOP.match(lines[i]) and not HEAD.match(lines[i]):
                    i += 1
                break
            body.append(lines[i])
            i += 1
        defs.append(classify(name, " ".join(x.strip() for x in body).strip(), file))
    return tuple(d for d in defs if d)


def classify(name, body, file):
    if not body:
        return None
    if body.startswith("{"):
        inner = body[1:body.rfind("}")] if "}" in body else body[1:]
        fields = []
        for f in split_top(inner.replace("\n", ";"), ";"):
            if ":" in f:
                fn, ft = f.split(":", 1)
                fields.append((fn.replace("mutable", "").strip(), ft.strip()))
        return TypeDef(name, "record", tuple(fields), file)
    if re.match(r"^(class|interface|struct)\b.*\bend$", body) or body in ("class end", "interface end"):
        return TypeDef(name, "opaque", (), file)
    cases_src = body[1:] if body.startswith("|") else body
    cases = split_top(cases_src, "|")
    if body.startswith("|") or len(cases) > 1 or re.match(r"^[A-Z]\w*\s+of\b", body):
        parsed = []
        for c in cases:
            cm = re.match(r"^([A-Z]\w*)(?:\s+of\s+(.*))?$", c.strip())
            if cm:
                parsed.append((cm.group(1), (cm.group(2) or "").strip()))
        return TypeDef(name, "union", tuple(parsed), file)
    return TypeDef(name, "abbrev", (body,), file)


def drop_label(part):
    m = re.match(r"^[a-z_]\w*\s*:\s*(.*)$", part.strip())
    return m.group(1) if m else part.strip()


def has_body(expr, env, seen=frozenset()):
    """(verdict, reason) for a type expression under the type environment env {name: TypeDef}."""
    e = expr.strip().replace("->", "\u2192")
    if not e:
        return False, "no payload"
    if len(split_top(e, "\u2192")) > 1:
        return False, "function"
    parts = split_top(e, "*")
    if len(parts) > 1:
        rs = [has_body(drop_label(p), env, seen) for p in parts]
        return any(r[0] for r in rs), "tuple(" + ", ".join(r[1] for r in rs) + ")"
    e = drop_label(e)
    m = re.match(r"^(.*?)\s+(option|voption|list|array|seq|Set)$", e) or re.match(r"^(.*)\[\]$", e)
    if m:
        return has_body(m.group(1), env, seen)
    g = re.match(r"^([\w.]+)\s*<(.*)>$", e)
    if g:
        base = g.group(1).split(".")[-1]
        if base.lower() in CONTAINERS:
            rs = [has_body(a, env, seen) for a in split_top(g.group(2), ",")]
            return any(r[0] for r in rs), base + "<" + ", ".join(r[1] for r in rs) + ">"
        e = base
    if e.startswith("(") and e.endswith(")"):
        return has_body(e[1:-1], env, seen)
    name = e.split(".")[-1]
    if name.lower() in PRIMITIVES:
        return False, name + " (scalar)"
    if name in seen:
        return False, name + " (recursive)"
    d = env.get(name)
    if d is None:
        return True, name + " (undefined here: assumed body)"
    s2 = seen | {name}
    if d.kind == "opaque":
        return True, name + " (opaque payload)"
    if d.kind == "abbrev":
        return has_body(d.parts[0], env, s2)
    if d.kind == "union":
        if len(d.parts) >= 2:
            return True, "%s (union, %d cases)" % (name, len(d.parts))
        cn, payload = d.parts[0]
        v, r = has_body(payload, env, s2)
        return v, "%s (single case %s of %s)" % (name, cn, r)
    data = [(fn, ft) for fn, ft in d.parts if "->" not in ft and "\u2192" not in ft]
    rs = [(fn,) + has_body(ft, env, s2) for fn, ft in data]
    return any(r[1] for r in rs), "%s {%s}" % (name, "; ".join("%s: %s" % (r[0], r[2]) for r in rs))


def candidates(defs, word):
    pat = re.compile(word, re.I)
    out = []
    for d in defs:
        if pat.search(d.name) and d.kind in ("record", "union", "abbrev"):
            out.append(("type " + d.name, d.name, d.file))
        if d.kind == "union":
            out += [("case %s.%s" % (d.name, c), p, d.file) for c, p in d.parts if pat.search(c) and p]
        if d.kind == "record":
            out += [("field %s.%s" % (d.name, f), t, d.file) for f, t in d.parts if pat.search(f) and "->" not in t]
    return out


def check(defs, word="command", label="C2"):
    env = {}
    for d in defs:
        env.setdefault(d.name, d)
    alarms, examined = [], []
    for where, expr, file in candidates(defs, word):
        v, reason = has_body(expr, env)
        examined.append({"candidate": where, "type": expr, "hasBody": v, "reason": reason, "file": file})
        if not v:
            alarms.append({"check": label, "candidate": where, "type": expr, "file": file,
                           "reason": "carrier has no body that can discriminate alternatives: " + reason})
    return alarms, examined
