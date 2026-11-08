# C2-001 checkpoint (SPR-C2-01)

- 2026-11-08 ~15:00 EST: code read; protocol protocols/SPR-C2-01.md preregistered before any build or key generation.
- Next: scratch clone, baseline build + suite (R0), throwaway key, trust patch, cases.
- ~15:15 EST: R0 baseline 1552 PASS / 0 FAIL. Throwaway TEST-ONLY keys generated (scratch only; public keys + SHA-256 fingerprints in raw/). Trust patch (patches/01). R1 trust populated: 1552 PASS / 1 FAIL (the predicted "pins no Registry release key yet" guard). R1k with embedded-trust scenario (patches/02): 1557 PASS / 1 FAIL; A4 production preview/apply qualifies Forma 0.7.0 via attested:>=0.2.0 <1.0.0:test-only-c2-001-2026-11-08; rogue key refused.
- Next: harness/ with real echelon-current 1.37.0 data (A1-A3, N1-N8, S1-S2), release-history analysis (H4).
