# Decision log

| ID | Time (EST) | Decision | Rationale |
|---|---|---|---|
| D-001 | 13:35 | Host sprint in cohort-based-engineering on the designated branch | Existing cross-system research program repo; plain-file lifecycle; avoids new repo |
| D-002 | 13:35 | Quota unobservable → cap at 8 concurrent specialists | Prompt §7: unknown quota ⇒ conservative concurrency |
| D-003 | 13:35 | Each track works in its own git worktree on a local branch `sprint/track-<X>`; Director merges into the designated branch | "No two workers modify the same working tree"; only designated branch is pushed |
| D-004 | 13:35 | Install .NET SDK 10.0.402 (pinned by praxis/rehearsal global.json) into /root/.dotnet | Needed for Praxis CLI and F#/WASM measurements; dotnet absent at start |
| D-005 | 13:35 | Track H launches after first track outputs land rather than at t0 | Synthesis needs inputs; saves idle compute |
