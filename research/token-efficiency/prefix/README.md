# Runtime prefix probes

Exploratory measurement of the Claude Code runtime prefix by configuration. Results are in
[`PREFIX-COMPOSITION.md`](PREFIX-COMPOSITION.md) and the raw data in [`prefix-probes.json`](prefix-probes.json).

## Reproduce

These are real API calls: 22 one-turn probes, about $0.63. The commands need an authenticated `claude` CLI, `python3`
and a scratch directory. Run them from the repository root:

```sh
python3 -I research/token-efficiency/prefix/probe-prefix.py run research/token-efficiency/prefix/prefix-probes.json \
  --claude /opt/node22/bin/claude --scratch "$SCRATCH/prefix-probe"
# a subset:  ... run OUT.json --only baseline tools-core
# recompute the summary from the raw probes (pure, no API calls):
python3 -I research/token-efficiency/prefix/probe-prefix.py summarize research/token-efficiency/prefix/prefix-probes.json
```

- The `--scratch` directory is wiped and recreated for each probe (subdirectories `cfg`, `home` and `work`).
- The committed `prefix-probes.json` came from two invocations of this script: everything except `tools-core`, then
  `--only tools-core`. The probes were merged in configuration order and the summary recomputed with `summarize`.
- Python 3 standard library only.
