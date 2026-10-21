#!/usr/bin/env bash
# Worker A adversarial probes on released Praxis 3.17.0 + Dokimos 0.7.0 (trust-root and policy bypass).
# usage: probes.sh PRAXIS DOKIMOS ORDO CONTRACT WORKDIR GENUINE-RECEIPT
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GENUINE="$6"
source "$HERE/gate-lib.sh" "$1" "$2" "$3" "$4" "$5"
policy_repo() { # policy_repo ID JSON: fresh repo with ros.json = JSON
  local r; r=$(new_repo "$1"); jq -n "$2" > "$r/ros.json"; git -C "$r" add -A; git -C "$r" commit -qm "policy"; echo "$r"; }
forge_nonattested() { local r="$1" id="$2" f; f=$(forge_store_result "$r" "$id"); forge_store_event "$r" "$id" "$f"; echo "$f"; }
# PROBE-1 control: ros.json requireAttestedEvidence + keyless authority -> expected ATTESTATION_REQUIRED
probe_keyless_under_attested() {
  local r f; r=$(policy_repo PROBE-1 '{workProtocol:{requireAttestedEvidence:true}}'); claim "$r" PROBE-1; f=$(forge_nonattested "$r" PROBE-1)
  authority "$H/keyless.json"; complete_explicit "$r" PROBE-1 "$f" "$H/keyless.json"
  emit PROBE-1 attested-policy "forged store result+event, keyless authority" "agent swaps to a keyless authority" "rejected (ATTESTATION_REQUIRED)" "$RC" "$OUT"; }
# PROBE-2: requireVerifiedCompletion alone (REL-GATE-003 behaviour): keyless authority, forged store evidence
probe_verified_only() {
  local r f; r=$(policy_repo PROBE-2 '{workProtocol:{requireVerifiedCompletion:true}}'); claim "$r" PROBE-2; f=$(forge_nonattested "$r" PROBE-2)
  authority "$H/keyless.json"; complete_explicit "$r" PROBE-2 "$f" "$H/keyless.json"
  emit PROBE-2 verified-only "forged store result+event, keyless authority" "REL-GATE-003: requireVerifiedCompletion without requireAttestedEvidence" "rejected if REL-GATE-003 resolved (ATTESTATION_REQUIRED)" "$RC" "$OUT" "$(identity "$r" PROBE-2)"; }
# PROBE-3: agent commits a ros.json change dropping requireAttestedEvidence, then uses a keyless authority
probe_policy_edit() {
  local r f; r=$(policy_repo PROBE-3 '{workProtocol:{requireAttestedEvidence:true}}'); claim "$r" PROBE-3
  jq -n '{workProtocol:{}}' > "$r/ros.json"; git -C "$r" commit -qam "agent drops attestation"
  f=$(forge_nonattested "$r" PROBE-3); authority "$H/keyless.json"; complete_explicit "$r" PROBE-3 "$f" "$H/keyless.json"
  emit PROBE-3 attested-policy-edited "ros.json edited in a commit + forged store evidence + keyless authority" "agent weakens repository policy in its own branch" "rejected" "$RC" "$OUT" "$(identity "$r" PROBE-3)"; }
# PROBE-4: agent-generated key pinned in an authority it controls (edited host authority or own PRAXIS_COMPLETION_AUTHORITY)
probe_own_key_authority() {
  local r sha d f k; r=$(policy_repo PROBE-4 '{workProtocol:{requireAttestedEvidence:true}}'); claim "$r" PROBE-4
  sha=$(git -C "$r" rev-parse HEAD); d="$(store "$r")/receipts/PROBE-4"; mkdir -p "$d"; f="$d/1-${sha:0:12}-$(cat /proc/sys/kernel/random/uuid).json"
  k=$(python3 -I "$HERE/forge-receipt-pub.py" "$GENUINE" "$f" "$r" PROBE-4 own)
  local pd; pd=$(base64 -d <<<"$(jq -r .payload "$GENUINE")" | jq -r '.validationPolicyDigest // .policyDigest // .verifier.policyDigest // empty')
  authority "$H/own-key.json" "$(jq -c --arg pd "$pd" '. + {policyDigest:$pd}' <<<"$k")"
  complete_derived "$r" PROBE-4 "$H/own-key.json"; local drc=$RC dout="$OUT"
  emit PROBE-4-derived attested-policy "self-signed receipt + authority pinning the agent's own key" "agent controls the authority file / PRAXIS_COMPLETION_AUTHORITY" "rejected only if the authority is outside agent control" "$drc" "$dout" "$(identity "$r" PROBE-4)"; }
probe_keyless_under_attested; probe_verified_only; probe_policy_edit; probe_own_key_authority
