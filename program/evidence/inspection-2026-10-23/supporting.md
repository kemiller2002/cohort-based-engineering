# Supporting-repository inspection (read-only), 2026-10-23

> Agent-generated read-only inspection report (2026-10-23), kept as the evidence CURRENT-STATE.md cites. File and line references are to the commit named below.

Scope: /home/user/conditor, /home/user/echelon-registry, /home/user/kemiller2002/{percepta,forma,limen,aegis}.
All clones are shallow (one commit each); git history and most tags are NOT available. Only conditor has a local tag (v0.10.8).
Nothing was modified; no Praxis command was run.

## 0. Cross-cutting facts

- Every repo's `./praxis` launcher (praxis:17-18) prefers `.echelon/ros.json` `installedVersion`, falling back to `ros.json` `rosVersion`.
  - `.echelon/ros.json` installedVersion = **3.7.2** in all six repos; `.echelon/toolchain.json` = `{praxis: 3.7.2, ordo: 1.5.0}` in all six.
  - Root `ros.json` `rosVersion` is stale/inconsistent: conditor 3.7.1, registry 3.7.1, percepta 3.4.0, forma (3.x, truncated), limen 1.2.1, aegis 3.0.0. HANDOFF.md files likewise state older versions (conditor/registry HANDOFF.md:7 "Praxis 3.7.1"; percepta HANDOFF.md:7 "ROS 3.4.0"; forma HANDOFF.md:7 "ROS 3.1.4"; limen HANDOFF "ROS 1.2.1"; aegis HANDOFF.md:7 "ROS 3.0.0").
  - Effective installed Praxis: **3.7.2 everywhere** (launcher uses installedVersion).
- PROJECT-CHARTER.md is an unfilled Praxis template ("Define the practical problem…", line 14) in conditor, echelon-registry, limen, aegis. Only percepta (Mission section) and forma (charter:14) have real charters. Responsibility therefore comes from README/docs.
- HANDOFF.md in conditor, registry, percepta, forma, aegis is the bootstrap template ("No first vertical slice … accepted") and is stale relative to the README. Limen's HANDOFF is real.
- AGENTS.md only documents `.praxis-inbox/<requestId>.json` on a `praxis-inbox/...` branch (remote protocol; AGENTS.md:230 in most, forma:271, limen:572). **None documents `.praxis/inbox/documents/`** in AGENTS.md; only forma `experiments/RLP-001/REPORT.md:70` states "Praxis owns requirement intake (`.praxis/inbox/documents/`)".
- Search for "Rehearsal 3", "Causa" (whole word), "VAC", "approved release set": **zero hits** in all six repos. "cohort": one hit, conditor/docs/requirements-import.md:59 (ECIR-declared cohort execution must not run on an unchecked/unapproved blueprint). "release set" (resolved release set) appears heavily in conditor and registry (see §5).

## 1. Conditor (kemiller2002/conditor)

Responsibility: CONFIRMED. README.md:3-7 "establishes a governed engineering environment from an empty repository… resolve a declarative project manifest, install the selected Echelon capabilities, verify the result"; README:9-18 first slice (validate conditor.json → resolve pinned components → deterministic plan → lifecycle install → verify → write `.conditor/lock.json` only after success). Also adopt (README:70-103), upgrade --current (245-311), workstation bootstrap with receipts/ledger (348-358, docs/workstation.md), native installers verify SHA-256 (README:59-61).

Intake: no `.praxis/`, no input-documents dir. Requirements live in `requirements/CONDITOR-REQUIREMENTS.md`, `docs/requirements/*.md`. No pending intake documents.

Praxis: installed 3.7.2 (.echelon/ros.json:5). Own `conditor.json` pins praxis **3.1.4**, ordo 1.5.0, visual-engineering 1.0.0, communication-engineering 1.0.0, no `registryAuthority`, execution disabled. Conditor repo has **no `.conditor/` dir (no lock, no authority)** — it does not govern itself through Conditor; its conditor.json is inconsistent with its installed Praxis 3.7.2.

