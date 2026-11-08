# V5-verification checkpoint (SPR-X-03)

- 16:13 EST start. Copied 24 workspaces to /home/user/sprint-scratch/V5/ws (originals untouched; copies verified by diff).
- Prereg commit 90f85c1 at 15:59:50 EST; earliest run artifact (pricing.py) 16:03 EST. PROTOCOL's "~16:05" label is wrong but prereg precedes runs.
- V4 oracle copied to scripts/v4_oracle/ (provenance hashes in raw/), control validation re-run: 7/7 OK (raw/test_oracle-output.txt).
- Task 1 DONE: 24/24 runs, 96/96 trap cells, 36/36 planted cells agree (raw/agreement.json). Verdict SPR-X-03.rescore VERIFIED.
- Next: stats (Fractions), arm check, prompt derivation, descriptive vs X-02, T5, confounds.
- 16:16 Task 2 DONE: primary 11/3, p = 1/2178 (392/853776) reproduced exactly; secondaries and Holm reproduced (raw/v5-stats.json). Verdicts SPR-X-03.primary and .secondaries VERIFIED (wording notes). T5 exclusion leaves the stat and p unchanged (all 12 D2b runs violated T5).
- 16:18 Tasks 3 and 7 DONE: 0 arm mismatches; no fixture modifications, disallowed imports or file access; C < K in every batch (raw/confounds.json). Verdicts .arm-assignment and .confounds VERIFIED.
- 16:18 Task 4 DONE: C/K/G_as_delivered reproduce byte for byte from frozen M + G sections before 'Task:' (raw/prompts_check.json). Delivered prompts not verifiable. Verdict .prompt-derivation VERIFIED (templates only).
- 16:20 Tasks 5 and 6 DONE: descriptive table reproduced; C~G and C~M(tokens) hold; K>M on D2b descriptive only (p 0.10 unadjusted) and reversed on D2c. T5 fair but low-discrimination (24/25 Haiku runs device-local); primary unchanged without T5. SO-01 drop sensitivity p = 1/8820 (corrected confounds note).
- 16:21 All tasks done. Tests: test_oracle (V4, re-run), test_v5stats, test_prompts_check, test_helpers all OK (raw/*-output.txt). 9 verdicts in verdicts.json. Final report delivered in hand-back (REPORT.md not written per harness rule).
- Note: times above corrected to the commit times (EST); earlier text had estimated times.
