# Repository access preflight

**Run:** 2026-11-08T13:43:40-05:00. **Tool:** `inventory/preflight.py` (unit tests in `inventory/test_preflight.py`).
**Method:** metadata and permissions from the GitHub search API (`gh api search/repositories`, the only gh use this environment permits); default branch and HEAD from `git ls-remote --symref`; content retrieval proven by a depth-1 blobless clone and `git ls-tree`; latest release approximated by highest semver git tag (GitHub Releases objects not queried here; Track C records releases); open PRs from `search/issues is:pr is:open`. No test pushes were made.

**Classification counts:** METADATA_ONLY 7, READ_WRITE 59

**Namespaces:** `kemiller2002` (searched; 197 repositories visible). `echelon-foundry` exists as a GitHub Organization (search/users), but `search/repositories q=org:echelon-foundry` returned HTTP 422 ("cannot be searched either because the resources do not exist or you do not have permission"): classified UNKNOWN — not evidence that it has no repositories. No manifest references it.
Manifest scan of all local checkouts found no other Echelon owner (other owners are third-party dependencies).
131 visible `kemiller2002` repositories were judged unrelated to Echelon (personal, talks, household) and excluded from the inventory; they are listed in REPOSITORY-ACCESS.json `excluded`.

**Write permission** has two columns: what GitHub reports for the account, and whether this session is scoped to push. Specialists push nowhere; only the Research Director integrates, and only to `claude/echelon-compute-sprint-nov8-bkaw2t` in cohort-based-engineering.

