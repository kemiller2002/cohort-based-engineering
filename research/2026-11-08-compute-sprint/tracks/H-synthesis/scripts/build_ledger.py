"""Build claims-ledger.json for Track H. Pure data + light joins against track findings and V1/V2 verdicts.

Usage: python3 -I build_ledger.py <tracks_dir> <out_path>
"""
import json
import os
import sys

TRACKS = sys.argv[1]
OUT = sys.argv[2]

# claimId -> (consequence rank, consequence if wrong, cross-track support ids, publication-use flag)
C = {
    # A economics
    "A-F-01": ("high", "Every cost figure in the sprint and any external cost claim inherits this total.", ["V1:A-F-01"], "cost baseline"),
    "A-F-03": ("high", "Coordinator-context ADR (ADR-S05) and the largest estimated saving rest on it.", ["V1:A-F-03"], "ADR-S05"),
    "A-F-04": ("medium", "Caching strategy and cost-structure statements would be wrong.", [], "outline-2"),
    "A-F-05": ("medium", "Fixed-prefix ~30% share drives the 'governance overhead' narrative; carry model is an ESTIMATE.", ["D:VAC-001 controls", "A:CONSTRUCT-008"], "outline-2"),
    "A-F-06": ("medium", "Rework share is cited for review/fix policy; categories are judgement.", ["B-F-11"], "outline-2"),
    "A-F-07": ("high", "ADR-S02 (.ros out of merge path) scope; the 'no app-code conflicts' half is already contradicted.", ["B-F-09", "V1:A-F-07", "A2:SPR-A2-01"], "ADR-S02"),
    "A-F-08": ("medium", "Dispatch/parallelism investment decisions.", ["V1:A-F-08"], "outline-2"),
    "A-F-09": ("low", "Reread-reduction tooling priority.", [], None),
    "A-F-10": ("medium", "Any duration metric built on Praxis wall_ms.", ["X-22"], "datasets"),
    "A-F-11": ("medium", "Runner capacity decisions.", ["B-F-08"], None),
    "A-F-12": ("high", "Headline '67% of CI minutes wasted' is the most quotable number in the sprint.", ["B-F-08"], "outline-2"),
    "A-F-13": ("high", "A2 CI-cache prototype and the 8% saving estimate.", ["A2 (pending)"], "outline-2"),
    "A-F-14": ("medium", "CI latency statements.", [], None),
    "A-F-16": ("high", "'Process instructions cost more than they save' would change guidance policy; n=3 pilots.", ["G-F-08", "D:VAC-001 controls"], "outline-2"),
    # B forensics
    "B-F-01": ("high", "'No run reached acceptance' is the sprint's top-line readiness statement.", ["G-F-11"], "outline-1"),
    "B-F-02": ("high", "R2 INVALID recomputation underpins the overclaim narrative.", ["G-F-11"], "outline-1"),
    "B-F-03": ("high", "ADR-S04 (mandatory dry run) depends on it; prevalence counts are one analyst's curation.", ["A-F-13", "C-F-12", "B2 (pending)"], "ADR-S04"),
    "B-F-04": ("high", "Overclaim narrative; attribution to computed verdict not established (see X-05).", ["E-F-02", "B-F-16"], "outline-1"),
    "B-F-05": ("medium", "Persistence-as-component recommendation.", [], None),
    "B-F-06": ("medium", "Live-checks-early recommendation; observational.", ["B-F-14"], None),
    "B-F-07": ("high", "Invalidates R5/R6 comparisons; also reproduces an audit verdict of DEVIATION.", [], "outline-1"),
    "B-F-08": ("medium", "Hardened CI template recommendation.", ["A-F-12", "A-F-11"], "outline-2"),
    "B-F-09": ("high", "ADR-002 evidence; conflict counts differ from A2's pre-scan (X-03).", ["A-F-07", "V1:A-F-07"], "ADR-S02"),
    "B-F-11": ("medium", "Review timing policy; no controlled comparison.", ["A-F-06"], None),
    "B-F-12": ("medium", "Owner-readiness preflight recommendation.", ["E-F-07", "E-F-08"], None),
    "B-F-13": ("medium", "Upstream-closure tracking recommendation.", ["C-F-09", "C-F-03"], None),
    "B-F-14": ("medium", "Contradicts the R10 report's own statement; branch metadata only.", ["E-F-16"], None),
    "B-F-16": ("high", "Actions-confirmed R1 overclaim; publishable example if verified.", ["G-F-11"], "outline-1"),
    # C architecture
    "C-F-01": ("high", "35-version skew drives CR-02 and the ecosystem catch-up wave.", ["C-F-02", "E-F-01"], "ADR-S01"),
    "C-F-02": ("high", "Explains why verified completion cannot run in most repos; mapping not re-executed.", ["E-F-01", "G-F-07"], "outline-1"),
    "C-F-03": ("high", "ADR-S01 (signed Registry sets) rests on the dual-catalog/lockstep claim.", ["C-F-18", "B-F-13"], "ADR-S01"),
    "C-F-04": ("high", "ADR-001 assumes the range-qualification path works once a key is trusted; not executed.", [], "ADR-S01"),
    "C-F-05": ("medium", "CR-04 deletion of 1,043 lines; behavioural equivalence not tested.", [], None),
    "C-F-07": ("medium", "'required' components not enforced.", [], None),
    "C-F-08": ("low", "Aegis 2.0.0 unreleased; NuGet not queried directly.", [], None),
    "C-F-09": ("medium", "Corroborates B-F-13 forma-workflow defect.", ["B-F-13"], "ADR-S01"),
    "C-F-12": ("medium", "CR-07 (move Indy-init tooling behind Praxis/Dokimos).", ["E-F-02"], "ADR-S03"),
    "C-F-13": ("high", "Security posture statement; org-level settings invisible.", ["E-F-13", "E-F-10"], None),
    "C-F-14": ("low", "README accuracy.", ["G-F-10"], None),
    "C-F-18": ("medium", "Approval-churn cost argument for ADR-001; owner time not measured.", ["C-F-03"], "ADR-S01"),
    # E security
    "E-F-01": ("high", "'Every complete state is self-declared' is the strongest governance claim in the sprint.", ["G-F-07", "C-F-02"], "outline-1"),
    "E-F-02": ("high", "ADR-S03 (trusted acceptance job) and the 'computed verdict is not independent' conclusion.", ["B-F-04", "C-F-12"], "ADR-S03"),
    "E-F-03": ("medium", "Claim-guard fix.", [], None),
    "E-F-04": ("medium", "Documented limit; server-side verification recommendation.", [], None),
    "E-F-05": ("medium", "'verified' label semantics.", [], None),
    "E-F-06": ("high", "Positive control: attested mode works on 3.25.0. If wrong, ADR-S03 fallback (Dokimos attested) fails.", [], "ADR-S03"),
    "E-F-07": ("high", "If branch protection actually exists via rulesets, several E findings drop in severity; rulesets unreadable.", ["B-F-12"], "ADR-S03"),
    "E-F-08": ("medium", "Owner attestation by review login; not executed.", ["E-F-07"], None),
    "E-F-09": ("medium", "Release attestation scope; not executed (dispatch prohibited).", [], None),
    "E-F-13": ("medium", "No lock files; supply-chain posture.", ["C-F-13"], None),
    "E-F-14": ("high", "'No live credential found' would be dangerous if wrong; heuristic scan; ext/full unscanned.", [], None),
    "E-F-15": ("medium", "'No prompt injection found'; keyword scan only.", [], None),
    "E-F-16": ("low", "causa-acceptance-r10 role.", ["B-F-14"], None),
    # G market
    "G-F-01": ("high", "Rules out a standalone governed-agent-platform product.", [], "outline-3"),
    "G-F-02": ("high", "Defines the narrow defensible claim; Kiro absence from one docs page.", ["E-F-06"], "outline-3"),
    "G-F-03": ("medium", "Cost telemetry is not a wedge.", [], "outline-3"),
    "G-F-04": ("medium", "Problem existence (trust gap); surveys self-selected.", [], "outline-3"),
    "G-F-05": ("medium", "Executive-evidence gap; McKinsey via secondary coverage.", [], "outline-3"),
    "G-F-06": ("high", "Regulatory timing; legal applicability needs counsel; OJ text not fetched.", [], "outline-3"),
    "G-F-07": ("high", "Flagship differentiator not in use; status data as of 2026-10-23.", ["E-F-01", "C-F-02"], "outline-1"),
    "G-F-08": ("high", "'Overhead without measured quality gain'; fixture ceiling effects.", ["A-F-16", "D:VAC-001"], "outline-2"),
    "G-F-12": ("medium", "Platform-dependency positioning; SO 2026 editorial highlights only.", [], "outline-3"),
    "G-F-13": ("low", "Context only; no SAM derived.", [], None),
    # B2 dry-run replay (wave 3)
    "B2-F-01": ("high", "Sizes ADR-S04's benefit: 4/8 brief (robust 2/8), 7/11 extended; matching rules partly finalised after first runs.", ["X-09", "DECISION-LOG D-022"], "ADR-S04"),
    "B2-F-02": ("medium", "R10-AUTH reproduces exactly pre-T0 (55/55 causes).", ["B-F-03"], "ADR-S04"),
    "B2-F-03": ("medium", "Approvals-format blockers catchable pre-T0.", ["B-F-12"], "ADR-S04"),
    "B2-F-04": ("medium", "Frozen-plan suite commands fail on pinned SDK pre-T0.", ["B-F-03"], "ADR-S04"),
    "B2-F-05": ("medium", "FSharp.Core skip detectable pre-T0; not preregistered.", ["B-F-13"], "ADR-S04"),
    "B2-F-08": ("high", "Semantic contract defects pass the whole pinned pipeline: the uncovered class that limits ADR-S04.", ["X-23"], "ADR-S04"),
    "B2-F-10": ("medium", "Dry-run cost is seconds per rehearsal (loaded host).", [], "ADR-S04"),
    # D experiments
    "D-F-03": ("high", "VAC-001 continuity saving is one of the few positive results and bears on ADR-S05; chain-level p=0.25.", ["X-12", "G-F-08"], "ADR-S05"),
    "D-F-05": ("medium", "Fresh-from-verified +86% (one chain) is the main counter-evidence to a coordinator cap.", ["X-12"], "ADR-S05"),
    "D-F-07": ("medium", "VAC-002 P3 underpowered; affects how its null result is cited.", ["X-15"], None),
    "D-F-08": ("medium", "Replicate counts used to size FX experiments; lower bounds.", [], "future-experiments"),
    "D-F-09": ("medium", "Incremental no-op build ~4% of clean CPU; one fixture.", ["X-25", "A-F-13"], "outline-2"),
    "D-F-10": ("medium", "Surface edits cost ~a clean build.", ["X-25"], None),
    "D-F-11": ("medium", "Affected-test run ~4% of full suite CPU; selection safety untested.", ["X-25"], "outline-2"),
    # A2 remediation
    "A2-F-01": ("high", "ADR-S02 core result: driver removes every .ros conflict on replay (v2 rule added after v1 16/26).", ["A-F-07", "B-F-09"], "ADR-S02"),
    "A2-F-02": ("high", "Driver preserves records; validate cannot detect duplicate lines (negative control).", [], "ADR-S02"),
    "A2-F-03": ("medium", "Real team merge error in R10 (dropped WI-0003); single instance.", [], "outline-2"),
    "A2-F-04": ("medium", "Bounds ADR-S02: 9 merges still need humans.", ["X-02"], "ADR-S02"),
    "A2-F-05": ("medium", "Praxis documented ordering rule fails on real histories: policy change needed.", [], "ADR-S02"),
    "A2-F-08": ("medium", "Release binary output byte-identical to source-built verifier; attestation not verified.", ["E-F-09"], "future-experiments"),
    "A2-F-09": ("medium", "~550 min saving ESTIMATE from caching; single determinism probe.", ["A-F-13", "D-F-09"], "future-experiments"),
    # C2 signed registry prototype
    "C2-F-02": ("high", "Range qualification works end to end with a trusted key.", ["C-F-04"], "ADR-S01"),
    "C2-F-05": ("high", "Attestation covers contract claim, not set integrity: limits what ADR-S01 can promise.", [], "ADR-S01"),
    "C2-F-08": ("high", "CR-01 needs new Registry-side infrastructure and process (contradicts 'no new infrastructure').", ["X-07"], "ADR-S01"),
    # B3 semantic checks / B4 spec-preflight
    "B3-F-01": ("medium", "Semantic check catches R8 INV-04 pre-T0; answer-informed design.", ["B4-F-01"], "ADR-S04"),
    "B3-F-02": ("medium", "Semantic check catches R8 command-body gap; does not generalise (B3-F-04).", ["B4-F-01"], "ADR-S04"),
    "B4-F-01": ("high", "Existing spec-preflight reproduces R8 catches with 0 control false alarms: reuse instead of new tooling.", ["B3-F-01", "B3-F-02"], "ADR-S04"),
    "B4-F-05": ("medium", "Indy-init CI drops the carrier check (no --catalog).", [], "future-experiments"),
    "B4-F-07": ("high", "Both semantic tools are lexically tuned; generality unproven.", ["B3-F-04"], "ADR-S04"),
    # D2 agent experiment
    "D2-F-02": ("high", "Governance block costs +6% tokens, +55% wall at equal acceptance (n=4/arm; Holm p=0.086 tokens).", ["A-F-16", "G-F-08", "D-F-04"], "outline-2"),
    "D2-F-03": ("low", "Checklist produces artefacts; value unmeasured.", [], None),
    # F fsharp-wasm
    "F-F-01": ("medium", "Untrimmed WASM payload R8/R9; single snapshot.", [], None),
    "F-F-02": ("medium", "Startup times; contended host, emulated 4G.", [], None),
    "F-F-03": ("high", "R10 global no-store fetch override re-downloads 10.1 MB per warm load; root cause a Limen gap.", ["F-F-12"], "future-experiments"),
    "F-F-07": ("medium", "Edit-publish loop ~10 s fixed WASM cost.", ["D-F-09"], None),
    "F-F-08": ("medium", "Agent F# compile errors are mostly type/name and quickly fixed.", ["F-F-09"], None),
    "F-F-09": ("medium", "CI failures are infrastructure, not compile errors; 5 logs sampled.", ["B-F-08", "A-F-12"], None),
    "F-F-10": ("medium", "WASM interpreter locals limit statically checkable; reproduces R5.", ["B-F-13"], None),
    "F-F-13": ("medium", "Existing Limen contract tooling unused in every rehearsal.", ["X-26"], None),
    "F-F-14": ("low", "Folio declared but not integrated (R10).", ["C-F-07"], None),
    "F-F-15": ("medium", "Accessibility: 0 axe violations on reachable routes; R10 contrast traced to known Forma tokens.", [], None),
    # E2 hardening prototypes
    "E2-F-01": ("medium", "Claim-guard fix refuses E-F-03; A1c residual bypass if marker never committed.", ["E-F-03"], "future-experiments"),
    "E2-F-02": ("medium", "Queue/event cross-check detects hand-edited completions; 0 FP on 1,881 rows.", ["E-F-11"], "future-experiments"),
    "E2-F-03": ("high", "Evidence containment + digest binding refuses E-F-01-style evidence with no suite impact.", ["E-F-01"], "future-experiments"),
    "E2-F-04": ("medium", "Claim-marker fix conflicts with Praxis invariant I8 (7 tests): owner decision.", ["X-26"], "future-experiments"),
    "E2-F-05": ("high", "Verifier-signed flow refuses fabricated bundles Indy-init accepts (local uid separation only).", ["E-F-02", "V2:E-F-02"], "ADR-S03"),
    "F-F-17": ("medium", "29-defect UI pattern set: 6 catchable by existing tools, 13 need new contracts; hand-curated.", ["X-26"], None),
}

