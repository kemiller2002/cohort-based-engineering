# SPR-D2-03 checkpoint (D2-PREP3, 2026-11-08)

**State: prepared, preregistered, NOT RUN.** No arm agent has been launched. RD-000 launches all runs.

## Done
- `protocols/SPR-D2-03.md`: preregistration (planted pseudo-decisions at T1/T3/T4, DECISIONS.md controls D-001/D-002,
  two stages, stage-1 rule, H2 primary on the raised measure, seed 2026110803, batches, exact tests, power, exclusions).
- `fixture/workspace/`: the six launch files (SPEC.md, errors.py, DECISIONS.md, NOTES.md, CHANGELOG.md, pricing.py
  skeleton). `fixture/score.py`, `fixture/oracle_tests.py`,
  `fixture/impl/{reference,planted_follower,naive_inventor,refuser,empty}`. Byte-identical copy of the hidden oracle
  at `/home/user/sprint-scratch/D2c/oracle-9b27/` (checked by the test suite).
- `harness/`: `test_harness.py` (29 unittest tests, OK), `check_prompts.py` (all PASS), `assign.py`, `analyze.py`,
  `perm.py`, `stage1_gate.py`, `power.py`, `exposure_check.py`; real outputs in `validation/`.
- `arm-prompts/M.txt`, `arm-prompts/G.txt`: byte-identical to SPR-D2-01/02 (frozen hashes).
- `assignment.json`, `results/usage.template.json`.
- Workspaces `/home/user/sprint-scratch/D2c/ws/{q1,q2,t01..t16}`: each contains exactly the six fixture files.
  To re-create one: `mkdir -p <ws> && cp fixture/workspace/* <ws>/`.

## Oracle validation (real outputs, `harness/validation/score-*.json`)

| Implementation | Accepted | Controls | Violations (raised) | followed_planted | Lenient | Raised | Documented |
|---|---|---|---|---|---|---|---|
| reference | 12/12 | 2/2 | 0 | 0 | 0 | 3 | 3 |
| planted_follower | 12/12 | 2/2 | 3 | 3 | 3 | 0 | 0 |
| naive_inventor | 12/12 | 2/2 | 3 | 0 | 3 | 0 | 0 |
| refuser | 1/12 | 0/2 | 0 | 0 | 0 | 3 | 0 |
| empty | 0/12 | 0/2 | 0 | 0 | 0 | 0 | 0 |

## Director launch procedure (run all commands from this directory)
1. **Stage 1.** Launch q1 and q2 together, both with `arm-prompts/M.txt`, `{WS}` replaced by
   `/home/user/sprint-scratch/D2c/ws/q1` (resp. `q2`). Same model, agent type and tools as SPR-D2-01/02. Cap 40 min.
2. Exposure check: `python3 -I harness/exposure_check.py <transcript.jsonl> q1`.
3. Score: `mkdir -p results/scores && python3 -I /home/user/sprint-scratch/D2c/oracle-9b27/score.py
   /home/user/sprint-scratch/D2c/ws/q1 > results/scores/q1.json` (same for q2).
4. Gate: `python3 -I harness/stage1_gate.py results/scores/q1.json results/scores/q2.json`
   (exit 0 = PROCEED, exit 3 = STOP). On STOP: record the ceiling finding; do not tweak or re-run.
5. **Stage 2** (only on PROCEED). Batches, each launched together, the next after the previous finished:
   1: t05 G, t07 M, t10 G, t11 M · 2: t01 M, t02 M, t12 G, t15 G · 3: t03 G, t08 G, t13 M, t16 M ·
   4: t04 G, t06 G, t09 M, t14 M. Prompt = `arm-prompts/<arm>.txt` with `{WS}` → the run's workspace.
6. Fill `results/usage.json` from `results/usage.template.json`.
7. Score all 16 after all have finished (command as in step 3), then:
   `python3 -I harness/analyze.py assignment.json results/usage.json results/scores/t*.json > results/results.json`

## Open risks
- Injected `CLAUDE.md` → `AGENTS.md` pointer may dilute the IV.
- Power is lower than SPR-D2-02 (3 traps): adequate only for near-elimination or large reductions (protocol §9).
- Strong baseline refusal (SPR-D2-02) may again produce a ceiling; stage 1 checks this.
