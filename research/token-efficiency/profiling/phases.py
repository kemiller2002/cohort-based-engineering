"""Rule-based phase classification for agent tool calls (cbe.token-overhead/1).

Pure functions only. A tool call is a dict {"name": str, "input": dict}. Rules are data:
an ordered tuple of (rule_id, phase, predicate); the first matching rule wins. A shell
command chained with && ; || or | is split into segments; the call takes the phase of
its highest-precedence segment (PRECEDENCE below), so `git commit && praxis work verify`
is verification, not handoff.
"""
import re

PHASES = (
    "requirement-ingestion",
    "repository-discovery",
    "planning-contract",
    "implementation",
    "coordination",
    "handoff",
    "testing",
    "verification",
    "completion",
    "reporting",
    "unattributed",
)

# Highest first: a compound command is attributed to the most "workflow-terminal" step it contains.
PRECEDENCE = (
    "completion",
    "verification",
    "testing",
    "coordination",
    "handoff",
    "implementation",
    "planning-contract",
    "requirement-ingestion",
    "repository-discovery",
    "reporting",
    "unattributed",
)

BRIEF_PATH = re.compile(r"(AGENT_BRIEF\.md|requirements/|DIRECTIVES\.md|\bbrief\b)", re.I)
CONTRACT_PATH = re.compile(r"(contract\.json|authority\.json|\.ecir\b)", re.I)
READ_CMD = re.compile(r"^(cat|head|tail|less|more|ls|find|tree|wc|file|stat|grep|rg|ag|awk|jq|sed\s+-n)\b")
WRITE_CMD = re.compile(r"(^sed\s+-i\b|^tee\b|^cat\s*>|>\s*\S+|^(mv|cp|rm|mkdir|touch)\b|^python3?\s+-c\b.*write)")

SHELL_RULES = (
    ("praxis-complete", "completion", re.compile(r"\bpraxis\s+work\s+complete(-verified)?\b")),
    ("praxis-verify", "verification", re.compile(r"\bpraxis\s+work\s+(verify|validate-run|completion-identity)\b")),
    ("praxis-claim", "coordination", re.compile(r"\bpraxis\s+work\s+(claim|claims|renew|release|recover|expire|start|backlog-transition)\b")),
    ("dotnet-test", "testing", re.compile(r"\bdotnet\s+test\b")),
    ("dotnet-build", "implementation", re.compile(r"\bdotnet\s+(build|restore|run)\b")),
    ("git-remote", "coordination", re.compile(r"\bgit\s+(push|pull|fetch|merge|rebase|remote|reset)\b")),
    ("git-commit", "handoff", re.compile(r"\bgit\s+(add|commit|tag)\b")),
    ("git-inspect", "repository-discovery", re.compile(r"\bgit\s+(status|log|diff|show|rev-parse|branch|ls-files|blame)\b")),
    ("env-setup", "coordination", re.compile(r"^(source|\.)\s+\S*env\.sh\b")),
    ("ordo-contract", "planning-contract", re.compile(r"\b(ordo\s|praxis\s+contract\b)")),
)

SEGMENT_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")
ENV_PREFIX = re.compile(r"^(?:[A-Z_][A-Z0-9_]*=\S*\s+)+")


def segments(command):
    """Shell segments, with leading VAR=value assignments and `cd dir` steps removed."""
    parts = (ENV_PREFIX.sub("", s.strip()) for s in SEGMENT_SPLIT.split(command or ""))
    return tuple(p for p in parts if p and not re.match(r"^cd\b", p))


def classify_segment(segment):
    """(rule_id, phase) for one shell segment."""
    hit = next(((rid, ph) for rid, ph, rx in SHELL_RULES if rx.search(segment)), None)
    if hit:
        return hit
    if WRITE_CMD.search(segment):
        return ("shell-write", "implementation")
    if READ_CMD.search(segment):
        if BRIEF_PATH.search(segment):
            return ("shell-read-brief", "requirement-ingestion")
        if CONTRACT_PATH.search(segment):
            return ("shell-read-contract", "planning-contract")
        return ("shell-read-repo", "repository-discovery")
    return ("shell-other", "unattributed")


def strongest(pairs):
    """The (rule, phase) pair whose phase ranks highest in PRECEDENCE."""
    return min(pairs, key=lambda p: PRECEDENCE.index(p[1]), default=("empty", "unattributed"))


def path_phase(path, default_rule, default_phase):
    if BRIEF_PATH.search(path or ""):
        return ("read-brief", "requirement-ingestion")
    if CONTRACT_PATH.search(path or ""):
        return ("read-contract", "planning-contract")
    return (default_rule, default_phase)


TOOL_RULES = {
    "Read": lambda i: path_phase(i.get("file_path", ""), "read-repo", "repository-discovery"),
    "Grep": lambda i: path_phase(i.get("path", ""), "grep-repo", "repository-discovery"),
    "Glob": lambda i: path_phase(i.get("path", ""), "glob-repo", "repository-discovery"),
    "LS": lambda i: ("ls-repo", "repository-discovery"),
    "Edit": lambda i: ("edit", "implementation"),
    "MultiEdit": lambda i: ("edit", "implementation"),
    "Write": lambda i: ("write", "implementation"),
    "NotebookEdit": lambda i: ("edit", "implementation"),
    "TodoWrite": lambda i: ("todo", "planning-contract"),
    "Task": lambda i: ("delegate", "coordination"),
    "Agent": lambda i: ("delegate", "coordination"),
    "SendMessage": lambda i: ("message", "coordination"),
}


def classify_call(call):
    """(rule_id, phase) for one tool call."""
    name, inp = call.get("name", ""), call.get("input") or {}
    if name == "Bash":
        return strongest(tuple(classify_segment(s) for s in segments(inp.get("command", ""))))
    rule = TOOL_RULES.get(name)
    return rule(inp) if rule else ("tool-" + (name or "unknown"), "unattributed")


def classify_request(calls, is_last):
    """(rule_id, phase) for a provider request from the tool calls it emitted."""
    if not calls:
        return ("final-message", "reporting") if is_last else ("think-only", "planning-contract")
    return strongest(tuple(classify_call(c) for c in calls))


def is_test_command(call):
    return call.get("name") == "Bash" and any(
        re.search(r"\bdotnet\s+test\b|\bpraxis\s+work\s+validate-run\b", s) for s in segments((call.get("input") or {}).get("command", ""))
    )


def canonical_call(call):
    """Identity of a call for duplicate detection: tool name plus whitespace-normalized input."""
    inp = call.get("input") or {}
    return (call.get("name", ""),) + tuple(sorted((k, re.sub(r"\s+", " ", str(v)).strip()) for k, v in inp.items() if k != "description"))
