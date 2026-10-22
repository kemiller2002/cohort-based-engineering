# VAC-002: Adaptive, risk-triggered enforcement (Arm E) against full enforcement (Arm D), Phases C and H

**Policy:** `harness/policy/adaptive-policy.json`, version 1.0.0. It was frozen before the pilot; the S6/S7
calibration on reference diffs only is described in its `calibrationNote`.

**Records:**

| File | Contents |
|---|---|
| `results/P1/E/policy-N.json` | One decision per unit: tier, signals fired, inputs |
| `results/P1/{D,E}/gate-*.json` | Gate results |
| `results/P1/contrasts.json` | Cost contrasts |

**Evidence class:** pilot, descriptive.

## 1. Was the policy hindsight-free?

Yes, by construction and by inspection:

- **Pre-decision signals** (S1–S5) come from the staged requirement, the contract's Ordo verdict and the harness
  commits since the last verification. Every arm has this information.
- **Post-turn signals** (S6–S12) come from E's own diff and report and from E's own earlier gates.
- **No forbidden inputs.** The policy code (`vac2.fsx policy`) reads no oracle, fault or other-arm file. The 12
  decision files list their inputs in full.

## 2. What it decided

| Position | Task | Tier | Signals |
|---|---|---|---|
| 1 | L01 | medium | S6 (4 tiers), S8 |
| 2 | L02 | medium | S4, S8 |
| 3 | L03 | medium | S8 |
| **4** | **L04** | **high** | **S1 contract conflict**, S4, S6, S8 |
| 5 | L05 | medium | S4, S5, S6, S8 |
| 6 | L06 | medium | S2, S4, S6, S8 |
| 7 | L07 | medium | S4, S6, S8 |
| **8** | **L08** | **high** | **S1 contract conflict**, S8 |
| 9 | L09 | medium | S2, S6, S8 |
| **10** | **L10** | **high** | S2, **S3 external `src/` change (D1)**, S4, S6, S8 |
| 11 | L11 | medium | S4, S8 |
| 12 | L12 | medium | S2, S8 |

**Escalation frequency:** low 0, medium 9, high 3. The three high-tier units are the corpus's two conflict units and
its dependency-change unit, the three the design marks hardest. No signal fired on oracle information.

**Why low never occurred.** S8 ("an assumption, open question or known issue in the report") fired on all 12 units.
The brief asks agents to record open questions, and every agent did. A signal that every careful agent triggers
cannot select. It is the main calibration defect of policy 1.0.0, found by the pilot, not by hindsight on outcomes.

## 3. Reliability: E against D

| Measure | D (always full) | E (adaptive) |
|---|---|---|
| Units accepted (hidden oracle) | 12/12 | 12/12 |
| First-pass accepted | 12/12 | 12/12 |
| Gate rejections | 0/12 | 0/12 |
| Consequential errors | 0 | 0 |
| Conflicts surfaced; premises rejected | 2/2; 3/3 | 2/2; 3/3 |

**Noninferiority (H4, margin δ = 5 points) is not established, and cannot be.**

- Both arms have 0 failures in 12 units.
- The preregistered power rule says a noninferiority claim needs at least 10 failures in D or E.
- With zero events, the data are compatible with anything from "E is as good as D" to "E fails on up to about 22% of
  units more often". That figure is the 95% upper bound for 12 units with 0 events, and it sets no bound on the
  difference.

## 4. Cost: E against D

| Measure | D | E | E − D |
|---|---|---|---|
| Agent cost (cli-estimate, A1) | $6.99 | $7.26 | **+$0.27 (+3.8%; exploratory −17.6% to +24.1%)** |
| Cost per accepted requirement | $0.259 | $0.269 | +3.8% |
| Gate host CPU, total | 1,313 s | 1,186 s | −9.7% |
| Gate host CPU per unit at the medium tier | — | 106.6 s | about −3% vs D's 109.5 s |
| Repair turns | 0 | 0 | 0 |
| Praxis protocol commands in the agent loop | yes | no | — |
| Verified state | yes | no | — |

**Cost per unit at E's high tier** was $1.93 over 3 units, against D's $2.18 for the same positions. At the medium
tier it was $5.33 over 9 units, against D's $4.82.

**Why adaptive enforcement saved nothing:**

1. **The gate is not where the cost is.**
   - D's gate is host CPU (about 110 s per unit, mostly build, tests and `archcheck`), not model tokens.
   - Dropping two cheap checks at the medium tier saved 3% of host time and $0 of model cost.
   - The policy could only save model cost through avoided repair rounds. There were none in either arm, because
     no gate ever rejected.
2. **E's agent-side controls equal C's**, and C cost the same as B. So E's extra cost over D is not explained by
   controls. It is within the task-level noise of one chain (E's agent made 123 tool calls against D's 107, and wrote
   6% more output).
3. **D's extra cost over B is about +13%**, mostly the Praxis protocol and scaffold (§ `PILOT-RESULTS.md` 2.2).
   Adaptive *gating* does not touch that cost. Only adaptive *protocol* use, such as skipping Praxis on low-risk
   units, could. Policy 1.0.0 did not vary the protocol, by design.

## 5. Marginal verification value (Phase H)

**Definition.** Marginal value = (consequential errors prevented or detected) ÷ (additional verification cost).

| Optimization or control | Additional cost (pilot) | Errors prevented or detected | Marginal value |
|---|---|---|---|
| Full gate every unit (D vs C-level agent) | +$0.84 agent (D − C) + 1,313 s host | 0 | 0 per $ (undefined benefit at ceiling) |
| Risk-triggered gate (E vs D) | +$0.27 agent, −127 s host | 0 vs 0 | — |
| Verified-state persistence (D, F) | Included in D; F's restarts +$0.38 each | 0; plus 1 false-positive entry (the instrument defect) | negative on this evidence |
| In-loop `archcheck` (C vs B) | −$0.05 agent, about 63 s host per unit | 0 | — |
| Ordo admission | Included in C | 0 architectural; it named 2 decision conflicts that A and B also caught | — |

**What was not tested.** Reusing validated decisions, incremental or AST-scoped architecture checks, changed-boundary
and dependency-aware verification, cached validation results, and batched verification were not separately
implemented in P1. The pilot shows where they *could* matter:

- Host gate time is about 110 s per unit, of which `archcheck` is about 25 s and `dotnet test` about 30–60 s under
  contention. Incremental and cached checks would cut host time, not model cost.
- Their reliability value cannot be measured until a corpus produces failures.

## 6. Classification

| Question | Answer | Class |
|---|---|---|
| Is adaptive enforcement noninferior to always-on enforcement? | Not established (0 failures in both arms) | **Inconclusive** |
| Does it cost less? | No measurable saving (+3.8% agent cost, −10% host time) | **Inconclusive**, leaning *contradicted* for this policy version |
| Is the policy hindsight-free and auditable? | Yes | **Demonstrated** (design property, inspected) |
| Does it escalate the hard units? | It escalated exactly the two conflict units and the dependency change | Supported but preliminary (n = 1 chain) |

**Recommendation.** See `RECOMMENDATIONS.md`: do **not** ship adaptive gating as an Ordo or Praxis feature on this
evidence. Its cost lever is wrong (host CPU, not tokens). If pursued, retarget it at the protocol, keeping verification
fixed, and remove S8 as an escalation signal.
