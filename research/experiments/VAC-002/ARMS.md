# VAC-002 arms

**Common to all six arms:**

- the same fixture (`fixture/repo`: the ARCH-001 Lending application plus VAC-002's base changes);
- the same chain of tasks in the same order;
- the same requirements, visible acceptance tests, decision records and natural-language architecture documents
  (`docs/architecture/`, SDE-DOCTRINE-003 plus the Lending instance);
- the same engineering directives (`../VAC-001/directives/DIRECTIVES.md`, byte-identical to VAC-001 and REL-001
  run-02/03);
- the same report schema and the same fault notes at the same units;
- the same model and configuration: `claude-opus-5-5`, effort medium, auto-compaction window 200,000 tokens;
- the same K1 isolation (one headless `claude -p` process per turn, fresh configuration directory per session);
- the same tools (Bash, Read, Edit, Write) and the same turn budget (45 minutes).

They differ only in the rows below.

| Arm | Agent lifetime | Controls the agent has | Host verification after the unit | Verified state |
|---|---|---|---|---|
| **A** | Fresh agent per unit; the handoff is the earlier agents' reports in `.vac/reports/` | None beyond the common material | None | No |
| **B** | One session for the whole chain (`--resume`) | None beyond the common material | None | No |
| **C** | One session | Ordo contract admission (`contracts/Lxx.json`, Ordo 1.17.0); in-loop `archcheck` (the ARCH-001 compiler-resolved verifier, full Lending policy); decisions recorded in `docs/decisions/DECISIONS.md` as `proposed` | None | No |
| **D** | One session | As C, plus the Praxis work protocol (Praxis 3.19.0: begin, checkpoint, complete, durable push) | **Full gate** after every unit, one repair round | Yes, written by the host after every gate |
| **E** | One session | As C (the agent is told a risk-dependent gate may run) | **Adaptive gate**: tier low, medium or high, chosen by the frozen policy `harness/policy/adaptive-policy.json`; one repair round | No |
| **F** | Restarted every 4 units (units 1, 5, 9, …): a new session whose only continuity is the repository, the verified state and the reports; long-lived between restarts | As D | Full gate, as D | Yes |

**The Praxis scaffold in D and F.** In D and F, `praxis init --project lending` adds Praxis's scaffold to the
repository at setup: `AGENTS.md`, `CLAUDE.md`, `ros/`, `.echelon/` and others. A K1 session started in the repository
loads `CLAUDE.md`, so D and F agents also receive Praxis's own agent contract. That is part of the Praxis treatment,
as in VAC-001's D arm. It also adds context tokens, which are counted.

## The gate (Dokimos's role)

**Who runs it.** The host runs the gate in harness state, on a fresh clone of the committed head. It is not the
hidden evaluation oracle and never reads it. VAC-001's gate fed the hidden oracle's failures back to the agent, so
there the scoring instrument doubled as a control. VAC-002 separates the two (deviation from VAC-001, recorded in
`PROTOCOL.md` §11).

**What it checks** (the high tier and arms D and F):

| Check | Passes when |
|---|---|
| `build` | The solution builds |
| `repositoryTests` | Every repository test passes, including every earlier unit's visible acceptance tests |
| `cleanTree` | No uncommitted paths |
| `architecture` | `archcheck verify` passes the full Lending policy |
| `contractAdmission` and `conflictRecorded` | When Ordo refuses the staged contract (an unresolved conflict), the report records the conflict |
| `reportEvidence` | Every decision's evidence exists (Layer 1) |
| `claimConsistency` | The report does not claim completion while the build or tests fail |

**When it rejects.** The agent receives the failing checks (test names, rule findings, invalid references) and one
repair turn in the same session. The gate then runs again. A unit that still fails is recorded as unresolved; the
next unit proceeds.

**Why Dokimos itself is not invoked.** The verifier and the agent share a uid in this container (REL-001 readiness
F6, still open), so a Dokimos receipt would not be independent. The host gate plays the role and is labelled as such.

## Arm E: adaptive enforcement

E's agent has C's in-loop controls. After E's turn, the policy computes a tier from 12 signals:

- 5 are known before the turn: an Ordo refusal, a staged decision revision, an external change to `src/` since the
  last verification, money or authority terms in the requirement, and ≥ 2 new commands.
- 7 come from E's own diff and report: tiers touched, build-surface edits, assumptions or open questions, a blocked
  outcome, an unresolved defect at the previous gate, decision-record edits, and fan-out.

The tier selects the gate's checks:

| Tier | Checks |
|---|---|
| low | Build, repository tests, clean tree |
| medium | Low, plus architecture, contract admission and conflict recording |
| high | Medium, plus report evidence and claim consistency |

**What the policy may use.** Every signal is information every arm has. The policy never reads the hidden oracle, the
fault catalogue or other arms. Each decision is written to `results/RUN/E/policy-N.json` with the signals that
fired. E never receives verified state: it tests adaptive *verification*, not verified *memory*.

## Arm F: restarted with verified-state reconstruction

F has exactly D's controls. At units 1, 5, 9, 13, … the session is replaced by a new one (as if context had been
lost), and that unit's brief says the agent is taking over. F's verified state, written by the gate, is what lets it
reconstruct.

What F is compared with:

| Comparison | What it isolates |
|---|---|
| F against A | Verified state as a reconstruction aid (both restart) |
| F against D | The cost and reliability of losing context under the same controls |

VAC-001's DR arm restarted every unit and cost +86% over D. F restarts every fourth unit, which is closer to a context
loss than to a fresh agent per change.

## The five-way comparison of Phase G

The mission asks for five mechanisms. Within six arms they map as follows; the gaps are stated, not hidden.

| Mechanism | Arm(s) | Note |
|---|---|---|
| 1. Natural-language guidance only | A, B | The four-tier documents and DEC records are in every repository |
| 2. Typed architectural decision records | C (bundled) | C bundles Ordo `ecir/1` contracts, typed decision nodes and `archcheck`. Typed records **alone** are not isolated by any arm, so their separate effect is reported as **not measured** |
| 3. Executable architectural constraints | C | `archcheck` in the loop; Ordo admission |
| 4. Full independent verification | D (and F) | The gate (architecture check included) after every unit |
| 5. Adaptive selective enforcement | E | The policy above |
