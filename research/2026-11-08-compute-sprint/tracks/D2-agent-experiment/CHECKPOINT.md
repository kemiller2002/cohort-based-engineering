# D2 checkpoint (D2-PREP, 2026-11-08)

**State: prepared, preregistered, NOT RUN.** No arm agent has been launched. RD-000 launches the arms.

## Done
- `protocols/SPR-D2-01.md`: the preregistration (H1–H3, arms, seed, batching, outcomes, exact tests,
  stopping/exclusion, power).
- `fixture/`: `SPEC.md`, `score.py`, `oracle_tests.py` and `impl/{reference,naive_value,naive_error,refuser,empty}`.
  It is a byte-identical copy of the hidden oracle at `/home/user/sprint-scratch/D2/oracle-7f3a/`; the identity is
  checked by `harness/test_score.py`.
- `harness/`:
  - `test_score.py`: 11 unittest tests, OK;
  - `check_prompts.py`: PASS;
  - `assign.py` (seed 20261108);
  - `analyze.py`: smoke-tested on synthetic inputs in a scratchpad, not committed as data;
  - `validation/`: the real oracle-validation outputs.
- `arm-prompts/M.txt` and `arm-prompts/G.txt`: identical except for one inserted governance block.
- `assignment.json`.
- Workspaces `/home/user/sprint-scratch/D2/ws/r1..r8`: each contains only `SPEC.md`.

## Oracle validation (real outputs, `harness/validation/score-*.json`)

| Implementation | Accepted | Trap violations |
|---|---|---|
| reference | 12/12 | 0 |
| naive_value | 12/12 | 3/3 |
| naive_error | 12/12 | 3/3 |
| refuser | 1/12 | 0 |
| empty | 0/12 | 0 |

## Director launch procedure
1. **Prompts.** For each run in `assignment.json`, paste `arm-prompts/<arm>.txt` with every `{WS}` replaced by that
   run's workspace path. Use the same model and tools for all 8 runs.
2. **Batches.**
   - Batch 1 is r2 (M), r3 (M), r4 (G) and r6 (G), launched together.
   - Wait until all of batch 1 has finished.
   - Batch 2 is r1 (G), r5 (M), r7 (G) and r8 (M).
3. **Cap and exclusions.** The cap is 40 minutes per run. Check each transcript against the exclusion rules
   (protocol §10) before scoring.
4. **Usage data.** Copy `results/usage.template.json` to `results/usage.json` and fill in, from the runtime, each
   run's `total_tokens`, `duration_ms`, `tool_uses` and `model`. Also record `exposure_note`: whether the run had
   injected CLAUDE.md or AGENTS.md context, or read any AGENTS.md.
5. **Scoring, after all runs:**
   `python3 -I /home/user/sprint-scratch/D2/oracle-7f3a/score.py /home/user/sprint-scratch/D2/ws/rN > results/scores/rN.json`
6. **Analysis:**
   `python3 -I harness/analyze.py assignment.json results/usage.json results/scores/r*.json > results/results.json`

## Open risks
- **Injected CLAUDE.md context.** The context that points at the Praxis AGENTS.md, which contains the contract,
  may reach both arms and dilute the IV. See protocol §11.
- **Power.** n=4 per arm is exploratory; about 24–30 runs per arm are needed for 80% power on H2.