# Verdict ids that cover track finding ids under another name
VERDICT_ALIASES = {"SPR-D2-01": ["D2-F-02", "D2-F-03"]}

# H-001 notes where a verifier's verdict covers only part of the claim
SCOPE_NOTES = {
    "E-F-07": "V2 verified the VERIFIED parts (protected=false, no rulesets via rules/branches endpoint, no CODEOWNERS). The SUPPORTED part (agent token admin, agent holds signing key) was not re-verified.",
    "E-F-02": "Ledger verifier only. requirements-compiler verify-plan untested by E and V2 (FX-03).",
    "B-F-01": "True but vacuous for 6 of 11 runs that never produced a computed verdict (V2 note). Cite as 'no run reached computed acceptance; 5 produced a non-accepting computed verdict, 6 produced none'.",
    "B-F-02": "Not acceptable is robust; the specific label INVALID is anachronistic (77 of 83 reasons are later-schema absences). Substantive reason ADRP-016 NOT_RUN alone gives INCOMPLETE.",
    "B-F-03": "Holds as 'first refusal that ended the governed verdict'; does NOT hold as 'dominant blocker' for R8 and is doubtful for R9, R10: product and verification incompleteness would independently have prevented acceptance.",
}

# Which verification track is assigned to each source track
ASSIGNED = {"A": "V1", "G": "V1", "B": "V2", "C": "V2", "E": "V2", "A2": "V3", "C2": "V3", "B4": "V3", "D2": "V3"}
TRACKNAME = {"A": "A-economics", "B": "B-forensics", "C": "C-architecture", "E": "E-security", "G": "G-market", "B2": "B2-dryrun", "D": "D-experiments", "A2": "A2-remediation", "C2": "C2-signed-registry", "B3": "B3-semantic", "B4": "B4-preflight", "D2": "D2-agent-experiment", "F": "F-fsharp-wasm", "E2": "E2-hardening"}


