"""VAC-002 Layer 3: VAC-001's adjudicate.py, reused unchanged, with the rubric's added label.

    python3 -I adjudicate.py agree REVIEW_DIR
    python3 -I adjudicate.py final REVIEW_DIR MAPPING DATASET

`silent-conflict-resolution` (RUBRIC.md) is an unsupported decision; it is not a hallucination class.
"""
import importlib.util
import json
import pathlib
import sys

_SRC = pathlib.Path(__file__).resolve().parents[3] / "VAC-001" / "harness" / "adjudicate.py"
_spec = importlib.util.spec_from_file_location("vac001_adjudicate", _SRC)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
base.UNSUPPORTED = base.UNSUPPORTED | {"silent-conflict-resolution"}

if __name__ == "__main__":
    cmd, review = sys.argv[1], pathlib.Path(sys.argv[2])
    out = base.agree(review) if cmd == "agree" else base.final(review, pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4]))
    if cmd == "final":
        out["schema"] = "cbe.vac-002.layer3/1"
    print(json.dumps(out, indent=1))
