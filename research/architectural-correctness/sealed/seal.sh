#!/usr/bin/env bash
# ARCH-001 freeze: encrypt the sealed tree and record its digests (coordinator only).
#   usage: seal.sh SEALED_DIR KEY_FILE OUT_DIR
# Writes OUT_DIR/arch001-sealed.tar.gz.enc, OUT_DIR/MANIFEST.sha256 (per file, sorted) and OUT_DIR/SEAL.json.
# The tarball is deterministic (sorted names, fixed owner and mtime), so its sha256 identifies the plaintext.
# The key file stays outside every repository until the results are published.
set -euo pipefail
SEALED=${1:?sealed dir}; KEY=${2:?key file}; OUT=${3:?out dir}
[ -s "$KEY" ] || { umask 077; head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > "$KEY"; }
mkdir -p "$OUT"
TAR=$(mktemp); trap 'rm -f "$TAR"' EXIT
( cd "$SEALED" && find . -type f -not -path '*/bin/*' -not -path '*/obj/*' | LC_ALL=C sort > "$TAR.list" \
  && xargs -a "$TAR.list" -d '\n' sha256sum ) > "$OUT/MANIFEST.sha256"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime='2026-10-21 00:00Z' -C "$SEALED" -T "$TAR.list" -cf - | gzip -n > "$TAR"
rm -f "$TAR.list"
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass "file:$KEY" -in "$TAR" -out "$OUT/arch001-sealed.tar.gz.enc"
jq -n --arg plain "$(sha256sum "$TAR" | cut -d' ' -f1)" --arg enc "$(sha256sum "$OUT/arch001-sealed.tar.gz.enc" | cut -d' ' -f1)" \
      --arg manifest "$(sha256sum "$OUT/MANIFEST.sha256" | cut -d' ' -f1)" --arg files "$(wc -l < "$OUT/MANIFEST.sha256")" \
      --arg openssl "$(openssl version)" --arg at "$(date -u +%FT%TZ)" \
  '{schema:"arch001.seal/1", plaintextTarGzSha256:$plain, ciphertextSha256:$enc, manifestSha256:$manifest, files:($files|tonumber),
    cipher:"aes-256-cbc pbkdf2 iter 200000 (openssl enc)", openssl:$openssl, sealedAt:$at,
    verify:"openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass file:KEY -in arch001-sealed.tar.gz.enc | sha256sum  # equals plaintextTarGzSha256"}' > "$OUT/SEAL.json"
cat "$OUT/SEAL.json"
