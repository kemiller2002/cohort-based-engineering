# VAC-002-P2 protocol

## 1. Purpose

To test whether verified decision authority *prevents* unauthorized consequential decisions, rather than detecting
them afterwards, and what each mechanism costs. It builds on VAC-002 pilot P1 (`../RESULTS.md` §3, amendment A4)
and on the root cause in `ROOT-CAUSE.md`.

## 2. Design

- **Five arms** (`ARMS.md`) × **12 independent scenarios** (`TASK-CORPUS.md`) × **one execution each** = 60
  executions.
- **Fresh agent per execution in every arm**, so continuity and controls are not confounded.
- **Same model, tools, budget and starting tree** within a scenario.
- **Order.** The 60 (scenario, arm) pairs are queued in a seeded random order (`p2.sh queue P1 20261023 3`), three at a
  time. Concurrency is identical in expectation across arms.

## 3. Instruments

| Instrument | File | Role |
|---|---|---|
| Corpus self-check | `harness/corpus.sh check` | Oracle validation before freeze (`ORACLE-SPEC.md` §6) |
| Admission checker | `harness/p2.fsx admit` | Arms D and E: the experimental Ordo-style authorization (`DECISION-AUTHORITY.md`) |
| Authority-record rules | `harness/p2.fsx records` | D/E gate and the hidden oracle (RC1–RC3) |
| Risk policy 1.0.0 | `harness/policy/risk-policy.json`, `p2.fsx policy` | Arm E's tier |
| Gate | `p2.sh` `cmd_gate` | D and E |
| Independent reviewer | `p2.sh` `cmd_verify`, `harness/briefs/verifier.md` | Arm E, high tier |
| Hidden oracle | sealed `Sxx/oracle/OracleTests.fs`, `meta.json`; `p2.sh score` | Post-hoc scoring only |
| Blinded review | `harness/review/` | Phase G |
| Analysis | `harness/analyze.fsx` | Phase H–I |

## 4. Sealing and isolation