Release: v0.10.8 (git tag; release/requested-version.txt = 0.10.8; Registry has releases/conditor/0.8.0…0.10.8). Distribution: self-contained native CLI per platform (release/echelon.release-input.json), github-release, checksums + build-provenance attestation (referenced by registry spec rolling-upgrade-requirements.md:118-121).
Public contracts consumed by others: `conditor.json` schema (schemas/conditor.schema.json), lock schema v4 (schemas/conditor-lock.schema.json), `conditor compatibility --json` (schemas/conditor-compatibility.schema.json) — consumed by Registry REG-RU-007 CI; component contract (docs/component-contract.md), web-package and NuGet-feed upgrade contracts.

CI: .github/workflows/ci.yml (dotnet build + `tests/Conditor.Tests` runner, CLI plan smoke, component-schema conformance, Indy Init preset plan smoke, Ordo adoption matrix, Chrona-shaped channel move rehearsals 1.22→1.23→1.24→1.25 with real releases, exact echelon-current resolved-set fetch and digest check); registry-lifecycle-proof.yml; release.yml; release-orchestrator.yml; praxis-validation.yml; remote-*.yml.

## 2. Echelon Registry (kemiller2002/echelon-registry)

Responsibility: CONFIRMED (with nuance). README.md:3 "discovery and interoperability specification for independently installable Echelon systems"; README:57-77 distribution catalog (system/v2, release/v2, profile/v1, catalog-snapshot/v1, resolved-release-set/v1); README:79-115 moving `echelon-current` channel. It is the compatibility/selection authority for consumers via resolved release sets (Conditor decision 0001). It explicitly does NOT record installations (README:42-48 — project-administration owns that).

Intake: none (no .praxis, no input dirs). No pending documents.
Praxis: installed 3.7.2; conditor.json pins ordo 1.5.0, praxis 3.7.2 with registryAuthority sha256 ea1b39a0… (profile echelon-current 1.2.0). Has `.conditor/lock.json` (schema 4) with reviewSignal SDE-STRUCT-001 on tools/resolve-profile.fsx (519 lines).
Release: no tags/CHANGELOG; versioning is per-artifact (profile echelon-current version 1.25.0; resolver 0.1.0).
Public contracts: schemas/ (release-manifest, profile, catalog-snapshot, resolved-release-set, current-channel), `channels/echelon-current/*.json`, `contracts/installation-*.v1.schema.json`, `followup-create.v1`, `spec/repository-lifecycle-contract.md` (echelon.repository-lifecycle v1), `actions/release-contract` (GitHub Action consumers use to generate echelon.release/v2 manifests).
CI: distribution-conformance.yml (resolve profiles twice for determinism, regenerate current channel and fail on byte diff, REG-RU-007 check against latest released Conditor binary verified by checksum + attestation, fixture validation, lifecycle-contract fixtures, frozen Indy Init resolution + freeze receipt, release-contract fixture); praxis-validation.yml.

## 3. Percepta

Responsibility: CONFIRMED. README.md:40 "`percepta` compiles and verifies semantic UI contracts and rendered evidence"; :41 `percepta-repo` is the repository lifecycle; :66-87 "What Percepta governs"; PROJECT-CHARTER Mission/Thesis/Non-goals (not a design system/component library). README:3 also calls it "the Echelon Foundry UI system repository".
Intake: `.praxis/processed/INPUT-55fa8f7cf70c3cbb/` (source 2026-10-14-PERCEPTA-VIS-001.md + claim.json). **No `.praxis/inbox/` dir → no pending documents.** `requirements/` holds ECHELON-BASELINE, PERCEPTA-CONTRACTS, VISUAL-DECISION-EXPERIMENT.
Praxis: installed 3.7.2 (ros.json says 3.4.0). conditor.json: communication-engineering 1.0.0, ordo 1.5.0, praxis 3.7.2, visual-engineering 1.0.1 + registryAuthority ea1b39a0….
Release: Registry records percepta 0.1.0 (tag `percepta-repo-v0.1.0`, commit 3027983f, executable percepta-repo); package.json 0.1.0; npm launcher `@echelon-foundry/percepta-repository-lifecycle` 0.1.0 (distribution/). Conditor pins the Percepta screen package at commit 9e630773 (conditor README:332).
Contracts: ScreenContract model (docs/CONTRACT-MODEL.md, VERIFICATION-MODEL.md), `.percepta/contracts/`, repository lifecycle owning `.echelon/percepta.json` + AGENTS.md region.
CI: percepta-core.yml (build Core/Foundation/Playwright adapter/CLI/adversarial tests), percepta-repository-lifecycle(.yml, -release.yml), echelon-bootstrap.yml, limen-verify.yml, percepta-experiment-0002.yml, praxis-validation.yml.

