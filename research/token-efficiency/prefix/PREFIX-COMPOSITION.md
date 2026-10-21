# Runtime prefix composition (EXPLORATORY)

**Status: exploratory measurement, 2026-10-21.** Not preregistered. It sizes the item that OVERHEAD-ANALYSIS.md
§3.2 and §5 item 5 left unmeasured, and it supports draft revision R1 of `experiments/REL-001/protocol/run-03.md`.

- Raw data: [`prefix-probes.json`](prefix-probes.json) (usage per call, CLI version, model, flags, loaded tools,
  timestamps).
- Script and exact command: [`probe-prefix.py`](probe-prefix.py), [`README.md`](README.md).

## Method

- Each probe is one headless, one-turn call: `claude -p "Reply with OK" --max-turns 1`.
  - Claude Code **2.1.306** (`/opt/node22/bin/claude`), model **`claude-opus-5-5`**.
  - The call mirrors the run-03 K1 launcher (`run-03/harness/launch-agent.sh`): `env -i`, a fresh `CLAUDE_CONFIG_DIR`
    and `HOME`, a fresh `--session-id`, a nonce in `--append-system-prompt`, `--permission-mode bypassPermissions`,
    `--strict-mcp-config` with no servers, and `stream-json` output.
  - It adds `IS_SANDBOX=1`, because this host runs as root and `bypassPermissions` is refused there otherwise.
  - It adds `--max-turns 1`.