def prefix(cid):
    return cid.split("-F-")[0]


def load_findings(track_dir):
    p = os.path.join(TRACKS, track_dir, "findings.json")
    if not os.path.exists(p):
        p = f"/home/user/sprint-wt/{track_dir}/research/2026-11-08-compute-sprint/tracks/{track_dir}/findings.json"
    d = json.load(open(p))
    items = d if isinstance(d, list) else d["findings"]
    return {f["id"]: f for f in items}


def load_verdicts(name):
    for base in (
        f"/home/user/sprint-wt/{name}/research/2026-11-08-compute-sprint/tracks/{name}/verdicts.json",
        os.path.join(TRACKS, name, "verdicts.json"),
    ):
        if os.path.exists(base):
            try:
                d = json.load(open(base))
            except json.JSONDecodeError:
                return {}, base + " (unparseable at read time)"
            items = d if isinstance(d, list) else d.get("verdicts", d.get("claims", []))
            out = {}
            for v in items:
                cid = v.get("claimId") or v.get("id")
                out[cid] = v
                # expand combined ids such as "A2-F-01/02" and known experiment aliases
                if "/" in cid and "-F-" in cid:
                    head, nums = cid.rsplit("-F-", 1)
                    for n in nums.split("/"):
                        out.setdefault(f"{head}-F-{n.zfill(2)}", dict(v, coveredVia=cid))
                for alias in VERDICT_ALIASES.get(cid, []):
                    out.setdefault(alias, dict(v, coveredVia=cid))
            return out, base
    return {}, None


