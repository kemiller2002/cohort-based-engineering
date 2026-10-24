# B4 integration result: invoice vertical slice

**Run:** 2026-10-23, by the program coordinator. **Status: EXPERIMENTAL.** This proves the path works on one synthetic
fixture. It does not show that the path prevents unauthorized decisions; that question belongs to EXP-1 and EXP-3.

**Inputs**

| Input | Revision or digest |
|---|---|
| Ordo slice | ordo `03b0d30` (PR #105), `experiments/verified-construction/` |
| Dokimos audit | dokimos `3ff803b` (PR #53), `experiments/rule-provenance/` |
| Handoff fixture | `contracts/fixtures/invoice-slice/handoff.json`, sha256 `ec5d0e6a…` |
| Construction trace | sha256 `eb85073c…` (copy: `construction-trace.json`) |
| Audit | copy: `provenance-audit.json` |

**Environment:** .NET SDK 10.0.402, Linux container.

**Reproduce:** `./run-b4.sh <ordo checkout> <dokimos checkout> [out]`.

## Flow, step by step

| Step | Component | Result | Evidence |
|---|---|---|---|
| 1 Intake | Praxis-shaped handoff (hand-authored; no exporter yet, B1) | Schema-valid | `contracts/fixtures/invoice-slice/handoff.json` |
| 2 Authorized decision model | Ordo `admit` | Fixture admitted. Refuse-and-record question accepted. Mutated handoffs rejected | Ordo tests (69/69) |
| 3 Ordo construction | Translator → existing Ordo.Core plan validation → unchanged Ordo.Construction emitter, plus the handwritten value layer | Generated sources and trace are byte-identical on rerun | `run.sh` determinism step |
| 4 F# compilation | `dotnet build` / `dotnet test` | 69 passed, 0 failed, including 13 compile-negative probes and 7 mutants caught | Re-run by the coordinator |
| 5 Dokimos evidence | `integrate` against the built `Invoice.Slice.dll` | `pass-with-owner-questions`: findings 3, proven 0, owner questions 3, blocking 0. All 6 invariant checks hold within the bound (depth 4) | `provenance-audit.json`, schema-valid |
| 6 Praxis completion | `praxis work complete --evidence` | **NOT_RUN.** The slice is not a Praxis work item, and verified completion with `work finish` is unreleased (A3). The evidence bundle has the form C4 expects | `run-b4.sh` writes `evidence-bundle.json` |

## Frozen slice outcomes (fixture README)

| # | Outcome | Status | Evidence |
|---|---|---|---|
| 1 | Payments above 10,000.00 are refused for **every** customer; no STR- exemption; no 25,000.00 limit | **PASS** | Ordo behaviour tests (10,000.01 refused for STR-001); the "re-add STR- exemption" and "drop limit" mutants caught; the Dokimos DEC-FIN-001 check holds for C-001 and STR-001; the Ordo trace excludes OBS-LEGACY-001/002 |
| 2 | Void on a partially paid invoice is refused with a code naming Q-FIN-001; trace disposition `deferred-pending-question` | **PASS, with one open observation** | Ordo tests; trace entries; Dokimos Q-FIN-001 check holds. The audit keeps 1 uncertain finding: the generated `undecided` function cannot reference the handwritten Q-FIN-001 mapping, because Ordo's emitter never writes question ids into generated code and the generated tier depends only downward. It is recorded in Ordo's LIMITATIONS.md |
| 3 | Persisting needs a validated, applied payment and the payments-service capability; violating code does not compile | **PASS** | 13 compile-negative probes. Limitation: minting the capability *inside* `Invoice.Slice` is checked only by a source scan |
| 4 | Dokimos reports OBS-LEGACY-001 and OBS-LEGACY-002 as non-blocking `uncertain-authority` questions routed to finance-controller; legacy code unchanged | **PASS** | `provenance-audit.json` findings; the Dokimos byte-preservation test |
| 5 | INV-INV-001..004 hold within the bound; a seeded drop-limit mutant is a proven, blocking `invariant-violation` | **PASS** | Invariants hold on the built Ordo DLL. In `./run.sh fixture`, the mutant gives exit 4 with a proven blocking finding; checker validation kills 7/7 mutants |

## What this shows and does not show

**Shows:**
- The C1 → C2 → C3 contracts compose across two repositories, using only existing Ordo machinery plus experimental
  code.
- An unresolved policy question stays a refusal-with-question all the way through, and is never turned into a rule.
- Inherited, unauthorized legacy rules are surfaced to their owner, not silently fixed or reused.
- Invalid persistence calls do not compile.

**Does not show:**
- **Prevention.** No agent was in the loop, so the slice says nothing about unauthorized decisions.
- **Audit accuracy.** Precision and recall of the lexical audit are unmeasured. Scanning the construction tool's own
  sources flagged about 50 ordinary helpers, which shows the scan is scope-sensitive (EXP-3 phase 1).
- **Praxis completion,** which was not run.

**Cost:** two coding agents and the coordinator. Tokens for this session are not exported by the runtime: `unavailable`.
