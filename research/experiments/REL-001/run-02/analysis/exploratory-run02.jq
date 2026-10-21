# REL-001 run-02 exploratory aggregates. Written after the data were seen, so NOT confirmatory.
# Usage (from REL-001/):
#   jq -s --slurpfile conc run-02/observations/concurrency.json -f run-02/analysis/exploratory-run02.jq \
#      run-02/observations/*/*.json > run-02/analysis/exploratory-results.json
# Confirmatory trials only (pilot observations are dropped). Means are per run; sums are totals.
def mean(f): (map(f) | map(select(. != null))) as $xs | if ($xs | length) == 0 then null else (($xs | add) / ($xs | length) * 1000 | round / 1000) end;
def total(f): map(f) | map(select(. != null)) | add;
def mode($c): $c[0][.run02.label // ""] // null;

map(select((.run02.pilot // false) | not))
| map(. + {conc: ($conc[0][.run_id // .runId // ""] // null)})
| group_by(.run02.armLetter)
| map({
    arm: .[0].run02.armLetter,
    runs: length,
    u6Runs: map(select(.run02.workItem == "LEDGER-U6")) | length,
    firstPassCorrect: (map(.run02.firstPassCorrect) | map(select(. != null)) | {true: map(select(.)) | length, of: length}),
    reworkTotal: total(.run02.rework.total),
    testRunsPerRun: mean(.run02.tests.total),
    agentTestRunsPerRun: mean((.run02.tests.bySource.agent.full // 0) + (.run02.tests.bySource.agent.focused // 0)),
    verifierTestRunsPerRun: mean(.run02.verification.verifierTestRuns // 0),
    fullSuiteRunsPerRun: mean(.run02.tests.full),
    testComputeMsPerRun: mean(.run02.tests.computeMs),
    toolCallsPerRun: mean(.run02.toolCalls),
    verificationCommandMsPerRun: mean(if .run02.verification then (.run02.verification.validateRunMs + .run02.verification.verifyMs + .run02.verification.completeVerifiedMs) else null end),
    completeVerifiedAttempts: total(.run02.verification.completeVerifiedCalls),
    completionCommitDiffersFromVerified: total(if .run02.reliability.completionCommitDiffersFromVerified == true then 1 else 0 end),
    identity: (map(.run02.workspaces // {} | to_entries[] | .value)
               | {headPastVerifiedWithSourceChanges: map(select(.completionIdentity.independent != null and (.completionIdentity.independent.onlyRos | not))) | length,
                  completionIdentityChecked: map(select(.completionIdentity.independent != null)) | length,
                  completionIdentityCleanAndOnlyRos: map(select(.completionIdentity.independent.onlyRos == true and .completionIdentity.independent.clean == true)) | length,
                  uncommittedTrackedChangesAtEnd: map(select((.uncommittedTrackedChanges // 0) > 0)) | length})
  })
| {label: "exploratory (not preregistered; computed after the data were seen)", arms: .}