def load_v1_pending():
    p = "/home/user/sprint-wt/V1-verification/research/2026-11-08-compute-sprint/tracks/V1-verification/CHECKPOINT.md"
    pend = set()
    if os.path.exists(p):
        for line in open(p):
            parts = [x.strip() for x in line.split("|")]
            if len(parts) > 3 and parts[1][:2] in ("A-", "G-", "B-", "C-", "E-") and parts[2] == "pending":
                pend.add(parts[1])
    return pend


findings = {}
for t in TRACKNAME.values():
    findings.update(load_findings(t))

v1, v1src = load_verdicts("V1-verification")
v2, v2src = load_verdicts("V2-verification")
v3, v3src = load_verdicts("V3-verification")
v1_pending = load_v1_pending()

entries = []
for cid, (rank, cons, support, use) in C.items():
    f = findings[cid]
    cls = f.get("classification")
    if cls not in ("VERIFIED", "SUPPORTED"):
        raise SystemExit(f"{cid} is {cls}, not VERIFIED/SUPPORTED")
    vt = ASSIGNED.get(prefix(cid))
    vmap = {"V1": v1, "V2": v2, "V3": v3}.get(vt, {})
    if cid in vmap:
        v = vmap[cid]
        iv = {"by": vt, "status": "done", "verdict": v.get("verdict"),
              "independence": v.get("independence"),
              "discrepancies": v.get("discrepancies", []),
              "verifierNotes": v.get("notes")}
        if v.get("coveredVia"):
            iv["coveredVia"] = v["coveredVia"]
        if cid in SCOPE_NOTES:
            iv["scopeNote"] = SCOPE_NOTES[cid]
    elif vt == "V1" and cid in v1_pending:
        iv = {"by": vt, "status": "queued", "verdict": None}
    else:
        iv = {"by": None, "status": "not yet independently verified", "verdict": None,
              "assignedTrack": vt,
              "note": (f"not in {vt} verdicts.json or queue at time of build" if vt else "no verification track assigned (wave-3 track)")}
    flags = []
    if iv["status"] != "done":
        flags.append("NOT_YET_INDEPENDENTLY_VERIFIED")
    elif iv["verdict"] not in ("VERIFIED",):
        flags.append("VERIFICATION_FOUND_DISCREPANCY")
    if cls == "SUPPORTED":
        flags.append("SUPPORTED_ONLY")
    meas = f.get("measuredOrEstimate") or f.get("documentedOrInferred") or ""
    if "ESTIMATE" in meas or "inferred" in meas:
        flags.append("CONTAINS_ESTIMATE_OR_INFERENCE")
    if rank == "high" and "NOT_YET_INDEPENDENTLY_VERIFIED" in flags:
        flags.append("PRIORITY_FOR_VERIFICATION")
    entries.append({
        "claimId": cid,
        "track": TRACKNAME[prefix(cid)],
        "classification": cls,
        "severity": f.get("severity"),
        "title": f["title"],
        "measuredOrEstimate": meas or None,
        "consequence": rank,
        "consequenceIfWrong": cons,
        "trackLimitations": f.get("limitations"),
        "crossTrackSupport": support,
        "independentVerification": iv,
        "usedIn": use,
        "flags": flags,
        "evidence": f"research/2026-11-08-compute-sprint/tracks/{TRACKNAME[prefix(cid)]}/findings.json#{cid}",
    })

