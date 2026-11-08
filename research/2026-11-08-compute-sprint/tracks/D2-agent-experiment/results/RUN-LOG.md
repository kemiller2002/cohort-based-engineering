# SPR-D2-01 run log (Director)

All arms: subagent_type general-purpose, run in background, same session model (inherited from the Director session; the identifier is kept out of repository artifacts). Prompts were pasted from arm-prompts/{M,G}.txt with {WS} substituted.

**Exposure note (applies to all runs):** subagents run inside the Director's session, so they may receive the session's injected CLAUDE.md context ("Read and follow AGENTS.md"). The Praxis AGENTS.md contains the same authority contract, so the M arm may be partly treated, which biases the result towards no difference. Transcripts are checked after the fact for reads of AGENTS.md, oracle-7f3a/, other workspaces and sprint-wt/, by grep counts only.

| runId | arm | batch | launched (UTC) |
|---|---|---|---|
| r2 | M | 1 | 2026-11-08T19:33:29Z |
| r3 | M | 1 | 2026-11-08T19:33:29Z |
| r4 | G | 1 | 2026-11-08T19:33:29Z |
| r6 | G | 1 | 2026-11-08T19:33:29Z |
