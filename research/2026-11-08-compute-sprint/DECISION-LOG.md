# Decision log

| ID | Time (EST) | Decision | Rationale |
|---|---|---|---|
| D-001 | 13:35 | Host sprint in cohort-based-engineering on the designated branch | Existing cross-system research program repo; plain-file lifecycle; avoids new repo |
| D-002 | 13:35 | Quota unobservable → cap at 8 concurrent specialists | Prompt §7: unknown quota ⇒ conservative concurrency |
| D-003 | 13:35 | Each track works in its own git worktree on a local branch `sprint/track-<X>`; Director merges into the designated branch | "No two workers modify the same working tree"; only designated branch is pushed |
| D-004 | 13:35 | Install .NET SDK 10.0.402 (pinned by praxis/rehearsal global.json) into /root/.dotnet | Needed for Praxis CLI and F#/WASM measurements; dotnet absent at start |
| D-005 | 13:35 | Track H launches after first track outputs land rather than at t0 | Synthesis needs inputs; saves idle compute |
| D-006 | 13:44 | Run repository access preflight (addendum). The inventory is 66 Echelon-relevant repos; 131 unrelated personal repos are excluded but listed | Addendum completion gate; classify everything relevant without noise |
| D-007 | 13:44 | Attach research-documents, causa-acceptance-r10, Indy-init-audits (read only) | Priority-1 inputs for Tracks B/D/E; were METADATA_ONLY |
| D-008 | 13:44 | Do not attach the 6 priority-3 private repos | Non-blocking; avoids widening access without need |
| D-009 | 13:44 | gh used for search only; permissions come from the search API `permissions` field instead of `gh repo view` / `gh api repos/...` | Environment policy restricts gh to search; the search API returns the same permission object |
| D-010 | 13:50 | Subagent report files are delivered as reply text and committed by the Director; all tracks were told not to work around the harness refusal | Harness refused G-001's REPORT.md write; workarounds would bypass a control |
| D-011 | 13:50 | Plan a second wave of tracks: G finished in 11.6 min, far under its deadline. Follow-ups will be chosen from first-wave findings rather than queued blindly | §4: prefer targeted follow-ups to the next queued task when findings emerge |
| D-012 | 13:56 | Launch wave 2: V1 (independent verification of A/G) and A2 (remediation prototypes for A's top waste items) | Tracks are finishing in under 20 minutes; Track A's `.ros` conflict and verifier-rebuild findings are cheap to test against real data; §8 requires independent verification of consequential findings |
| D-013 | 14:00 | Launch wave 3: H (synthesis) early, V2 (verify B/C/E), B2 (pre-T0 dry-run replay) | Five tracks done; B's top recommendation is directly testable retrospectively; E's High findings need independent reproduction |
| D-014 | 14:00 | Not pursued: live GitHub tests of branch protection or red-check completion | Would require outward-facing actions on live repos, which this sprint does not authorize |
| D-015 | 14:16 | Accept V2-001's self-reported clean-up of stray `.git/praxis` and `scripts/.ros` | Director confirmed: `.git/praxis` absent, working tree clean, `git fsck` clean, no stray `.ros` in any worktree. The cause (cd inside a command substitution) is fixed by a root-guard in the script |
| D-016 | 14:16 | Adopt V2 corrections: B-F-03 restated (first refusal, not dominant blocker); B-F-02 INVALID caveated (substantively INCOMPLETE); C-F-01 "9 more" → 8 | Independent verification outranks the originating track |
