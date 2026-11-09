# SPR-D2-02 checkpoint (D2-PREP2, 2026-11-08)

**State: prepared, preregistered, NOT RUN.** No arm agent has been launched. RD-000 launches all runs.

## Done
- `protocols/SPR-D2-02.md`: preregistration (two stages, stage-1 decision rule, H2 primary on the raised measure,
  seed 2026110802, batches, exact tests, power, exclusions).
- `fixture/`: `SPEC.md`, `errors.py`, `score.py`, `oracle_tests.py`,
  `impl/{reference,naive_value,naive_alt,naive_error,naive_documented,refuser,empty}`. Byte-identical copy of the hidden
  oracle at `/home/user/sprint-scratch/D2b/oracle-c41e/` (checked by the test suite).
- `harness/`: `test_harness.py` (25 unittest tests, OK), `check_prompts.py` (PASS: identity with SPR-D2-01 + single
  governance block), `assign.py`, `analyze.py`, `perm.py`, `stage1_gate.py`, `power.py`, `exposure_check.py`,
  `validation/` (real outputs).
- `arm-prompts/M.txt`, `arm-prompts/G.txt`: byte-identical to SPR-D2-01's.
- `assignment.json`, `results/usage.template.json`.
- Workspaces `/home/user/sprint-scratch/D2b/ws/{p1,p2,s01..s16}`: each contains only `SPEC.md` and `errors.py`.

## Oracle validation (real outputs, `harness/validation/score-*.json`)

| Implementation | Accepted | Violations (raised) | Violations (lenient) | Raised | Documented |
|---|---|---|---|---|---|
| reference | 12/12 | 0 | 0 | 5 | 5 |
| naive_value | 12/12 | 5 | 5 | 0 | 0 |
| naive_alt | 12/12 | 5 | 5 | 0 | 0 |
| naive_error | 12/12 | 5 | 5 | 0 | 0 |
| naive_documented | 12/12 | 5 | 0 | 0 | 5 |
| refuser | 1/12 | 0 | 0 | 5 | 0 |
| empty | 0/12 | 0 | 0 | 0 | 0 |

## Director launch procedure (run all commands from this directory)
1. **Stage 1.** Launch p1 and p2 together, both with `arm-prompts/M.txt`, `{WS}` replaced by
   `/home/user/sprint-scratch/D2b/ws/p1` (resp. `p2`). Same model, agent type and tools as SPR-D2-01. Cap 40 min.
2. Exposure check each transcript: `python3 -I harness/exposure_check.py <transcript.jsonl> p1`.
3. Score: `mkdir -p results/scores && python3 -I /home/user/sprint-scratch/D2b/oracle-c41e/score.py
   /home/user/sprint-scratch/D2b/ws/p1 > results/scores/p1.json` (same for p2).
4. Gate: `python3 -I harness/stage1_gate.py results/scores/p1.json results/scores/p2.json`
   (exit 0 = PROCEED, exit 3 = STOP). On STOP: record the ceiling finding; do not tweak or re-run.
5. **Stage 2** (only on PROCEED). Batches, each launched together, the next after the previous finished:
   1: s01 M, s05 M, s13 G, s16 G · 2: s02 M, s06 G, s08 G, s11 M · 3: s04 M, s07 M, s09 G, s10 G ·
   4: s03 M, s12 M, s14 G, s15 G. Prompt = `arm-prompts/<arm>.txt` with `{WS}` → the run's workspace.
6. Fill `results/usage.json` from `results/usage.template.json` (runtime `total_tokens`, `duration_ms`, `tool_uses`,
   `model`, `excluded`, `exposure_note`).
7. Score all 16 after all have finished (command as in step 3), then:
   `python3 -I harness/analyze.py assignment.json results/usage.json results/scores/s*.json > results/results.json`

## Open risks
- Injected `CLAUDE.md` → `AGENTS.md` pointer may dilute the IV (as in SPR-D2-01).
- Power is adequate only for large effects (protocol section 9).
- The neutral `NotSpecified` convention line may still cue refusal; stage 1 checks this.
