#!/usr/bin/env bash
# VAC-002-P2 freeze: encrypt the sealed store with VAC-002's seal.sh (reused) and record P2's contents.
#   freeze.sh SEALED_DIR KEY_FILE      writes sealed/ (ciphertext, manifest, SEAL.json)
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"; EXP="$(cd "$H/.." && pwd)"
"$H/../../harness/seal.sh" "$1" "$2" "$EXP/sealed" > /dev/null
mv "$EXP/sealed/vac002-sealed.tar.gz.enc" "$EXP/sealed/p2-sealed.tar.gz.enc"
jq --arg enc "$(sha256sum "$EXP/sealed/p2-sealed.tar.gz.enc" | cut -d' ' -f1)" '.schema = "cbe.vac-002-p2.seal/1" | .ciphertextSha256 = $enc
  | .contents = "Sxx/oracle (hidden FUNC and AUTH facts), Sxx/ref, Sxx/trap-*, Sxx/valid-*, gen/ (variant generators), support/ (oracle projects), meta.json (reference decisions), confirmatory-variants.md, validation/ (pre-freeze self-check outputs and change log), PREFREEZE-LOG.md"
  | .verify = "openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass file:KEY -in p2-sealed.tar.gz.enc | sha256sum  # equals plaintextTarGzSha256"' \
  "$EXP/sealed/SEAL.json" > "$EXP/sealed/SEAL.json.tmp" && mv "$EXP/sealed/SEAL.json.tmp" "$EXP/sealed/SEAL.json"
cat "$EXP/sealed/SEAL.json"
