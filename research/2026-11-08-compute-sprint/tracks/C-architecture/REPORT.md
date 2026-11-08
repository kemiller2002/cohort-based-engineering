# Track C — Echelon Architecture Audit (2026-11-08)

> Committed by RD-000 from C-001's final hand-back text (the harness refuses subagent report-file writes; DECISION-LOG D-010). Worker final commit: `0899de6`.
>
> Outputs:
> - `inventory.json`: 35 systems × 15 fields.
> - `dependency-graph.json` / `.dot`: 35 nodes, 378 edges (206 contract/schema, 64 package-ref, 63 CLI-invocation, 45 doc-only-claim).
> - `findings.json`: C-F-01..18.
> - `complexity-reductions.json`: CR-01..09.
> - `tools/`: `archgraph.py` and `build_inventory.py`, with 34 passing tests; `tools/run.sh` regenerates everything.
> - `data/`.

## Method
- **Sources.** 33 public repositories were cloned read-only into `/home/user/ext` (revisions in `data/source-revisions.tsv`), plus local Indy-init and indy-init-rehearsal-010.
- **Edge extraction.** `tools/archgraph.py` derives typed edges from:
  - Directory.Packages.props, *.fsproj, package.json, NuGet.config;
  - conditor.json and its authority file;
  - `.echelon/{ros,sde,limen,tutela,…}.json` installed manifests and foundations.json;
  - limen.config.json and aegis-boundaries.json;
  - JSON `schema` references;
  - workflow commands, `npx @echelon-foundry/*` and `uses: kemiller2002/*`;
  - README mentions that have no code or config edge, recorded as doc-only claims.
- **Pin baseline.** Pins are compared with the approved set **echelon-current 1.37.0** (owner-approved 2026-11-05, registry commit 89db708).
- **Release dates.**
  - Praxis and Ordo: GitHub Releases (MCP).
  - All other repositories: the tagged commit's date, because the Releases API was not in this session's MCP scope.
  - Aegis: the Registry's NuGet release record, because the repository has no tags.

## Findings

