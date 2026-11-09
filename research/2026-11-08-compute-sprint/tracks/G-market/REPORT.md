# Track G: Commercial research report

**Worker:** G-001 (Market and Competitive Research). **Compiled by:** RD-000 from G-001's committed outputs and its final hand-back. The harness refused G-001's own write of this file ("subagents should return findings as text"), so the Director assembled it. Nothing here goes beyond what G-001's files state.
**As of:** 2026-11-08. **Final worker commit:** `825963b`. **Measured agent cost:** 203,767 subagent tokens, 91 tool uses, 11.6 min wall clock (runtime-reported).

Sources: [sources.jsonl](sources.jsonl) (46 entries, URL and retrieval time each) · Competitors: [competitors.json](competitors.json) (19 vendors) · Findings: [findings.json](findings.json) (13) · [commercial-models.md](commercial-models.md) · [evidence-gaps.md](evidence-gaps.md)

## Method

Primary-source web research (vendor pricing and product pages, official docs, published surveys), read alongside the Mercatus 2026-09-23 portfolio research and Echelon's own experiment record in cohort-based-engineering. **Documented** demand (cited) is kept separate from **inferred** demand. No customer interviews, market-size estimates for Echelon or willingness-to-pay figures were produced, because none exist.

## Findings

| ID | Class | Finding |
|---|---|---|
| G-F-01 | VERIFIED | Agent orchestration plus baseline governance now comes bundled with existing seats: Copilot Business/Enterprise ($19/$39) includes Agent HQ (third-party agents), an access control plane with audit logging, and Code Quality. Kiro Teams costs $20/seat |
| G-F-02 | VERIFIED | Writing requirements before code is mainstream (Kiro generates requirements, design and tasks documents). Kiro's documentation does not describe keeping stable requirement IDs through to a deterministic verification manifest; that is the remaining gap |
| G-F-03 | VERIFIED | AI adoption, cost and impact measurement is a crowded, priced category: Swarmia ($5/dev add-on), LinearB ($29–59/user), Jellyfish token-spend monitoring, Atlassian–DX |
| G-F-04 | SUPPORTED | Developers report a trust gap with AI output: Stack Overflow 2025 found 46% distrust AI accuracy and 66% call its answers "almost right"; DORA 2025 links AI adoption to lower delivery stability |
| G-F-05 | SUPPORTED | Executives lack evidence of AI payoff (McKinsey 2025, secondary coverage). Gartner forecasts that more than 40% of agentic AI projects will be cancelled by end of 2027 |
| G-F-06 | SUPPORTED | Regulation is not a 2026 urgency trigger: the EU AI Act Digital Omnibus moved high-risk obligations to Dec 2027 and Aug 2028 |
| G-F-07 | VERIFIED | Echelon's flagship differentiator, verified completion, is implemented in Praxis 3.25.0 but enabled in no Echelon repository (owner decision OD-9 on the verifier key is still open) |
| G-F-08 | VERIFIED* | In Echelon's own REL-001 run-02, every arm scored 39/39 correct. Optimized Echelon cost $0.1555 per correct requirement against $0.1147 for a bare agent (+35.5%), with no measured quality gain on current fixtures |
| G-F-09 | INCONCLUSIVE | No vendor reviewed describes a verifier, independent of the implementing agent, that signs a completion receipt tied to requirement IDs and a revision |
| G-F-10 | INCONCLUSIVE | The public echelon-foundry site claims "40%+ throughput" and "80% reconciliation reduction"; no evidence for either was located |
| G-F-11 | CONTRADICTED | The hypothesis that Echelon can sell outcome-based delivery now is contradicted by its rehearsal record: R2's acceptance is invalid under the ledger contract and R3 was NOT ACCEPTED |
| G-F-12 | SUPPORTED | Coding-agent use is concentrating on Claude Code (66%) and Copilot (59%) (Stack Overflow 2026), so Echelon should position itself as an agent-agnostic evidence layer |
| G-F-13 | SUPPORTED | Gartner forecasts $576.5B in 2026 AI services spending. The figure shows the budget category exists but implies nothing about Echelon's addressable market |

\*G-F-08 restates an internal experiment result; Track D's independent recomputation is the verification of record (see FINDINGS.md).

## Commercial models (weighted score out of 5; judgement, not measurement)

| Model | Score |
|---|---|
| 1a. Consulting: AI-assisted engineering evidence diagnostic | **3.60** |
| 1b. Consulting: independent verification review | 2.95 |
| 2. Licensed Echelon platform | 2.20 |
| 3. Managed software factory / outcome-based delivery | 2.15 |

Weights, assumptions and sensitivity are in commercial-models.md. 1a stays first unless evidence readiness is weighted below 10% *and* scalability above 30%.

## Recommendation

**What to sell first:** a fixed-scope **AI-assisted engineering evidence diagnostic**. It is aimed at engineering leaders already paying for Copilot, Claude Code or Cursor, and measures cost per *accepted* change, overclaimed completion and requirement loss on the client's own work. It also configures the governance tools the client already owns. Echelon's systems are used as instruments inside the engagement, not sold as a product.

**Defer:** licensing the platform, and managed or outcome-based delivery.

**Possible later product:** a narrow, independent completion verifier, pursued only if experiment V4 shows it catches overclaims that agent self-review misses.

## Evidence still needed

These are preregistered, with criteria, in evidence-gaps.md:

| ID | Experiment |
|---|---|
| V1 | 12–15 buyer problem interviews |
| V2 | Positioning message test |
| V3 | Concierge paid diagnostic at two price cells (signal: at least 2 of 10 pay) |
| V4 | Enable verified completion and measure its catch rate (blocked on OD-9) |
| V5 | Head-to-head against Copilot's controls and Kiro specs using Track D's harness |
| V6 | Install the tools outside Echelon |
| V7 | Trace or withdraw the public site's claims |

## Limitations

- McKinsey, Gartner and EU Official Journal pages could not be fetched directly, so those figures are SUPPORTED rather than VERIFIED.
- Vendor capabilities come from vendor pages, not hands-on comparison.
- All scores are analyst judgement.
