# REL-001 run-01 harness

Protocol: [`../protocol/run-01.md`](../protocol/run-01.md). Binaries are downloaded from their
GitHub releases, checked against the release checksum files and kept under
`/tmp/claude-0/rel001/bin` (override with `REL001_BIN`); they are never committed. Every case
runs in a fresh directory under `/tmp/claude-0/rel001/runs/<runId>` (`REL001_RUNS`).

| Path | Purpose |
| --- | --- |
| `lib.sh` | shared helpers: arms, binary pins (sha256 recorded per result), fresh repositories |
| `a/run.sh ARM` | Experiment A, concurrent ownership -> `results/a/ARM.jsonl` |
| `b/run.sh ARM` | Experiment B, contracts (`fixtures/b/cases.json`) -> `results/b/ARM.jsonl` |
| `c/run.sh ARM` | Experiment C, completion verification -> `results/c/ARM.jsonl` |
| `summarize.fsx a\|b\|c` | `results/<exp>/summary.json` (counts only) |
| `d/randomize.py` | preregistered D trial order (seed 20261019) |
| `d/make-contracts.py` | regenerates `fixtures/d/tasks/Tn/contract.json` from `requirement.md` |
| `d/setup.sh ARM TASK RUNID` | D workspace: repo, arm's Praxis (+ Dokimos), queue, `AGENT_BRIEF.md`, `env.sh`, `run.json` |
| `d/score.sh RUNID [--transcripts DIR \| --report F] [--out F]` | hidden-oracle scoring -> observation JSON |
| `d/smoke-agent.sh RUNID` | scripted reference-solution "agent"; **harness checks only, never observations** |

Rerun A, B, C (ARM = `baseline` or `treatment`):

    for e in a b c; do for arm in baseline treatment; do bash harness/$e/run.sh $arm; done; dotnet fsi harness/summarize.fsx $e; done

Experiment D trial (one run of the preregistered order):

    export REL001_MODEL_PROVIDER=anthropic REL001_MODEL=<model id> REL001_MODEL_CONFIG=<agent config file>
    bash harness/d/setup.sh treatment T3 REL-001-D-T3-r2-treatment
    # start a fresh agent session in /tmp/claude-0/rel001/runs/REL-001-D-T3-r2-treatment/repo,
    # give it AGENT_BRIEF.md, write logs/agent.json {startedAt, endedAt}, copy its transcripts
    bash harness/d/score.sh REL-001-D-T3-r2-treatment --transcripts <copied transcripts> \
      --out observations/treatment/REL-001-D-T3-r2-treatment.json
