
## Workflow

The contract, the completion authority and a host verifier are configured through the
environment (`PRAXIS_ORDO_CONTRACT`, `PRAXIS_COMPLETION_AUTHORITY`,
`PRAXIS_VERIFIER_SOCKET`). They are host files and services outside the repository; do
not edit them.

1. Claim the work item (keep the token; the lease covers the time budget):
   `praxis work claim --id {{ITEM}} --token {{TOKEN}} --lease-seconds 3600{{STORE}}`
2. Implement the requirement and its tests.
3. Commit: `git add -A && git commit -m "{{ITEM}}: ..."` (verification refuses a dirty
   worktree, untracked files included).
4. Verify: `praxis work verify --id {{ITEM}} --token {{TOKEN}}{{STORE}}`. The host verifier runs the
   tests at `HEAD` and returns signed receipts.
5. Complete: `praxis work complete-verified --id {{ITEM}} --token {{TOKEN}}{{STORE}}`. It derives
   everything else from the claim, the receipts and the host files, and records a
   metadata-only commit.
   If it is refused, read the codes, fix the cause, commit, re-run step 4 and retry
   (within the attempt limit).
