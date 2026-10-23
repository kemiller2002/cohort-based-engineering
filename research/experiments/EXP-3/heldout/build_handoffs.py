#!/usr/bin/env python3
"""Build the held-out corpus's authority handoffs by the preregistered rules (PREREGISTRATION.md section 4).

  python3 -I build_handoffs.py

Reuses harness/exp3.py's own build_handoff (requirements, decisions, approvals, parameters; observations, policy
questions and invariants empty; fixed produced.at, revision and authority-contract hash) unchanged, so the held-out
handoffs are built exactly as the phase-1 ones. Each scenario's tree is complete (no overlays), so materialisation is
the tree itself. Writes handoffs/<id>.handoff.json and validates each against the 0.1 schema. Runs no audit.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness"))
import exp3  # noqa: E402


def main():
    rev = exp3.git_rev()
    out = HERE / "handoffs"
    out.mkdir(exist_ok=True)
    for sd in sorted(p for p in (HERE / "scenarios").iterdir() if p.is_dir()):
        sid = sd.name
        h = exp3.build_handoff(sid, sd / "tree", rev)
        exp3.validate("echelon-authority-handoff-0.1.schema.json", h)
        (out / f"{sid}.handoff.json").write_text(json.dumps(h, indent=2) + "\n")
        print(sid, "requirements", len(h["requirements"]), "decisions", len(h["decisions"]))


if __name__ == "__main__":
    main()
