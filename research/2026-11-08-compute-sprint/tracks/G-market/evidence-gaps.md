# Evidence gaps and validation experiments

Track G-market. As of 2026-11-08. Each gap names what would close it. Experiments are designed so that they can
fail. **Nothing here has been run.**

## A. Demand and buyer evidence (none exists for Echelon)

| Gap | Why it matters | Status |
|---|---|---|
| G1. No buyer conversations recorded for any Echelon offering | Every demand statement in REPORT.md is either documented for a *population* (surveys) or inferred | NOT TESTED |
| G2. No willingness-to-pay or price signal | The diagnostic price is unknown. Commercial-models A4 refuses to assume one | NOT TESTED |
| G3. Unknown which buyer role owns the problem: VP Engineering (quality and stability), CFO/finance (AI spend), or risk/compliance (governance) | It determines message, channel and proof asset | NOT TESTED |
| G4. Unknown whether buyers distinguish "independent verification" from the self-review and audit logs they already get (Copilot, CodeRabbit) | G-F-09 rests on this | INCONCLUSIVE |
| G5. Mercatus 2026-09-23 findings 2–6 still have no citations | They should not be relied on until sourced | Open |

## B. Product and capability evidence

| Gap | Why it matters | Status |
|---|---|---|
| G6. Verified completion is not enabled in any Echelon repository; the verifier key decision (OD-9) is open | No assurance claim can be made until it runs (G-F-07) | Blocked on owner |
| G7. No measured catch rate for the independent verifier compared with a human reviewer or with agent self-review | This is the core of the 1b and licensed-verifier value proposition | NOT TESTED |
| G8. No quality advantage shown above ceiling; Echelon adds cost on current fixtures (G-F-08) | Without it, the product pitch is only about cost and process | NOT TESTED (Track D scope) |
| G9. Echelon tooling has not been installed or used in a non-Echelon, client-like repository | Assumption A3 in commercial-models.md | NOT TESTED |
| G10. No hands-on comparison with GitHub Agent HQ's control plane, Kiro specs or Code Quality on the same task | The differentiation scores rest on vendor pages | NOT TESTED |
| G11. Public site outcome claims ("40%+ throughput", "80% reconciliation") have no located evidence packet (G-F-10) | Credibility risk for an evidence-first brand | INCONCLUSIVE |

## C. Market and compliance facts not confirmed from primary sources

| Gap | Current classification |
|---|---|
| McKinsey State of AI 2025 figures (primary page returned 503) | SUPPORTED via secondary coverage |
| Gartner press releases (403 on direct fetch) | SUPPORTED via consistent coverage |
| EU AI Act Omnibus dates (Official Journal text not fetched) | SUPPORTED (law-firm analyses) |
| Google Gemini Code Assist end of sale; Antigravity Pro/Ultra prices | SUPPORTED / INCONCLUSIVE |
| SonarQube AI Code Assurance pricing | INCONCLUSIVE (third-party figures conflict) |
| Atlassian DX pricing; Jellyfish pricing | NOT TESTED / not public |
| GitHub ISO/IEC 42001 certification (secondary sources only) | INCONCLUSIVE |
| SOC 2 requirements for selling to enterprise buyers | Not researched in depth. Every enterprise tier reviewed lists SSO and audit logs (S-003..S-008, S-027, S-028); Echelon holds no attestation. A licensed product (model 2) would need SOC 2 Type II, which is a known cost and lead-time gap |

## D. Validation experiments (recommended order)

| ID | Experiment | Method | Pre-registered success / kill criteria | Closes |
|---|---|---|---|---|
| V1 | Problem interviews by buyer role | 12–15 structured interviews: at least 4 engineering leaders, 3 finance/FinOps, 3 risk/compliance, 2 investors or diligence buyers. Recruit from people already paying for Copilot, Claude Code or Cursor. Use Mercatus `ProblemPattern` and `BuyingGroup` records; no selling | **Continue** if at least 50% of engineering leaders describe an unmet need to prove agent work is "done" or worth its cost, and can name the current spend or workaround. **Kill or reframe** if most say the Copilot or LinearB dashboards suffice | G1, G3, G4 |
| V2 | Message and unit test (Mercatus CEX-07 variant) | Three positioning variants: (a) "Prove your coding agents' work is done," (b) "Cost per accepted change, not seats," (c) "Govern agents with what you already own." Run as the same short explainer in interviews or a landing-page test | Measure comprehension within 60 s, recall, and requested next step. Pick the variant with the highest next-step rate only if it beats the others by a predefined margin | G4, A2 |
| V3 | Concierge paid diagnostic offer | Offer a fixed-scope two- to three-week diagnostic at two price cells to 10 or more qualified prospects from V1. Price cells are set before outreach and recorded in Mercatus | **Signal:** at least 2 paid commitments. **Kill:** zero paid at either cell after 10 qualified offers | G2 |
| V4 | Enable verified completion in one Echelon repository and measure the catch rate | Turn on `requireVerifiedCompletion` with an attested verifier (needs OD-9). For 20 or more work items, compare the verifier's refusals with an independent fresh-agent review and a human review, and with agent self-claims | Report the overclaim rate caught and missed, with intervals. **Claimable** only if the verifier catches overclaims that self-review misses at a materially higher rate | G6, G7 |
| V5 | Head-to-head with incumbent governance on one fixture | Run the same requirement set through (a) Copilot coding agent with the control plane and Code Quality, (b) Kiro spec mode, (c) Claude Code plus Echelon. Score requirement loss, overclaimed completion, cost per accepted requirement and evidence completeness | Echelon is differentiated only where it beats both incumbents on requirement loss or overclaim detection. Otherwise drop the platform pitch | G10, G8 |
| V6 | Out-of-house install | Install Praxis and Dokimos via Conditor into a client-like open-source repository the team does not control (read-only fork) | Time to first verified item, and number of manual fixes | G9 |
| V7 | Claim hygiene | For each public site claim, locate or create an evidence packet, or remove the claim | 100% of headline numbers either traced or withdrawn | G11 |

V1–V3 need no new engineering and can start immediately. V4 is blocked on owner decision OD-9. V5 overlaps Track D's
matched-task experiment and should reuse its harness.
