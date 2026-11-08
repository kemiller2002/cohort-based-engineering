#!/usr/bin/env bash
# SPR-E2-03 trusted-acceptance simulation. usage: spr-e2-03.sh > raw/spr-e2-03.jsonl
# Everything happens under /home/user/sprint-scratch/E2/tac (verifier = root, candidate = uid 65534 via setpriv).
# Reads (never writes) E's and V2's fabrication scripts and a scratch clone of Indy-init.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); SRC="$HERE/trusted_acceptance"
T=/home/user/sprint-scratch/E2/tac; INDY=/home/user/sprint-scratch/E2/indy-init
E_FAB=/home/user/sprint-wt/E-security/research/2026-11-08-compute-sprint/tracks/E-security/scripts/indy_fabricated_acceptance.py
V2_FAB=/home/user/sprint-wt/V2-verification/research/2026-11-08-compute-sprint/tracks/V2-verification/scripts/fabricate_acceptance.py
case "$T" in /home/user/sprint-scratch/E2/*) ;; *) echo "GUARD" >&2; exit 97;; esac
[ "$(id -u)" = 0 ] || { echo "verifier side must run as root" >&2; exit 97; }
AS_CAND=(setpriv --reuid=65534 --regid=65534 --clear-groups -- env HOME=/nonexistent PATH=/usr/bin:/bin)
G=(-c safe.directory=* -c user.email=cand@example.invalid -c user.name=candidate -c commit.gpgsign=false)

rm -rf "$T"; mkdir -p "$T"/{verifier,tools,runs}; chmod 755 "$T" "$T"/*
cp "$SRC"/tac_core.py "$SRC"/tac_keys.py "$SRC"/candidate_forge.py "$T/tools/"; chmod 644 "$T"/tools/*
# --- verifier repository (root): job, verdict, plan, pinned public key; private key in keys/ (0700, git-ignored)
V="$T/verifier"; cp "$SRC"/tac_core.py "$SRC"/tac_keys.py "$SRC"/verifier_job.py "$SRC"/trusted_verdict.py "$SRC"/plan.json "$V/"
mkdir -p "$V/keys" "$V/trust"; chmod 700 "$V/keys"; printf 'keys/\nwork/\n' > "$V/.gitignore"
python3 -I -c 'import sys; sys.path.insert(0, sys.argv[1]); import tac_keys, pathlib as p; tac_keys.generate(p.Path(sys.argv[2]), p.Path(sys.argv[3]))' "$V" "$V/keys/signing.pem" "$V/trust/verifier.pub"
git init -q -b main "$V"; git -C "$V" "${G[@]}" add -A; git -C "$V" "${G[@]}" commit -qm "verifier: job, verdict, plan, pinned key"
# --- candidate repository (uid 65534): commit A correct, B buggy, C cheating
C="$T/candidate"; mkdir -p "$C"; chown 65534:65534 "$C"
cand_commit() { cp "$SRC/$1" "$T/tools/$1"; chmod 644 "$T/tools/$1"
  "${AS_CAND[@]}" bash -c 'cp "$1" "$2/calc.py" && git -C "$2" "${@:4}" add -A && git -C "$2" "${@:4}" commit -qm "$3" && git -C "$2" rev-parse HEAD' _ "$T/tools/$1" "$C" "$2" "${G[@]}"; }
"${AS_CAND[@]}" git init -q -b main "$C"
A=$(cand_commit candidate_calc_ok.py "calc: correct"); B=$(cand_commit candidate_calc_buggy.py "calc: mul bug"); CH=$(cand_commit candidate_calc_cheat.py "calc: cheat")

job() { python3 -I "$V/verifier_job.py" "$V" "$C" "$1" "$2" "$T/runs/$2" 2>&1; }
verdict() { python3 -I "$V/trusted_verdict.py" --verifier-dir "$V" "$@" 2>&1; }
emit() { # CASE EXPECTED EXIT OUTPUT [NOTE]
  jq -cn --arg c "$1" --arg x "$2" --argjson rc "$3" --arg o "$4" --arg n "${5:-}" '($o | try fromjson catch {raw:$o[-600:]}) as $d |
    {case:$c, expected:$x, exit:$rc, verdict:($d.verdict // null), reasons:($d.reasons // null), notes:($d.notes // null),
     statuses:($d.statuses // null), raw:($d.raw // null), note:$n}'; }

OUT=$(job "$A" P1); emit P1-job "job runs on correct commit" $? "$OUT"
OUT=$(verdict --manifest "$T/runs/P1/manifest.json" --evidence-root "$T/runs/P1" --pinned-source-sha "$A"); emit P1 "ACCEPTED" $? "$OUT"
OUT=$(job "$B" N1); emit N1-job "job runs on buggy commit" $? "$OUT"
OUT=$(verdict --manifest "$T/runs/N1/manifest.json" --evidence-root "$T/runs/N1" --pinned-source-sha "$B"); emit N1 "FAILED" $? "$OUT"
OUT=$(job "$CH" N2); emit N2-job "job runs on cheating commit" $? "$OUT" "candidate stdout is judged, not trusted"
OUT=$(verdict --manifest "$T/runs/N2/manifest.json" --evidence-root "$T/runs/N2" --pinned-source-sha "$CH"); emit N2 "FAILED" $? "$OUT"

# T1/T2: the original fabricated bundles, produced by E's and V2's own scripts (old verifier result recorded too)
W1="$T/fab-E"; OUT=$(python3 -I "$E_FAB" "$INDY" "$W1" 2>&1); emit T1-old-verifier "baseline reproduction: Indy verifier ACCEPTED" 0 "$OUT"
S1=$(git -C "$W1/candidate" rev-parse HEAD); D1=$(sha256sum "$W1/bundle/evidence-manifest.json" | cut -d' ' -f1)
OUT=$(verdict --manifest "$W1/bundle/evidence-manifest.json" --evidence-root "$W1/bundle" --pinned-source-sha "$S1" --evidence-manifest-sha256 "$D1"); emit T1 "REFUSED" $? "$OUT"
W2="$T/fab-V2"; OUT=$(python3 -I "$V2_FAB" "$INDY" "$INDY/tools/compute-acceptance-verdict.py" "$W2" 2>&1)
emit T2-old-verifier "baseline reproduction: Indy verifier ACCEPTED" 0 "$(jq -c '{verifier_exit, verdict: .result.verdict, artifacts}' <<<"$OUT" 2>/dev/null || echo "$OUT")"
S2=$(git -C "$W2/candidate" rev-parse HEAD); D2=$(sha256sum "$W2/bundle/evidence-manifest.json" | cut -d' ' -f1)
OUT=$(verdict --manifest "$W2/bundle/evidence-manifest.json" --evidence-root "$W2/bundle" --pinned-source-sha "$S2" --evidence-manifest-sha256 "$D2"); emit T2 "REFUSED" $? "$OUT"

# T3: candidate forges a trusted-format bundle signed with its own key
F="$T/candidate-out"; mkdir -p "$F"; chown 65534:65534 "$F"
OUT=$("${AS_CAND[@]}" python3 -I "$T/tools/candidate_forge.py" "$V/plan.json" "$A" "$F/forged" 2>&1); emit T3-forge "candidate builds forged bundle as uid 65534" $? "$OUT"
OUT=$(verdict --manifest "$F/forged/manifest.json" --evidence-root "$F/forged" --pinned-source-sha "$A"); emit T3 "REFUSED" $? "$OUT"
# T4: candidate cannot read the key or write the verifier's output
OUT=$("${AS_CAND[@]}" cat "$V/keys/signing.pem" 2>&1); emit T4-read-key "EACCES" $? "$OUT"
OUT=$("${AS_CAND[@]}" sh -c 'echo x > "$1/entries/R-MUL.json"' _ "$T/runs/N1" 2>&1); emit T4-write-evidence "EACCES" $? "$OUT"
# T5: replay A's genuine bundle for pinned B
OUT=$(verdict --manifest "$T/runs/P1/manifest.json" --evidence-root "$T/runs/P1" --pinned-source-sha "$B"); emit T5 "REFUSED" $? "$OUT"
# T6: edit a genuine signed FAIL to PASS (a) without and (b) with updating the manifest digest
cp -r "$T/runs/N1" "$T/runs/T6a"; python3 -I - "$T/runs/T6a/entries/R-MUL.json" <<'PY'
import sys, json; p=sys.argv[1]; d=json.load(open(p)); d["body"]["status"]="PASS"; open(p,"w").write(json.dumps(d))
PY
OUT=$(verdict --manifest "$T/runs/T6a/manifest.json" --evidence-root "$T/runs/T6a" --pinned-source-sha "$B"); emit T6a "REFUSED" $? "$OUT"
cp -r "$T/runs/T6a" "$T/runs/T6b"; python3 -I - "$T/runs/T6b" <<'PY'
import sys, json, hashlib, pathlib; r=pathlib.Path(sys.argv[1]); m=json.loads((r/"manifest.json").read_text())
for e in m["body"]["entries"]: e["sha256"]=hashlib.sha256((r/e["path"]).read_bytes()).hexdigest()
(r/"manifest.json").write_text(json.dumps(m))
PY
OUT=$(verdict --manifest "$T/runs/T6b/manifest.json" --evidence-root "$T/runs/T6b" --pinned-source-sha "$B"); emit T6b "REFUSED" $? "$OUT"
# T7: caller-supplied wrong digest is ignored
OUT=$(verdict --manifest "$T/runs/P1/manifest.json" --evidence-root "$T/runs/P1" --pinned-source-sha "$A" --evidence-manifest-sha256 0000000000000000000000000000000000000000000000000000000000000000)
emit T7 "ACCEPTED (unchanged) with ignored-digest note" $? "$OUT"
# T8: drop an entry
cp -r "$T/runs/P1" "$T/runs/T8"; rm "$T/runs/T8/entries/R-REV.json"
OUT=$(verdict --manifest "$T/runs/T8/manifest.json" --evidence-root "$T/runs/T8" --pinned-source-sha "$A"); emit T8 "REFUSED" $? "$OUT"
