# V5-verification checkpoint (SPR-X-03)

- 16:13 EST start. Copied 24 workspaces to /home/user/sprint-scratch/V5/ws (originals untouched; copies verified by diff).
- Prereg commit 90f85c1 at 15:59:50 EST; earliest run artifact (pricing.py) 16:03 EST. PROTOCOL's "~16:05" label is wrong but prereg precedes runs.
- V4 oracle copied to scripts/v4_oracle/ (provenance hashes in raw/), control validation re-run: 7/7 OK (raw/test_oracle-output.txt).
- Task 1 DONE: 24/24 runs, 96/96 trap cells, 36/36 planted cells agree (raw/agreement.json). Verdict SPR-X-03.rescore VERIFIED.
- Next: stats (Fractions), arm check, prompt derivation, descriptive vs X-02, T5, confounds.
- 16:40 Task 2 DONE: primary 11/3, p = 1/2178 (392/853776) reproduced exactly; secondaries and Holm reproduced (raw/v5-stats.json). Verdicts SPR-X-03.primary and .secondaries VERIFIED (wording notes). T5 exclusion leaves the stat and p unchanged (all 12 D2b runs violated T5).
