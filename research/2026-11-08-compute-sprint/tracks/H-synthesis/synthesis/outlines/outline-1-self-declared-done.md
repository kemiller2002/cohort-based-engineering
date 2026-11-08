# Outline 1: "Done, according to whom? Eleven agent-built rehearsals and the verification gap"

- **Type:** Long-form engineering blog post or technical report.
- **Status:** OUTLINE ONLY. Not cleared for publication.
- **Prerequisites before drafting:**
  - V2 has independently verified E-F-01, E-F-02 and B-F-01.
  - The owner has made a disclosure decision on unfixed bypasses (DS-E-BYPASS caveat).
  - The owner has made a visibility decision on private rehearsal repositories (datasets.json globalCaveats).

**Evidence classes:**

| Class | Meaning |
|---|---|
| VERIFIED+IV | Reproduced by the track and by an independent verification track |
| VERIFIED | Reproduced by the track only |
| SUPPORTED | Based on documents or code reading |
| INCONCLUSIVE | Evidence does not settle it |
| NOT TESTED | No one tested it |
| ESTIMATE | A modelled number |

Each claim carries its class and finding ID. Claims marked **[DO NOT STATE]** are tempting framings the evidence does not support.

## Thesis (one sentence)

Across eleven governed, agent-built rehearsals, the recurring failure was not that agents could not write code. It was that "done" was declared by the party doing the work, and the mechanisms meant to check it were either switched off or fed by the producer.

## 1. Setup

- What a rehearsal is: a 420-minute timed build of the same application family, with frozen requirements and a computed acceptance verdict from R4 onward. Source: B REPORT §2. *(descriptive)*
- Caveat up front: rehearsals differ in scope, topology, stack and T0 definition, so this is not a trend analysis. **SUPPORTED**, B-F-10, B-F-15; matrix X-15.

## 2. The outcome record

- No run from R1 to the Causa build reached acceptance under Indy-init's computed verdict. **VERIFIED+IV**, B-F-01 / V2.
  - Mandatory wording (V2): 5 runs produced a non-accepting computed verdict, and 6 produced none. R1 passed its own frozen criteria, before the contract existed. R5 came closest (G0–G7 PASS, INCOMPLETE).
- R2's self-declared ACCEPTED is not acceptable under the program's own verifier. **VERIFIED+IV**, B-F-02 / V2.
  - Say "not acceptable", not "INVALID". The INVALID label comes mostly from applying a later schema; the substantive reason is a P0 requirement recorded NOT_RUN while the ledger declared accepted=true.
- R1 treated RC2–RC5 as Accepted for about 2.5 hours while its own deploy/accept workflow was red. Four consecutive failures are in the Actions record. **VERIFIED**, B-F-16. V2 pending.
- **[DO NOT STATE]** "Things improved over time." No controlled evidence exists. **INCONCLUSIVE**, B-F-15.

## 3. Over-claim moves rather than disappears

- After the computed verdict arrived (R4), no run claimed acceptance against its verifier. **SUPPORTED**, B-F-04. Attribution to the verdict alone is not established.
- Over-claim reappeared at the evidence layer: in R5, 13 of 22 spot-checked passing obligations were over-tagged. **SUPPORTED**, B-F-04.

## 4. The checker trusts the producer

- Indy-init's verdict tool returned ACCEPTED for a README-only repository with 118 fabricated PASS artifacts. The reason: in rehearsal-005, the "independent" manifest digest is printed by the candidate's own tool in the same job. **VERIFIED+IV** (local fixture), E-F-02 / V2, which also ran it at the verifier ref rehearsal-005 pinned.
  - Untested: whether rehearsal-005's second check, `verify-plan`, would catch it. **NOT TESTED**; FX-03.
- Framing to use: the computed verdict changed behaviour, but it was never an independent control. Matrix X-05.
- **[DO NOT STATE]** "Acceptance became verified in R4."

## 5. "Complete" is self-declared everywhere

- Plain `praxis work complete` accepted `/etc/hostname` as test evidence. 0 of 45 (E) or 47 (V2) surveyed ros.json files enable verified completion. **VERIFIED+IV**, E-F-01 / V2.
  - Corroborated by Praxis's own rollout doc and an independent scan of 90 config files. **VERIFIED+IV**, G-F-07 / V1.
- Part of the reason is version skew: 23 repositories pin Praxis 3.7.2, which predates attested completion (3.20.0). **SUPPORTED**, C-F-02. The capability-to-version mapping was not re-executed.

## 6. The good news: the attested path works

- Praxis 3.25.0 with Dokimos 0.11.1 in attested mode refused every forgery in the 17-case regression. Evidence from revision A cannot be cited at revision B. **VERIFIED**, E-F-06. V2 pending.
- Remaining local-state gaps: deleting the claim store (E-F-03), moving local refs (E-F-04, a documented limit), and zero-evidence unattested "verified" (E-F-05). All **VERIFIED** in local fixtures.
- Deployment preconditions are missing: no branch protection and no ruleset on praxis, ordo and Indy-init `main`, and no CODEOWNERS (**VERIFIED+IV**, V2). The agent credential is reportedly admin (**SUPPORTED**, from the R7 audit). E-F-07.

## 6b. Governance was the first point of failure, not the only one

- From R8 onward, governance or verification machinery was the first refusal that ended the governed verdict. **VERIFIED+IV** in that narrow sense, B-F-03 / V2 PARTIALLY VERIFIED.
- Even without it, R8 had 346/613 P0 obligations not run, and R9 implemented 0/541 executable obligations (V2).
- **[DO NOT STATE]** "the runs failed because of governance" (matrix X-23).
- **Retrospective test of a pre-T0 dry run.**
  - Mechanical checks catch 4/8 of the brief's blockers, robustly 2/8 (**SUPPORTED**, B2-F-01). They run in seconds (**VERIFIED**, B2-F-10).
  - Semantic checks catch R8's two semantic blockers (**VERIFIED**, B3-F-01/F-02; answer-informed).
  - An existing tool, spec-preflight, already did this after R8 (**VERIFIED**, B4-F-01). Indy-init CI ran it with the key option off (**VERIFIED**, B4-F-05).
  - **[DO NOT STATE]** that these checks would catch the next package's defects. Prospective generality is **NOT TESTED** (B4-F-07; FX-14).
- **Theme to close on.** The pattern is "built but not adopted" (matrix X-26): verified completion, range qualification, Limen contracts and spec-preflight options were all available and unused. **Corroborated across six tracks.**

## 7. What we are changing (proposals, not results)

| Proposal | Status |
|---|---|
| Trusted acceptance job outside the candidate repository | Proposed. ADR-S03 |
| Mandatory pre-T0 governance dry run | Proposed. ADR-S04; B2 replay pending |
| Enable attested completion where acceptance depends on it; close the cheap gaps | Proposed. IM-03, IM-05 |

- **[DO NOT STATE]** that any of these fixes works. All are **NOT TESTED**.

## 8. Limits section (mandatory)

- One application family, one owner, one model family.
- B's event curation was done by a single analyst (FX-08).
- E's bypasses ran in local fixtures only, with no GitHub-side test.
- Rulesets: V2 found none on the three core repositories. Others (conditor, causa) were not queryable.

## Figures (candidates)

- Table: per-run verdict and basis, from rehearsal-summary.csv (with its unit column kept).
- Diagram: who produces vs who checks evidence in rehearsal-005's acceptance job.
- Bypass matrix: refused vs succeeded, after fixes ship only.
