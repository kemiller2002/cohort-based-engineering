# Reproducing VAC-002-P2

Every step runs in a Claude Code cloud container like the one used here: Linux x64, 4 CPUs, Claude Code 2.1.308 at
`/opt/node22/bin/claude`, authenticated through the inherited environment. Paths are defaults; override them with
the `P2_*` variables in `harness/p2.sh`.

## 1. Tools

```sh
curl -sSL -o dotnet-install.sh https://dot.net/v1/dotnet-install.sh
bash dotnet-install.sh --version 10.0.402 --install-dir /root/.dotnet
export DOTNET_ROOT=/root/.dotnet PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
```

`jq`, `openssl`, `git` and `python3` are used by the shell scripts. No other dependency. The F# scripts use only the
.NET base library, except `p2.fsx`, which references `FSharp.SystemTextJson` 1.3.13 from NuGet.

## 2. Unseal

```sh
cd research/experiments/VAC-002/P2
mkdir -p /home/user/.p2-sealed
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass file:sealed/p2-sealed.key -in sealed/p2-sealed.tar.gz.enc \
  | tee >(sha256sum) | tar -xz -C /home/user/.p2-sealed   # sha256 = sealed/SEAL.json .plaintextTarGzSha256
```

The key is published at `sealed/p2-sealed.key` after the pilot was scored. Before that it was kept outside every
repository.

## 3. Oracle validation (before any agent)

```sh
harness/corpus.sh check            # expected last line: RESULT: PASS (43 passed, 0 failed)
harness/tests/authz-cases.sh       # expected last line: RESULT: PASS
```

The sealed generators rebuild every reference, trap and valid alternative from the base by exact edits:

```sh
for s in /home/user/.p2-sealed/gen/S*.py; do python3 "$s"; done
```

`gen/S01.py` derives its alternative from the sealed S01 reference. S01's reference and trap were taken from
VAC-002's sealed `ref-L04` and arm B's `Policy` defect.

## 4. Stand-in smoke (no model)

`harness/smoke/fake-claude.sh` stands in for the CLI:

```sh
FAKE_VARIANT=<dir with a variant's files> FAKE_PLAN=<decisions.json> P2_CLAUDE=harness/smoke/fake-claude.sh \
P2_SEALED=/nonexistent P2_RESULTS=/tmp/smoke P2_WORK=/tmp/smoke-work harness/p2.sh exec SMOKE1 S04 E
```

## 5. Pilot

The plaintext must be absent; `p2.sh exec` refuses to start while `/home/user/.p2-sealed/S01` exists.

```sh
rm -rf /home/user/.p2-sealed
harness/p2.sh exec SMOKE S05 A; harness/p2.sh exec SMOKE S05 E      # model smoke
harness/p2.sh queue P1 20261023 3                                     # the pilot: 60 executions, 3 at a time
harness/p2.sh cost P1                                                 # spend, each session counted once
```

## 6. Scoring and analysis

```sh
# unseal (§2), then:
for d in results/P1/S*-?; do x=$(basename $d); harness/p2.sh score P1 ${x%-*} ${x##*-}; done
for d in results/P1/S*-[DE]; do x=$(basename $d); harness/p2.sh score P1 ${x%-*} ${x##*-} implement; done
dotnet fsi --quiet --exec harness/analyze.fsx results/P1 /home/user/.p2-sealed/meta.json results/P1/analysis.json
```

## 7. Blinded review

```sh
harness/review/bundle.sh P1 /home/user/.p2-state/review-P1 /home/user/.p2-state/review-P1-mapping.json 20261024
harness/review/review.sh /home/user/.p2-state/review-P1 R1 & harness/review/review.sh /home/user/.p2-state/review-P1 R2 & wait
dotnet fsi --quiet --exec harness/review/agreement.fsx /home/user/.p2-state/review-P1 results/P1/review
```

Adjudication by R3 runs on `disagreements.jsonl` (`REVIEW.md` gives the exact command used).

## 8. Agent workspaces

Every execution's repository, with every commit the agent and the harness made, is archived as a git bundle in
`results/P1/workspaces/SCEN-ARM.bundle`. The heads in each `setup.json` resolve in it:

```sh
git clone results/P1/workspaces/S01-B.bundle /tmp/S01-B && git -C /tmp/S01-B checkout "$(jq -r .heads.final results/P1/S01-B/setup.json)"
```

Turn streams and transcripts are kept in harness state, not in the repository. Their usage summaries are in
`turn-*.json`.
