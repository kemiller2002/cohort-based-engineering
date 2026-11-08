"""Pure checks and classifiers for SPR-B2-01. No I/O: inputs are parsed data, outputs are plain dicts/lists."""
import re
from datetime import datetime

CAUGHT, NOT_CAUGHT, NOT_REPLAYABLE = "CAUGHT", "NOT CAUGHT", "NOT REPLAYABLE"
VERIFIER_APPROVALS_SCHEMA = "causa.requirements-approvals/1"


# ---- inputs ---------------------------------------------------------------------------------------------------------

def parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def is_pre_t0(commit_time, t0):
    return parse_time(commit_time) < parse_time(t0)


# ---- D1 approvals -----------------------------------------------------------------------------------------------------

def approvals_schema_problems(approvals, expected=VERIFIER_APPROVALS_SCHEMA):
    """Schema-id check of an approvals document against the verifier's format."""
    found = approvals.get("schema") if isinstance(approvals, dict) else None
    return [] if found == expected else [f"approvals schema is {found!r}, the verifier reads {expected!r}"]


def approvals_problems_in(lines):
    """Verifier trust problems that concern the approvals file (not the stub ledger/evidence)."""
    return [l for l in lines if re.search(r"approval", l, re.IGNORECASE)]


# ---- D2 suite commands ------------------------------------------------------------------------------------------------

def dotnet_test_targets(command):
    """Positional project/directory arguments of a `dotnet test ...` command line (options and their values skipped)."""
    tokens = re.findall(r'"[^"]*"|\S+', command)
    if tokens[:2] != ["dotnet", "test"]:
        return []
    targets, skip = [], False
    for t in tokens[2:]:
        if skip:
            skip = False
            continue
        if t.startswith("-"):
            skip = "=" not in t and t not in ("--no-build", "--no-restore", "--list-tests")
            continue
        targets.append(t.strip('"'))
    return targets


def playwright_projects(command):
    return re.findall(r"--project[= ](\S+)", command)


def classify_suite_run(result_text, exit_code):
    """Classify one executed suite command from its output."""
    if "MSB1008" in result_text:
        return "MSB1008"
    if re.search(r'Project\(s\) "?[\w,-]+"? not found', result_text):
        return "UNDEFINED_PLAYWRIGHT_PROJECT"
    if re.search(r"could not find dependent assembly|FSharp\.Core", result_text) and "skipp" in result_text.lower():
        return "ASSEMBLY_SKIPPED"
    return "OK" if exit_code == 0 else "OTHER_FAILURE"


# ---- D4 dependency cycles -----------------------------------------------------------------------------------------

def strongly_connected(graph):
    """Tarjan's SCCs of {node: iterable(successors)}; returns the components with a cycle (size>1 or self-loop)."""
    index, low, on, stack, out, counter = {}, {}, set(), [], [], [0]
    nodes = set(graph) | {m for vs in graph.values() for m in vs}

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph.get(v, ()):
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
            if len(comp) > 1 or v in graph.get(v, ()):
                out.append(sorted(comp))

    for n in sorted(nodes):
        if n not in index:
            visit(n)
    return out


def merge_edges(*edge_maps):
    out = {}
    for m in edge_maps:
        for k, vs in m.items():
            out.setdefault(k, set()).update(vs)
    return out


def declared_edges(slices):
    """V1: slice -> declared dependsOn."""
    return {s["id"]: set(s.get("dependsOn", [])) for s in slices}


def test_owner_edges(slices, test_obligations, obligation_requirement):
    """V2: S -> T when an acceptance test of S binds an obligation whose requirement slice T owns (T != S).

    test_obligations: {testId: [obligationId]}, obligation_requirement: {obligationId: requirementId}."""
    owner = {r: s["id"] for s in slices for r in s.get("requirements", [])}
    edges = {}
    for s in slices:
        for t in s.get("acceptanceTests", []):
            for o in test_obligations.get(t, []):
                o_owner = owner.get(obligation_requirement.get(o))
                if o_owner and o_owner != s["id"]:
                    edges.setdefault(s["id"], set()).add(o_owner)
    return edges


def assertion_need_edges(slices, needs_rules):
    """V3: S -> N for every governed assertion of S that the pinned needs file says needs slice N."""
    needs = {}
    for r in needs_rules:
        for a in r.get("assertions", []):
            needs.setdefault(a, set()).update(r.get("needs", []))
    edges = {}
    for s in slices:
        for a in s.get("governedAssertions", []):
            ns = needs.get(a, set()) - {s["id"]}
            if ns:
                edges.setdefault(s["id"], set()).update(ns)
    return edges


def cycle_containing(cycles, members):
    return [c for c in cycles if set(members) <= set(c)]


# ---- D5 rules binding -----------------------------------------------------------------------------------------------

def rules_binding_problems(rules_repository, target_identities):
    """Process-evidence rules must be bound to an identity of the target repository."""
    if rules_repository in set(target_identities):
        return []
    return [f"process-evidence rules require repository {rules_repository!r}; the target is {sorted(set(target_identities))}"]


# ---- D6 time budgets --------------------------------------------------------------------------------------------------

def budget_verdict(cap_minutes, estimate_seconds):
    over = estimate_seconds > cap_minutes * 60
    return {"capMinutes": cap_minutes, "estimateSeconds": round(estimate_seconds, 1),
            "estimateMinutes": round(estimate_seconds / 60, 1), "exceedsCap": over}


def max_by_kind(step_rows, kinds):
    """kinds: {kind: predicate(step_row) -> bool}; returns {kind: max seconds (0 when none)} over the rows."""
    return {k: max([float(r["seconds"] or 0) for r in step_rows if pred(r)] or [0.0]) for k, pred in kinds.items()}


# ---- outcome ------------------------------------------------------------------------------------------------------

def outcome(replayable, matched):
    if not replayable:
        return NOT_REPLAYABLE
    return CAUGHT if matched else NOT_CAUGHT


def catch_rate(outcomes):
    caught = sum(1 for o in outcomes if o == CAUGHT)
    replayable = sum(1 for o in outcomes if o in (CAUGHT, NOT_CAUGHT))
    return {"caught": caught, "replayable": replayable, "notReplayable": len(outcomes) - replayable,
            "rate": round(caught / replayable, 3) if replayable else None}