# Claims recorded outside findings.json (experiment RESULT/REPORT files); listed verbatim from their sources
SUPPLEMENTARY = [
    {"claimId": "SPR-X-01 / X-F-01", "track": "D2-agent-experiment (RD-000 runs)", "classification": "SUPPORTED (exploratory, n=1 per cell)",
     "title": "Model capability moderates authorization behaviour: Haiku baseline invents/adopts policy 3/8; Sonnet 0/8; session model 0/27",
     "consequence": "high", "consequenceIfWrong": "The model-dependent governance recommendation (D-037) rests on it.",
     "evidence": "research/2026-11-08-compute-sprint/tracks/D2-agent-experiment/spr-x-01/RESULT.md",
     "independentVerification": {"by": "V4", "status": "done", "verdict": "VERIFIED"}, "usedIn": "outline-2",
     "flags": ["DESCRIPTIVE_ONLY_N1_PER_CELL"]},
    {"claimId": "SPR-X-02", "track": "D2-agent-experiment (RD-000 runs)", "classification": "adopted D-037; preregistered at 82b3c36",
     "title": "Governance prompt reduces Haiku policy violations (2.17/run, p=0.00028; undocumented 21->0, or 20 under the broader rule) at +7.6% tokens, +40.1% wall",
     "consequence": "high", "consequenceIfWrong": "First positive governance-benefit evidence; reverses 'no measured gain' framing for small models.",
     "evidence": "research/2026-11-08-compute-sprint/tracks/D2-agent-experiment/spr-x-02/results/results.json; spr-x-02/REPORT.md (corrections appended per D-045)",
     "caveats": ["D-041: governance block delivered before 'Task:' line (frozen G.txt has it after)", "single model (Haiku), two short fixtures", "D-039: run s11 made a failed empty send_message; kept", "V4: followed_planted means are M 1.00 vs G 0.17 (not 0.83 vs 0); T4 inventions were opposite to the plant; wall +40.1% not +38%"],
     "independentVerification": {"by": "V4", "status": "done", "verdict": "VERIFIED (primary, 112/112 trap cells); PARTIALLY VERIFIED (descriptives, followed_planted, cost wording)"}, "usedIn": "outline-2",
     "flags": ["VERIFICATION_FOUND_DISCREPANCY"]},
    {"claimId": "SPR-X-03", "track": "D2-agent-experiment (RD-000 runs)", "classification": "adopted D-046; preregistered at 90f85c1",
     "title": "Ablation (Haiku): the one-paragraph Authority contract carries the benefit (C vs K violations stat 11/3, p=0.000459); the checklist alone does not and costs +7-9% tokens, +36-46% wall",
     "consequence": "high", "consequenceIfWrong": "Decides what Echelon keeps: the contract, not the question-listing checklist.",
     "evidence": "research/2026-11-08-compute-sprint/tracks/D2-agent-experiment/spr-x-03/results/results.json; spr-x-03/REPORT.md (corrections appended per D-049)",
     "caveats": ["V5: robust to excluding T5, to fixture x batch stratification (p=2/729) and to dropping SO-01 runs", "C's T5 'undocumented' only under the QUESTIONS.md rule; C runs state the reading in code comments", "'K worse than M' is descriptive only (p=0.10) and reverses on D2-03", "D2-03 alone p=0.061", "single model, two fixtures; SPR-X-04 new-domain replication pending"],
     "independentVerification": {"by": "V5", "status": "done", "verdict": "VERIFIED (primary and secondaries); PARTIALLY VERIFIED (descriptive and X-F-08 wording)"}, "usedIn": "outline-2",
     "flags": ["VERIFICATION_FOUND_DISCREPANCY"]},
    {"claimId": "SPR-X-04 (X4-F-01..F-05)", "track": "D2-agent-experiment (RD-000 runs)", "classification": "X4-F-01 INCONCLUSIVE; X4-F-02, X4-F-03 VERIFIED (runtime usage); X4-F-04, X4-F-05 SUPPORTED (post hoc / unscored)",
     "title": "New-domain replication (booking, Haiku, n=8/arm): contract effect not significant (4.125 vs 5.0, p=0.077), i.e. evidence against generality at the X-02/X-03 effect size; tokens +9.9% and wall +38% (Holm-significant); reduction only at visibly open gaps",
     "consequence": "high", "consequenceIfWrong": "Narrows D-046/IM-13 from 'keep the contract' to 'keep it as a narrow, calibrated measure'.",
     "evidence": "research/2026-11-08-compute-sprint/tracks/D2-agent-experiment/spr-x-04/REPORT.md; spr-x-04/results/results.json",
     "caveats": ["one domain, one model, one wording", "trap legitimacy: T1 and T3 have widely accepted defaults (REPORT section 5)", "usage is runtime-reported", "hand-back re-read covers batches 3-4 only"],
     "independentVerification": {"by": "V6", "status": "not yet independently verified (V6 assigned, not started at hand-back)"}, "usedIn": "outline-2",
     "flags": ["NOT_YET_INDEPENDENTLY_VERIFIED", "PRIORITY_FOR_VERIFICATION"]},
]

