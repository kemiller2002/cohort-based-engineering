# VAC-001: verified agent continuity

This experiment measures whether long-lived agents, with or without Ordo controls and independently verified
state, keep reliability and cost stable across a chain of successive changes.

- **Protocol:** [`../../verified-agent-continuity/research-protocol.md`](../../verified-agent-continuity/research-protocol.md)
- **Manifest:** [`../../verified-agent-continuity/experiment-manifest.json`](../../verified-agent-continuity/experiment-manifest.json)

## Layout

| Path | Contents |
|---|---|
| `harness/vac.sh` | Unit lifecycle: `setup`, `stage`, `verify`, `state` |
| `harness/vac.fsx` | F# functions: `archcheck` (VAC-RULES 1.0.0), `evidence` (Layer 1), `observe`, `state` (verified / provisional / rejected), `usage` (transcript tokens and cost, X4 scan) |
| `harness/render.py` | Brief renderer (pure) |
| `harness/detector-controls.sh` | Mutation controls for `archcheck` |
| `briefs/brief.md` | The single brief template |
| `arm-files/` | C/D treatment files: `RULES.md`, `DECISIONS.md` |
| `faults/faults.json` | Phase 5 synthetic false premises, used only in run F1 workspaces |
| `directives/DIRECTIVES.md` | The common directives pack, byte-identical to REL-001 run-03 |
| `evidence/` | Fixture self-check and detector-control outputs |
| `results/RUN/ARM/` | `setup.json`, `verify-N-ATTEMPT.json` (`cbe.vac-001.observation/1`), `usage-N.json`, `verified-state-N.json` (D) |

The fixture is REL-001 run-03's, used unchanged and never copied into a workspace except for the files each
unit stages.

## Requirements

- .NET SDK 10.0.402, plus the .NET 8 runtime for Ordo.
- Ordo built from `ordo@bb43c26`.
- Praxis built from `praxis@986211c`.
- `jq` and `python3`.

Paths can be overridden with `VAC_ORDO`, `VAC_PRAXIS_DLL`, `VAC_WORK`, `VAC_STATE` and `VAC_RESULTS`.

## Run one unit

```sh
harness/vac.sh setup P1 B                 # once per arm and run
harness/vac.sh stage P1 B 1 V7            # prints the brief path; deliver it to the agent
harness/vac.sh verify P1 B 1              # after the agent's turn
harness/vac.sh state P1 D 1               # arm D only
dotnet fsi --quiet --exec harness/vac.fsx usage --transcript T.jsonl --from ISO --to ISO --prices ../../pricing/anthropic.price-table.json
```