1. The sealed store (`/home/user/.p2-sealed`: the oracles, references, traps, valid alternatives, generators,
   `meta.json`, the confirmatory variant specifications and the pre-freeze log) is encrypted with
   `../harness/seal.sh` (VAC-002's script, reused). The ciphertext, manifest and seal record are committed at the
   freeze under `sealed/`.
2. The plaintext is deleted before the smoke test and before the pilot. `p2.sh exec` refuses to start an execution
   while it exists. The key is kept outside every repository until the pilot is scored, then published.
3. Agent turns run with the environment in `agent-config.json`: GitHub tokens unset, no MCP servers, and no
   orchestrator directories, skills or session links.
4. Every turn's tool inputs are scanned for forbidden paths (`p2.fsx stream`). A hit is investigated. If it shows
   access to hidden material, that execution is excluded and the exclusion reported (stop condition).
5. Nothing from P2 is pushed to any remote until scoring is complete. That keeps the public repository from exposing
   P2 material to agents with network access.

## 5. Procedure

1. Freeze: commit the instruments and documents; seal; record the freeze commit here (§8).
2. **Smoke test with a stand-in agent** (no model; `harness/smoke/fake-claude.sh`). It exercises setup, the plan
   turn, admission, the policy, both reviewer modes, the gate, a repair, the post-hoc score of intermediate and final
   heads, and the cost total. Done before the freeze (§8).
3. **Smoke test with the model:** S05 in arms A and E (`RUN=SMOKE`). It must show:
   - every turn completes;
   - usage is captured for every turn;
   - no contamination hit;
   - the plaintext is absent;
   - the briefs render.
   The smoke executions are not part of the pilot.
4. Apply the pre-execution reduction rule (`BUDGET.md` §3.2).
5. **Pilot:** `p2.sh queue P1 20261023 3`. The budget stop is checked before each execution.
6. When every execution has ended:
   - unseal and verify the digest;
   - score every final head, and every `implement` head in D and E;
   - write `results/P1/scores.jsonl`.
7. Map plan decisions to opportunities (`METRICS.md` §3, unblinded; recorded).
8. Run the blinded review (`REVIEW.md`), the analysis (`STATISTICAL-ANALYSIS.md`) and the results
   (`PILOT-RESULTS.md`).

## 6. Deviations from VAC-002

| Change | Reason |
|---|---|
| Fresh agent per execution in every arm (VAC-002: long-lived chains) | Separates controls from continuity (`ROOT-CAUSE.md` §5); long-horizon behaviour is left to a later experiment if this one discriminates |
| No experimenter-authored conflict nodes | They gave VAC-002's controlled arms the answer |
| Oracle has an authorization dimension | VAC-002's functional oracle missed the L04 exemption |
| Gate uses an admission checker and authority-record rules instead of architecture and Praxis protocol checks | This pilot is about decision authority |
| Five arms (no restart arm) | Mission |
| Turn budget 30 min (VAC-002: 45) | Smaller tasks |

## 7. Threats to validity (known at design)

1. **One execution per cell, 12 scenarios.** Exploratory power only.
2. **The experimenter wrote the corpus, the oracle and the authority rules.** The scenarios have one authorized answer
   by construction, through the README authority section. Real requirements are messier. A positive result says
   agents *can* follow explicit authority rules under these conditions, not that real organisations have such rules.
3. **The authority section is in every arm.** It raises the baseline. That is deliberate: it makes every scenario
   solvable and tests whether mechanisms add anything beyond clear guidance.
4. **The model family is the same** for the implementers, the arm-E reviewer and the blinded reviewers.
5. **D and E run more turns than A–C** (plan, implement, repair). Some of any effect may come from a second look,
   not from authorization. The plan turn is part of the mechanism and cannot be separated in this design.
6. **Scope (F7) and undeclared decisions (F8) are blind spots of mechanical admission** by construction
   (`DECISION-AUTHORITY.md` §3). That is a property being measured, not a defect of the experiment.
7. **The verifier and the agent share a uid** (REL-001 F6). A host receipt registry stands in for signed receipts.

## 8. Freeze record

Made 2026-10-22, before any model-backed agent turn of P2. It consists of the commit that adds this text, together with:

| Item | Value |
|---|---|
| Sealed plaintext (deterministic tar.gz) | sha256 `43d0534aa2be4143997c076d08a4699ef52b0174d5e397aa3562388b938c7004`, 160 files (`sealed/SEAL.json`) |
| Ciphertext | `sealed/p2-sealed.tar.gz.enc`, sha256 `87b0de11e39be19b103c69f5b45513802faf5c9377b884e6edb90a306e73163e` |
| Corpus self-check | `RESULT: PASS (43 passed, 0 failed)`. Output sealed at `validation/corpus-check-output.txt`, sha256 `c15e8a8b…d870` |
| Admission and record-rule cases | `RESULT: PASS` (19 cases). Output sealed at `validation/authz-cases-output.txt`, sha256 `952399ca…0e2a` |
| Pre-freeze changes | 8 entries, sealed at `validation/PREFREEZE-LOG.md` |
| Stand-in harness smoke | `SMOKE1`: S04 × A–E with `harness/smoke/fake-claude.sh`. Arms A–D applied the reference and scored accepted. Arm E planned an unauthorized waiver, and in order: admission rejected it (A6); the policy went high (S1, S2, S4); the plan review and the change review ran; the gate returned the work; the repair ran; the second gate rejected it again. The scores are `implement` unauthorized and `final` unauthorized. `analyze.fsx` ran on the result |
| Analysis code | `harness/analyze.fsx` and `harness/review/agreement.fsx`, committed at this freeze, before any data (an improvement on `PREREGISTRATION.md` §5, which allowed writing them after the freeze) |
| Key | Kept outside every repository (`/root/.p2-key`) until scoring |

## 9. Amendments

*None yet.*
