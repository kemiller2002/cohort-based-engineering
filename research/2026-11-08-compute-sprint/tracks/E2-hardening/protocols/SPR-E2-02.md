# SPR-E2-02 — Evidence-path hardening for plain `work complete` (E-F-01)

Preregistered 2026-11-08 ~14:40 EST, before the patched build. Start revision praxis 12bf995 (+ SPR-E2-01 commit in the
same scratch branch; patch file is the incremental diff).

## Design under test
- Default ON: every `--evidence TYPE=PATH` given to plain `work complete` must resolve (after `..` normalisation and
  symlink resolution of every path component) inside the repository root; otherwise the command is refused before any
  state change with `ERROR PRX.EVIDENCE.OUTSIDE_REPOSITORY: ...` (exit 1).
- Explicit opt-out: `ros.json` `workProtocol.allowExternalEvidence: true` restores the 3.25.0 behaviour.
- Binding: for each accepted evidence file, a record {workItem, type, path, sha256, commit (HEAD), committedAtHead}
  is appended to tracked `.ros/evidence/bindings.jsonl` immediately before the completion is persisted.

## Hypothesis
H3: with the default policy, E NX-1 / V2 case A (`--evidence tests=/etc/hostname`) is refused with
OUTSIDE_REPOSITORY; an in-repo test log is accepted and gets a binding whose sha256 equals `sha256sum` of the file and
whose commit equals `git rev-parse HEAD`.

## Attack cases
- B1 = NX-1: tests=/etc/hostname.  B2: tests=../../../../etc/hostname (relative traversal).
- B3: in-repo symlink `logs/t.log -> /etc/hostname`.  B4: in-repo directory symlink `d -> /etc`, tests=d/hostname.

## Positive controls
- P1: tests=logs/test-run.log (a real file produced by running a small test command in the fixture) accepted; binding
  recorded with correct digest/commit.  P2: with `allowExternalEvidence: true`, B1 is accepted (opt-out works, and the
  binding still records the digest).  P3: nonexistent in-repo path still refused with the old message.

## Measures / success criteria
B1–B4 refused (exit 1, code present); P1–P3 behave as stated; existing tests pass, or failing ones are listed and shown
to encode the old behaviour (out-of-repo evidence). VERIFIED if all hold on the built binary.

## Known non-goals (stated in advance)
The binding proves *which bytes at which commit* were cited, not that tests ran or passed; an agent can still write a
fake log inside the repository. That residual is E-F-01's deeper half and is addressed only by verified completion.
