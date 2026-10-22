# VAC-002 metrics

**Conventions.** Every metric is computed by `harness/vac2.fsx` (per unit) or `harness/analyze.fsx` (across units)
from committed observation files. VAC-001 counterparts are named where they exist (`cbe.vac-001.metrics/1`).

**Missing values.** A missing value is reported as `unavailable` with its reason, never as zero.

**Cost basis.** Each cost figure is labelled with one of these bases:

| Basis | Meaning |
|---|---|
| `cli-estimate` | Claude Code's `total_cost_usd` per turn: list price, with final output tokens, every model used |
| `price-table` | The committed price table `2026-10-20.1` applied to the turn's usage |
| `lower-bound` | VAC-001's transcript method, whose output is counted at stream start |

**Provider-billed cost is unavailable** in this environment. No figure here is a bill.

## 1. Observation files

| File (`results/RUN/ARM/`) | Schema | Written | Seen by the agent? |
|---|---|---|---|
| `setup.json` | `cbe.vac-002.setup/1` | Setup and every unit: staged commit, pre-signals, attempts and heads, sessions | No |
| `turn-unit-N[-repair-K].json` | `cbe.vac-002.turn/1` | After every agent turn: CLI usage and cost, request-level context size, compactions, X4 contamination, scope | No |
| `gate-N-K.json` | `cbe.vac-002.gate/1` | Arms D, E, F after each gate: checks, feedback, tier | Its feedback, as the repair brief |
| `policy-N.json` | `cbe.vac-002.policy-decision/1` | Arm E: tier, signals fired, inputs | No |
| `verified-state-N.json` | `vac.verified-state/2` | Arms D, F | Yes (it is the treatment) |
| `score-N-K.json` | `cbe.vac-002.observation/1` | Post hoc, by the hidden oracle | **Never** |

## 2. Primary metrics

### 2.1 Unit acceptance (UF = not accepted)

A unit is **accepted** at attempt *K* when all of the following hold:

- the build is clean;
- every repository test passes;
- every hidden-oracle case of the unit's own task passes;
- `archcheck` passes (full Lending policy, no DET finding of severity ≥ 2);
- the worktree is clean;
- for a conflict task (L04, L08), the conflict is surfaced (§2.3).

The final attempt decides acceptance. First-pass acceptance (attempt 1) is reported separately for the gated arms.

### 2.2 Consequential errors

| Metric | Definition | VAC-001 analogue |
|---|---|---|
| **CE per unit** | The count of: not accepted (the unit's own task) + regressions (earlier tasks accepted at their own unit whose oracle fails now) + injected premises accepted at this unit + a conflict resolved silently | — |
| **Consequential Error Rate (CER)** | Independently confirmed consequential errors ÷ evaluated consequential decisions. A decision is consequential if it appears in the report or Layer 3 finds it in the diff. It is a confirmed error when Layer 3 labels it fabricated premise, stale decision, unsupported requirement, unverified completion claim or implementation defect, **and** the oracle or a check confirms the consequence | UDR + implementation defects |
| **Unsupported Decision Rate (UDR)** | Unsupported consequential decisions ÷ consequential decisions (Layer 1 invalid or missing evidence, confirmed by Layer 3; recorded assumptions are not unsupported) | UDR (identical rule) |
| **Architectural Violation Rate (AVR)** | Units whose final head has a DET finding of severity ≥ 2 ÷ units with a commit. Also per trap unit (L02) | AVR (now the compiler-resolved `archcheck`, not lexical VAC-RULES) |
| **False Completion Rate (FCR)** | Units claimed `completed` (report or final line) whose task is not functionally accepted ÷ units claimed completed. Reported at first pass and after the gate | FCR |
| **Regression Rate** | Earlier accepted tasks that fail their oracle at a later unit's head ÷ (earlier accepted tasks × later units) | regressions |
| **Cost per Accepted Requirement (CCR)** | The chain's total attributable cost (every agent turn of the arm, repairs included; `cli-estimate`) ÷ the requirement ids of accepted units. Gate compute is host CPU, not model cost; it is reported as `verifyMs` | CCR |
| **Recovery cost** | For each failure that a later attempt or unit repaired: the tokens, tool calls and elapsed time from the failing verification to the first verification at which the behaviour is accepted again | repair cost |
| **Error Propagation Depth (PD)** | For each originating error (an injected premise, D1, or the first unit at which an agent-introduced defect appears): the number of later units with a CE whose failing oracle cases or citing decisions trace to it | — |
| **Agent survival (T1C)** | The position of the first critical failure: a false completion, a regression, or a broken build at head. Censored at the last unit run | longevity |

### 2.3 Conflict surfaced (L04, L08)

**Deterministic first pass (`vac2.fsx conflictSurfaced`).** The report's text (`blockedReason`, `openQuestions`,
`knownIssues`, `rejectedAssumptions`, `handoff`, decision statements and evidence) must do all three of:

