# Reproducing VAC-002-P3

Everything runs in a Claude Code cloud container like the one used here: Linux x64, 2 CPUs, Ubuntu 24.04, Claude Code
2.1.309 at `/opt/node22/bin/claude`. The model endpoint is reached directly (no egress proxy for agents); NuGet is
not reachable.

## 1. Tools

```sh
curl -sS -o sdk.tgz https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.402/dotnet-sdk-10.0.402-linux-x64.tar.gz
mkdir -p /root/.dotnet && tar -xzf sdk.tgz -C /root/.dotnet
export DOTNET_ROOT=/root/.dotnet PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
```

**Other tools.** `jq`, `openssl`, `git` and `python3` (standard library only) are used by the scripts.

**No packages are needed.**

- The fixtures' tests run on the TestKit (`fixture/testkit/`, deviation D1).
- `p3.fsx` and `analyze.fsx` use only the .NET base library.

## 2. Repository state

```sh
git clone https://github.com/kemiller2002/cohort-based-engineering && cd cohort-based-engineering
git checkout experiment/vac-002-p3-authority-ablation
cd research/experiments/VAC-002/P3
sha256sum -c harness/FROZEN.sha256        # the Stage 2 freeze
```

**P2 lives in `../P2/`.** It is merged from `10e1adf`, which is PR #20 on PR #18's branch.

## 3. Unseal

Each store decrypts into `/home/user/.p3-sealed/<store>`:

```sh
unseal() { mkdir -p /home/user/.p3-sealed/$1 && openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass file:$2 -in $3 | tar -xz -C /home/user/.p3-sealed/$1; }
unseal p2   ../P2/sealed/p2-sealed.key                     ../P2/sealed/p2-sealed.tar.gz.enc
unseal p3d  sealed/discovery/p3d-sealed.key                sealed/discovery/p3d-sealed.tar.gz.enc
unseal p3d2 sealed/discovery-r2/p3d2-sealed.key            sealed/discovery-r2/p3d2-sealed.tar.gz.enc
unseal p3c  sealed/confirmatory/p3c-sealed.key             sealed/confirmatory/p3c-sealed.tar.gz.enc
```

Each `SEAL.json` gives the plaintext digest to check against.

## 4. Oracle validation (before any agent)

```sh
harness/corpus.sh check D01 D02 D03 D04 D05 D06 D07 D08 D09 D10 D11 D12   # RESULT: PASS (43 passed, 0 failed)
harness/corpus.sh check D13 D14 D15 D16                                   # RESULT: PASS (17 passed, 0 failed)
harness/corpus.sh check D17 D18 D19 D20 D21                               # RESULT: PASS (18 passed, 0 failed)
harness/corpus.sh check C01 C02 C03 C04 C05 C06                           # RESULT: PASS (22 passed, 0 failed)
for s in D01 D02 D03 D04 D05 D06 D07 D08 D09 D10 D11 D12 D13 D14 D15 D16 D17 D18 D19 D20 D21 C01 C02 C03 C04 C05 C06; do
  harness/p3.sh expose $s /tmp/expose; done                               # every check true (ARM-EXPOSURE-MANIFEST.json)
```

**Variant generators.** They rebuild every reference, trap and valid alternative from the P2 fixtures by exact
edits: `python3 /home/user/.p3-sealed/<store>/gen/<scenario>.py`.

## 5. Stand-in smoke (no model)

```sh
mkdir -p /home/user/.p3-state/SMOKE/D05-A-r1
echo "export FAKE_VARIANT=/home/user/.p3-sealed/p2/S05/ref FAKE_PLAN=<plan.json>" > /home/user/.p3-state/SMOKE/D05-A-r1/smoke.env
P3_CLAUDE=harness/smoke/fake-claude.sh P3_SEALED=/nonexistent P3_RESULTS=/tmp/smoke harness/p3.sh exec SMOKE D05 A 1
```

## 6. Executions

**Delete every plaintext store first.** `p3.sh exec` refuses to start while one exists.

```sh
rm -rf /home/user/.p3-sealed
harness/p3.sh queue S1A1 20261023 2 A 2 D01 D02 D03 D04 D05 D06 D07 D08 D09 D10 D11 D12 D13 D14 D15 D16   # Stage 1, round 1
harness/p3.sh queue S1R2 20261025 2 A 3 D17 D18 D19 D20 D21                                              # round 2 (A3)
harness/p3.sh queue S1B  20261027 2 B 3 D17 D18 D19 D20 D21                                              # sizing run (A4)
harness/p3.sh queue S2   20261031 2 ABCDE 3 C01 C02 C03 C04 C05 C06                                      # Stage 2 (CR-1)
harness/p3.sh spent                                                                                      # P3 total
```

**`results/S1/` and `results/S1-void/`** record the void first attempt (amendment A1).

## 7. Scoring, review and analysis

```sh
# unseal (§3), then for each RUN and execution:
harness/p3.sh score RUN SCEN ARM REP [final|implement]
# blinded review
harness/review/bundle.sh /home/user/.p3-state/review-RUN /home/user/.p3-state/review-RUN-mapping.json SEED RUN
harness/review/review.sh /home/user/.p3-state/review-RUN R1 & harness/review/review.sh /home/user/.p3-state/review-RUN R2 & wait
dotnet fsi --quiet --exec ../P2/harness/review/agreement.fsx /home/user/.p3-state/review-RUN OUT
# Stage 1 and the sizing run
dotnet fsi --quiet --exec harness/analyze.fsx stage1 results/RUN META_P2 META_STORE BASIS results/RUN/review/adjudicated.json results/RUN/stage1-analysis.json
# sample size
dotnet fsi --quiet --exec harness/sizing.fsx 0.55 0.0667 "0.6667,1,1,0,1" 20000 20261029
# Stage 2
dotnet fsi --quiet --exec harness/analyze.fsx stage2 /home/user/.p3-sealed/p3c/meta.json /home/user/.p3-sealed/p3c/basis.json results/S2/review/adjudicated.json results/S2/stage2-analysis.json results/S2
```

**Review seeds.** S1A1 20261024, S1R2 20261026, S1B 20261028, S2 20261101.

**Review adjudication.** The adjudicated file is built from R1 and R2 by the `jq` program recorded in each
`review/README.md`. R3 runs only where the two disagree on the primary label.

## 8. Agent workspaces

Every execution's repository, with every commit, is archived in `results/RUN/workspaces/X.bundle`. The heads in each
`setup.json` resolve in it:

```sh
git clone results/S2/workspaces/C03-E-r1.bundle /tmp/x && git -C /tmp/x checkout "$(jq -r .heads.final results/S2/C03-E-r1/setup.json)"
```

Turn streams are kept in harness state, not in the repository. Their usage summaries are in each `turn-*.json`,
and every brief an agent received is in `brief-*.md`.
