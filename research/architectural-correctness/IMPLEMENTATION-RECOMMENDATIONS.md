# ARCH-001 implementation recommendations

These recommendations rest on [REPORT.md](REPORT.md) and on the gaps in [BASELINE.md](BASELINE.md). Each one is
labelled by the strength of its support:

- **Finding:** shown by the confirmatory results.
- **Gap:** a capability verified missing by inspection. It is independent of the trial outcomes.
- **Not supported:** tested, with no benefit shown. Do not mandate.

None of them changes a production architectural policy. Each needs owner review before adoption.

## Recommendations

| # | Recommendation | Basis | Destination | Intake document |
|---|---|---|---|---|
| R1 | Run architecture verification independently, **outside the agent loop**, by default. A compiler-resolved dependency/boundary check should run at completion or in CI, against host-held policy, bound to the commit. It should not be an in-brief agent tool. | **Finding.** In-loop enforcement (D vs C) added +4.0% model cost (inside the equivalence margin), about +48% wall time and 6.4 verifier runs per trial, with zero violations prevented in 128 requirements. The verifier caught all 7 planted traps out of the loop (`fixtures/check.sh`). | Praxis, Dokimos | `praxis/.praxis/inbox/documents/2026-10-21-ARCH-001-01-independent-architecture-validation.md` |
| R2 | Give Dokimos a compiler-derived architecture rule family that supersedes the DOK-R008 regex. It should cover the evaluated project graph and FCS typed-symbol rules (forbidden namespaces and symbols by tier, boundary rules), with a zero-tolerance mode rather than only a ratchet. `archcheck` (`verifier/`) is a working reference implementation, with 22 selftest samples and determinism checks. | **Gap.** DOK-R008 is a regex over `<ProjectReference>` lines: blind to `open`, type and function use, and it fails only on growth past a baseline. No typed analysis exists in the ecosystem. | Dokimos | `dokimos/.praxis/inbox/documents/2026-10-21-ARCH-001-02-compiler-derived-architecture-rules.md` |
| R3 | Each Echelon application declares its project → tier map and presentation scope (AR-28). An unmapped project is a finding. | **Gap.** No application declares tiers. A verifier cannot decide direction without the map (A1). Summa and Signal have no dependency-direction check. | Dokimos (consumed by R1/R2); applications adopt it later | Part of R2's document |
| R4 | Keep Ordo decision contracts as an opt-in for work with consequential or conflicting decisions. Do not mandate them for routine work. Do not add architecture-rule contract node kinds yet. | **Not supported.** Decision fidelity was 78/78 in every arm. Arm A refused T5's conflicting requirement from the repository's DEC records alone. C − B review −0.16 (exploratory). | Ordo (no change) | — |
| R5 | Ordo may record decision → code/test trace evidence, which today exists only as a brief convention. This is optional and low priority. | **Gap.** Ordo traces requirement → decision → verification obligation and stops before code (BASELINE §2.2). In C/D, agents cited every contract decision when asked (ARC-TRC-01: 0 untraced), so the convention is cheap. | Ordo | `ordo/.praxis/inbox/documents/2026-10-21-ARCH-001-03-decision-to-code-trace-evidence.md` |
| R6 | Architecture packs in agent briefs (arm B) are optional quality aids, not correctness controls. | **Finding (exploratory).** +15.3% cost [+8.2, +23.5]. No change in mechanically checked outcomes. Blinded review +0.59/6 (p = 0.013, exploratory). Fewer swallowed-failure heuristics. | Praxis (no mandate) | — |
| R7 | Replicate on violation-prone work before any mandate is reconsidered. Use brownfield fixtures with existing violations and inconsistent layering, larger multi-feature tasks, real Summa/Signal changes, and more than one model. Add H7 (grouping) as a separate factor experiment. | **Finding.** The ceiling (0 violations in every arm) limits every architecture conclusion. | Cohort-Based Engineering | `cohort-based-engineering/.praxis/inbox/documents/2026-10-21-ARCH-001-04-violation-prone-replication.md` |

## What is deliberately not recommended

- **Mandatory in-loop `archcheck` gating for all agent work.** No benefit was shown, and the overhead was measured.
- **Mandatory Ordo contracts.** No fidelity gain was shown.
- **Changes to the production architecture policy in Summa or Signal** (out of scope; owner review required).
  R3's tier maps are an adoption step for the applications' owners.

## Lessons for experiment infrastructure

These are engineering findings from running ARCH-001, recorded in PROTOCOL §13:

1. **Integrity rules must be visible in the instruments that use them.** The verifier refuses a contract inside the
   evaluated repository. Arm D's brief and gate passed exactly that, so the treatment silently failed in the pilot
   (A1). Gates should print a refusal's reason verbatim.
2. **Never detect features with `cmd --help | grep -q` under `pipefail`.** Detection failed silently, and probes were
   dropped from scoring for a whole run (A4). Pin the tool and pass the option unconditionally.
3. **Define regression against the follow-up reference, not against the whole initial oracle.** Tests that a
   follow-up supersedes must be excluded mechanically (A3).
