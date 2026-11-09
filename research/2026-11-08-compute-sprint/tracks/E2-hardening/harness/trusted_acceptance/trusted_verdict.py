#!/usr/bin/env python3
"""SPR-E2-03 trusted verdict.

usage: trusted_verdict.py --manifest FILE --evidence-root DIR --verifier-dir DIR --pinned-source-sha SHA
                          [--evidence-manifest-sha256 HEX]   (accepted only to show it is ignored)
Exit: 0 ACCEPTED, 3 FAILED, 4 REFUSED, 2 usage/unreadable.
"""
import argparse
import json
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tac_core as core  # noqa: E402
import tac_keys as keys  # noqa: E402

EXIT = {"ACCEPTED": 0, "FAILED": 3, "REFUSED": 4}


def reader(root: Path):
    def read(rel):
        p = PurePosixPath(rel)
        if not rel or p.is_absolute() or ".." in p.parts:
            return None
        f = root / rel
        return f.read_bytes() if f.is_file() else None
    return read


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--evidence-root", required=True)
    ap.add_argument("--verifier-dir", required=True)
    ap.add_argument("--pinned-source-sha", required=True)
    ap.add_argument("--evidence-manifest-sha256")
    a = ap.parse_args(argv)
    try:
        verifier_dir = Path(a.verifier_dir)
        verify, public_raw = keys.verifier((verifier_dir / "trust" / "verifier.pub").read_text())
        plan_raw = (verifier_dir / "plan.json").read_bytes()
        manifest_raw = Path(a.manifest).read_bytes()
    except OSError as ex:
        print(json.dumps({"verdict": "UNREADABLE", "reasons": [str(ex)]}))
        return 2
    out = core.decide(manifest_raw, reader(Path(a.evidence_root)), verify, core.key_id(public_raw),
                      a.pinned_source_sha, json.loads(plan_raw), core.sha256_hex(plan_raw), a.evidence_manifest_sha256)
    out["reasons_total"] = len(out["reasons"])
    out["reasons"] = out["reasons"][:12]
    print(json.dumps(out))
    return EXIT[out["verdict"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
