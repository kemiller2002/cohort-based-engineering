# REL-001 instrumentation records

Records here validate measurement, not outcomes. They are **not** observations
of either REL-001 arm and are excluded from `analysis/analyze.fsx`.

- `2026-10-19-integration-session.json`: the Echelon reliability integration
  session (orchestrator plus four parallel agents). It shows that Claude Code
  provider usage is measurable end to end: Praxis `telemetry reliability-report`
  agrees exactly with an independent dedupe by `message.id`. Output tokens are a
  lower bound, and cost is unavailable because no price table was supplied. No
  requirement completed through Dokimos-gated `complete-verified`, so cost per
  independently verified requirement is undefined for this record.
