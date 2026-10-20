# Directives pack provenance

`DIRECTIVES.md` is the Echelon directives pack given to arms B, C and D of REL-001 run-02.
Every line in it, other than the preamble and the `## From <repo>: <path>` headings, is copied
verbatim from the source below at the recorded commit. Kept lines are whole lines, except where
marked "excerpt": those are whole sentences copied character for character. Nothing was
reworded, reordered within a passage, or added.

- `DIRECTIVES.md` sha256: `d02787165e41e24b2db6659c644343e5d4704b005a29e4bf95e2938aa4e38003`
- size: 123 lines, 1242 words (`LC_ALL=C.UTF-8 wc -l -w`), 8,819 bytes

## Selection rule

Kept: coding, testing, engineering and requirement-interpretation guidance that applies to
implementing a requirement in an F# repository without any Echelon tool. Removed: every
instruction that needs Praxis, Ordo or Dokimos tooling (work-item lifecycle, CLI commands,
registry records, telemetry, provenance, tool configuration or reports), plus document
metadata and descriptive material that states no directive. Each removal is listed below
with its source lines and reason.

## Sources

### praxis: `AGENTS.md` (Praxis agent contract)

- repository: https://github.com/kemiller2002/praxis
- commit (repository HEAD at extraction): `26a1ae368b302486e8d87163bbcf256346a99034`
- last commit touching the file: `e21444fb08cc5bc7b3ffc4f43a3317d8ff4b2a00`
- file sha256 at that commit: `b4ee32505f55e6f8a012a8afc8098542fc38e1517ca1fafe72caaa6c16b2d9fc` (304 lines)
- kept lines: 53, 58-62, 66, 68, 70, 72-75, 77-78, 83, 85

| Removed lines | Reason |
|---|---|
| 1-45 | front matter: document metadata and Praxis provenance records, not directives |
| 47-51 | title and mission statement of the Praxis tool, not a directive |
| 55 | `./ros` / `./praxis` alias note: Praxis CLI |
| 57 | read the Praxis governance index: Praxis registry document |
| 63-64 | pointers to the Agent Operating Manual, REP Specification and Engineering Standards: Praxis governance documents outside the requested source list (not inlined; see note) |
| 76 | cite `EV-`/`HY-`/`TH-`/`DF-` records: Praxis registry |
| 79 | execution telemetry as evidence: Praxis telemetry |
| 80 | `./praxis sync check` upstream-drift rule: Praxis CLI |
| 81 | REP artifact threshold in the Agent Operating Manual: Praxis research-package lifecycle |
| 87-91 | Work Protocol: Praxis work-item lifecycle and CLI (`work begin/complete`, `registry build`, `validate`, `provenance record`, backlog) |
| 93-119 | Upstream synchronization: `./praxis sync check` and `ros.json` policy |
| 121-164 | Durable checkpoints and continuity: `praxis work checkpoint/continue`, `.ros` state, telemetry steps, fallback reconciliation |
| 166-209 | Agent Identity and Provenance: Praxis actor identity, `provenance record`, `validate` |
| 211-231 | Remote execution: Praxis remote protocol and inbox |
| 233-267 | Lifecycle commands: Praxis installation, upgrade and `.echelon/ros.json` bookkeeping |
| 269-304 | F# CLI: Praxis CLI syntax and Praxis's own repository rule (F#-only, enforced by `./praxis architecture check`); applies to Praxis's repository and tooling |

### praxis: `docs/agent-mistake-prevention.md` (Praxis: preventing agent mistakes by construction)

- repository: https://github.com/kemiller2002/praxis
- commit (repository HEAD at extraction): `26a1ae368b302486e8d87163bbcf256346a99034`
- last commit touching the file: `2a0158727484dfd075e8d6f0b32f597d07b72764`
- file sha256 at that commit: `aa8ae1e536a5564dceed0977d55de00713943e60be9a5551788a57123d78620a` (63 lines)
- kept lines: 7-7 (excerpt: whole sentences), 45-47 (excerpt: whole sentences)

| Removed lines | Reason |
|---|---|
| 1-5 | title and issue links |
| 8-10 (after the first sentence) | qualification about requirements, modelling and cryptographic receipts (a Praxis/Dokimos mechanism); only the first sentence of the objective is kept |
| 12-31 | First implemented boundary: Praxis `LocalJournaledDispatch` / `CheckedLocalWorkerPacket` internals |
| 33-43 | Prevention inventory table: each mechanism is owned by and implemented in Praxis, Ordo or Dokimos tooling (packets, blueprints, host capabilities, journaled transitions) |
| 47-50 (from 'Avoid a parallel validator') | refers to Praxis's packet rules and the local coordinator/two-worker runtime |
| 52-63 | Validation and remaining work: Praxis PR status |

### dokimos: `docs/rules/DOK-FS-001.md` (Dokimos rule DOK-FS-001)

- repository: https://github.com/kemiller2002/dokimos
- commit (repository HEAD at extraction): `828208f46b7d1073534bd02873d6298b62ad1de2`
- last commit touching the file: `c9359074c31b5b183b7b370e9e02973656ab8e92`
- file sha256 at that commit: `0af5a1a34d17d8c60764d3ccf9ef02b00d50d0bed9f2465e9de1689e49bf9221` (25 lines)
- kept lines: 1, 7, 9, 11, 13, 15

