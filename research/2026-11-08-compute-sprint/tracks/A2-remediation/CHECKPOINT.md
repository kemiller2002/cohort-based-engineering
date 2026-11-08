# A2-remediation checkpoint log (worker A2-001)

## 2026-11-08T14:27-0500 — CP-1
- Preregistered SPR-A2-01/02/03 (protocols/, commits 3e11073, 300ccae, fad75d3).
- ros-history merge driver (F#, tools/ros-merge-driver, 26 unit tests pass). v1 replay on 26 logged R8 merges:
  16/26 resolved; v2 (Amendment 1, relaxed-order) 26/26 resolved, 0 lost, 0 duplicated.
- Full R8 (86 merges) and R10 (34 conflicted) replays done with v2 on the shallow clone; one R8 replay
  (538eab03, PR1) was invalid because the source clone is shallow (no merge base). Clone unshallowed
  from GitHub; R8 all-86 replay re-running (raw/replay-r8-all86-unshallow-v2.jsonl).
- praxis validate (native 3.24.0 release) on driver results: running (raw/validate-r8-ros58.jsonl);
  negative controls recorded (raw/validate-negative-controls.json).
- SPR-A2-03 computed (raw/failfast-counterfactual.json) with disclosed strict-gate sensitivity.
- Next: SPR-A2-02 builds (serial, after replays finish), experiments.json, findings.json.