| ID | Finding | Class |
|---|---|---|
| C-F-01 | Ecosystem-wide pin staleness. 23 of 33 repos install Praxis 3.7.2. 15 bind their Conditor authority to set 1.2.0 and 9 to sets 1.3.0–1.24.0, against the approved 1.37.0. Of 375 consumer pins, 169 match the approved set and 200 are behind. The repos that produce the set are themselves on 1.2.0: registry, dokimos, limen, forma, percepta, aegis and tutela. Only causa and rehearsal-010 match. | VERIFIED |
| C-F-02 | Those 23 repos cannot run Praxis 3.8–3.25 features: the claim lifecycle, `work finish`, attested completion and the requirements manifest. | SUPPORTED |
| C-F-03 | There are two catalogs of qualified versions: Conditor's built-in `components/*.component.json` and the Registry catalog. Every new set requires a Conditor release: 13 Conditor releases for 12 sets in 14 days, under "RELEASE TRIGGER (qualifies echelon-current 1.Y.0)" commits. The two catalogs disagree on which components they cover. | VERIFIED |
| C-F-04 | Conditor can already qualify version ranges from signed Registry sets, but its trusted Registry keys list is empty (`registry-release-keys.json:4`). This is unchanged since 10-23. | VERIFIED |
| C-F-05 | Praxis pins Ordo.Core 1.8.2, which has no constructibility contract. Praxis carries its own 1,043 lines of Ordo contract admission using the same ORDO.CONTRACT.* codes. Ordo 1.20.0 now provides that module. | VERIFIED |
| C-F-06 | Iter (F# routing) has zero consumers. It duplicates the released Limen.Routing, which praxis, chrona, signal and summa use. | VERIFIED |
| C-F-07 | The profile marks 12 components as required. Causa and rehearsal-010 lack dokimos, tutela, visual-engineering, communication-engineering and percepta-semantic. Tutela is installed in only 2 repos. Dokimos reaches CI by 3 different install paths. | VERIFIED |
| C-F-08 | Aegis 2.0.0 has been in source and docs since 10-05 but was never released. All 16 consumers use 1.0.0. | VERIFIED |
| C-F-09 / C-F-10 | Components are used outside the Registry. Causa pins forma-workflow, which Conditor qualifies but the Registry does not catalog. Specula uses Limen F# 0.9.1, which the Registry has not qualified. | VERIFIED |
| C-F-11 | Arca 0.6.0 was a breaking change. It holds Chrona, Signal and Summa on Arca 0.5.0, and Chrona on set 1.31.0. | VERIFIED |
| C-F-12 | Indy-init contains about 39k lines of tooling. Its requirements-compiler (16k lines) reads Praxis's on-disk files directly and re-implements ledger, continuation and token-economics logic. | SUPPORTED |
| C-F-13 | No repository runs dependency vulnerability scanning (no CodeQL, audit step, OSV or Dependabot). | VERIFIED |
| C-F-14 | README inaccuracies. Summa's README describes a project-administration hub, but the code is an invoicing ledger. Dokimos assigns security to "Aegis/Tutors", but neither has that role. Seven READMEs state stale ROS or Praxis versions. | VERIFIED |
| C-F-15 | Several repos have nothing usable: observer is empty, census and armamentarium are documentation only, and vitium is a proposal. Their stated scopes overlap Summa, Conditor+Registry, and Dokimos/Specula. Limen.Outbox overlaps Arca's offline queue. | SUPPORTED |
| C-F-16 | Conditor's default versions are stale (Praxis 3.6.0, Ordo 1.4.0, Forma 0.5.0). They apply only when a request omits a version. | SUPPORTED |
| C-F-17 | About 53 tool-owned files are copied into each governed repo. 23 repos carry an identical copy of Ordo 1.5.0's `.sde` directory. | VERIFIED |
| C-F-18 | The owner approved 12 release sets in 13 days. Combined with C-F-03, one component release costs a component release, a Conditor release, a Registry set and an owner approval. | VERIFIED |

## Changes since CURRENT-STATE (2026-10-23)
- **Releases.**

  | Component | 2026-10-23 | Now |
  |---|---|---|
  | Praxis | 3.19 | 3.25 |
  | Ordo | 1.17 | 1.20 |
  | Dokimos | 0.7 | 0.11.1 |
  | Forma | 0.9.1 | 0.13.0 |
  | Conditor | 0.10.8 | 0.10.21 |
  | Release set | 1.26 | 1.37 |

  percepta-semantic is new and now at 0.4.0.
- **The §7 Dokimos gap is resolved.** Set 1.27.0 added the verified-completion pairing.
- **The set 1.2.0 pin count was understated.** CURRENT-STATE named 5 repos; the measured count is 15.
- **Praxis no longer self-pins.** It has no `.echelon/ros.json`; its `foundations.json` declares Ordo 1.8.2 and Aegis 1.0.0.
- **Unchanged:** Aegis and the empty trust keys.

## Complexity reductions (ranked)
1. **CR-01:** Sign Registry sets and turn on Conditor's existing range qualification. This ends the lockstep Conditor releases.
2. **CR-02:** Move every repository to the approved set in one wave, producers first, or freeze the dormant ones.
3. **CR-03:** Archive iter and observer; freeze vitium and armamentarium.
4. **CR-04:** Move Praxis to Ordo.Core 1.20.0 and delete its duplicate contract admission.
5. **CR-05:** Either install the profile's "required" components or make them optional.
6. **CR-06:** Have installers reference context by version instead of copying it into each repo.
7. **CR-07:** Move the durable parts of Indy-init's tooling behind Praxis and Dokimos contracts.
8. **CR-08:** Close the small catalog and version gaps.
9. **CR-09:** Add one dependency-vulnerability step to the shared foundations-verify workflow, which 12 repos already call.

None of these needs new infrastructure.

## Gaps
- **CI status:** checked only for praxis, ordo, mercatus and signal, all green on main. The other repos are outside this session's MCP scope, so their CI is NOT TESTED.
- **Coverage:** line coverage was not measured. inventory.json reports test-file to source-file counts instead.
- **Builds:** none were run; Track F owns builds.
- **Graph rendering:** Graphviz is not installed, so the .dot file is unrendered.
- **Not checked:**
  - whether the duplicated implementations behave the same;
  - the Vitium/Census overlap, which is judged from stated scope only.
- **Not inspected:** research-documents (private).