| Repository | Class | Vis. | Arch. | Default | Revision | Latest tag | GH push | Session push | Agents | Prio | Open PRs | Problems |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [kemiller2002/cohort-based-engineering](https://github.com/kemiller2002/cohort-based-engineering) | READ_WRITE | public | False | main | 2c4434e50 | — | True | yes | RD,D,H | 1 | 2 | — |
| [kemiller2002/Indy-init](https://github.com/kemiller2002/Indy-init) | READ_WRITE | public | False | main | dae2347d2 | indy-init-requirements-v4.1.6 | True | yes | B,A,E | 1 | 3 | — |
| [kemiller2002/indy-init-rehearsal-001](https://github.com/kemiller2002/indy-init-rehearsal-001) | READ_WRITE | public | False | main | dd63ab4ab | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/indy-init-rehearsal-002](https://github.com/kemiller2002/indy-init-rehearsal-002) | READ_WRITE | private | False | main | b053d1da4 | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/indy-init-rehearsal-003](https://github.com/kemiller2002/indy-init-rehearsal-003) | READ_WRITE | private | False | main | 59cf4d215 | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/indy-init-rehearsal-004](https://github.com/kemiller2002/indy-init-rehearsal-004) | READ_WRITE | private | False | main | 78a1b15aa | — | True | yes | B,A,F,E | 1 | 4 | — |
| [kemiller2002/indy-init-rehearsal-005](https://github.com/kemiller2002/indy-init-rehearsal-005) | READ_WRITE | private | False | main | b972cb446 | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/indy-init-rehearsal-006](https://github.com/kemiller2002/indy-init-rehearsal-006) | READ_WRITE | private | False | main | 41fb6d62e | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/indy-init-rehearsal-007](https://github.com/kemiller2002/indy-init-rehearsal-007) | READ_WRITE | private | False | main | f61493fa0 | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/indy-init-rehearsal-008](https://github.com/kemiller2002/indy-init-rehearsal-008) | READ_WRITE | private | False | main | fd8fba983 | — | True | yes | B,A,F,E | 1 | 1 | — |
| [kemiller2002/indy-init-rehearsal-009](https://github.com/kemiller2002/indy-init-rehearsal-009) | READ_WRITE | private | False | main | 0e760501b | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/indy-init-rehearsal-010](https://github.com/kemiller2002/indy-init-rehearsal-010) | READ_WRITE | private | False | main | 95b3ed4df | — | True | yes | B,A,F,E | 1 | 0 | — |
| [kemiller2002/causa](https://github.com/kemiller2002/causa) | READ_WRITE | public | False | main | 97c0a98fb | — | True | no | B,F | 1 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/causa-data](https://github.com/kemiller2002/causa-data) | READ_WRITE | public | False | main | c6940d50e | causa-storage-v1.1.0 | True | no | B | 2 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/causa-acceptance-r10](https://github.com/kemiller2002/causa-acceptance-r10) | READ_WRITE | private | False | main | e1e79666d | — | True | no | B,E | 1 | 0 | attached mid-session via add_repo (read) after initial METADATA_ONLY result; GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/causa-testing-repo](https://github.com/kemiller2002/causa-testing-repo) | READ_WRITE | public | False | main | 46b4d5258 | — | True | no | B,E | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/causa-write-test](https://github.com/kemiller2002/causa-write-test) | READ_WRITE | public | False | main | 891c24de3 | — | True | no | B,E | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/gate-proof-r10](https://github.com/kemiller2002/gate-proof-r10) | READ_WRITE | public | False | proof | 0e1ef29bd | — | True | no | B,E | 2 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/Indy-init-audits](https://github.com/kemiller2002/Indy-init-audits) | READ_WRITE | private | False | main | 10aededce | — | True | no | B,E | 1 | 0 | attached mid-session via add_repo (read) after initial METADATA_ONLY result; GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/research-documents](https://github.com/kemiller2002/research-documents) | READ_WRITE | private | False | main | b372a7f8a | — | True | no | D,A,H | 1 | 7 | attached mid-session via add_repo (read) after initial METADATA_ONLY result; GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/praxis](https://github.com/kemiller2002/praxis) | READ_WRITE | public | False | main | 12bf99512 | v3.25.0 | True | yes | C,A,E | 1 | 16 | — |
| [kemiller2002/ordo](https://github.com/kemiller2002/ordo) | READ_WRITE | public | False | main | db6d39ed2 | v1.20.0 | True | yes | C,D | 1 | 12 | — |
| [kemiller2002/dokimos](https://github.com/kemiller2002/dokimos) | READ_WRITE | public | False | main | fecbe0c51 | dokimos-v0.11.1 | True | no | C,E,D | 1 | 3 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/conditor](https://github.com/kemiller2002/conditor) | READ_WRITE | public | False | main | 528ef4576 | v0.10.21 | True | no | C,E | 1 | 6 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/echelon-registry](https://github.com/kemiller2002/echelon-registry) | READ_WRITE | public | False | main | 575240233 | — | True | no | C | 2 | 4 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/aegis](https://github.com/kemiller2002/aegis) | READ_WRITE | public | False | main | 2c28b6e20 | — | True | no | C,E | 2 | 4 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/vigila](https://github.com/kemiller2002/vigila) | READ_WRITE | public | False | main | feab75517 | — | True | no | C,E | 3 | 3 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/tutela](https://github.com/kemiller2002/tutela) | READ_WRITE | public | False | main | 476dc6823 | v0.1.0 | True | no | C | 3 | 3 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/vitium](https://github.com/kemiller2002/vitium) | READ_WRITE | public | False | main | 02730f8b7 | — | True | no | C | 3 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/fides](https://github.com/kemiller2002/fides) | READ_WRITE | public | False | main | 78ff31e0e | v0.2.0 | True | no | C,E | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/iter](https://github.com/kemiller2002/iter) | READ_WRITE | public | False | main | de9f97c55 | — | True | no | C | 3 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/arca](https://github.com/kemiller2002/arca) | READ_WRITE | public | False | main | 8cfa064ab | v0.7.0 | True | no | C | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/percepta](https://github.com/kemiller2002/percepta) | READ_WRITE | public | False | main | 4a5368823 | percepta-semantic-v0.4.0 | True | no | C,F | 2 | 4 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/limen](https://github.com/kemiller2002/limen) | READ_WRITE | public | False | main | 743cdb9be | v0.9.1 | True | no | C,F | 1 | 6 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/forma](https://github.com/kemiller2002/forma) | READ_WRITE | public | False | main | dba08a005 | v0.13.0 | True | no | C,F | 1 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/forma-studio](https://github.com/kemiller2002/forma-studio) | READ_WRITE | public | False | main | 904d3b455 | — | True | no | C,F | 2 | 2 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/folio](https://github.com/kemiller2002/folio) | READ_WRITE | public | False | main | 217d644e3 | v0.4.1 | True | no | C,F | 2 | 2 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/specula](https://github.com/kemiller2002/specula) | READ_WRITE | public | False | main | 7bdeba3b0 | — | True | no | C,F | 3 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/signal](https://github.com/kemiller2002/signal) | READ_WRITE | public | False | main | e19101f53 | — | True | yes | C,F | 2 | 2 | — |
| [kemiller2002/mercatus](https://github.com/kemiller2002/mercatus) | READ_WRITE | public | False | main | a841f3038 | — | True | yes | G,C | 1 | 1 | — |
| [kemiller2002/observer](https://github.com/kemiller2002/observer) | READ_WRITE | public | False | main |  | — | True | no | C | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here; repository exists but is empty (no commits); nothing to research |
| [kemiller2002/census](https://github.com/kemiller2002/census) | READ_WRITE | public | False | main | 7ed3a1204 | — | True | no | C | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/summa](https://github.com/kemiller2002/summa) | READ_WRITE | public | False | main | 8b0e93ea7 | contracts-v0.1.0 | True | no | C | 3 | 2 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/chrona](https://github.com/kemiller2002/chrona) | READ_WRITE | public | False | main | 481e389be | — | True | no | C | 3 | 4 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/tekmerion](https://github.com/kemiller2002/tekmerion) | READ_WRITE | public | False | main | 45a7ce831 | v0.2.0 | True | no | C | 3 | 6 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/strata](https://github.com/kemiller2002/strata) | READ_WRITE | public | False | main | 6bd1cd0e2 | v0.1.1 | True | no | C | 3 | 2 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/armamentarium](https://github.com/kemiller2002/armamentarium) | READ_WRITE | public | False | main | 48cecde55 | — | True | no | C | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/echelon-diagnostic-framework](https://github.com/kemiller2002/echelon-diagnostic-framework) | READ_WRITE | public | False | main | 41fea6ffc | — | True | no | C | 3 | 7 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/echelon-engineering-system](https://github.com/kemiller2002/echelon-engineering-system) | READ_WRITE | public | False | main | 4ca2f981e | — | True | no | C | 2 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/echelon-foundry](https://github.com/kemiller2002/echelon-foundry) | READ_WRITE | public | False | main | 8c6b45358 | — | True | no | G,C | 2 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/time-tracking-application](https://github.com/kemiller2002/time-tracking-application) | READ_WRITE | public | False | main | 38a0b657e | — | True | yes | A,D | 2 | 3 | — |
| [kemiller2002/time-entry-state-machine](https://github.com/kemiller2002/time-entry-state-machine) | READ_WRITE | private | False | main | c120adaf4 | — | True | yes | D | 2 | 2 | — |
| [kemiller2002/time-tracking-data](https://github.com/kemiller2002/time-tracking-data) | READ_WRITE | private | False | main | bed7232df | — | True | yes | A | 2 | 1 | — |
| [kemiller2002/construct-010-trials](https://github.com/kemiller2002/construct-010-trials) | READ_WRITE | public | False | main | fb55bc4d0 | — | True | no | D | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/SDE-Engineering-Trial-1-Greenfield-Construction](https://github.com/kemiller2002/SDE-Engineering-Trial-1-Greenfield-Construction) | METADATA_ONLY | private | False | claude/time-entry-sde-requirements-00nzbr |  | — | True | no | D,B | 3 | 2 | git probe: fatal: could not read Username for 'https://github.com': terminal prompts disabled; private repository not attached to this session; git read refused by proxy; remediation: add_repo (read); GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/SDE-Engineering-Trial-2-Greenfield-Construction](https://github.com/kemiller2002/SDE-Engineering-Trial-2-Greenfield-Construction) | METADATA_ONLY | private | False | main |  | — | True | no | D,B | 3 | 3 | git probe: fatal: could not read Username for 'https://github.com': terminal prompts disabled; private repository not attached to this session; git read refused by proxy; remediation: add_repo (read); GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/disposable-test-repository](https://github.com/kemiller2002/disposable-test-repository) | METADATA_ONLY | private | False | main |  | — | True | no | E | 3 | 1 | git probe: fatal: could not read Username for 'https://github.com': terminal prompts disabled; private repository not attached to this session; git read refused by proxy; remediation: add_repo (read); GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/ROS-WorkerDaemon](https://github.com/kemiller2002/ROS-WorkerDaemon) | METADATA_ONLY | private | False | main |  | — | True | no | C | 3 | 4 | git probe: fatal: could not read Username for 'https://github.com': terminal prompts disabled; private repository not attached to this session; git read refused by proxy; remediation: add_repo (read); GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/framework-engineering](https://github.com/kemiller2002/framework-engineering) | READ_WRITE | public | False | main | d77473c37 | — | True | no | C | 3 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/visual-engineering](https://github.com/kemiller2002/visual-engineering) | READ_WRITE | public | False | main | 1bda5ff24 | visual-engineering-v1.0.1 | True | no | F | 3 | 1 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/application-visual-language](https://github.com/kemiller2002/application-visual-language) | METADATA_ONLY | private | False | main |  | — | True | no | F | 3 | 3 | git probe: fatal: could not read Username for 'https://github.com': terminal prompts disabled; private repository not attached to this session; git read refused by proxy; remediation: add_repo (read); GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/sales-and-marketing](https://github.com/kemiller2002/sales-and-marketing) | READ_WRITE | public | False | main | 72a6ecd16 | — | True | no | G | 2 | 2 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/echelon-organization-administration](https://github.com/kemiller2002/echelon-organization-administration) | METADATA_ONLY | private | False | main |  | — | True | no | G | 3 | 2 | git probe: fatal: could not read Username for 'https://github.com': terminal prompts disabled; private repository not attached to this session; git read refused by proxy; remediation: add_repo (read); GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/millers-Indy](https://github.com/kemiller2002/millers-Indy) | READ_WRITE | public | False | main | 1cffc7134 | — | True | no | B | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/holiday-list-creator](https://github.com/kemiller2002/holiday-list-creator) | READ_WRITE | public | False | main | 243b165ee | — | True | no | B | 3 | 0 | GitHub reports push permission, but this session is not scoped to push here |
| [kemiller2002/holiday-list](https://github.com/kemiller2002/holiday-list) | METADATA_ONLY | private | False | main |  | — | True | no | B | 3 | 0 | git probe: fatal: could not read Username for 'https://github.com': terminal prompts disabled; private repository not attached to this session; git read refused by proxy; remediation: add_repo (read); GitHub reports push permission, but this session is not scoped to push here |

## Renamed repositories (manifest aliases resolved by HEAD SHA)

| Referenced name | Resolves to | Evidence |
|---|---|---|
| kemiller2002/Repository-Operating-System | kemiller2002/praxis | ls-remote HEAD 12bf99512 matches canonical HEAD |
| kemiller2002/repository-operating-system | kemiller2002/praxis | ls-remote HEAD 12bf99512 matches canonical HEAD |
| kemiller2002/state-directed-engineering | kemiller2002/ordo | ls-remote HEAD db6d39ed2 matches canonical HEAD |
| kemiller2002/echelon-signal | kemiller2002/signal | ls-remote HEAD e19101f53 matches canonical HEAD |
| kemiller2002/echelon-design-system | kemiller2002/forma | ls-remote HEAD dba08a005 matches canonical HEAD |
| kemiller2002/research-publisher | kemiller2002/tekmerion | ls-remote HEAD 45a7ce831 matches canonical HEAD |
| kemiller2002/consulting-company | kemiller2002/echelon-foundry | ls-remote HEAD 8c6b45358 matches canonical HEAD |
| kemiller2002/echelon-print-components | kemiller2002/folio | ls-remote HEAD 217d644e3 matches canonical HEAD |

## Completion gate

**PASSED at 2026-11-08 ~14:00 EST.** All 66 inventory repositories have an explicit classification, and so do both namespaces (`kemiller2002` searched; `echelon-foundry` UNKNOWN). No inventory repository is NOT_FOUND or ACCESS_DENIED.

## Missing access procedure: outcomes

| Repository | Initial result | Exact failure | Renamed/transferred? | Action | Blocked investigations |
|---|---|---|---|---|---|
| research-documents | METADATA_ONLY | `fatal: could not read Username for 'https://github.com': terminal prompts disabled` (private, not attached) | No: search lists it under kemiller2002 with matching name | Attached via `add_repo` (read); cloned `b372a7f` | **Unblocked.** Track D re-analysis of frozen raw evidence; Track A token data |
| causa-acceptance-r10 | METADATA_ONLY | same | No | Attached (read); cloned `e1e7966` | **Unblocked.** Track B R10 acceptance; Track E acceptance-spoofing audit |
| Indy-init-audits | METADATA_ONLY | same | No (canonical case `Indy-init-audits`) | Attached (read); cloned `10aeded` | **Unblocked.** Track B audit records; Track E |
| SDE-Engineering-Trial-1/2-Greenfield-Construction | METADATA_ONLY | same | No | Not attached (priority 3) | None critical. Track D could use them as historical Ordo trial data; recorded as a gap |
| disposable-test-repository | METADATA_ONLY | same | No | Not attached; Track E uses local fixtures instead | None |
| ROS-WorkerDaemon | METADATA_ONLY | same | No | Not attached (priority 3) | Track C cannot inspect it; inventory entry is metadata-only |
| application-visual-language | METADATA_ONLY | same | No | Not attached (priority 3) | Track F loses one historical visual-language source; public `visual-engineering` is readable |
| echelon-organization-administration | METADATA_ONLY | same | No | Not attached (priority 3) | Track G loses internal org notes; non-blocking |
| holiday-list | METADATA_ONLY | same | No | Not attached; public sibling `holiday-list-creator` is readable | None |
| observer | UNKNOWN (first run) | blobless clone: `warning: You appear to have cloned an empty repository` | No | Reclassified READ_WRITE; repository is empty (no commits) | None. Nothing to research |
| echelon-foundry (org) | UNKNOWN | `search/repositories q=org:echelon-foundry` → HTTP 422 | n/a | Not retried. No manifest references the org, and all Echelon repositories resolve under kemiller2002 | None known |

**Remediation (owner action, optional):** attach the remaining private repos with `add_repo` if Ordo trial history (SDE trials) or ROS-WorkerDaemon is wanted. Confirm whether the `echelon-foundry` organization is meant to hold repositories. If it is, grant this GitHub App access to it.

## Ordering note

Tracks A–G started at 13:37 EST, about 20 minutes before this addendum was received. Until the gate passed they read only local checkouts and public clones, and all of those repositories are now verified READ_WRITE. No cross-repository experiment had started before verification. The three newly attached private repositories were sent to the relevant tracks once the gate passed.
