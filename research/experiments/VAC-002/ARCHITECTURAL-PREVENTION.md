# VAC-002: Does the four-tier architecture prevent mistakes, or only detect them? (Phase G)

**Sources:**

| Source | Contents |
|---|---|
| `results/P1/phase-g.json` | One row per unit: in-loop `archcheck` and Ordo runs and their verdicts from the turn streams; gate architecture results; scored heads |
| `results/P1/score-*.json` | `architecture`: the full `archcheck` report of every final head |
| `results/P1/gate-*.json` | The gates' `architecture` checks |

**Method:** `METRICS.md` §4. **Evidence class:** pilot, descriptive; one chain per arm.

## 1. The three mechanisms, measured separately

**Violation opportunities.** Every unit is an opportunity, because every unit touched Tier 4 presentation. L02 is the
designed trap, where the easiest implementation reads Tier 1 fields or calls Tier 2 from the CLI.

| Mechanism | What counts | A | B | C | D | E | F |
|---|---|---|---|---|---|---|---|
| Invalid implementation **proposed** (in any `archcheck` run, gate or scored head) | units | 0* | 0* | 0 | 0 | 0 | 0 |
| **Prevented**: Ordo refused admission before implementation | units | — | — | 2 (L04, L08) | 2 (+1 re-check) | 2 | 2 |
| Prevented: the compiler rejected a forbidden reference | units | 0 | 0 | 0 | 0 | 0 | 0 |
| **Detected** in the loop (`archcheck` reported a finding) | units | — | — | 0 of 27 runs | 0 of 30 | 0 of 30 | 0 of 34 |
| Detected by the gate | units | — | — | — | 0 of 12 | 0 of 12 | 0 of 12 |
| **Corrected** after detection | units | — | — | 0 | 0 | 0 | 0 |
| **Escaped** (a final head with a DET finding of severity ≥ 2) | units | 0 | 0 | 0 | 0 | 0 | 0 |

\* A and B have no checker in the loop. Only their final heads can be observed, so for them "proposed" can only be
counted as "escaped". Neither had any.

**Rates.** Prevention, detection and correction rates are **undefined**, because no invalid implementation was ever
proposed. The escaped-error rate is **0/72**. With zero events, the upper 95% bound on the per-unit violation
probability is 3.1% pooled over 72 units, and 22% for any single arm's 12 units.

**What Ordo did prevent.** It refused the two contracts whose requirements contradict other requirements or an
accepted decision (L04, L08). That is a *decision* conflict, not an architectural violation. And A and B surfaced the
same conflicts without Ordo (§3).

## 2. The five-way comparison

| Mechanism | Arm(s) | Violations it prevented | Violations it detected | Cost (agent, relative to the natural-language baseline B) | Classification |
|---|---|---|---|---|---|
| 1. Natural-language guidance only | B (A) | — (0 occurred) | — | baseline | Inconclusive: nothing to prevent |
| 2. Typed architectural decision records | not isolated (bundled in C) | — | — | — | **Not measured** (`ARMS.md`) |
| 3. Executable architectural constraints (in-loop `archcheck` plus Ordo admission) | C | 0 | 0 | −0.7% (exploratory −12% to +10%) | Inconclusive (benefit); **cost not distinguishable from zero** |
| 4. Full independent verification | D, F | 0 | 0 | +12.9% (D) | Inconclusive (benefit); cost supported but preliminary |
| 5. Adaptive selective enforcement | E | 0 | 0 | +17.2% | Inconclusive (benefit); no cost saving over 4 (§ `ADAPTIVE-ENFORCEMENT.md`) |

## 3. Reading

1. **The architecture was not violated, with or without enforcement.**
   - ARCH-001 found this over 64 single-task trials. VAC-002 now finds it over 72 *chained* units, with a trap task
     and with arms that never saw a checker.
   - Every agent placed L02's overdue logic in Tier 2/3 and rendered a Tier 3 view. The trap path, computing it in the
     CLI from `Loan.DueDate` or `Fines.daysLate`, was never taken.
   - The likely reason: the four-tier documents and the existing code's own layering are in every repository, so even
     the "natural-language only" arms had a strong exemplar.
2. **Prevention versus detection cannot be separated on this evidence.** Zero proposals means zero opportunities for
   either. The instruments are validated (the self-check catches the L02 trap: 10 DET findings), so the zero is not a
   blind spot of the checker for the violation class it targets.
3. **Executable constraints were cheap here.** C cost the same as B (−0.7%), unlike VAC-001 (+14%) and ARCH-001 (D/C
   +4%). In-loop `archcheck` costs host time (20–30 s per run, about 2.5 runs per unit), not model tokens.
4. **Ordo's measured contribution is decision-conflict refusal, not architecture.**
   - Its refusals named exactly the conflicting requirement, and C–F agents recorded them.
   - A and B reached the same outcome by reading the requirement against the decision records.
   - Because the experimenters authored the contracts' conflict nodes (`TASK-CORPUS.md` §2), this is an upper bound on
     Ordo's help, and it still did not change the outcome.

## 4. What would be needed to measure prevention

Violations must actually occur. Candidates (R-EXP-4 in `RECOMMENDATIONS.md`):

- a brownfield fixture that already contains a few boundary violations to imitate (ARCH-002 is building this);
- a fixture without the four-tier documents in the natural-language arms;
- tasks whose only *working* implementation within the turn budget crosses a boundary unless a port is added.

The rule for measuring prevention is unchanged: a prevented error (never representable or admitted) is not the same
as a detected and repaired one, and the two are counted separately.
