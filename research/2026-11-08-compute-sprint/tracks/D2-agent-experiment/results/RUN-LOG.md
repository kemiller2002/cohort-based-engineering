# SPR-D2-01 run log (Director)

All arms: subagent_type general-purpose, run in background, same session model (inherited from the Director session; the identifier is kept out of repository artifacts). Prompts were pasted from arm-prompts/{M,G}.txt with {WS} substituted.

**Exposure note (applies to all runs):** subagents run inside the Director's session, so they may receive the session's injected CLAUDE.md context ("Read and follow AGENTS.md"). The Praxis AGENTS.md contains the same authority contract, so the M arm may be partly treated, which biases the result towards no difference. Transcripts are checked after the fact for reads of AGENTS.md, oracle-7f3a/, other workspaces and sprint-wt/, by grep counts only.

| runId | arm | batch | launched (UTC) |
|---|---|---|---|
| r2 | M | 1 | 2026-11-08T19:33:29Z |
| r3 | M | 1 | 2026-11-08T19:33:29Z |
| r4 | G | 1 | 2026-11-08T19:33:29Z |
| r6 | G | 1 | 2026-11-08T19:33:29Z |
| r5 | M | 2 | 2026-11-08T19:35:51Z |
| r8 | M | 2 | 2026-11-08T19:35:51Z |
| r1 | G | 2 | 2026-11-08T19:35:51Z |
| r7 | G | 2 | 2026-11-08T19:35:51Z |

## Batch 1 exposure check (Director, 2026-11-08T19:35:51Z)
`/home/user/sprint-tools/exposure.py` parses each run's tool calls and prints counts only. For r2, r3, r4 and r6 the counts are 0 for oracle-7f3a, AGENTS.md, CLAUDE.md, /home/user/sprint-wt, /home/user/praxis and other workspaces. Tool-call counts (4/4/6/5) equal the runtime-reported tool_uses.

Injected context: the string "AGENTS.md" occurs 56 times in every transcript, M and G alike, so the session's CLAUDE.md pointer was present in both arms. The authority-contract text occurs 0 times in the M transcripts and once in each G transcript (its prompt). No run read AGENTS.md. Exposure to the contract text was therefore limited to the G arm; the pointer itself was equal across arms. No exclusions.
