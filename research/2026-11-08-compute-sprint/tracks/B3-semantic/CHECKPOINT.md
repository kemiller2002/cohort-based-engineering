# B3-semantic checkpoint

- Preregistration 1af19bc (protocol + code, nothing run). First run f783da9 (D1 candidate fix found by synthetic tests
  before any package run). Post-hoc ablation/probe 73d3c3e. Findings/experiments: final commit.
- Status: COMPLETE. R8-INV04 CAUGHT (C1-loop), R8-CMDBODY CAUGHT (C2); 0 primary alarms on v4.1.2 / v4.1.5 / v4.1.6.
  Causa T18->T20 derivable pre-T0 via INV-21 sources (C4), noisy. Zero-FP depends on answer-informed rules (ablation);
  C2 fails out of sample (12 alarms, 0 judged real).
- Reproduce: `cd checks && python3 -m unittest discover -s tests -v && python3 -m semcheck.run && python3 -m semcheck.summarize`.
- Report: delivered in the hand-back text (subagent REPORT.md writes are refused by the harness).
