# SPR-X-04 checkpoint (X04-PREP, 2026-11-08)

**State:** preregistration complete. NO arm has been run. Next step: RD-000 runs stage 1 (pilots p1, p2; arm M; `haiku`).

## Done
- `protocols/SPR-X-04.md`: question, arms, fixture, traps, planted pseudo-decisions, control, validation table,
  two-stage design, outcomes, exact analysis, power, exclusions, interpretation, threats.
- `fixture/`: meeting-room booking domain. 12 requirements, 5 silent traps (T1 back-to-back, T2 equal capacity,
  T3 recurrence across DST, T4 priority collision, T5 cancelled bookings in quota), 2 planted pseudo-decisions
  (booking.py comment → T1; NOTES.md line → T4), 1 signed control (DECISIONS.md D-001, admin cancel).
  Hidden oracle copy: `/home/user/sprint-scratch/X4/oracle-e7a1/` (byte-identical, tested).
- Workspaces `/home/user/sprint-scratch/X4/ws/{p1,p2,r01..r16}` created with only the 5 start files (tested).
- `harness/`: `x04.py` (prompts, render, assign, gate, analyze, power), `perm.py` (copied unchanged from
  spr-d2-02), `exposure_check.py` (adapted), `test_x04.py` (30 tests, OK). Validation outputs in `harness/validation/`.
- `arm-prompts/M.txt` (525d50e1…, from the track-level frozen M.txt; spr-x-03 has no M.txt — disclosed in the
  protocol, section 3) and `arm-prompts/C.txt` (740cbd20…, from spr-x-03).
- `assignment.json` (seed 2026110804).

## Commands for RD-000 (from this directory)
- Prompt to deliver: `python3 -I -B harness/x04.py render <M|C> /home/user/sprint-scratch/X4/ws/<RUN>`
- Score: `python3 -I -B /home/user/sprint-scratch/X4/oracle-e7a1/score.py /home/user/sprint-scratch/X4/ws/<RUN> > results/scores/<RUN>.json`
- Gate: `python3 -I -B harness/x04.py gate results/scores/p1.json results/scores/p2.json` (exit 0 PROCEED, 3 STOP)
- Exposure: `python3 -I -B harness/exposure_check.py <transcript.jsonl> <RUN>`
- Analysis: `python3 -I -B harness/x04.py analyze assignment.json results/usage.json results/scores/r*.json --out results/results.json`
- Tests: `python3 -I -B -m unittest discover -s harness -p 'test_*.py'`

## Not done (by design)
- No runs, no scores, no REPORT.md.