## 4. Forma

Responsibility: CONFIRMED. README:12, 26-30 ("zero-runtime. Semantic HTML, CSS, design tokens, accessibility contracts, and visual patterns"); PROJECT-CHARTER.md:14 ("reusable visual, semantic, accessibility, motion, and communication foundation"), :16 HTML/CSS only. Layout catalog (requirements/LAYOUT-CATALOG.md), accessibility requirements, RLP relational-layout experiments.
Intake: `.praxis/inbox/documents/` present. **4 pending (unclaimed) documents**: `2026-10-21-RLP-001.md`, `2026-10-21-RLP-001-EXT-01.md`, `2026-10-22-RLP-002.md` (self-labelled "Unprocessed source material", line 3), `echelon-runtime-version-stamp.md` ("proposed source input", → RQ-FORMA-2026-A004). Caveat: RLP-001/002 are already cited as sources by research/experiments/EX-FORMA-2026-0001/0003 and experiments/RLP-001/REPORT.md:82, and RQ-FORMA-2026-A004 exists and 0.9.1 ships the runtime stamp — so the content was used but never claimed/moved through Praxis (no claim.json). Three processed claims exist (.praxis/processed/INPUT-a452…, -55d9…, -a8ac…; FORMA-COLOR-001/002, design-by-construction).
Praxis: installed 3.7.2. conditor.json: ordo 1.5.0, praxis 3.7.2, visual-engineering 1.0.1 + authority ea1b39a0…. README:21-24 still says "Ordo 1.3.0, ROS 3.1.4" (stale).
Release: package `@echelon-foundry/design-system`; package.json/CHANGELOG **0.9.1** (CHANGELOG.md:10); Registry knows 0.3.0, 0.4.1, 0.5.0, 0.6.1, 0.9.0 → **0.9.1 is not recorded in the Registry**. Sub-packages forma-conformance 0.2.0, forma-workflow 1.0.0.
Contracts: public HTML/class/token contracts under semver (CHANGELOG:3-4, QD-004); `runtime` entry point registers `window.__ECHELON_RUNTIME__` (ECHELON-RUNTIME-1).
CI: ~25 workflows incl. conformance.yml (Playwright chromium/firefox/webkit, character grid), design-system-pilot-validation.yml (zero-runtime boundary, motion, package contract, Figma contract), forma-site-validation, release-forma, publish, praxis-validation.

## 5. Limen

