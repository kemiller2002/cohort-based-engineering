# Reproducing VAC-002

Every step below runs in a Claude Code cloud container like the one used here: Linux x64, 4 CPUs, Claude Code
2.1.308 at `/opt/node22/bin/claude`, authenticated through the inherited environment. Paths are defaults; each is
overridable (`VAC2_*` variables in `harness/vac2.sh`).

## 1. Tools

```sh
# .NET SDK 10.0.402 and the .NET 8 runtime (for Ordo), into /root/.dotnet
curl -sSL -o dotnet-install.sh https://dot.net/v1/dotnet-install.sh
bash dotnet-install.sh --version 10.0.402 --install-dir /root/.dotnet
bash dotnet-install.sh --channel 8.0 --install-dir /root/.dotnet
export DOTNET_ROOT=/root/.dotnet PATH=/root/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1

mkdir -p /home/user/.vac2-tools
# archcheck (ARCH-001 verifier)
dotnet publish research/architectural-correctness/verifier/src/Archcheck/Archcheck.fsproj -c Release -o /home/user/.vac2-tools/archcheck
# Ordo 1.17.0 at bb43c26 and Praxis 3.19.0 at 986211c
git clone https://github.com/kemiller2002/ordo /tmp/ordo && git -C /tmp/ordo fetch --depth 1 origin bb43c26c106f4cbe972234636c5c67edc235c188 \
  && git -C /tmp/ordo worktree add /home/user/.vac2-tools/ordo-src bb43c26c106f4cbe972234636c5c67edc235c188
dotnet build /home/user/.vac2-tools/ordo-src/src/Sde.Cli/Sde.Cli.fsproj -c Release
git clone https://github.com/kemiller2002/praxis /tmp/praxis && git -C /tmp/praxis fetch --depth 1 origin 986211c19161bab339eebc565fb4d8edb2007d38 \
  && git -C /tmp/praxis worktree add /home/user/.vac2-tools/praxis-src 986211c19161bab339eebc565fb4d8edb2007d38
dotnet build /home/user/.vac2-tools/praxis-src/src/Praxis.Cli -c Release
```

Expected digest: `sde.dll` sha256 `37c52bf39cf043be5215edc1cb65df63b3f0b132ffc6d37c95b9662cfce7d6a7`. Every setup
file records the sha256 of the tools it used.

## 2. Unseal the hidden material

```sh
cd research/experiments/VAC-002
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass file:sealed/vac002-sealed.key -in sealed/vac002-sealed.tar.gz.enc \
  | tee >(sha256sum) | tar -xz -C /home/user/.vac2-sealed     # the sha256 equals sealed/SEAL.json .plaintextTarGzSha256
```

`sealed/vac002-sealed.key` is published only after the run; before that, the key stays outside every repository.

## 3. Corpus self-check

```sh
fixture/check.sh /home/user/.vac2-sealed /home/user/.vac2-state/check | tee fixture/check-output.txt
```

The expected last line is `RESULT: PASS`. The script checks:

- every reference passes every cumulative oracle, the repository tests and `archcheck`;
- every trap passes the repository tests and fails its target;
- the base fails L01's oracle;
- the dependency update alone breaks L09.

To rebuild contracts and `task.json` (Ordo verdicts included):

```sh
python3 -I fixture/make-contracts.py fixture /home/user/.vac2-tools/ordo-src/src/Sde.Cli/bin/Release/net8.0/sde /home/user/.vac2-sealed
```

## 4. Harness smoke (no model)

```sh
VAC2_RESULTS=/tmp/smoke harness/smoke/smoke-chain.sh SMOKE F    # stand-in agent applies the sealed references
```

It exercises stage, turn, gate, repair, verified state, the dependency change, conflict units and post-hoc scoring.

## 5. The pilot

Seal or move the plaintext oracle out of reach, then start one chain per arm, all concurrently. The launch order
comes from `random.Random(20261022).sample`:

```sh
TASKS="L01 L02 L03 L04 L05 L06 L07 L08 L09 L10 L11 L12"
for arm in $(python3 -c 'import random; print(*random.Random(20261022).sample(list("ABCDEF"),6))'); do
  harness/vac2.sh setup P1 $arm
  nohup harness/vac2.sh chain P1 $arm $TASKS > /home/user/.vac2-state/P1-$arm.log 2>&1 &
done
```

**Budget.** After each unit boundary, total the `cli-estimate` cost:

```sh
jq -s 'map(.usage.costUsdCli // 0) | add' results/P1/*/turn-*.json
```

At $95, create `/home/user/.vac2-state/P1/STOP`. Every chain then stops before its next unit (`BUDGET.md`).

## 6. Scoring and analysis

```sh
# unseal (section 2), then score every unit's final attempt and, for gated arms, attempt 1
for arm in A B C D E F; do for u in $(seq 1 12); do
  harness/vac2.sh score P1 $arm $u
  [ -f results/P1/$arm/gate-$u-2.json ] && harness/vac2.sh score P1 $arm $u 1
done; done
dotnet fsi --quiet --exec harness/analyze.fsx summary results P1 fixture /home/user/.vac2-sealed
dotnet fsi --quiet --exec harness/plots.fsx results/P1/analysis.json results/P1/figures
dotnet fsi --quiet --exec harness/analyze.fsx dataset results P1
```

## 7. Layer 3

```sh
dotnet fsi --quiet --exec harness/analyze.fsx blind results P1 /home/user/vac-work /home/user/.vac2-state/layer3-P1 20261022 /home/user/.vac2-state/layer3-mapping.json
harness/layer3/review.sh /home/user/.vac2-state/layer3-P1 R1
harness/layer3/review.sh /home/user/.vac2-state/layer3-P1 R2
python3 -I ../VAC-001/harness/adjudicate.py agree /home/user/.vac2-state/layer3-P1
# R3 adjudicates the disagreements: review.sh BUNDLE R3 BUNDLE/disagreements-items.jsonl
python3 -I ../VAC-001/harness/adjudicate.py final /home/user/.vac2-state/layer3-P1 /home/user/.vac2-state/layer3-mapping.json results/P1/decision-dataset.jsonl
```

## 8. Confirmatory runs

Confirmatory runs are not authorized without a spending ceiling. To run them:

1. Build L13–L25 (and the 50- and 100-change extensions) the same way, following `TASK-CORPUS.md` §4.
2. Re-run the self-check and the freeze.
3. Set the replicate count from `PILOT-RESULTS.md` §5.
4. Run `vac2.sh chain R25 ARM ...` per replicate.
