# Commercial models: scored comparison

Track G-market, worker G-001. As of 2026-11-08. Source IDs (S-NNN) refer to `sources.jsonl`, finding IDs
(G-F-NN) to `findings.json`.

**Read this first.** The scores are the analyst's judgement applied to the evidence listed. They are not
measurements. No customer interview, price test or willingness-to-pay data exists for any Echelon offering
(Mercatus CEX-01..08 are defined but not run), so every revenue-related input below is an **assumption to test**,
not a finding.

## Models compared

| ID | Model | What is sold | Primary buyer |
|---|---|---|---|
| 1a | Consulting: **AI-assisted engineering evidence diagnostic** (Mercatus PGS-F05 / F03 / F02) | Fixed-scope, fixed-fee engagement. Echelon measures how a team's coding agents actually perform on its own work (cost per accepted change, rework, overclaimed completion, requirement loss, stability effects) and configures the governance the client already owns (Copilot control plane, Kiro specs, CI gates). Output is a decision packet: scale / constrain / stop, plus an operating model | VP/Director of Engineering or CTO; finance co-sponsor for AI spend |
| 1b | Consulting: **independent verification / second opinion on agent-built software** (PGS-F04) | Assurance-style review of an agent-delivered change set or system against its requirements, with an evidence packet | CTO, risk/compliance, investor/acquirer doing diligence |
| 2 | **Licensed Echelon platform** (Praxis, Ordo, Dokimos, Conditor etc.) | Software subscription for self-run governed agent delivery | Platform engineering / developer productivity lead |
| 3 | **Managed software factory / outcome-based delivery** | Echelon delivers accepted software increments using its agent system, priced per accepted requirement or milestone | Product/business owner who wants delivered software |

## Criteria and weights

| Criterion | Weight | What 5 means |
|---|---|---|
| Evidence readiness | 25 | Echelon's own repositories and experiments already support the core claim (G-F-07, G-F-08, G-F-11) |
| Differentiation vs bundled incumbents | 20 | Not substitutable by features buyers already get in Copilot / Kiro / Swarmia / LinearB (G-F-01..03) |
| Time to first revenue | 15 | Sellable within weeks with current assets |
| Delivery and liability risk (inverted) | 10 | Low risk of failing a commitment or of an overclaim |
| Gross margin potential | 10 | High margin at steady state |
| Scalability beyond founder time | 10 | Revenue not bound to the founder's hours |
| Learning value toward productization | 10 | Each sale produces evidence that de-risks a later product |

## Scores (1–5)

| Criterion (weight) | 1a Diagnostic | 1b Verification review | 2 License | 3 Managed factory |
|---|---|---|---|---|
| Evidence readiness (25) | **4**: EDF method, VAC-001 and ARCH-002 results, and Praxis/Dokimos usable as internal instruments without being sold as proven | 2: the attested verifier is not enabled anywhere yet (G-F-07); a review would rest on human judgement plus tools | 1: B4 integration was not connected; verified completion is off; telemetry gaps (G-F-07) | 1: R2 acceptance is invalid under the ledger contract and R3 was NOT ACCEPTED (G-F-11) |
| Differentiation (20) | 3: SIs and DX/LinearB/Jellyfish consultants offer AI-impact assessments; Echelon's edge is the unit (cost per *accepted* requirement) and experimental discipline | **4**: independence from the agent vendor appears unoccupied (G-F-09, INCONCLUSIVE) | 2: the overlap with bundled Copilot/Kiro/AgentCore features is large (G-F-01, G-F-02) | 3: Devin, Factory and SIs compete; evidence of done would differentiate if it worked |
| Time to first revenue (15) | **4** | 3 | 1 | 2 |
| Risk, inverted (10) | **4**: fixed scope, advisory output | 2: assurance language creates liability if the verifier misses a defect | 2: support burden, and security reviews (SOC 2 etc.) needed before enterprise sale | 1: commits to outcomes Echelon has not yet delivered reliably |
| Margin (10) | 3 | 3 | **4** | 2: delivery-time variance is unknown (R2 took 721 min against a 420-min ceiling) |
| Scalability (10) | 2 | 3 | **5** | 3 |
| Learning value (10) | **5**: every engagement yields real-world task data, buyer objections and price signals | 4 | 3 | 4 |
| **Weighted total** | **3.60** | 2.95 | 2.20 | 2.15 |

Sensitivity: 1a stays first unless evidence readiness is weighted below 10 *and* scalability above 30. Model 2 overtakes
1a only once verified completion is enabled and replicated outside Echelon (raising its evidence score to at least 3)
**and** the overlap with incumbents is shown to be small (differentiation of at least 4).

## Explicit assumptions (each untested unless noted)

1. **A1. Budget exists for third-party AI-engineering assessment.** It is inferred from documented executive
   uncertainty about AI value (G-F-05) and developer distrust (G-F-04). Echelon has no direct evidence that buyers pay
   for it.
2. **A2. Buyers accept "cost per accepted requirement" as a meaningful unit.** Inferred. Measurement vendors sell
   adoption, activity and PR throughput instead (S-014, S-015, S-017). Test: V2 in evidence-gaps.md.
3. **A3. Echelon tooling can be used inside a client repository without the full Echelon stack.** Plausible because
   Praxis is plain-file and installable by Conditor. Not tested in a non-Echelon repository.
4. **A4. Price.** No price is asserted. Comparable reference points exist only for software, not services: Swarmia
   $45–55, LinearB $29–59 and CodeRabbit $24–90 per developer per month (S-014, S-015, S-027). A diagnostic price must
   be discovered by experiment V3, not assumed.
5. **A5. Model compute is not the binding cost.** Measured internally at $0.11–0.16 per correct requirement on
   fixtures (S-043). This supports pricing on assurance or outcomes rather than on compute pass-through. Fixtures
   understate real work.
6. **A6. Founder capacity is the constraint for 1a.** The model accepts this deliberately, because 1a is a learning
   vehicle and not the end state.
7. **A7. Regulatory urgency is low in 2026** (G-F-06), so the lead trigger is cost, quality or stability pain, not
   compliance.

## Consulting-to-product pathway

1. **Diagnostic (1a)**, using Echelon tools as instruments and not as deliverables. Collect real task data,
   objections and repeated analysis steps.
2. **Repeatable assessment kit:** the scripts, telemetry ingestion and report templates the diagnostic reuses.
   These become a productized fixed-price offering.
3. **Verification review (1b),** once verified completion is enabled in at least one Echelon repository and its catch
   rate against an independent human reviewer has been measured (V4).
4. **Licensed verifier, narrow scope:** an independent completion-verification service that plugs into the PR
   checks of GitHub, Kiro and other agent platforms (G-F-09, G-F-12). It is not a whole platform.
5. **Managed delivery (3)** only after at least two consecutive accepted rehearsals inside the time ceiling, with
   computed rather than self-declared verdicts.

The Mercatus portfolio scenarios already describe step 1 as "diagnostic front door" (PGS-F01) and
"diagnostic → controlled experiment → evidence → decision → operating model" (PGS-F05). This analysis keeps that
direction. What is new is the competitive evidence that steps 2 and 4 must avoid features that incumbents bundle
(G-F-01..03), and the internal evidence that steps 3 and 5 are blocked today (G-F-07, G-F-11).
