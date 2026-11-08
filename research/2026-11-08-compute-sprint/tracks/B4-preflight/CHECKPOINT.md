# B4-preflight checkpoint

- Preregistration 3b7c9f7 (protocol + harness, nothing run). Raw runs 2ee03be.
- Version: percepta-semantic-v0.4.0 = 4a53688 (R9/competition pin) = percepta HEAD; also first commit 0ad2bd3.
- Result: docs claim reproduced exactly. R8 v4.1.1 exit 3; INV-04 x T-S31/T-S32, CommandEnvelope carrier, DEV-R8-12
  gap, one extra non-blocking pair. v4.1.2/v4.1.5/v4.1.6: exit 0, zero findings. Median 0.26-0.37 s. 0ad2bd3 identical.
- CI condition (no --catalog, as Indy-init preflight-tooling.yml runs it for v4.1.5) cannot detect the carrier defect.
- Not blind: same Claude session wrote tool, R9 handoff claims, v4.1.2 correction (after R8 records, 2026-11-02).
- Post-hoc probe: both tools lexically fragile; percepta misses reworded bound, 2-cycle, string tag, reworded catalog.
- Next: experiments.json, findings.json, final report.