- No tool is invoked, so the call makes exactly one request.
- **Metric:** first-request context = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`,
  from the first usage iteration of the `result` event. It includes the short user message (about 4 tokens) and the
  nonce line. Both are the same in every configuration.
- One factor is varied at a time, with 3 replicates per configuration.
- The arm-context rows append a run-03 file to the prompt, so they have 1 replicate each. Tokenization is
  deterministic; replicates of the same text differ by at most 8 tokens.
- 22 probes in the dataset; estimated probe cost is about $0.63 at price table 2026-10-20.1, with 1-hour cache writes.

## Results (first-request context tokens)

| Configuration | Flags beyond the K1 baseline | Tools loaded | n | Mean | Range | Δ vs baseline |
|---|---|---|---|---|---|---|
| **baseline** (run-03 K1 as drafted) | none | 25 (default set) | 3 | **16,513** | 16,510–16,516 | 0 |
| tools-minimal | `--tools Bash,Read,Edit,Write,Glob,Grep` | 6 | 3 | 7,374 | 7,373–7,375 | −9,139 |
| **tools-core** (adopted in run-03 R1) | `--tools Bash,Read,Edit,Write` | 4 | 3 | **5,821** | 5,818–5,826 | **−10,692** |
| no-slash | `--disable-slash-commands` | 24 (no `Skill`) | 3 | 19,734 | 19,732–19,737 | **+3,221** |
| trimmed | tools-minimal + `--disable-slash-commands` | 6 | 3 | 7,375 | 7,374–7,376 | −9,138 |
| no-tools (reference) | `--tools ""` | 0 | 3 | 2,703 | 2,702–2,704 | −13,810 |

The 2.1.306 default set, as loaded under K1 isolation, is: `Task, Bash, CronCreate, CronDelete, CronList, DesignSync,
Edit, EnterWorktree, ExitWorktree, ListAgents, Monitor, NotebookEdit, PushNotification, Read, RemoteTrigger,
ReportFindings, ScheduleWakeup, SendMessage, Skill, TaskStop, ToolSearch, WebFetch, WebSearch, Workflow, Write`. It
also lists 19 skills. It has **no `Glob` or `Grep`**. No MCP servers are loaded in any configuration.

### Composition of the K1 baseline (differences of measured means)

| Component | Tokens | Share of 16,513 |
|---|---|---|
| System prompt, nonce line and user message (no-tools) | 2,703 | 16% |
| Definitions of `Bash, Read, Edit, Write` (tools-core − no-tools) | 3,118 | 19% |
| The other 21 default tools, plus anything sent only with them, such as the skill listing (baseline − tools-core) | **10,692** | **65%** |

- `Glob` and `Grep` together add 1,553 tokens (tools-minimal − tools-core). They are not in the default set.
- `--disable-slash-commands` **adds** 3,221 tokens when the default tools are loaded. The mechanism is unmeasured;
  the flag also removes the `Skill` tool. With the minimal tools it changes nothing (+1 token), so R1 does not use it.

### Arm-specific context (measured deltas, appended inline to the trimmed configuration)

| Content | Δ tokens vs trimmed (7,375) | OVERHEAD-ANALYSIS §3.5 estimate (bytes/4) |
|---|---|---|
| `directives/DIRECTIVES.md` (arms B, C, D) | +3,741 | 2,726 |
| `briefs/workflow-c.md` (arm C) | +583 | not given separately |
| `briefs/workflow-d.md` (arm D) | +465 | not given separately |
| `briefs/core.md` + `briefs/outcome.md` (all arms) | +415 | not given separately |

- Each delta includes a fixed label of about 10 tokens.
- This content is **not** part of the fixed runtime prefix. Agents read it with a tool, and it is then carried in
  history on every later request.
- The directives pack measures about 37% above the bytes/4 estimate.

### Cache behaviour seen in the probes

- Every cache write was a **1-hour** write (`ephemeral_1h_input_tokens`). OVERHEAD-ANALYSIS priced writes at 5 minutes.
- A fresh `CLAUDE_CONFIG_DIR` and a nonce do not make a K1 first request fully cold. The leading prefix is still
  read from cache when an earlier process used the same tool set:
  - baseline: 10,727 tokens;
  - tools-core: 3,324 tokens;
  - the very first tools-core probe of the session read 0 tokens.
- This is what run-03 M2 measures. Trials run back to back will usually share this part.

## Estimated saving (run-03 K1, tools-core vs baseline)

- **Per request:** 10,692 tokens.
  - $0.00214 at the cache-read price ($0.20/Mtok).
  - $0.0535 if written with a 5-minute write ($5/Mtok); $0.0855 with a 1-hour write ($8/Mtok).
- **Per 11-request run:** 117,612 tokens. 11 is the pooled median of requests per run in run-02, from
  OVERHEAD-ANALYSIS §3.5 and `out/run-02-context-sizes.json`.
  - $0.0235 if every request reads the removed tokens from cache.
  - $0.1069 if the first request writes them with a 1-hour write and the other 10 read them.
  - $0.0748 with a 5-minute first write.
- Prices are from `research/pricing/anthropic.price-table.json`, tableVersion 2026-10-20.1, `claude-opus-5-5`.

## Limits

- **Not the 40.6k prefix.** The 40.6k prefix of run-01 and run-02 (§3.2) came from **K0** sub-agents inside a host
  session, with that session's tools, MCP servers and CLAUDE.md, on an earlier CLI version. It is not re-measured here.
  - One non-isolated `claude -p` call with this host session's environment read 36,042 tokens on its first request.
  - That call used the session's default model, not `claude-opus-5-5`, and n = 1. It is an anecdote, not data. It
    agrees in size with the 36,070-token calibration in §3.2.
  - The K1 isolation alone already removes most of that host context. R1 removes 65% of what remains.
- **Server-side gating.** The default tool list may depend on account or server-side gating, such as `DesignSync`,
  `Workflow` and `ReportFindings`. The trial host must re-measure it with the pinned CLI. The saving changes if the
  default set changes; the `--tools` profile itself does not.
- **Prefix size only.** A smaller tool set may change agent behaviour, for example sub-agent use or web lookups, and
  so the number of requests. That effect is not measured here. It is arm-identical in run-03 by construction.
- **Not measured:** whether Bash-based `grep` or `find` replaces dedicated search tools at a token cost. The default
  set has no Glob or Grep either, so R1 does not change this.