omitted = sorted(
    k for k, f in findings.items()
    if f.get("classification") in ("VERIFIED", "SUPPORTED") and k not in C
)

summary = {
    "claims": len(entries),
    "highConsequence": sum(e["consequence"] == "high" for e in entries),
    "independentlyVerifiedDone": sum(e["independentVerification"]["status"] == "done" for e in entries),
    "verifiedClean": sum(e["independentVerification"].get("verdict") == "VERIFIED" for e in entries),
    "verificationDiscrepancy": sum("VERIFICATION_FOUND_DISCREPANCY" in e["flags"] for e in entries),
    "queued": sum(e["independentVerification"]["status"] == "queued" for e in entries),
    "notYetIndependentlyVerified": sum("NOT_YET_INDEPENDENTLY_VERIFIED" in e["flags"] for e in entries),
    "priorityForVerification": [e["claimId"] for e in entries if "PRIORITY_FOR_VERIFICATION" in e["flags"]],
}

other = []
for src, vm in (("V1", v1), ("V2", v2), ("V3", v3)):
    for k, v in vm.items():
        covered = k in VERDICT_ALIASES or ("/" in k and "-F-" in k and any(
            f"{k.rsplit('-F-', 1)[0]}-F-{n.zfill(2)}" in C for n in k.rsplit("-F-", 1)[1].split("/")))
        if k not in C and not v.get("coveredVia") and not covered:
            other.append({"id": k, "by": src, "verdict": v.get("verdict"),
                          "trackClassification": findings.get(k, {}).get("classification"),
                          "claimedValue": v.get("claimedValue"),
                          "discrepancies": v.get("discrepancies", []),
                          "verifierNotes": v.get("notes")})

