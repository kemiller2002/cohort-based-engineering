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
