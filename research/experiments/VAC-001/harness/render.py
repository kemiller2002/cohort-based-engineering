"""Render one VAC-001 unit brief from briefs/brief.md. Pure: inputs are arguments and files, output is stdout."""
import argparse
import json
import pathlib
import re

SECTION = re.compile(r"<!-- section: ([a-zA-Z-]+) -->\n")


def sections(text):
    parts = SECTION.split(text)
    return dict(zip(parts[1::2], parts[2::2]))


def fill(template, values):
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], template)


def note(fault_id, faults_path, task):
    if fault_id == "none":
        return ""
    fault = next(f for f in json.loads(pathlib.Path(faults_path).read_text())["faults"] if f["id"] == fault_id)
    return "## Context from the team lead\n\n" + fault["note"].replace("{{TASK}}", task) + "\n"


def brief(a):
    s = sections(pathlib.Path(a.briefs, "brief.md").read_text())
    long_lived = a.arm in ("B", "C", "D")
    previous = (f"The previous unit's report is `{a.previous_report}`." if a.previous_report != "none"
                else "This is the first unit.")
    values = {
        "UNIT": str(a.unit), "TASK": a.task, "ITEM": f"LEDGER-{a.task}", "REPO": a.repo, "ENV": a.env,
        "WORKSPACE": a.workspace, "DIRECTIVES": a.directives, "PREVIOUS": previous,
        "NOTE": note(a.fault, a.faults, a.task),
    }
    values["CONTINUITY"] = fill(s["continuity-L"] if long_lived else s["continuity-A"], values).strip()
    intro = s["intro-first"] if a.first == "yes" else s["intro-next"]
    controls = ([s["controls-C"]] if a.arm in ("C", "D", "DR") else []) + ([s["controls-D"]] if a.arm in ("D", "DR") else [])
    return "\n".join(fill(part, values).strip() + "\n" for part in [intro, s["task"], *controls, s["report"]])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ["arm", "unit", "task", "fault", "workspace", "repo", "env", "directives", "briefs", "faults",
                 "previous-report", "first"]:
        p.add_argument("--" + name, required=True)
    print(brief(p.parse_args()), end="")
