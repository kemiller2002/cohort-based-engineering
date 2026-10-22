# VAC-002 P1 Layer 3: blinded decision review

| File | Contents |
|---|---|
| `items.jsonl` | The 186 blinded items (seeded sample, seed 20261022, `PROTOCOL.md` §9) |
| `blind-mapping.json` | Blinded key → run, arm, unit, decision id. It was held outside the bundle during review |
| `labels-R1-*.jsonl`, `labels-R2-*.jsonl` | Two independent reviewer sessions (`harness/layer3/review.sh`) |
| `disagreements.jsonl`, `disagreements-items.jsonl`, `labels-R3-*.jsonl` | The one disagreement and its adjudication by R3 |
| `agreement.json` | Agreement statistics |
| `adjudicated.jsonl`, `summary.json` | Final labels, unblinded, and the per-arm summary, with reviewer cost |
| `RUBRIC.md` | The rubric as given to reviewers: VAC-001's rubric plus the A2 additions |

**Not included.**

| Material | Why |
|---|---|
| Repository snapshots (`trees/`) | Rebuilt by `analyze.fsx blind` from the arm workspaces |
| Reviewer transcripts | Private session transcripts, not committed |

**Void bundles.** Two earlier bundles were voided before any valid label: amendments A2 and A3 in `PROTOCOL.md`.
Their labels are not used.

**Commands run:**

```sh
dotnet fsi --quiet --exec harness/analyze.fsx blind results P1 /home/user/vac-work /home/user/.vac2-state/layer3-P1 20261022 /home/user/.vac2-state/layer3-P1-mapping.json
harness/layer3/review.sh /home/user/.vac2-state/layer3-P1 R1    # and R2, concurrently
python3 -I harness/layer3/adjudicate.py agree /home/user/.vac2-state/layer3-P1
harness/layer3/review.sh /home/user/.vac2-state/layer3-P1 R3 /home/user/.vac2-state/layer3-P1/disagreements-items.jsonl
python3 -I harness/layer3/adjudicate.py final /home/user/.vac2-state/layer3-P1 /home/user/.vac2-state/layer3-P1-mapping.json results/P1/decision-dataset.jsonl
```
