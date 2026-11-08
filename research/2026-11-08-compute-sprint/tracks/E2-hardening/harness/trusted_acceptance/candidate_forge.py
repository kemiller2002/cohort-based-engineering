#!/usr/bin/env python3
"""T3: run AS THE CANDIDATE (uid 65534). Generates its own Ed25519 key and a bundle in the trusted format claiming
PASS for every plan requirement for SHA, written to OUT (a candidate-writable directory)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tac_core as core  # noqa: E402
import tac_keys as keys  # noqa: E402


def main(plan_path, sha, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    public_raw = keys.generate(out / "own.pem", out / "own.pub")
    sign, _ = keys.signer(out / "own.pem")
    kid = core.key_id(public_raw)
    plan_raw = Path(plan_path).read_bytes()
    files = {}
    for req in json.loads(plan_raw)["requirements"]:
        entry = core.make_entry("forged", "forged-job", sha, req["id"], req, req["expect"].get("exit_code", 0),
                                req["expect"].get("stdout", ""), "t", "t", kid)
        files[f"entries/{req['id']}.json"] = core.signed_document(entry, sign)
    for rel, raw in files.items():
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(raw)
    manifest = core.make_manifest("forged", "forged-job", sha, core.sha256_hex(plan_raw), kid, files)
    (out / "manifest.json").write_bytes(core.signed_document(manifest, sign))
    # Variant: claim the pinned verifier key id while signing with its own key.
    print(json.dumps({"forged_kid": kid}))


if __name__ == "__main__":
    main(*sys.argv[1:4])
