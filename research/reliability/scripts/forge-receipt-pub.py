#!/usr/bin/env python3
"""REL-001 gate/experiment C helper: forge a verification receipt (echelon.verification-receipt/1, DSSE).

usage: python3 -I forge-receipt.py TEMPLATE-ENVELOPE OUT REPO WORK-ITEM own|trusted [CLAIMANT]
Takes a GENUINE receipt as the format template, re-binds its payload to REPO's HEAD and tree, WORK-ITEM,
generation 1 and CLAIMANT (default gate/agent), status passed, and signs the PAE with a freshly generated
ECDSA P-256 key (IEEE-P1363 signature). `own`: the envelope names the new key's own keyid (a self-signed
receipt); `trusted`: it names the template's (trusted) keyid (an impostor). Prints the new key's keyid.
"""
import base64, hashlib, json, subprocess, sys, uuid, datetime
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives import hashes, serialization
template, out, repo, item, mode = sys.argv[1:6]
claimant = sys.argv[6] if len(sys.argv) > 6 else "gate/agent"
env = json.load(open(template))
payload = json.loads(base64.b64decode(env["payload"]))
git = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, check=True).stdout.strip()
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
payload.update({"receiptId": str(uuid.uuid4()), "workItemId": item, "claimant": claimant, "fencingGeneration": 1,
                "commit": git("rev-parse", "HEAD"), "treeId": git("rev-parse", "HEAD^{tree}"), "status": "passed", "exitCode": 0,
                "startedAt": now, "observedAt": now})
key = ec.generate_private_key(ec.SECP256R1())
spki = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
own = "sha256:" + hashlib.sha256(spki).hexdigest()
keyid = own if mode == "own" else env["signatures"][0]["keyid"]
payload["verifier"] = dict(payload.get("verifier") or {}, keyId=keyid)
body = json.dumps(payload, separators=(",", ":")).encode()
ptype = env["payloadType"].encode()
pae = b"DSSEv1 %d %s %d %s" % (len(ptype), ptype, len(body), body)
r, s = decode_dss_signature(key.sign(pae, ec.ECDSA(hashes.SHA256())))
sig = base64.b64encode(r.to_bytes(32, "big") + s.to_bytes(32, "big")).decode()
open(out, "w").write(json.dumps({"payloadType": env["payloadType"], "payload": base64.b64encode(body).decode(), "signatures": [{"keyid": keyid, "sig": sig}]}, separators=(",", ":")))
print(json.dumps({"keyId": own, "publicKey": base64.b64encode(spki).decode()}))