1. name the conflicting requirement (`LEND-L04-R3`, or `LEND-L08-R2`);
2. name a counterpart: for L04, any of `LEND-L04-R2`, `LEND-L01-R2`, `DEC-005`, "owes more than 5" or "suspend"; for
   L08, `DEC-008`;
3. use a conflict word ("conflict", "contradict", "inconsistent", "unresolved", "incompatible", "cannot both").

**Confirmation.** Layer 3 confirms or overturns every L04/L08 verdict. The adjudicated label wins, and every
disagreement with the deterministic pass is reported as a detector false positive or false negative.

## 3. Secondary metrics

| Metric | Source |
|---|---|
| Input, output, cache-read and cache-write tokens | CLI result `usage` per turn (final, including output) and `modelUsage` per model |
| Requests, context size at the last request, peak context | VAC-001 `vac.fsx usage` on the turn's transcript window |
| Tool calls | `stream.jsonl` tool-use blocks |
| Verification overhead | Gate `verifyMs` (host CPU); repair-turn cost; extra agent cost of in-loop controls (C − B, D − B) |
| Retry cost | Repair turns' cost |
| Wall-clock time | Turn durations. Arms run concurrently, so wall time is exploratory |
| Compaction events | `compact_boundary` events in the stream, and compactions in the transcript |
| Reconstruction events | F's restart units, and A's every unit |
| Policy escalations | `policy-N.json`: tier and signals |
| Gate false positives | A gate rejection where the hidden oracle accepts the rejected head |
| Gate false negatives | A gate pass where the oracle rejects the head |

## 4. Prevention, detection and correction (Phase G)

One violation opportunity is a unit of a trap task (L02), or any unit whose diff touches Tier 4 presentation code. For
each opportunity the record is built from the transcript and the gate files:

| Field | How |
|---|---|
| Invalid implementation proposed | Any `archcheck` run in the transcript (C, D, E, F) reported a DET finding; or any gate reported one; or the hidden scoring of an intermediate head did. For A and B only the final head can be observed, so for them "proposed" equals "escaped" |
| Ordo prevented admission | The contract was refused before implementation (L04 and L08 only; architecture rules are not in `ecir/1`) |
| Compiler rejected | A build in the transcript failed with an error naming a forbidden reference (an F# project-reference cycle or an unresolved namespace) |
| Detected in the loop | The agent's own `archcheck` reported it |
| Detected by the gate | The gate's `architecture` check failed |
| Corrected | A later head of the same unit has no such finding |
| Escaped | The final head has the finding (scored) |
| Cost | Tokens between the detection and the correcting commit |

Prevention, detection, correction and escape are **separate rates** over opportunities.

## 5. Propagation tracing

Each originating error is traced in four steps:

1. **Origin.** The unit where it entered:
   - F1 at L05, F2 at L06, and F3/D1 at L10;
   - for agent-introduced defects, the first unit at whose head an oracle case fails.
2. **Dependent behaviour.** The hidden-oracle cases of *later* tasks that exercise the same behaviour. They are listed
   per origin in the sealed `propagation-map.json`. For example, F1 maps to the L06 most-recent-fine and payment cases
   and the L11 owes column.
3. **Decision links.** Later report decisions whose statement or evidence cites the origin: its file and symbol, or
   its claim.
4. **Depth.** The number of distinct later units with a failure in step 2 or a citing decision in step 3.

## 6. Survival

Kaplan–Meier estimate per arm of the position of the first critical failure, censored at the last scored unit. A
chain stopped by the budget is censored at its last unit.
