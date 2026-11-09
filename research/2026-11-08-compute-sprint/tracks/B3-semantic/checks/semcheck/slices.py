"""C4 (Causa question): implied slice dependencies from invariant sources.

A slice S that must pass an invariant test t needs the slices that own the invariant's source requirements. Edge
S -> owner(req) for every invariant test t in S.acceptanceTests, invariant I that lists t, req in I.sources,
owner(req) != S (owner = the slice whose 'requirements' list holds req). Variants:
  C4-all     : every invariant test
  C4-browser : only invariant tests that run in a browser (id prefix 'playwright:')
Cycles are strongly connected components of declared dependsOn plus implied edges."""


def owners(slices):
    out = {}
    for s in slices:
        for r in s.get("requirements", []):
            out.setdefault(r, set()).add(s["id"])
    return out


def implied_edges(slices, invariants, browser_only):
    own = owners(slices)
    by_test = {}
    for inv in invariants:
        for t in inv.get("tests", []):
            by_test.setdefault(t["id"], []).append(inv)
    edges = {}
    for s in slices:
        for tid in s.get("acceptanceTests", []):
            if browser_only and not tid.startswith("playwright:"):
                continue
            for inv in by_test.get(tid, []):
                for req in inv.get("sources", []):
                    for o in own.get(req, ()):
                        if o != s["id"]:
                            edges.setdefault((s["id"], o), []).append({"test": tid, "invariant": inv["id"], "source": req})
    return edges


def scc(nodes, adj):
    """Tarjan, iterative-safe for small graphs (recursion depth <= node count)."""
    import sys
    sys.setrecursionlimit(max(1000, 4 * len(nodes)))
    index, low, stack, on, out, counter = {}, {}, [], set(), [], [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in sorted(adj.get(v, ())):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            out.append(sorted(comp))

    for v in sorted(nodes):
        if v not in index:
            visit(v)
    return out


def check(slices, invariants, browser_only):
    declared = {(s["id"], d) for s in slices for d in s.get("dependsOn", [])}
    implied = implied_edges(slices, invariants, browser_only)
    adj = {}
    for a, b in declared | set(implied):
        adj.setdefault(a, set()).add(b)
    nodes = {s["id"] for s in slices}
    comps = [c for c in scc(nodes, adj) if len(c) > 1]
    new = {k: v for k, v in implied.items() if k not in declared}
    return {"check": "C4-%s" % ("browser" if browser_only else "all"),
            "impliedEdges": len(implied), "impliedNotDeclared": len(new),
            "cycles": [{"slices": c, "size": len(c),
                        "impliedEdgesInside": sorted("%s->%s" % k for k in new if k[0] in c and k[1] in c)}
                       for c in comps],
            "edgeEvidence": {"%s->%s" % k: v for k, v in sorted(new.items())}}