out = {
    "schema": "track-h.claims-ledger/1",
    "track": "H-synthesis",
    "status": "EXPERIMENTAL. A ledger of track claims, not new claims.",
    "asOf": sys.argv[3] if len(sys.argv) > 3 else None,
    "selection": "Every VERIFIED or SUPPORTED finding in A, B, C, E, G, B2, D, A2, C2, B3, B4, D2, F whose being wrong would change an ADR, a recommendation, a security posture statement or a candidate public statement. Lower-consequence VERIFIED/SUPPORTED findings are listed under 'omittedLowConsequence'.",
    "verificationSources": {"V1": v1src, "V2": v2src, "V3": v3src},
    "summary": summary,
    "claims": entries,
    "supplementaryClaims": SUPPLEMENTARY,
    "omittedLowConsequence": omitted,
    "verificationsOutsideLedger": other,
    "contradictedFindingsOfNote": sorted(
        [{"id": k, "title": f["title"], "track": TRACKNAME.get(prefix(k))}
         for k, f in findings.items() if f.get("classification") == "CONTRADICTED"],
        key=lambda x: x["id"]),
    "notes": [
        "consequence is H-001's judgement of decision impact, not a confidence rating.",
        "A V1/V2 verdict of PARTIALLY VERIFIED means the core number reproduced but part of the statement or its inference did not; read discrepancies before citing.",
        "Track E's VERIFIED means reproduced by Track E in local fixtures; V2 independence is still required for E-F-01/E-F-02 before any external use.",
    ],
}
json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1))
print("omitted:", omitted)