| Removed lines | Reason |
|---|---|
| 3 | status line (candidate rule) of the Dokimos catalog |
| 17-25 | Evidence history: Dokimos's own modules and analyzer promotion criteria |

### dokimos: `docs/rules/DOK-COMPLEXITY-001.md` (Dokimos rule DOK-COMPLEXITY-001)

- repository: https://github.com/kemiller2002/dokimos
- commit (repository HEAD at extraction): `828208f46b7d1073534bd02873d6298b62ad1de2`
- last commit touching the file: `7ea4e1532d4de5ded9ea2ee57a7580623e4389e0`
- file sha256 at that commit: `bdc442ebc14f7716cb94f06956213ebe712872be4caeb8eea8cbb3a097dc9900` (29 lines)
- kept lines: 1, 13, 15, 25

| Removed lines | Reason |
|---|---|
| 3-11 | status, purpose and evidence dimensions of the Dokimos lexical complexity metric |
| 17 | Dokimos self-analysis numbers |
| 19-24 | policy for gating and correlating the Dokimos metric (tool behaviour) |
| 27-29 | metric promotion evidence |

### dokimos: `docs/quality/RATCHET-RULES.md` (Dokimos change-quality ratchet rules)

- repository: https://github.com/kemiller2002/dokimos
- commit (repository HEAD at extraction): `828208f46b7d1073534bd02873d6298b62ad1de2`
- last commit touching the file: `b176c53e430afcb3c41ab0253479af8761501e8d`
- file sha256 at that commit: `0551d0813cb4ded4037648ebe7fd769688cfcc66b12c91664b51e4676f0187b6` (222 lines)
- kept lines: 15, 113-122

| Removed lines | Reason |
|---|---|
| 1-13 | status, baseline and exception mechanics of `dokimos ratchet` (tool-maintained baseline) |
| 17-98 | commands, exit codes and the `dokimos.ratchet` report contract |
| 100-111 | rule-ID policy and the Dokimos lexical analyzer's scope |
| 123 | DOK-G001 row: introduced findings from `dokimos evaluate` |
| 125-222 | semantics of baseline scopes, the exceptions file and process, policy migration and gate ratchets: Dokimos tooling |

### ordo: `doctrine/STATE-DIRECTED-ENGINEERING.md` (Ordo (SDE) doctrine: bounded reasoning scope)

- repository: https://github.com/kemiller2002/ordo
- commit (repository HEAD at extraction): `9a8a2dee539a5c9befc2eb3cc98cfe36739aab06`
- last commit touching the file: `de31d70d24399ebf26ab10522590f6bf7d6a67d4`
- file sha256 at that commit: `588c8bce169544166e319e79ca70e373de85beb325637c9b6359c11a1f24f600` (135 lines)
- kept lines: 76, 83-88

| Removed lines | Reason |
|---|---|
| 1-75 | front matter, scope list, status and research motivation of the methodology |
| 78-81 | framing sentence (kept the principle statement it introduces) |
| 90-135 | evidence status, confidence classes, research layering and the ROS/`./ros` relationship (tooling) |

### ordo: `doctrine/STATE-PROGRAMMING.md` (Ordo (State Programming) doctrine: central concepts)

- repository: https://github.com/kemiller2002/ordo
- commit (repository HEAD at extraction): `9a8a2dee539a5c9befc2eb3cc98cfe36739aab06`
- last commit touching the file: `8f78c503693d1674675669abeaf31e95b39cc73c`
- file sha256 at that commit: `141a4581b566819fb1c4682989bbab8ae3732032f817512c83546c26e940bbe5` (105 lines)
- kept lines: 27, 29-56

| Removed lines | Reason |
|---|---|
| 1-26 | front matter, title and scope sentence |
| 58-105 | what State Programming is not, language neutrality, relationship to other doctrine, evidence status: descriptive, no implementation directives |

## Notes

- **Ordo source location.** The coordinator pointed to `ordo/docs/architecture/` and the root
  `README.md`. Those files hold the `ecir/1` wire format, tool behaviour (admission, readiness,
  pattern registry, decision classification of construction plans) and lifecycle commands; the
  README states no principle. The design-by-construction principle statements live in
  `ordo/doctrine/`, so the pack takes them from `doctrine/STATE-DIRECTED-ENGINEERING.md`
  (bounded reasoning scope) and `doctrine/STATE-PROGRAMMING.md` (central concepts).
- **Not inlined:** Praxis `AGENTS.md` points to `docs/00-governance/Engineering-Standards.md`
  and the Agent Operating Manual. They were not in the requested source list, so they are not
  part of the pack, and the pointer line is removed (a reference the agent could not follow).
- **Kept verbatim although they mention Echelon vocabulary:** the Authority paragraph names
  "accepted domain REPs and theory" and "canonical governance"; Core Rules mention "canonical
  policy"; the DOK-R rule table's Signal column describes what the Dokimos detector looks for,
  and DOK-R004's remediation says "track it in the work queue". None of them requires running
  a tool, and editing them would break verbatim copying, so they stay as written.
- **Reproduction:** for each source, `git -C <repo> show <commit>:<path>` and take the kept
  line numbers; the excerpts are exact substrings of those lines.
