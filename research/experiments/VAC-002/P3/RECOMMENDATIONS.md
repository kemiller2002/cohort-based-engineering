# VAC-002-P3 recommendations

**Rule** (the mission's §12).

- **Adopt** only where the experiment demonstrates a benefit, or where another independently justified requirement
  supports adoption.
- **Executable authorization** needs evidence of prevented errors, not passing checker tests.
- **Nothing is promoted to a production default** because it was tested here.
- **Requirements go to each repository's Praxis intake** (`.praxis/inbox/documents/`). No GitHub issues are created.

Evidence classes are those of `PREREGISTRATION.md` §9.

## 1. The five candidates

| | Candidate | What P3 found | Evidence class | Decision |
|---|---|---|---|---|
| **A** | **Authority section in the Praxis agent contract** (the four-sentence contract) | Stage 2: 3/18 against 7/18 without it, risk difference −0.22, p = 0.125, every discordant block in its favour. Discovery: 1/15 against 11/15 on the incidental corpus. Cost +6% per execution. Cheapest per accepted requirement of all five arms ($0.158) | Benefit **preliminary** (confirmatory test inconclusive; exploratory evidence strong). Cost **demonstrated** | **Adopt, on an independent justification.** CBE principle 3 already requires that agents "never invent unresolved business policy"; the contract states that requirement to the agent at a measured cost of +6%. It is adopted as a statement of existing policy, **not** as a demonstrated reliability control. Its prevention effect needs a powered confirmation (§3) |
| **B** | Lightweight decision checklist (three questions, on top of the contract) | Identical to the contract alone in all 18 blocks (0 discordant); +2% cost over B; P2 also found no measurable value | **Inconclusive** (no added value observed, twice) | **Do not adopt.** Its incremental value is unshown, and it adds report fields and tokens |
| **C** | Typed Ordo decision records (schema 0.2), unchecked | Identical to the contract alone in all 18 blocks; +15% cost over B (+22% over A) | **Inconclusive** for prevention | **Do not adopt as a prevention control. Defer** as documentation: records were informative to readers in P2, but that is not what P3 measured |
| **D** | Executable authorization (contract v0.2 admission and gate) | 7/18, the same as no controls and worse than B in all 4 discordant blocks. 0 unauthorized decisions prevented, detected or corrected. 10 / 10 rejected decisions were authorized or harmless; 4 led to harm (3 unauthorized code defaults, 1 crash). +67% cost over B; median wall time 2× | Prevention **contradicted** in direction (not significant). Control-induced harm **demonstrated** as a mechanism, **preliminary** as a rate. Cost **demonstrated** | **Do not adopt; remove from any default.** Requires the redesign in R-ADM-1..3 and a new test showing errors prevented before reconsideration |
| **E** | Independent review | The blinded review (post hoc, not a gate) agreed with the oracle on every confirmed error, including all 15 C06 errors that no agent-side control prevented. It found 2 consequential problems the oracle had no probe for (C01-E-r3, D17-r2) and rejected 3 oracle flags with stated reasons (D01 ×2, C03-E-r3). About $0.31 per item for two reviewers | Detection of incidental code-reuse errors **demonstrated** on this corpus (post hoc). Value as a gate **not tested** in P3. P2's adaptive gate over-blocked | **Further testing.** Review detects what every agent-side control missed when the authority question is embedded in reused code. Test it as a targeted, non-blocking provenance review routed to owners (R-REV-1) |

## 2. Requirements

| ID | System | Requirement | Evidence | Class |
|---|---|---|---|---|
| **R-PRAX-1** | Praxis | Add the four-sentence authority contract (`AUTHORITY-CONTRACT.md`) to the standard agent brief for implementation work, worded as frozen. Measure it in Praxis telemetry as a contract version | Candidate A | **Adopt** (justified by CBE principle 3; benefit preliminary) |
| **R-ADM-1** | Ordo / contract | "Refuse the uncovered case and record the question" must be an authorized outcome that needs no authority source. A recorded question must never be rejected | C03-E-r1, C04-E-r1/r3: rejecting a recorded question led to an unauthorized code default | **Implement before any further test of executable authorization** (an established defect) |
| **R-ADM-2** | Ordo / contract | Rule A5 (no self-citation) must not reject a decision that refuses or defers by citing the agent's own unresolved question | C03-E-r3: a correct refusal was rejected at the gate and repaired into a crash | **Implement before any further test** (an established defect) |
| **R-ADM-3** | Ordo / contract | Rule A6 must not apply to presentation choices (ordering, wording) or to keeping accepted behaviour unchanged | C01 ×3 (tie-break), C02 ×2 (keeping the invoice due date): 5 false rejections | **Implement before any further test** (an established defect) |
| **R-PROV-1** | Dokimos (and Ordo construction) | **Rule provenance audit.** Every business-rule function, constant or branch in a rules module traces to an accepted decision record or requirement. An untraceable exemption, default or superseded rule is flagged before new work reuses it, and reported to the owner, not silently fixed | The dominant failure in P3. **Every one of the 36 confirmed unauthorized decisions** across all stages reused a rule embedded in existing code without a source: D03, D17, D18, D19, D21, C03, C04, C05, C06. C06's exemption beat every arm, including the contract, the checklist, records and the checker | **Additional experiment required** (highest priority) |
| **R-REV-1** | Dokimos / CBE | A targeted independent review asking one question of a change: which existing rules does it reuse, and what is each one's source? Findings go to owners, not as blocking gates | Candidate E; P2's blocking review over-blocked | **Additional experiment required** |
| **R-EXP-1** | CBE research | A powered confirmation of H1. On the observed confirmatory baseline (0.39), the frozen sizing simulation gives **28 blocks at p_B = 0.10 and 39 at p_B = 0.17** (arms A and B only, power 0.80). That costs about $1.15 per block including double review, so roughly $35–45. The simulation assumes a proportional effect in every scenario, which is optimistic where a scenario defeats both arms. A wider mechanism sample than six scenarios is needed, because one scenario (C06) carried all arms' residual errors | `STATISTICAL-ANALYSIS.md` §8.1, §8.3 | **Additional experiment required** (needs a new budget authorization) |
| **R-EXP-2** | CBE research | A long-horizon test of the contract. The same agent continues across a chain of work items in which earlier items introduce untraceable rules that later items reuse | P3 used fresh agents only, by design (mission §7) | **Additional experiment required** |
| **R-EXP-3** | CBE research | Corpus guidance. Announced temptations (notes, handoffs, proposals) no longer discriminate on this model, with 1/40 errors without any instruction. Future corpora should embed the authority question in reused code and data | `DISCOVERY-RESULTS.md` | **Implement now** (in corpus design) |

## 3. What should be deferred or removed

- **Remove** executable authorization (contract v0.2 as implemented) from any default path, until R-ADM-1..3 are
  fixed and a new test shows prevented errors.
- **Do not adopt** the decision checklist.
- **Defer** typed decision records as a prevention control.
- **Defer** blocking independent review. P3 measured only post-hoc review.

## 4. Praxis intake written

| Repository | File | Content |
|---|---|---|
| cohort-based-engineering | `.praxis/inbox/documents/2026-10-23-VAC-002-P3-01-authority-contract-results.md` | Results; R-PRAX-1 rationale; R-EXP-1..3 |
| cohort-based-engineering | `.praxis/inbox/documents/2026-10-23-VAC-002-P3-02-executable-authorization-harms.md` | Candidate D; R-ADM-1..3 |
| cohort-based-engineering | `.praxis/inbox/documents/2026-10-23-VAC-002-P3-03-rule-provenance.md` | R-PROV-1 and R-REV-1 |

**Praxis, Ordo and Dokimos.** Their intake documents are written in this repository under
`.praxis/inbox/documents/` and addressed to those owners. Those repositories were not attached to this session,
whose GitHub scope covered cohort-based-engineering only. The documents state their target repository, so they can
be moved there unchanged.
