
## Workflow

The contract for this work item is `{{CONTRACT}}` (Ordo `ecir/1`); the completion
authority is `{{AUTHORITY}}`. Both are host files outside the repository; do not edit them.

1. Claim the work item (keep the token; the lease covers the time budget):
   `praxis work claim --id {{ITEM}} --token {{TOKEN}} --lease-seconds 3600{{STORE}}`
   Note the `generation` in the output (1 for a fresh claim).
2. Implement the requirement and its tests.
3. Commit: `git add -A && git commit -m "{{ITEM}}: ..."` (validate-run refuses a dirty worktree).
4. Run the tests through Praxis so the result is recorded as evidence:
   `praxis work validate-run --id {{ITEM}} --token {{TOKEN}} --generation 1 --validation unit-tests --evidence-id EV-TESTS{{STORE}} -- dotnet test Ledger.slnx`
   Note `resultPath` in the output.
5. Complete with independent verification:
   `praxis work complete-verified --id {{ITEM}} --token {{TOKEN}} --generation 1 --commit $(git rev-parse HEAD) --verification-revision $(git rev-parse HEAD) --authority {{AUTHORITY}} --ordo-contract {{CONTRACT}} {{REQ_ARGS}} --validation unit-tests=passed:EV-TESTS --evidence EV-TESTS=RESULT_PATH{{STORE}}`
   If it is refused, read the codes, fix the cause, commit, re-run step 4 and retry
   (within the attempt limit).