Responsibility: CONFIRMED. README.md:3 "explicit boundary that keeps browser capabilities separate from application authority"; :25-33 kernel vs engine via JSON-serializable data; :41-52 npm package is a TypeScript boundary, F#/.NET WASM consumers in-repo. HANDOFF objective "Keep Limen's browser boundary small and generic while proving … F# WebAssembly".
Intake: TWO locations. `input-document/` (requirments.md [sic], time-entry-state-machine-extension-request.md) — legacy, kept deliberately as evidence trail (docs/ROADMAP.md:143-150); and `.praxis/inbox/documents/echelon-runtime-version-stamp.md` (→ RQ-LIMEN-2026-A007) **pending/unclaimed**, although the feature is implemented (scripts/stamp-runtime.ts, test/runtime-version.test.ts, CHANGELOG, last commit "feat/runtime-version-stamp"). No `.praxis/processed/`.
Praxis: installed 3.7.2 (ros.json 1.2.1). conditor.json: ordo 1.5.0, praxis 3.7.2, visual-engineering 1.0.1 + authority ea1b39a0…. Limen is NOT declared in any consumer's conditor.json; registry spec rolling-upgrade-requirements.md:128-133 says Limen is pinned via package.json + .echelon/foundations.json.
Release: `@echelon-foundry/limen` package.json **0.9.1** (CHANGELOG:19, 2026-10-21); Registry knows 0.6.2, 0.7.0, 0.7.1, 0.8.0, 0.9.0 → **0.9.1 not recorded**. limen-fsharp 0.8.0/0.9.0 in Registry.
Contracts: `contract/*.contract.json` (adapters, coordination, core, credentials, environment, events, federation, files, focus, frozen …), conformance vectors (forms/http/routing/sessions/store…), lifecycle CLI init/status/verify/upgrade/doctor.
CI: ci.yml (npm ci, test:cli, build:cli, npm run check, real-Chrome smoke of F# WASM site), limen-verify.yml, pages.yml, publish.yml, praxis-validation.yml.

## 6. Aegis

Responsibility: CONFIRMED. README.md:3-7 "standard mechanism for handling and recovering from unexpected operational failure in .NET applications"; packages table (Core fault model/capture/redaction/recovery/escalation/presentation; Store.GitHub; Integration.GitHub); Scope README:44-51; `aegis-boundaries.json` declares fault boundaries (schema aegis/boundaries/v1).
Intake: `Input-documents/` (capital I) with 3 .txt files (initial, persistent logging, additional requirements). These were consumed: cited in docs/aegis/README.md:14, research/decisions/DF-AEGIS-2026-DBBD:12-13, DF-AEGIS-2026-0CA3:13, and .ros/events (work.completed REQ-INTAKE-001). No `.praxis/` dir → no Praxis-claimed intake, nothing pending in a Praxis inbox. Has `.dokimos/` and dokimos.yml.
Praxis: installed 3.7.2 (ros.json 3.0.0). conditor.json: ordo 1.5.0, praxis 3.7.2, visual-engineering 1.0.1 + authority ea1b39a0….
Release: Registry knows only `EchelonFoundry.Aegis.Core` **1.0.0** (nuget). Source fsproj Version = **2.0.0** for Core, Store.GitHub, Integration.GitHub (src/*/ *.fsproj:10); docs/aegis/README.md:201-242 describes 2.0.0 as a major release (Store.Malformed behaviour change). Whether 2.0.0 is published on nuget.org: **could not determine** (no tags in shallow clone). Either way, 2.0.0 is not in the Registry.
CI: build.yml (dotnet restore/build/test Aegis.sln), dokimos.yml (build/test evidence capture), publish-nuget.yml, praxis-validation.yml.

## 7. Compatibility evidence in depth

### Registry model
- `registry/systems-v2.json`: canonical identities.
- `releases/<system>/<ver>.release.json` (65 files, all `echelon.release/v2`, all releaseStage stable / lifecycleState active). There is **no "approved" field** in release manifests.
- `snapshots/echelon-current.catalog.json` (echelon.catalog-snapshot/v1; 16 systems, 50 release rows, each with manifest path+sha256). **Inclusion in the snapshot is the approval gate**: release files NOT in the snapshot are praxis 3.14.0, 3.15.0 and all 13 conditor releases (Conditor is not a profile component).
- `profiles/echelon-current.profile.json` v1.25.0: "Moving stable channel for the current Registry-approved Echelon repository environment. Version ranges select the newest compatible active stable releases from the channel catalog snapshot." allowedReleaseStages [stable]; semver ranges per component, required vs optional.
- `tools/resolve-profile.fsx` (profile + snapshot + platform → `echelon.resolved-release-set/v1` with exact version/tag/commit/release-manifest sha256/artifact sha256). `channels/echelon-current/{platform}.json` are generated, never hand-edited (README:81); `channel.json` binds profile sha256 83450d91…, snapshot sha256 7a394e98…, per-platform set digests (linux-x64 06026da5…). Hashes verified locally: all match.
- Immutable sets: `profiles/echelon-engineering.profile.json` (0.1.0: Praxis 3.6.0, Ordo 1.4.0), `echelon-engineering-0.2.0` (+Dokimos 0.2.0) with `resolved/echelon-engineering/0.2.0/*` (6 platforms); `dokimos-proof` 0.1.0; `freezes/indy-init-0.1.0.freeze.json` (echelon.environment-freeze/v1; exact pins praxis 3.6.0, ordo 1.4.0, percepta 0.1.0, aegis 1.0.0, limen 0.6.2, forma 0.3.0, folio 0.3.0, each with releaseManifestSha256; resolved-set sha for linux-x64/osx-arm64).
- Channel-move gate REG-RU-007 (spec/rolling-upgrade-requirements.md:95-126; README:84-87): echelon-current SHALL NOT select a version of a consumer-declared component (conformance/conditor-declared-components.json: arca, fides, folio, forma, limen-fsharp, ordo, praxis, summa-contracts, visual-engineering) that the latest released Conditor refuses; enforced in distribution-conformance.yml by `conformance/validate-conditor-qualification.fsx` against `conditor compatibility --json`. REG-RU-001..006 (auto registration PRs etc.) "not implemented" (spec:33-34).
- Signed attestations (REG-SIG-001..008): Conditor `trust/registry-release-keys.json` keys = [] ("Empty until the Echelon Registry signs release attestations; while empty, every project binding stays under exact per-version qualification").

### Newest approved compatible release set (echelon-current profile 1.25.0, linux-x64, set sha256 06026da5…)
Required: praxis 3.16.0, ordo 1.17.0, percepta 0.1.0, dokimos 0.6.0, visual-engineering 1.0.1, communication-engineering 1.0.0, tutela 0.1.0, aegis 1.0.0, limen 0.9.0, forma 0.9.0, folio 0.4.0.
Optional: strata 0.1.1, arca 0.5.0, fides 0.2.0, summa-contracts 0.1.0, limen-fsharp 0.9.0.
Conditor 0.10.8 qualifies every consumer-declared selection (components/*.component.json qualifiedVersions: praxis …3.14.0, 3.16.0; ordo …1.8.2, 1.17.0; forma …0.9.0; folio 0.3.0, 0.4.0; limen …0.9.0 [not 0.8.0]; visual-engineering 1.0.0, 1.0.1).

### What the six repos actually pin (older approved set)
All five consumer repos (registry, percepta, forma, limen, aegis) carry byte-identical `.conditor/authority/resolved-release-set.json` sha256 **ea1b39a0…** = profile **echelon-current 1.2.0** (sha 703de3a3…), linux-x64, catalogSnapshot bffd0e5a…: praxis 3.7.2, ordo 1.5.0, percepta 0.1.0, dokimos 0.2.0, visual-engineering 1.0.1, communication-engineering 1.0.0, tutela 0.1.0, aegis 1.0.0, limen 0.7.1, forma 0.4.1, folio 0.3.0, strata 0.1.0 (optional). They are 23 profile versions behind the channel but internally consistent. The 1.2.0 profile/snapshot are no longer in the registry tree (moving channel overwritten; only recoverable from git history, unavailable in this shallow clone, or from the consumer copies).

### Excluding newer-but-unapproved releases
1. Not in snapshot → not resolvable (praxis 3.14.0/3.15.0).
2. Not registered at all → invisible: forma 0.9.1, limen 0.9.1, aegis 2.0.0 exist in source but have no release manifest (REG-RU-001 gap).
3. Profile ranges + stable-only.
4. REG-RU-007 CI gate vs latest released Conditor.
5. Conditor side: README:231 "A newer upstream release is not automatically considered compatible merely because it exists"; README:251 "does not scrape product repositories for moving tags or infer that the highest GitHub release is compatible"; decision docs/decisions/0001-registry-version-authority.md: VersionConflict / AbsentFromAuthority refusals (src/Conditor.Core/RegistryAuthorityBinding.fs:35-77), no fallback to embedded catalog; embedded qualification still applies (Compatibility.fs validateWithAttested). upgrade --current needs explicit `--resolved-set` + `--resolved-set-sha256` + `--authorize <plan-digest>`, refuses downgrades and silent component additions (README:256-279, 309); refuses changed authority bytes after planning (Adoption.fs:633, CurrentUpgrade.fs:975).

### Conditor installation evidence
- `.conditor/lock.json` schema v4: full manifest + manifestSha256, per-component descriptorSha256, authority kind (`embedded-component-descriptor` or Registry authority), sourceReference, reviewSignals (README:247).
- `conditor.json` `registryAuthority` {kind resolved-release-set, path, sha256} + byte copy of the set in `.conditor/authority/`.
- Workstation: plan with digest, per-step typed receipts (file digest, `praxis --version`), append-only ledger `~/.conditor/workstation/ledger.jsonl`, ownership classes; "A step whose receipt already matches is reused" (docs/workstation.md:94-95); evidence docs/evidence/2026-10-02-registry-lifecycle-clean-host-proof.md (second application: all steps reused, zero drift).
- Durable environment receipt CON-INDY-050..054 (docs/requirements/indy-init-competition-proof.md:91-99; incl. resolved-set digest, artifact digests, and "verify a current environment against a prior receipt/release-set identity and explain drift") — document status "draft"; **no code references found** for an environment receipt. `conditor drift`/`status` partly cover drift.
- Profiles: profiles/echelon-engineering.profile.json (workstation profile, still Praxis 3.6.0 pins, not used for selection per docs/workstation.md:59-61), minimal.profile.json.
- Tests: RegistryAuthorityBindingTests, CurrentUpgradeTests (deterministic digest, stale authorization refused, zero remaining drift, opt-in only at selected version), AdoptionTests (unqualified refused), DeclaredWebBindingTests (no downgrade step), WorkstationSelectionTests (refuses downgrading installed praxis). Note: tests/Conditor.Tests/EchelonCurrent.fs pins a hybrid selection (praxis 3.16.0 but ordo 1.5.0, forma 0.5.0, folio 0.3.0) that no longer matches channel 1.25.0; `examples/indy-init.conditor.json` (praxis 3.16.0, ordo 1.5.0, forma 0.5.0, folio 0.3.0, limen 0.9.0) likewise does not match 1.25.0 despite Compatibility.fs notes saying "the indy-init preset follows echelon-current".

### A6 classification: **2 — Implemented but incomplete**
Implemented and tested: digest-pinned reuse of a prior Registry resolved set as repository-local authority; refusal of versions not selected by that authority; no scraping of newer tags; explicit authorized plans to move; receipt-matched reuse of installed binaries; Registry-side exclusion via snapshot + REG-RU-007 CI.
Incomplete: (a) durable environment receipt / verify-against-prior-receipt (CON-INDY-050..054) is draft-only; (b) echelon-current history is not retained as immutable in the registry tree (only consumers' byte copies; immutable sets exist only for echelon-engineering 0.1/0.2, dokimos-proof, indy-init freeze); (c) "approved" is implicit (snapshot inclusion + qualification), no explicit approval record; (d) attestation trust keys empty; REG-RU-001..006 not implemented so newer releases (forma 0.9.1, limen 0.9.1, aegis 2.0.0) are unregistered rather than explicitly assessed; (e) Conditor itself is not governed by its own lock/authority (conditor.json pins praxis 3.1.4 vs installed 3.7.2).

## 8. conditor.json inventory

| repo | praxis | ordo | dokimos | visual-eng | comm-eng | registryAuthority | lock |
|---|---|---|---|---|---|---|---|
| conditor | 3.1.4 | 1.5.0 | – | 1.0.0 | 1.0.0 | none | none |
| echelon-registry | 3.7.2 | 1.5.0 | – | – | – | ea1b39a0… (ec-current 1.2.0) | yes |
| percepta | 3.7.2 | 1.5.0 | – | 1.0.1 | 1.0.0 | ea1b39a0… | yes |
| forma | 3.7.2 | 1.5.0 | – | 1.0.1 | – | ea1b39a0… | yes |
| limen | 3.7.2 | 1.5.0 | – | 1.0.1 | – | ea1b39a0… | yes |
| aegis | 3.7.2 | 1.5.0 | – | 1.0.1 | – | ea1b39a0… | yes |

No repo declares Dokimos in conditor.json (Dokimos 0.2.0 is in the pinned resolved set; aegis has `.dokimos/` + dokimos.yml outside Conditor). All `execution.enabled: false`.

## 9. Could not determine
- Git history/tags (shallow clones): actual GitHub release lists for registry, percepta, forma, limen, aegis; whether Aegis 2.0.0 / Forma 0.9.1 / Limen 0.9.1 are published.
- Whether Praxis 3.7.2 natively processes `.praxis/inbox/documents/` (not run); inferred only from praxis.inbox-claim/1 claim files in percepta/forma.
- Historical content of echelon-current profile 1.2.0 and its snapshot (bffd0e5a…) inside the registry.
- Anything about Rehearsal 3, Causa, VAC: no mentions exist in these repos.
