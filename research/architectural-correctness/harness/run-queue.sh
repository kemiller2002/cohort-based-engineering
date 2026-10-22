#!/usr/bin/env bash
# ARCH-001 queue runner (new).
#   usage: run-queue.sh ORDER.json [--concurrency N] [--dry-run] [--limit M]
# Executes the trials of an order file (randomize.py) in `seq` order with at most N trials at once (default 3;
# ARCH001_CONCURRENCY). Each trial is ONE process (`trial.sh run RUNID`) that runs its two phases one after the other,
# so no two phases of the same trial ever run at once; trial.sh also holds a per-run lock. Resumable: a run id
# with RUN/state/done, an X1 record or an interrupted phase is skipped (trial.sh decides and logs it), so the queue
# can be re-run after a stop. Logs: $ARCH001_RUNS/.queue/<order name>.log (one line per trial start/end).
# Note: REL-001 run-02 A3 found that concurrency inflates wall time; wall-time metrics are reported with the
# concurrency recorded here, and cost/token metrics are unaffected.
source "$(dirname "$0")/lib.sh"
ORDER="${1:?usage: run-queue.sh ORDER.json [--concurrency N] [--dry-run] [--limit M]}"; shift
CONC="${ARCH001_CONCURRENCY:-3}"; DRY=false; LIMIT=0
while [ $# -gt 0 ]; do case "$1" in --concurrency) CONC="$2"; shift 2;; --dry-run) DRY=true; shift;; --limit) LIMIT="$2"; shift 2;;
  *) echo "unknown $1" >&2; exit 2;; esac; done
mkdir -p "$RUNS/.queue"; LOG="$RUNS/.queue/$(basename "$ORDER" .json).log"
mapfile -t IDS < <(jq -r '.trials | sort_by(.seq) | .[].runId' "$ORDER")
[ "$LIMIT" -gt 0 ] && IDS=("${IDS[@]:0:$LIMIT}")
pending() { local id; for id in "${IDS[@]}"; do [ -f "$RUNS/$id/state/done" ] || echo "$id"; done; }
if $DRY; then echo "order $(basename "$ORDER"): ${#IDS[@]} trials, $(pending | wc -l) pending, concurrency $CONC"; pending | head -20; exit 0; fi
echo "$(utc) queue start $(basename "$ORDER") concurrency=$CONC trials=${#IDS[@]}" >> "$LOG"
running=0
for id in "${IDS[@]}"; do
  [ -f "$RUNS/$id/state/done" ] && continue
  while [ "$running" -ge "$CONC" ]; do wait -n || true; running=$((running - 1)); done
  ( echo "$(utc) start $id concurrency=$CONC" >> "$LOG"
    set +e; ARCH001_QUEUE_CONCURRENCY="$CONC" bash "$H/trial.sh" run "$id" > "$RUNS/.queue/$id.out" 2>&1; rc=$?
    echo "$(utc) end $id exit=$rc" >> "$LOG" ) &
  running=$((running + 1))
done
wait
echo "$(utc) queue end $(basename "$ORDER")" >> "$LOG"
echo "done: $(pending | wc -l) of ${#IDS[@]} still without state/done (see $LOG)"
