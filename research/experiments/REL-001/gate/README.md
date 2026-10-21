# REL-001 completion gate

`gate-report.json` (`cbe.rel-001.gate-report/1`) is the machine-readable gate. **Current result (2026-10-20T13:18Z, amendment A5 plus the coordinator evaluation): PASS for the attested configuration, FAIL for the non-attested configuration** on released Praxis 3.17.0, Dokimos 0.7.0 and Ordo 1.17.0.

- P4 passes as preregistered in run-01. Its original GATE-3 shape is a forged result with no event (GATE-3U), and it is rejected.
- The stricter case added afterwards (P4S) behaves differently by mode:
  - In non-attested mode, a forged result plus a forged validation event in the out-of-tree store still completes an item (GATE-3, C3b). This is blocker REL-GATE-003, filed in the Praxis intake.
  - **Re-run on Praxis v3.18.0 (2026-10-21T01:51Z):**
    - Same outcomes as 3.17.0 in every case.
    - REL-GATE-003 is resolved: `requireVerifiedCompletion` now implies attestation, and GATE-3 completes only where no
      attestation is required, labelled `unattested`.
    - REL-GATE-004 is open: the attestation policy and authority must come from a source the agent cannot write.
  - **From the release containing praxis#279 (REL-GATE-004):** use `scripts/gate-evidence-binding-v319.sh`, and run experiment C with
    `REL001_PIN_VERIFIER_KEY=1`. Attested repositories must pin the host verifier keyid (`workProtocol.trustedVerifierKeyIds`).
    The v319 script adds GATE-A5 (PROBE-3) and GATE-A6 (PROBE-4). See amendment A6 in `protocol/run-01.md`.
  - Attested mode refuses every forgery (GATE-A1..A3) and verifies the genuine pass (GATE-A4).
- O3, O4 and D3 were re-measured at the release tags.

Reproduce with `scripts/gate-evidence-binding-v317.sh PRAXIS DOKIMOS ORDO CONTRACT WORKDIR [non-attested|attested|both]`; on 3.17.0 the original script below is refused for every case with `PRX.COMPLETION.DIRTY_WORKTREE`. **Previous result (2026-10-20T01:10Z): PASS.** All 16 conditions pass on released Praxis 3.16.0, Ordo 1.17.0 and Dokimos 0.6.0. REL-GATE-002 is resolved: Experiment B's treatment arm now accepts 0 of 11 invalid cases. Earlier evaluations are kept under `history`, including the FAIL on O2 (2026-10-19T22:20Z) and the PASS on 3.15.0 (21:45Z). **First result
(2026-10-19): FAIL, so the experiment was not started.** 12 conditions pass, 3 fail and 1 is blocked.

The failure is in completion evidence binding (P4, D2). The released Praxis 3.14.0 and
Dokimos 0.6.0 accept a failing test log, and a file that is not a test report at all, as
verified completion evidence. Praxis asserts every evidence file it can hash as *passed at
the verification revision*, and it never sends the freshness members that Dokimos supports.
Dokimos's own checks are sound, but they check an assertion Praxis never established. Running
Experiments C and D on this pipeline would measure a verification step that cannot fail
for bad evidence, so their results would be invalid.

The blocker is filed in the Praxis intake as
`.praxis/inbox/documents/2026-10-19-REL-GATE-001-evidence-binding.md` (kemiller2002/praxis),
and it links the existing work item PRAXIS-REL-005.

## Reproduce

    scripts/gate-evidence-binding.sh PRAXIS_BIN DOKIMOS_BIN ORDO_CONTRACT WORKDIR

Run it with the release assets `praxis-linux-x64.tar.gz` (v3.14.0) and `dokimos-linux-x64.tar.gz`
(dokimos-v0.6.0), after checking them against the releases' checksum files. Use Ordo's
`examples/ecir/consumer/valid-contract.json` as the contract. Each case prints one JSON line;
both currently report `"outcome": "verified"`. `evidence/` holds that output and the suite
results behind the PASS conditions.

## Rerunning

Re-evaluate the gate from the newest releases. Before filing any blocker, search Praxis
`.praxis/inbox`, `.praxis/processed` and `.ros/work/queue.json` for its `REL-GATE-*` id and the
linked work item, so that a rerun never duplicates intake.
