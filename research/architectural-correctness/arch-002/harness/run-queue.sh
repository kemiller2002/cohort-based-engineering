#!/usr/bin/env bash
# ARCH-002 queue runner (adapted from ARCH-001 harness/run-queue.sh; see ../PROVENANCE.md).
#   usage: run-queue.sh ORDER.json [--concurrency N] [--fixture-concurrency F=N[,G=M]] [--dry-run] [--limit M]
# Executes the trials of an order file (randomize.py) in `seq` order with at most N trials at once (default 3;
# ARCH002_CONCURRENCY), and at most N_F at once of fixture F. N_F comes from --fixture-concurrency, else
# ARCH002_FIXTURE_CONCURRENCY (same F=N,G=M form), else fixtures/<F>/fixture.json .maxConcurrency, else N. Summa
# builds are heavier than Lending's, so its fixture.json can cap it (e.g. 1 or 2) while Lending runs at N.
# Order is strict: the next trial waits until both limits allow it (no skipping ahead), so the randomized order is
# the execution order. Each trial is ONE process (`trial.sh run RUNID`) running its two phases one after the other;
# trial.sh also holds a per-run lock. Resumable: a run id with RUN/state/done, an X1 record or an interrupted phase
# is skipped (trial.sh decides and logs it). Logs: $ARCH002_RUNS/.queue/<order name>.log.
# Wall-time metrics are reported with the concurrency recorded here (REL-001 run-02 A3); cost and tokens are unaffected.
source "$(dirname "$0")/lib.sh"
ORDER="${1:?usage: run-queue.sh ORDER.json [--concurrency N] [--fixture-concurrency F=N,...] [--dry-run] [--limit M]}"; shift
CONC="${ARCH002_CONCURRENCY:-3}"; FCONC="${ARCH002_FIXTURE_CONCURRENCY:-}"; DRY=false; LIMIT=0
while [ $# -gt 0 ]; do case "$1" in --concurrency) CONC="$2"; shift 2;; --fixture-concurrency) FCONC="$2"; shift 2;;
  --dry-run) DRY=true; shift;; --limit) LIMIT="$2"; shift 2;; *) echo "unknown $1" >&2; exit 2;; esac; done
mkdir -p "$RUNS/.queue"; LOG="$RUNS/.queue/$(basename "$ORDER" .json).log"
mapfile -t IDS < <(jq -r '.trials | sort_by(.seq) | .[].runId' "$ORDER")
[ "$LIMIT" -gt 0 ] && IDS=("${IDS[@]:0:$LIMIT}")
declare -A LIMITS=()
for kv in ${FCONC//,/ }; do LIMITS["${kv%%=*}"]="${kv#*=}"; done
fixture_limit() {  # FIXTURE -> its concurrency limit
  local f="$1" v
  if [ -n "${LIMITS[$f]:-}" ]; then echo "${LIMITS[$f]}"; return; fi
  v=$(jq -r '.maxConcurrency // empty' "$FIXTURES/$f/fixture.json" 2>/dev/null || true); echo "${v:-$CONC}"
}
pending() { local id; for id in "${IDS[@]}"; do [ -f "$RUNS/$id/state/done" ] || echo "$id"; done; }
if $DRY; then
  echo "order $(basename "$ORDER"): ${#IDS[@]} trials, $(pending | wc -l) pending, concurrency $CONC"
  for f in $(printf '%s\n' "${IDS[@]}" | while read -r i; do fixture_of "$i"; done | sort -u); do echo "  fixture $f: limit $(fixture_limit "$f")"; done
  pending | head -20; exit 0
fi
echo "$(utc) queue start $(basename "$ORDER") concurrency=$CONC fixtureConcurrency=${FCONC:-fixture.json/default}" >> "$LOG"
declare -A PID_FIX=()
reap() { local p; for p in "${!PID_FIX[@]}"; do kill -0 "$p" 2>/dev/null || { wait "$p" 2>/dev/null || true; unset "PID_FIX[$p]"; }; done; }
running_of() { local p n=0; for p in "${!PID_FIX[@]}"; do [ "${PID_FIX[$p]}" = "$1" ] && n=$((n + 1)); done; echo "$n"; }
for id in "${IDS[@]}"; do
  [ -f "$RUNS/$id/state/done" ] && continue
  f=$(fixture_of "$id"); lim=$(fixture_limit "$f")
  while reap; [ "${#PID_FIX[@]}" -ge "$CONC" ] || [ "$(running_of "$f")" -ge "$lim" ]; do sleep 5; done
  ( echo "$(utc) start $id concurrency=$CONC fixture=$f fixtureLimit=$lim" >> "$LOG"
    set +e; ARCH002_QUEUE_CONCURRENCY="$CONC" bash "$H/trial.sh" run "$id" > "$RUNS/.queue/$id.out" 2>&1; rc=$?
    echo "$(utc) end $id exit=$rc" >> "$LOG" ) &
  PID_FIX[$!]="$f"
done
wait
echo "$(utc) queue end $(basename "$ORDER")" >> "$LOG"
echo "done: $(pending | wc -l) of ${#IDS[@]} still without state/done (see $LOG)"
