# Run-02 protocol notes

These are events that are not exclusions under X1–X6 but are recorded for the analysis. They come from the agents' own final reports, which the transcripts confirm.

- **REL-001-R2-U6-r1-directives, agent-2:** to take a baseline, it moved the visible acceptance test file to its scratchpad, outside the workspace the brief allows, then restored it and deleted the copy. This breaks the brief's "work only inside" limit. It is not X4, since no oracle was involved, and not X6, since no host file was touched. It is scored as is.
- **REL-001-R2-U6-r1-echelon-optimized, agent-1:** it reported possibly leaving a background poller watching the claim. Before scoring, the orchestrator found no such process; the only one present was the trial's own verifier daemon.
- **Host load:** from trial 22 until the REL-GATE-003 Praxis change is finished, a Praxis development agent shared the host, with its builds and tests at `nice -n 19`. Only time metrics can be affected. The affected trials are listed in `concurrency.json` under `hostLoad`.
