# E-security checkpoint log

## 13:45 EST — CP-E-01
- Praxis 3.25.0 (12bf995) built in /home/user/sprint-scratch/E/praxis (Release, 0 errors, 1m46s).
- Workflow auditor scripts/wf_audit.py + 7 unit tests (pass); data/workflow-audit.json over 155 workflows.
- Checked workProtocol flags across 45 ros.json files: none enables verified completion.
- Next: Dokimos build; governance-bypass fixture experiments.

## 13:49 EST — CP-E-02 (heading time corrected; earlier draft mislabelled)
- Dokimos 0.11.1 (fecbe0c) and Ordo sde (db6d39e) built in scratch; wrappers in /home/user/sprint-scratch/E/bin.
- E-X01: REL-001 gate v319 re-run on Praxis 3.25.0/Dokimos 0.11.1: all 17 cases match v3.19.0 expectations (GATE-3 non-attested forgery still verifies, documented).
- E-X02: scripts/bypass-cases.sh, 13 new cases (NX-1..NX-10). Succeeded: NX-1, NX-2b, NX-4, NX-5B, NX-6B, NX-7, NX-9, NX-10(labelled unattested). Refused: NX-2a, NX-3, NX-5a, NX-6a, NX-8.
- E-X10: fabricated 118-artifact evidence bundle for README-only candidate -> Indy-init verifier ACCEPTED.
- Branch protection: praxis main protected=false, causa-acceptance-r10 branches protected=false (GitHub API).
- Next: secret scan, supply chain, prompt-injection scan, REPORT/findings.

## 13:56 EST — CP-E-03
- Secret scan (59 repos, 128,562 blobs): no live credential after triage. Supply-chain inventory: 0 NuGet lock files.
- findings.json written (16 findings: 3 High, 6 Medium... see file). All unit tests (19) pass.
- REPORT.md is NOT committed (Director instruction: harness refuses subagent report files); full text goes in the final reply.
- Next: requirement-trace case if time permits.
