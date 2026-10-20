#!/usr/bin/env bash
# REL-001 Experiment D scoring. usage: harness/d/score.sh RUNID [--report REPORT.json | --transcripts DIR] [--out FILE]
# Runs the HIDDEN oracle (fixtures/d/oracle/Tn) against the run's final commit in a separate
# scoring directory, reads the run's events and harness logs, and prints one
# cbe.rel-001.observation/1 document (with the additive `scoring` block) to stdout or --out.
# Without a reliability report, token/cost metrics are unavailable and instrumentation is incomplete.
source "$(dirname "$0")/../lib.sh"
RUN_ID="${1:?usage: score.sh RUNID [--report F | --transcripts DIR] [--out F]}"; shift
REPORT=""; TRANSCRIPTS=""; OUT=""
while [ $# -gt 0 ]; do case "$1" in --report) REPORT="$2"; shift 2;; --transcripts) TRANSCRIPTS="$2"; shift 2;; --out) OUT="$2"; shift 2;; *) echo "unknown $1" >&2; exit 2;; esac; done
RUN_DIR="$RUNS/$RUN_ID"; REPO="$RUN_DIR/repo"; FIX="$REL/fixtures/d"
[ -f "$RUN_DIR/run.json" ] || { echo "no run.json in $RUN_DIR" >&2; exit 2; }
RJ="$RUN_DIR/run.json"; ARM=$(jq -r .arm "$RJ"); TASK=$(jq -r .task "$RJ"); ITEM=$(jq -r .workItem "$RJ")
SC="$RUN_DIR/score"; rm -rf "$SC"; mkdir -p "$SC"
FINAL=$(git -C "$REPO" rev-parse HEAD)
DIRTY=$(git -C "$REPO" status --porcelain --untracked-files=no -- . ':!.ros' ':!.praxis' | wc -l)

# --- X4 oracle contamination: oracle module names or test bodies anywhere in the run repository's history or worktree
contam=0
for m in OracleT1 OracleT2 OracleT3; do
  if git -C "$REPO" log --all -p 2>/dev/null | grep -q "module $m" || grep -rqs "module $m" "$REPO" --exclude-dir=.git; then contam=1; fi
done
# Amendment A3: the oracle shares the disk with the run, so the agent's own transcripts are
# also checked for any reference to the oracle directory or modules.
if [ -n "$TRANSCRIPTS" ] && grep -rqsE "fixtures/d/oracle|module OracleT[0-9]" "$TRANSCRIPTS"; then contam=1; fi

# --- oracle at the final commit, outside the run repository
mkdir -p "$SC/src"; git -C "$REPO" archive "$FINAL" | tar -x -C "$SC/src"
mkdir -p "$SC/oracle"
sed "s#LEDGER_PROJECT_PATH#$SC/src/src/Ledger/Ledger.fsproj#" "$FIX/oracle/Oracle.fsproj" > "$SC/oracle/Oracle.fsproj"
cp "$FIX/oracle/$TASK/OracleTests.fs" "$SC/oracle/OracleTests.fs"
set +e; (cd "$SC/oracle" && dotnet test --logger "trx;LogFileName=oracle.trx" --results-directory "$SC/results" > "$SC/oracle-output.txt" 2>&1); ORACLE_RC=$?; set -e
TRX="$SC/results/oracle.trx"
ORACLE=$(python3 -I - "$TRX" "$(jq -c .requirementIds "$RJ")" <<'PY'
import json, re, sys, xml.etree.ElementTree as ET, os
trx, reqs = sys.argv[1], json.loads(sys.argv[2])
tests = []
if os.path.exists(trx):
    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
    for r in ET.parse(trx).getroot().iterfind(".//t:UnitTestResult", ns):
        tests.append({"name": r.get("testName"), "outcome": r.get("outcome")})
per = {}
for q in reqs:
    mine = [t for t in tests if re.search(r"\b%s\b" % re.escape(q), t["name"] or "")]
    per[q] = {"tests": len(mine), "passed": sum(t["outcome"] == "Passed" for t in mine),
              "pass": bool(mine) and all(t["outcome"] == "Passed" for t in mine)}
print(json.dumps({"built": os.path.exists(trx), "tests": sorted(tests, key=lambda t: t["name"]), "requirements": per}))
PY
)

# --- events and harness logs
EV="$REPO/.ros/events/events.jsonl"; PL="$RUN_DIR/logs/praxis.jsonl"; DL="$RUN_DIR/logs/dotnet.jsonl"
cnt() { [ -f "$EV" ] && { grep "\"type\":\"$1\"" "$EV" | grep -c "$ITEM" || true; } || echo 0; }
attempts=0; rejections=0
if [ -f "$PL" ]; then
  attempts=$(jq -s '[.[] | select(.argv[0]=="work" and (.argv[1]=="complete" or .argv[1]=="complete-verified"))] | length' "$PL")
  rejections=$(jq -s '[.[] | select(.argv[0]=="work" and (.argv[1]=="complete" or .argv[1]=="complete-verified") and .exit != 0)] | length' "$PL")
fi
testRuns=0; [ -f "$DL" ] && testRuns=$(jq -s '[.[] | select(.argv[0]=="test")] | length' "$DL")
validateRuns=$(cnt work.validation.observed)
claimRejected=$(cnt work.claim.rejected)
staleRej=0; [ -f "$EV" ] && staleRej=$(grep "$ITEM" "$EV" | grep -E '"type":"work\.(claim|completion)\.rejected"' | grep -cE 'STALE|stale-|PRX\.CLAIM\.EXPIRED|"expired"' || true)
reverts=$(git -C "$REPO" log --format=%s "$FINAL" | grep -c '^Revert ' || true)
resets=$(git -C "$REPO" reflog 2>/dev/null | grep -c ': reset: ' || true)
if [ "$ARM" = treatment ]; then
  recorded=$( [ "$(cnt work.completion.verified)" -gt 0 ] && echo true || echo false )
  firstAccepted=$( [ -f "$PL" ] && jq -s '[.[] | select(.argv[0]=="work" and .argv[1]=="complete-verified")][0].exit == 0' "$PL" || echo false )
else
  recorded=$( [ "$(cnt work.completed)" -gt 0 ] && echo true || echo false )
  firstAccepted=$( [ -f "$PL" ] && jq -s '[.[] | select(.argv[0]=="work" and .argv[1]=="complete")][0].exit == 0' "$PL" || echo false )
fi
# elapsed: logs/agent.json {startedAt, endedAt} written by the session driver; else first..last praxis invocation.
elapsed=null
if [ -f "$RUN_DIR/logs/agent.json" ]; then elapsed=$(jq '((.endedAt|sub("\\.[0-9]+Z$";"Z")|fromdate) - (.startedAt|sub("\\.[0-9]+Z$";"Z")|fromdate)) * 1000' "$RUN_DIR/logs/agent.json")
elif [ -f "$PL" ]; then elapsed=$(jq -s 'if length<2 then null else ((.[-1].at|sub("\\.[0-9]+Z$";"Z")|fromdate) - (.[0].at|sub("\\.[0-9]+Z$";"Z")|fromdate)) * 1000 end' "$PL"); fi

# --- optional reliability report (tokens); the treatment Praxis is the read-only measurement tool for both arms
if [ -z "$REPORT" ] && [ -n "$TRANSCRIPTS" ]; then
  REPORT="$SC/reliability-report.json"
  (cd "$REPO" && "$TREATMENT_PRAXIS" telemetry reliability-report --transcripts "$TRANSCRIPTS" --out "$REPORT" >/dev/null)
fi
TOOL_CALLS=None
if [ -n "$TRANSCRIPTS" ]; then TOOL_CALLS=$(cat "$TRANSCRIPTS"/*.jsonl | jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | .id' 2>/dev/null | sort -u | wc -l); fi
ELAPSED_PY=${elapsed/null/None}
plainCompleted=$(cnt work.completed); verifiedEvents=$(cnt work.completion.verified)
freshAcq=0; [ -f "$EV" ] && freshAcq=$(grep '"type":"work.claim.acquired"' "$EV" | grep "$ITEM" | grep -vc '"recovered":true' || true)
if [ -n "$REPORT" ]; then RSHA=$(sha256sum "$REPORT" | cut -d' ' -f1); RDOC=$(jq -c . "$REPORT"); else RSHA=""; RDOC=null; fi

python3 -I - "$RJ" "$ORACLE" "$RDOC" "$RSHA" <<PY > "$SC/observation.json"
import json, sys
run = json.load(open(sys.argv[1])); oracle = json.loads(sys.argv[2]); report = json.loads(sys.argv[3]); rsha = sys.argv[4] or None
arm = run["arm"]; reqs = run["requirementIds"]
recorded = "$recorded" == "true"; contaminated = $contam == 1
attempts, rejections, test_runs, validate_runs = $attempts, $rejections, $testRuns, $validateRuns
rework = max(0, attempts - 1) + $reverts + $resets
oracle_pass = {q: oracle["requirements"].get(q, {}).get("pass", False) for q in reqs}
verified = sum(1 for q in reqs if oracle_pass[q] and recorded)
escaped = sum(1 for q in reqs if recorded and not oracle_pass[q])
def m(v, unit, avail=None, num=None, den=None, basis=None):
    a = avail or ("unavailable" if v is None else "available")
    d = {"availability": a, "value": None if a == "unavailable" else v, "unit": unit}
    if num is not None or den is not None: d["numerator"], d["denominator"] = num, den
    if basis: d["basis"] = basis
    return d
def rep(path):
    node = report
    for k in path.split("."):
        node = (node or {}).get(k) if isinstance(node, dict) else None
    return node if isinstance(node, dict) else None
def tok(name):
    # Amendment A4: the transcript directory holds only this run's agent, so every
    # deduplicated provider observation in it is the run's, attributed by Praxis or not.
    parts = [r for r in (rep("usage.tokens." + name), rep("usage.unattributed.tokens." + name))
             if r and r.get("availability") != "unavailable" and r.get("value") is not None]
    if not parts: return m(None, "tokens")
    return m(sum(r["value"] for r in parts), "tokens", "available",
             sum(r.get("numerator") or 0 for r in parts), sum(r.get("denominator") or 0 for r in parts))
tokens = {k: tok(k) for k in ["input", "output", "cacheRead", "cacheWrite", "total"]}
missing = [k for k, v in [("tokensInput", tokens["input"]), ("tokensOutput", tokens["output"]), ("tokensCacheRead", tokens["cacheRead"]),
           ("tokensCacheWrite", tokens["cacheWrite"]), ("tokensTotal", tokens["total"])] if v["availability"] != "available"]
def cost(name):
    r = rep("usage.cost." + name)
    if not r or r.get("availability") == "unavailable": return m(None, "USD", basis="estimated" if name == "estimated" else "billed")
    return m(r.get("value"), r.get("unit", "USD"), r.get("availability"), basis="estimated" if name == "estimated" else "billed")
ce, cb = cost("estimated"), cost("billed")
missing += [k for k, v in [("costEstimated", ce), ("costBilled", cb)] if v["availability"] != "available"]
tt = tokens["total"]
tpv = m(tt["value"] / verified, "tokens/requirement", None, tt["value"], verified) if tt["availability"] == "available" and verified > 0 else m(None, "tokens/requirement", None, tt["value"], verified)
cpv = m(ce["value"] / verified, "USD/requirement", None, ce["value"], verified, "estimated") if ce["availability"] == "available" and verified > 0 else m(None, "USD/requirement", basis="estimated")
treat = arm == "treatment"
obs = {
  "schema": "cbe.rel-001.observation/1", "experimentId": "REL-001", "runId": run["runId"], "supersedes": None,
  "arm": arm, "scenario": "nominal", "replicate": int("${REL001_REPLICATE:-1}"),
  "status": "excluded" if contaminated else ("completed" if recorded else "failed"),
  "statusReason": "X4 oracle contamination" if contaminated else (None if recorded else "no recorded completion"),
  "exclusion": {"rule": "X4", "decidedBeforeScoring": True} if contaminated else None,
  "task": {"taskId": run["task"], "requirementIds": reqs, "acceptanceCriteriaDigest": run["acceptanceCriteriaDigest"],
           "complexity": {"class": run["complexity"], "basis": "preregistered task class (protocol/run-01.md)"}},
  "environment": {"repositories": [{"name": "rel001-d-fixture", "commit": run["initialCommit"]},
                                   {"name": "cohort-based-engineering", "commit": run["cohortBasedEngineeringCommit"]}],
                  "tools": run["tools"], "enforcement": run["enforcement"]},
  "model": {"provider": run["model"]["provider"] or "unknown", "configuredModel": run["model"]["configuredModel"] or "unknown",
            "servedModels": sorted({a.get("model") for a in (report or {}).get("agents", []) if isinstance(a, dict) and a.get("model")}),
            "configurationDigest": run["model"]["configurationDigest"]},
  "cache": {"state": "cold", "note": None}, "concurrency": {"agents": 1},
  "retryPolicy": {"maxAttempts": 3, "description": "at most 3 completion attempts (preregistered)"},
  "instrumentation": {"status": "complete" if not missing else "incomplete", "missing": missing},
  "report": {"schema": "praxis.telemetry-reliability-report", "schemaVersion": 1, "sha256": rsha, "priceTable": None},
  "metrics": {
    "tokensInput": tokens["input"], "tokensOutput": tokens["output"], "tokensCacheRead": tokens["cacheRead"],
    "tokensCacheWrite": tokens["cacheWrite"], "tokensTotal": tokens["total"], "costEstimated": ce, "costBilled": cb,
    "verifiedRequirements": m(verified, "requirements"), "costPerVerifiedRequirement": cpv, "tokensPerVerifiedRequirement": tpv,
    "firstPassVerificationRate": m((verified / len(reqs)) if "$firstAccepted" == "true" else 0.0, "ratio"),
    "reworkFrequency": m(rework, "events"),
    "completionRejectionFrequency": m(rejections / attempts, "ratio", None, rejections, attempts) if attempts else m(None, "ratio"),
    "duplicateOwnershipAttempts": m($claimRejected, "attempts") if treat else m(None, "attempts"),
    "staleWriteRejections": m($staleRej, "rejections") if treat else m(None, "rejections"),
    "elapsedMs": m($ELAPSED_PY, "ms"), "activeMs": m(None, "ms"), "toolCalls": m($TOOL_CALLS, "calls"),
    "testRuns": m(test_runs, "runs"), "escapedDefects": m(escaped, "defects")},
  # gates: duplicate active claims = fresh (non-recovery) acquisitions beyond the first; invalid accepted
  # decisions = 0 only because setup.sh refuses a contract either Ordo or Praxis does not admit;
  # unverified completions = a plain work.completed with no Dokimos-verified completion.
  "gates": {"duplicateActiveClaims": max(0, $freshAcq - 1) if treat else None, "invalidAcceptedDecisions": 0 if treat else None,
            "unverifiedCompletions": (1 if ($plainCompleted > 0 and $verifiedEvents == 0) else 0) if treat else None},
  "scoring": {"finalCommit": "$FINAL", "uncommittedTrackedChanges": $DIRTY, "oracleExit": $ORACLE_RC, "oracleBuilt": oracle["built"],
              "oracleDigest": run["oracleDigest"], "requirements": oracle["requirements"], "recordedCompletion": recorded,
              "verified": verified == len(reqs), "escapedDefect": escaped > 0, "completionAttempts": attempts, "rejections": rejections,
              "validateRuns": validate_runs, "testRuns": test_runs, "rework": {"total": rework, "extraCompletionAttempts": max(0, attempts - 1),
              "revertCommits": $reverts, "resets": $resets}, "oracleContamination": contaminated}}
print(json.dumps(obs, indent=2))
PY
if [ -n "$OUT" ]; then cp "$SC/observation.json" "$OUT"; fi
cat "$SC/observation.json"
