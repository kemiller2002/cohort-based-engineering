# Outline 3: "The unclaimed layer: independent verification of agent-built software" (positioning paper)

- **Type:** Commercial positioning paper. Internal first; external only after the prerequisites below.
- **Status:** OUTLINE ONLY. Not cleared for publication.
- **Prerequisites:**
  - FX-10 (buyer interviews).
  - IM-03/IM-05 shipped, so Echelon uses its own verified completion.
  - G-F-10 resolved: either locate evidence for the site's outcome claims or remove them.

**Evidence classes:**

| Class | Meaning |
|---|---|
| VERIFIED+IV | Reproduced by the track and by an independent verification track |
| VERIFIED | Reproduced by the track only |
| SUPPORTED | Based on documents or code reading |
| INCONCLUSIVE | Evidence does not settle it |
| NOT TESTED | No one tested it |
| ESTIMATE | A modelled number |

For market claims, G's own labels are kept: "documented" (a source says so) vs "inferred" (G's reasoning). Claims marked **[DO NOT STATE]** are tempting framings the evidence does not support.

## Thesis

Agent orchestration, spec-driven development and AI cost dashboards are already bundled or crowded. The open position, if it holds, is a verifier that is independent of the implementing agent and signs completion against requirement IDs and a revision.

## 1. What buyers already get

- Agent orchestration and baseline governance come bundled in existing seats: Copilot Business/Enterprise, Kiro Teams, Foundry and AgentCore. **VERIFIED** (documented), G-F-01. Several features are in preview.
- Spec-driven development is mainstream (Kiro). **VERIFIED** (documented), G-F-02.
  - The narrower claim is that Kiro's docs do not describe requirement-ID preservation through to a verification manifest. That rests on one docs page. **INFERRED**.
- AI cost and adoption measurement is a priced, crowded category. **VERIFIED** (documented), G-F-03.

## 2. The problem is real for developers

- There is a developer trust gap with AI output (Stack Overflow 2025/2026, DORA 2025). **SUPPORTED** (documented), G-F-04. The surveys are self-selected.
- Executives lack evidence of payoff, and agentic project cancellations are forecast. **SUPPORTED** (documented), G-F-05. The Gartner figure is a prediction, not a measurement.
- **[DO NOT STATE]** that buyers will pay a third party for verification. **NOT TESTED** (FX-10).

## 3. Why independence matters: our own evidence

- Self-produced evidence can be forged:
  - REL-001 GATE-3 (non-attested mode, documented).
  - Indy-init's acceptance verifier ACCEPTED a fabricated bundle when the producer supplied the pin. **VERIFIED**, E-F-02.
- An attested, key-bound verifier refused every forgery in the 17-case regression. **VERIFIED**, E-F-06.
- This is the core technical argument, and it is Echelon's own data. It is a strength only if Section 4 is fixed first.

## 4. Honesty gate: where Echelon stands today

- Verified completion is implemented but enabled nowhere. **VERIFIED+IV**, G-F-07 / V1, and E-F-01.
- No rehearsal reached governed acceptance. **SUPPORTED**, B-F-01; G-F-11 CONTRADICTED the "ready for outcome delivery" hypothesis.
- Echelon's process overhead costs 35% or more extra tokens without a measured quality gain on current fixtures. **VERIFIED+IV**, G-F-08 / V1, with ceiling and output-lower-bound caveats.
- The public site makes outcome claims with no located evidence. Track G rated this **INCONCLUSIVE**; V1 rated it **VERIFIED** as "no evidence located" (G-F-10 / V1).
  - V1 adds that the 40% figure contradicts the site's own case study, and that both figures are consulting-engagement outcomes, not software measurements. Their truth is NOT TESTED.
- **[DO NOT STATE]** "production-proven verified completion", or any throughput or cost-reduction figure for clients.

## 5. Positioning options (inferred; for discussion)

- An agent-agnostic evidence layer over Claude Code, Copilot and Codex rather than another agent. **SUPPORTED**/inferred, G-F-12.
- An independent definition of done as a service or engagement instrument, using cost per accepted requirement as the unit. **INCONCLUSIVE**, G-F-09 and G-F-03.
  - The unit needs a definition of "accepted" that survives E-F-02 (matrix X-13).
- Regulation is not a 2026 urgency trigger. **SUPPORTED** (documented dates), G-F-06; applicability is inferred, not legal advice.

## 6. Platform risk

- Anthropic or GitHub could add independent completion verification. Track this. **INFERRED**, G-F-12.

## 7. Limits (mandatory)

- Vendor absence is inferred from marketing pages (weak evidence).
- Supply-chain attestation tooling (SLSA, in-toto) was not surveyed.
- No buyer interviews.
- One model family in the experiments.
